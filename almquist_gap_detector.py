#!/usr/bin/env python3
"""
ALMQUIST RAG - Gap Detector
Detekce mezer v RAG databázi pomocí clustering low-quality queries
"""

import sqlite3
import numpy as np
from sklearn.cluster import DBSCAN
from collections import Counter, defaultdict
import json
from datetime import datetime

class AlmquistGapDetector:
    """Detekuje gaps v RAG pokrytí pomocí ML clustering"""

    def __init__(self, db_path="/home/puzik/almquist_queries.db"):
        self.db_path = db_path

    def get_low_quality_queries(self, min_queries=50):
        """Získat low-quality queries pro clustering"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
        SELECT
            id, query_text, profession_id, query_embedding, best_score
        FROM queries
        WHERE
            (is_low_quality = 1 OR best_score < 0.4)
            AND query_embedding IS NOT NULL
        ORDER BY timestamp DESC
        LIMIT ?
        ''', (min_queries * 3,))  # Fetch more than needed

        rows = cursor.fetchall()
        conn.close()

        queries = []
        for row in rows:
            queries.append({
                'id': row[0],
                'text': row[1],
                'profession': row[2],
                'embedding': np.frombuffer(row[3], dtype=np.float32),
                'score': row[4]
            })

        return queries

    def cluster_queries(self, queries, eps=0.3, min_samples=3):
        """Cluster podobné dotazy pomocí DBSCAN"""
        if len(queries) < min_samples:
            print(f"⚠️  Málo dotazů pro clustering ({len(queries)} < {min_samples})")
            return []

        # Prepare embeddings matrix
        embeddings = np.array([q['embedding'] for q in queries])

        # DBSCAN clustering
        clustering = DBSCAN(eps=eps, min_samples=min_samples, metric='cosine').fit(embeddings)

        # Group queries by cluster
        clusters = defaultdict(list)
        for idx, label in enumerate(clustering.labels_):
            if label != -1:  # Ignore noise (-1)
                clusters[label].append(queries[idx])

        return list(clusters.values())

    def extract_topic(self, cluster_queries):
        """Extrahovat common topic z clusteru dotazů"""
        # Jednoduché extrahování klíčových slov
        # V produkci: použít LLM nebo NLP knihovnu

        all_text = " ".join([q['text'].lower() for q in cluster_queries])

        # Czech stopwords
        stopwords = {
            'jak', 'co', 'kde', 'kdy', 'kdo', 'jaký', 'který', 'musím',
            'mám', 'je', 'to', 'a', 'v', 'na', 'pro', 'se', 'za', 'z',
            'do', 'od', 'po', 'při', 'o', 's', 'u', 'k', 'mezi'
        }

        # Extract words
        words = all_text.split()
        words = [w for w in words if len(w) > 3 and w not in stopwords]

        # Count frequency
        word_freq = Counter(words)

        # Top keywords
        top_keywords = [word for word, freq in word_freq.most_common(5)]

        # Simple topic = top 3 keywords joined
        topic = " ".join(top_keywords[:3]) if top_keywords else "unknown topic"

        return topic

    def detect_gaps(self, min_queries_per_cluster=3):
        """Hlavní funkce - detekovat gaps"""
        print("\n🔍 ALMQUIST GAP DETECTOR")
        print("="*70)

        # 1. Get low quality queries
        print("\n1. Načítám low-quality dotazy...")
        queries = self.get_low_quality_queries()
        print(f"   ✓ Načteno {len(queries)} dotazů")

        if len(queries) < min_queries_per_cluster:
            print(f"   ⚠️  Málo dotazů pro analýzu (potřeba alespoň {min_queries_per_cluster})")
            return []

        # 2. Cluster queries
        print("\n2. Clusteruji podobné dotazy...")
        clusters = self.cluster_queries(queries, eps=0.3, min_samples=min_queries_per_cluster)
        print(f"   ✓ Nalezeno {len(clusters)} clusterů")

        # 3. Analyze each cluster
        print("\n3. Analyzuji clustery...")
        gaps = []

        for i, cluster in enumerate(clusters):
            # Extract topic
            topic = self.extract_topic(cluster)

            # Profession distribution
            profession_counts = Counter([q['profession'] for q in cluster if q['profession']])
            most_common_profession = profession_counts.most_common(1)[0][0] if profession_counts else None

            # Average score (how bad is retrieval)
            avg_score = np.mean([q['score'] for q in cluster if q['score']])

            # Query IDs
            query_ids = [q['id'] for q in cluster]

            gap = {
                'cluster_id': i,
                'topic': topic,
                'profession': most_common_profession,
                'query_count': len(cluster),
                'avg_score': avg_score,
                'query_ids': query_ids,
                'sample_queries': [q['text'] for q in cluster[:3]]  # Sample
            }

            gaps.append(gap)

            print(f"\n   Cluster {i}:")
            print(f"     Topic: {topic}")
            print(f"     Queries: {len(cluster)}")
            print(f"     Profession: {most_common_profession}")
            print(f"     Avg score: {avg_score:.3f}")
            print(f"     Samples:")
            for sq in gap['sample_queries']:
                print(f"       - {sq}")

        # 4. Prioritize gaps
        print("\n4. Prioritizuji gaps...")
        gaps_sorted = self.prioritize_gaps(gaps)

        # 5. Save to database
        print("\n5. Ukládám do databáze...")
        self.save_gaps(gaps_sorted)

        print("\n" + "="*70)
        print(f"✅ Detekováno {len(gaps_sorted)} gaps")

        return gaps_sorted

    def prioritize_gaps(self, gaps):
        """Prioritizovat gaps podle důležitosti"""
        for gap in gaps:
            # Priority score
            score = (
                gap['query_count'] * 10 +  # Frequency matters most
                (1 - gap['avg_score']) * 20 +  # Lower retrieval score = higher priority
                (5 if gap['profession'] else 0)  # Has profession = bonus
            )
            gap['priority_score'] = score

        # Sort by priority
        gaps_sorted = sorted(gaps, key=lambda x: x['priority_score'], reverse=True)

        return gaps_sorted

    def save_gaps(self, gaps):
        """Uložit gaps do databáze"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        for gap in gaps:
            cursor.execute('''
            INSERT INTO coverage_gaps (
                detected_at, topic_cluster, profession_id,
                query_count, avg_score, status
            ) VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                datetime.now(),
                gap['topic'],
                gap['profession'],
                gap['query_count'],
                gap['avg_score'],
                'detected'
            ))

        conn.commit()
        conn.close()

    def get_active_gaps(self):
        """Získat aktivní gaps"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute('''
        SELECT * FROM coverage_gaps
        WHERE status = 'detected'
        ORDER BY query_count DESC, avg_score ASC
        LIMIT 20
        ''')

        gaps = []
        for row in cursor.fetchall():
            gaps.append(dict(row))

        conn.close()
        return gaps

    def mark_gap_resolved(self, gap_id, chunk_id=None):
        """Označit gap jako vyřešený"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
        UPDATE coverage_gaps
        SET status = 'resolved',
            suggested_chunk_id = ?
        WHERE id = ?
        ''', (chunk_id, gap_id))

        conn.commit()
        conn.close()

    def generate_report(self):
        """Vygenerovat report gaps"""
        gaps = self.get_active_gaps()

        print("\n" + "="*70)
        print("📊 ALMQUIST RAG - COVERAGE GAPS REPORT")
        print("="*70)

        if not gaps:
            print("\n✅ Žádné aktivní gaps!")
            return

        print(f"\n🔍 Nalezeno {len(gaps)} aktivních gaps:\n")

        for i, gap in enumerate(gaps, 1):
            print(f"{i}. [{gap['profession_id'] or 'unknown'}] {gap['topic_cluster']}")
            print(f"   Queries: {gap['query_count']}")
            print(f"   Avg score: {gap['avg_score']:.3f}")
            print(f"   Status: {gap['status']}")
            print(f"   Detected: {gap['detected_at'][:10]}")
            print()

        print("="*70)


def main():
    """Hlavní funkce"""
    detector = AlmquistGapDetector()

    # Detect gaps
    gaps = detector.detect_gaps(min_queries_per_cluster=2)  # Low threshold for demo

    # Generate report
    detector.generate_report()

    # Save report to JSON
    if gaps:
        report_path = f"/home/puzik/detected_gaps_{datetime.now().strftime('%Y%m%d')}.json"
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(gaps, f, indent=2, ensure_ascii=False)
        print(f"\n💾 Report saved: {report_path}")


if __name__ == "__main__":
    main()
