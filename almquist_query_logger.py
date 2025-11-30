#!/usr/bin/env python3
"""
ALMQUIST RAG - Query Logger
Logování všech uživatelských dotazů, RAG retrievals a user feedback
Pro self-learning systém
"""

import sqlite3
import json
from datetime import datetime
from pathlib import Path
import numpy as np
from sentence_transformers import SentenceTransformer

class AlmquistQueryLogger:
    """Logger pro všechny uživatelské dotazy a feedback"""

    def __init__(self, db_path="/home/puzik/almquist_queries.db"):
        self.db_path = db_path
        self.init_database()

        # Model pro embedding queries (same as RAG)
        self.model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')

    def init_database(self):
        """Inicializace databáze"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Queries table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS queries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            session_id TEXT,
            user_id TEXT,
            profession_id TEXT,
            query_text TEXT NOT NULL,
            query_embedding BLOB,

            -- RAG retrieval
            top_chunks_ids TEXT,
            top_chunks_scores TEXT,
            best_score REAL,

            -- LLM response
            response_text TEXT,
            response_time_ms INTEGER,

            -- User feedback
            feedback_type TEXT,
            feedback_value INTEGER,
            feedback_comment TEXT,
            follow_up_query_id INTEGER,

            -- Flags
            is_answered BOOLEAN DEFAULT 1,
            needs_review BOOLEAN DEFAULT 0,
            is_low_quality BOOLEAN DEFAULT 0
        )
        ''')

        # Coverage gaps table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS coverage_gaps (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            detected_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            topic_cluster TEXT,
            profession_id TEXT,
            query_count INTEGER,
            avg_score REAL,
            status TEXT DEFAULT 'detected',
            suggested_chunk_id INTEGER
        )
        ''')

        # Suggested chunks table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS suggested_chunks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            topic TEXT,
            profession_id TEXT,
            chunk_type TEXT,

            source_query_ids TEXT,
            suggested_text TEXT,
            confidence_score REAL,
            external_sources TEXT,

            status TEXT DEFAULT 'pending',
            reviewed_by TEXT,
            reviewed_at DATETIME,
            final_text TEXT,

            integrated_at DATETIME,
            chunk_id TEXT
        )
        ''')

        # External sources table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS external_sources (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source_type TEXT,
            source_url TEXT,
            scraped_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            content TEXT,
            keywords TEXT,
            relevance_score REAL,
            processed BOOLEAN DEFAULT 0
        )
        ''')

        conn.commit()
        conn.close()

    def log_query(self, query_text, session_id=None, user_id=None, profession_id=None):
        """Zalogovat uživatelský dotaz"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Embedovat query
        query_embedding = self.model.encode([query_text], normalize_embeddings=True)[0]

        cursor.execute('''
        INSERT INTO queries (
            timestamp, session_id, user_id, profession_id,
            query_text, query_embedding
        ) VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            datetime.now(),
            session_id,
            user_id,
            profession_id,
            query_text,
            query_embedding.tobytes()
        ))

        query_id = cursor.lastrowid
        conn.commit()
        conn.close()

        return query_id

    def log_retrieval(self, query_id, chunks_ids, chunks_scores):
        """Zalogovat RAG retrieval results"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        best_score = max(chunks_scores) if chunks_scores else 0.0

        cursor.execute('''
        UPDATE queries
        SET top_chunks_ids = ?,
            top_chunks_scores = ?,
            best_score = ?
        WHERE id = ?
        ''', (
            json.dumps(chunks_ids),
            json.dumps(chunks_scores),
            best_score,
            query_id
        ))

        conn.commit()
        conn.close()

    def log_response(self, query_id, response_text, response_time_ms):
        """Zalogovat LLM odpověď"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
        UPDATE queries
        SET response_text = ?,
            response_time_ms = ?
        WHERE id = ?
        ''', (
            response_text,
            response_time_ms,
            query_id
        ))

        conn.commit()
        conn.close()

    def log_feedback(self, query_id, feedback_type, feedback_value=None, comment=None):
        """Zalogovat user feedback"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Určit jestli je to low quality na základě feedbacku
        is_low_quality = (
            (feedback_type == 'thumbs_down') or
            (feedback_type == 'rating' and feedback_value <= 2)
        )

        cursor.execute('''
        UPDATE queries
        SET feedback_type = ?,
            feedback_value = ?,
            feedback_comment = ?,
            is_low_quality = ?,
            needs_review = ?
        WHERE id = ?
        ''', (
            feedback_type,
            feedback_value,
            comment,
            is_low_quality,
            is_low_quality,  # needs_review if low quality
            query_id
        ))

        conn.commit()
        conn.close()

    def log_follow_up(self, original_query_id, follow_up_query_id):
        """Zalogovat follow-up dotaz"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
        UPDATE queries
        SET follow_up_query_id = ?
        WHERE id = ?
        ''', (
            follow_up_query_id,
            original_query_id
        ))

        # Original query pravděpodobně neodpověděl dobře → needs review
        cursor.execute('''
        UPDATE queries
        SET needs_review = 1
        WHERE id = ?
        ''', (original_query_id,))

        conn.commit()
        conn.close()

    def get_stats(self, days=7):
        """Získat statistiky za posledních N dní"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        stats = {}

        # Total queries
        cursor.execute('''
        SELECT COUNT(*) FROM queries
        WHERE timestamp >= datetime('now', '-' || ? || ' days')
        ''', (days,))
        stats['total_queries'] = cursor.fetchone()[0]

        # Average best score
        cursor.execute('''
        SELECT AVG(best_score) FROM queries
        WHERE timestamp >= datetime('now', '-' || ? || ' days')
        AND best_score IS NOT NULL
        ''', (days,))
        stats['avg_best_score'] = cursor.fetchone()[0] or 0.0

        # Low quality queries
        cursor.execute('''
        SELECT COUNT(*) FROM queries
        WHERE timestamp >= datetime('now', '-' || ? || ' days')
        AND is_low_quality = 1
        ''', (days,))
        stats['low_quality_count'] = cursor.fetchone()[0]

        # Thumbs up/down ratio
        cursor.execute('''
        SELECT
            SUM(CASE WHEN feedback_type = 'thumbs_up' THEN 1 ELSE 0 END) as thumbs_up,
            SUM(CASE WHEN feedback_type = 'thumbs_down' THEN 1 ELSE 0 END) as thumbs_down
        FROM queries
        WHERE timestamp >= datetime('now', '-' || ? || ' days')
        ''', (days,))
        row = cursor.fetchone()
        stats['thumbs_up'] = row[0] or 0
        stats['thumbs_down'] = row[1] or 0

        if stats['thumbs_up'] + stats['thumbs_down'] > 0:
            stats['thumbs_up_rate'] = stats['thumbs_up'] / (stats['thumbs_up'] + stats['thumbs_down'])
        else:
            stats['thumbs_up_rate'] = 0.0

        # Average rating
        cursor.execute('''
        SELECT AVG(feedback_value) FROM queries
        WHERE timestamp >= datetime('now', '-' || ? || ' days')
        AND feedback_type = 'rating'
        AND feedback_value IS NOT NULL
        ''', (days,))
        stats['avg_rating'] = cursor.fetchone()[0] or 0.0

        # Queries by profession
        cursor.execute('''
        SELECT profession_id, COUNT(*) as cnt
        FROM queries
        WHERE timestamp >= datetime('now', '-' || ? || ' days')
        AND profession_id IS NOT NULL
        GROUP BY profession_id
        ORDER BY cnt DESC
        ''', (days,))
        stats['by_profession'] = {row[0]: row[1] for row in cursor.fetchall()}

        conn.close()
        return stats

    def get_low_quality_queries(self, limit=100):
        """Získat low-quality dotazy pro gap detection"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute('''
        SELECT
            id, query_text, profession_id, query_embedding,
            best_score, feedback_type, feedback_value
        FROM queries
        WHERE
            (is_low_quality = 1 OR best_score < 0.4)
            AND query_embedding IS NOT NULL
        ORDER BY timestamp DESC
        LIMIT ?
        ''', (limit,))

        queries = []
        for row in cursor.fetchall():
            queries.append({
                'id': row['id'],
                'query_text': row['query_text'],
                'profession_id': row['profession_id'],
                'embedding': np.frombuffer(row['query_embedding'], dtype=np.float32),
                'best_score': row['best_score'],
                'feedback_type': row['feedback_type'],
                'feedback_value': row['feedback_value']
            })

        conn.close()
        return queries

    def mark_as_reviewed(self, query_id):
        """Označit query jako reviewed"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
        UPDATE queries
        SET needs_review = 0
        WHERE id = ?
        ''', (query_id,))

        conn.commit()
        conn.close()


def main():
    """Demo použití"""
    logger = AlmquistQueryLogger()

    # Simulace query logging
    print("📝 Logování demo dotazů...")

    # Query 1
    query_id = logger.log_query(
        "Jak si založit živnost?",
        session_id="sess_123",
        user_id="user_456",
        profession_id="zivnostnik_obecny"
    )
    print(f"   Query ID: {query_id}")

    # Simulace retrieval
    logger.log_retrieval(query_id, chunks_ids=[1, 5, 12], chunks_scores=[0.78, 0.65, 0.52])

    # Simulace response
    logger.log_response(query_id, "Pro založení živnosti...", response_time_ms=1234)

    # Simulace feedbacku
    logger.log_feedback(query_id, "thumbs_up")

    # Query 2 - low quality
    query_id2 = logger.log_query(
        "Musím platit EET jako lékař?",
        profession_id="soukromy_lekar"
    )
    logger.log_retrieval(query_id2, chunks_ids=[3, 7], chunks_scores=[0.32, 0.28])  # Low scores
    logger.log_feedback(query_id2, "thumbs_down", comment="Neodbovědělo to na mou otázku")

    # Stats
    print("\n📊 Statistiky:")
    stats = logger.get_stats(days=30)

    print(f"   Total queries: {stats['total_queries']}")
    print(f"   Avg retrieval score: {stats['avg_best_score']:.3f}")
    print(f"   Low quality queries: {stats['low_quality_count']}")
    print(f"   Thumbs up rate: {stats['thumbs_up_rate']*100:.1f}%")
    print(f"   Avg rating: {stats['avg_rating']:.2f}/5")

    if stats['by_profession']:
        print("\n   By profession:")
        for prof, count in stats['by_profession'].items():
            print(f"     {prof}: {count}")

    # Low quality queries
    print("\n🔍 Low quality queries:")
    low_q = logger.get_low_quality_queries(limit=10)
    for q in low_q:
        print(f"   ID {q['id']}: '{q['query_text']}' (score: {q['best_score']:.2f})")

    print(f"\n✅ Database: {logger.db_path}")


if __name__ == "__main__":
    main()
