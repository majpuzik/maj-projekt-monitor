#!/usr/bin/env python3
"""
ALMQUIST Legal RAG - Database Setup
Creates SQLite database for legal documents (laws & court decisions)
"""

import sqlite3
from pathlib import Path
from datetime import datetime

class LegalDatabaseSetup:
    """Setup legal sources database"""

    def __init__(self, db_path="/home/puzik/almquist_legal_sources.db"):
        self.db_path = db_path

    def create_database(self):
        """Create database with all tables"""
        print("=" * 70)
        print("🏛️  ALMQUIST LEGAL DATABASE SETUP")
        print("=" * 70)

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # 1. Laws table
        print("\n📜 Creating 'laws' table...")
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS laws (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            law_number TEXT NOT NULL UNIQUE,
            law_name TEXT NOT NULL,
            law_type TEXT,
            category TEXT,
            full_text TEXT,
            effective_from DATE,
            effective_to DATE,
            last_amendment TEXT,
            source_url TEXT,
            added_to_rag INTEGER DEFAULT 0,
            rag_chunk_ids TEXT,
            crawled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP
        )
        ''')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_laws_number ON laws(law_number)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_laws_category ON laws(category)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_laws_rag ON laws(added_to_rag)')
        print("   ✓ Laws table created with indexes")

        # 2. Court decisions table
        print("\n⚖️  Creating 'court_decisions' table...")
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS court_decisions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            case_number TEXT NOT NULL,
            court_level TEXT NOT NULL,
            court_name TEXT,
            decision_type TEXT,
            decision_date DATE,
            ecli TEXT UNIQUE,
            legal_area TEXT,
            affected_laws TEXT,
            keywords TEXT,
            summary TEXT,
            full_text TEXT,
            source_url TEXT,
            added_to_rag INTEGER DEFAULT 0,
            rag_chunk_ids TEXT,
            crawled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP
        )
        ''')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_decisions_case ON court_decisions(case_number)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_decisions_court ON court_decisions(court_level)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_decisions_ecli ON court_decisions(ecli)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_decisions_area ON court_decisions(legal_area)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_decisions_rag ON court_decisions(added_to_rag)')
        print("   ✓ Court decisions table created with indexes")

        # 3. Crawl history table
        print("\n📊 Creating 'crawl_history' table...")
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS crawl_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source TEXT NOT NULL,
            source_type TEXT NOT NULL,
            crawled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            status TEXT,
            items_found INTEGER DEFAULT 0,
            items_added INTEGER DEFAULT 0,
            error_message TEXT
        )
        ''')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_crawl_source ON crawl_history(source)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_crawl_type ON crawl_history(source_type)')
        print("   ✓ Crawl history table created with indexes")

        # 4. Content changes table
        print("\n🔄 Creating 'content_changes' table...")
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS content_changes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            document_type TEXT NOT NULL,
            document_id INTEGER NOT NULL,
            change_type TEXT,
            detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            old_hash TEXT,
            new_hash TEXT,
            significance TEXT
        )
        ''')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_changes_type ON content_changes(document_type)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_changes_docid ON content_changes(document_id)')
        print("   ✓ Content changes table created with indexes")

        # 5. Sources configuration table
        print("\n⚙️  Creating 'sources_config' table...")
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS sources_config (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source_name TEXT NOT NULL UNIQUE,
            source_type TEXT NOT NULL,
            base_url TEXT,
            api_key TEXT,
            enabled INTEGER DEFAULT 1,
            crawl_frequency TEXT,
            last_crawl TIMESTAMP,
            notes TEXT
        )
        ''')
        print("   ✓ Sources config table created")

        conn.commit()

        # Insert default sources
        print("\n🌐 Inserting default sources...")
        default_sources = [
            ('zakonyprolidi_api', 'law', 'https://www.zakonyprolidi.cz/api', None, 1, 'weekly', None, 'Primary law source - API access'),
            ('zakonyprolidi_web', 'law', 'https://www.zakonyprolidi.cz/cs/aktualni', None, 1, 'weekly', None, 'Backup law source - web scraping'),
            ('nsoud_sbirka', 'court_decision', 'https://sbirka.nsoud.cz', None, 1, 'daily', None, 'Nejvyšší soud - sbírka rozhodnutí'),
            ('usoud_nalus', 'court_decision', 'https://nalus.usoud.cz', None, 1, 'daily', None, 'Ústavní soud - databáze NALUS'),
            ('nssoud_vyhledavac', 'court_decision', 'https://vyhledavac.nssoud.cz', None, 1, 'daily', None, 'Nejvyšší správní soud - vyhledávač'),
            ('nssoud_sbirka', 'court_decision', 'https://sbirka.nssoud.cz', None, 1, 'daily', None, 'Nejvyšší správní soud - sbírka'),
        ]

        cursor.executemany('''
        INSERT OR IGNORE INTO sources_config
        (source_name, source_type, base_url, api_key, enabled, crawl_frequency, last_crawl, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', default_sources)

        conn.commit()
        print(f"   ✓ Inserted {len(default_sources)} default sources")

        # Summary
        print("\n" + "=" * 70)
        print("✅ DATABASE SETUP COMPLETE")
        print("=" * 70)
        print(f"Database: {self.db_path}")
        print("Tables created:")
        print("  • laws (zákony)")
        print("  • court_decisions (rozsudky)")
        print("  • crawl_history")
        print("  • content_changes")
        print("  • sources_config")
        print("\nReady for legal document crawling!")
        print("=" * 70)

        conn.close()

    def show_stats(self):
        """Show database statistics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        print("\n📊 Database Statistics:")

        # Laws
        cursor.execute('SELECT COUNT(*) FROM laws')
        law_count = cursor.fetchone()[0]
        cursor.execute('SELECT COUNT(*) FROM laws WHERE added_to_rag = 1')
        laws_in_rag = cursor.fetchone()[0]
        print(f"\n  Laws:")
        print(f"    Total: {law_count}")
        print(f"    In RAG: {laws_in_rag}")

        # Court decisions
        cursor.execute('SELECT COUNT(*) FROM court_decisions')
        decision_count = cursor.fetchone()[0]
        cursor.execute('SELECT COUNT(*) FROM court_decisions WHERE added_to_rag = 1')
        decisions_in_rag = cursor.fetchone()[0]
        print(f"\n  Court Decisions:")
        print(f"    Total: {decision_count}")
        print(f"    In RAG: {decisions_in_rag}")

        # By court level
        cursor.execute('''
        SELECT court_level, COUNT(*)
        FROM court_decisions
        GROUP BY court_level
        ''')
        court_stats = cursor.fetchall()
        if court_stats:
            print(f"\n    By court level:")
            for court, count in court_stats:
                print(f"      {court}: {count}")

        # Crawl history
        cursor.execute('SELECT COUNT(*) FROM crawl_history')
        crawl_count = cursor.fetchone()[0]
        print(f"\n  Crawl History: {crawl_count} runs")

        # Sources
        cursor.execute('SELECT COUNT(*) FROM sources_config WHERE enabled=1')
        enabled_sources = cursor.fetchone()[0]
        print(f"\n  Active Sources: {enabled_sources}")

        conn.close()


def main():
    """Main function"""
    setup = LegalDatabaseSetup()
    setup.create_database()
    setup.show_stats()


if __name__ == "__main__":
    main()
