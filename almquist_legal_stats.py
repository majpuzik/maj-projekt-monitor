#!/usr/bin/env python3
"""
ALMQUIST Legal RAG - Statistics & Monitoring
Comprehensive stats and reporting for legal RAG system
"""

import sqlite3
import json
import numpy as np
from pathlib import Path
from datetime import datetime
import sys

class LegalRAGStats:
    """Statistics and monitoring for Legal RAG"""

    def __init__(self,
                 legal_db="/home/puzik/almquist_legal_sources.db",
                 rag_dir="/home/puzik/almquist_legal_rag"):
        self.legal_db = legal_db
        self.rag_dir = Path(rag_dir)

    def get_database_stats(self):
        """Get comprehensive database statistics"""
        conn = sqlite3.connect(self.legal_db)
        cursor = conn.cursor()

        stats = {}

        # Laws stats
        cursor.execute('SELECT COUNT(*) FROM laws')
        stats['total_laws'] = cursor.fetchone()[0]

        cursor.execute('SELECT COUNT(*) FROM laws WHERE added_to_rag = 1')
        stats['laws_in_rag'] = cursor.fetchone()[0]

        cursor.execute('''
        SELECT category, COUNT(*)
        FROM laws
        GROUP BY category
        ORDER BY COUNT(*) DESC
        ''')
        stats['laws_by_category'] = cursor.fetchall()

        # Court decisions stats
        cursor.execute('SELECT COUNT(*) FROM court_decisions')
        stats['total_decisions'] = cursor.fetchone()[0]

        cursor.execute('SELECT COUNT(*) FROM court_decisions WHERE added_to_rag = 1')
        stats['decisions_in_rag'] = cursor.fetchone()[0]

        cursor.execute('''
        SELECT court_level, COUNT(*)
        FROM court_decisions
        GROUP BY court_level
        ORDER BY COUNT(*) DESC
        ''')
        stats['decisions_by_court'] = cursor.fetchall()

        cursor.execute('''
        SELECT decision_type, COUNT(*)
        FROM court_decisions
        GROUP BY decision_type
        ORDER BY COUNT(*) DESC
        ''')
        stats['decisions_by_type'] = cursor.fetchall()

        # Crawl history
        cursor.execute('''
        SELECT source, COUNT(*), SUM(items_added), MAX(crawled_at)
        FROM crawl_history
        GROUP BY source
        ORDER BY MAX(crawled_at) DESC
        ''')
        stats['crawl_history'] = cursor.fetchall()

        conn.close()

        return stats

    def get_rag_stats(self):
        """Get RAG system statistics"""
        stats = {}

        # Load metadata
        metadata_path = self.rag_dir / "metadata.json"
        if metadata_path.exists():
            with open(metadata_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            stats['total_chunks'] = data.get('total_chunks', 0)
            stats['last_updated'] = data.get('updated_at', 'Unknown')

            # Count by document type
            metadata = data.get('metadata', [])
            by_type = {}
            by_category = {}
            by_court = {}

            for meta in metadata:
                doc_type = meta.get('document_type', 'unknown')
                by_type[doc_type] = by_type.get(doc_type, 0) + 1

                if doc_type == 'law':
                    cat = meta.get('category', 'unknown')
                    by_category[cat] = by_category.get(cat, 0) + 1
                elif doc_type == 'court_decision':
                    court = meta.get('court_level', 'unknown')
                    by_court[court] = by_court.get(court, 0) + 1

            stats['chunks_by_type'] = list(by_type.items())
            stats['chunks_by_category'] = list(by_category.items())
            stats['chunks_by_court'] = list(by_court.items())

        # Embeddings stats
        embeddings_path = self.rag_dir / "embeddings.npy"
        if embeddings_path.exists():
            embeddings = np.load(embeddings_path)
            stats['embeddings_shape'] = embeddings.shape
            stats['embeddings_size_mb'] = embeddings.nbytes / 1024 / 1024

        return stats

    def print_report(self):
        """Print comprehensive statistics report"""
        print("=" * 70)
        print("📊 ALMQUIST LEGAL RAG - COMPREHENSIVE STATISTICS")
        print("=" * 70)
        print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        # Database stats
        db_stats = self.get_database_stats()

        print("\n" + "─" * 70)
        print("📚 LAWS DATABASE")
        print("─" * 70)
        print(f"Total laws:           {db_stats['total_laws']}")
        print(f"Laws in RAG:          {db_stats['laws_in_rag']} ({db_stats['laws_in_rag']/max(db_stats['total_laws'],1)*100:.1f}%)")

        if db_stats['laws_by_category']:
            print("\nLaws by category:")
            for cat, count in db_stats['laws_by_category']:
                print(f"  {cat:25s}: {count:3d}")

        print("\n" + "─" * 70)
        print("⚖️  COURT DECISIONS DATABASE")
        print("─" * 70)
        print(f"Total decisions:      {db_stats['total_decisions']}")
        print(f"Decisions in RAG:     {db_stats['decisions_in_rag']} ({db_stats['decisions_in_rag']/max(db_stats['total_decisions'],1)*100:.1f}%)")

        if db_stats['decisions_by_court']:
            print("\nDecisions by court:")
            for court, count in db_stats['decisions_by_court']:
                print(f"  {court:25s}: {count:3d}")

        if db_stats['decisions_by_type']:
            print("\nDecisions by type:")
            for dtype, count in db_stats['decisions_by_type']:
                dtype_str = dtype if dtype else 'unknown'
                print(f"  {dtype_str:25s}: {count:3d}")

        # RAG stats
        rag_stats = self.get_rag_stats()

        print("\n" + "─" * 70)
        print("🤖 RAG SYSTEM")
        print("─" * 70)
        print(f"Total chunks:         {rag_stats.get('total_chunks', 0)}")
        print(f"Last updated:         {rag_stats.get('last_updated', 'Unknown')}")

        if 'embeddings_shape' in rag_stats:
            print(f"Embeddings shape:     {rag_stats['embeddings_shape']}")
            print(f"Embeddings size:      {rag_stats['embeddings_size_mb']:.1f} MB")

        if rag_stats.get('chunks_by_type'):
            print("\nChunks by document type:")
            for dtype, count in rag_stats['chunks_by_type']:
                print(f"  {dtype:25s}: {count:4d}")

        if rag_stats.get('chunks_by_category'):
            print("\nLaw chunks by category:")
            for cat, count in sorted(rag_stats['chunks_by_category'], key=lambda x: x[1], reverse=True):
                print(f"  {cat:25s}: {count:4d}")

        if rag_stats.get('chunks_by_court'):
            print("\nDecision chunks by court:")
            for court, count in rag_stats['chunks_by_court']:
                print(f"  {court:25s}: {count:4d}")

        # Crawl history
        print("\n" + "─" * 70)
        print("📡 CRAWL HISTORY")
        print("─" * 70)
        if db_stats['crawl_history']:
            print(f"{'Source':30s} {'Runs':>6s} {'Added':>7s} {'Last Crawl':20s}")
            print("─" * 70)
            for source, runs, added, last_crawl in db_stats['crawl_history']:
                added_str = str(added) if added else '0'
                print(f"{source:30s} {runs:6d} {added_str:>7s} {str(last_crawl)[:19]:20s}")

        # Summary
        print("\n" + "=" * 70)
        print("✅ SUMMARY")
        print("=" * 70)
        print(f"Total documents:      {db_stats['total_laws'] + db_stats['total_decisions']}")
        print(f"Total RAG chunks:     {rag_stats.get('total_chunks', 0)}")
        print(f"Coverage:             {db_stats['laws_in_rag']} laws + {db_stats['decisions_in_rag']} decisions")
        print("=" * 70)

    def get_health_check(self):
        """Health check - returns issues if any"""
        issues = []

        # Check database exists
        if not Path(self.legal_db).exists():
            issues.append("❌ Legal database not found")

        # Check RAG directory
        if not self.rag_dir.exists():
            issues.append("❌ RAG directory not found")

        # Check FAISS index
        if not (self.rag_dir / "faiss_index.bin").exists():
            issues.append("❌ FAISS index not found")

        # Check metadata
        if not (self.rag_dir / "metadata.json").exists():
            issues.append("❌ RAG metadata not found")

        # Check embeddings
        if not (self.rag_dir / "embeddings.npy").exists():
            issues.append("❌ Embeddings file not found")

        # Check database contents
        db_stats = self.get_database_stats()
        if db_stats['total_laws'] == 0:
            issues.append("⚠️  No laws in database")
        if db_stats['laws_in_rag'] < db_stats['total_laws']:
            issues.append(f"⚠️  {db_stats['total_laws'] - db_stats['laws_in_rag']} laws not yet in RAG")
        if db_stats['total_decisions'] == 0:
            issues.append("⚠️  No court decisions in database")
        if db_stats['decisions_in_rag'] < db_stats['total_decisions']:
            issues.append(f"⚠️  {db_stats['total_decisions'] - db_stats['decisions_in_rag']} decisions not yet in RAG")

        return issues


def main():
    """Main function"""
    stats = LegalRAGStats()

    # Print comprehensive report
    stats.print_report()

    # Health check
    print("\n" + "=" * 70)
    print("🏥 HEALTH CHECK")
    print("=" * 70)
    issues = stats.get_health_check()
    if issues:
        for issue in issues:
            print(issue)
    else:
        print("✅ All systems operational")
    print("=" * 70)


if __name__ == "__main__":
    main()
