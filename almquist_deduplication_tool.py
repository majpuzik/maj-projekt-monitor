#!/usr/bin/env python3
"""
ALMQUIST DEDUPLICATION TOOL
Odstranění duplicitních dokumentů z databáze a RAG systému

Funkcionalita:
- Detekce duplicit v SQLite databázi (podle ID i content hash)
- Vyčištění databáze (ponechá nejnovější verzi)
- Detekce duplicit v RAG metadata
- Vyčištění RAG (rebuild s deduplikovanými daty)
"""

import sqlite3
import json
import hashlib
import numpy as np
import faiss
from pathlib import Path
from datetime import datetime
from collections import defaultdict
import shutil


class AlmquistDeduplicator:
    """Deduplikace databáze a RAG systému"""

    def __init__(
        self,
        legal_db: str = "/home/puzik/almquist_legal_sources.db",
        rag_dir: str = "/home/puzik/almquist_legal_rag",
        backup_dir: str = "/home/puzik/almquist_rag_backups"
    ):
        self.legal_db = legal_db
        self.rag_dir = Path(rag_dir)
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(exist_ok=True)

    def compute_content_hash(self, text: str) -> str:
        """Compute SHA256 hash of text content"""
        return hashlib.sha256(text.encode('utf-8')).hexdigest()

    def analyze_db_duplicates(self):
        """Analyze duplicates in database"""
        print("\n" + "="*70)
        print("🔍 ANALYZING DATABASE DUPLICATES")
        print("="*70)

        conn = sqlite3.connect(self.legal_db)
        cursor = conn.cursor()

        # Check laws
        cursor.execute("""
            SELECT COUNT(*) as total, COUNT(DISTINCT law_number) as unique_laws
            FROM laws WHERE full_text IS NOT NULL
        """)
        total_laws, unique_laws = cursor.fetchone()
        law_duplicates = total_laws - unique_laws

        print(f"\n📋 LAWS:")
        print(f"   Total: {total_laws}")
        print(f"   Unique: {unique_laws}")
        print(f"   Duplicates: {law_duplicates}")

        if law_duplicates > 0:
            cursor.execute("""
                SELECT law_number, COUNT(*) as cnt
                FROM laws WHERE full_text IS NOT NULL
                GROUP BY law_number HAVING cnt > 1
                ORDER BY cnt DESC LIMIT 5
            """)
            print(f"\n   Top duplicates:")
            for law_num, cnt in cursor.fetchall():
                print(f"      {law_num}: {cnt} copies")

        # Check court decisions
        cursor.execute("""
            SELECT COUNT(*) as total, COUNT(DISTINCT case_number) as unique_cases
            FROM court_decisions WHERE full_text IS NOT NULL
        """)
        total_cases, unique_cases = cursor.fetchone()
        case_duplicates = total_cases - unique_cases

        print(f"\n⚖️  COURT DECISIONS:")
        print(f"   Total: {total_cases}")
        print(f"   Unique: {unique_cases}")
        print(f"   Duplicates: {case_duplicates}")

        if case_duplicates > 0:
            cursor.execute("""
                SELECT case_number, COUNT(*) as cnt
                FROM court_decisions WHERE full_text IS NOT NULL
                GROUP BY case_number HAVING cnt > 1
                ORDER BY cnt DESC LIMIT 5
            """)
            print(f"\n   Top duplicates:")
            for case_num, cnt in cursor.fetchall():
                print(f"      {case_num}: {cnt} copies")

        # Check content-based duplicates (hash)
        print(f"\n🔐 CONTENT HASH ANALYSIS:")
        print(f"   Computing hashes for court decisions...")

        cursor.execute("""
            SELECT id, case_number, full_text, crawled_at
            FROM court_decisions WHERE full_text IS NOT NULL
        """)

        hash_to_records = defaultdict(list)
        for row in cursor.fetchall():
            doc_id, case_num, text, crawled = row
            content_hash = self.compute_content_hash(text)
            hash_to_records[content_hash].append({
                'id': doc_id,
                'case_number': case_num,
                'crawled_at': crawled
            })

        content_duplicates = sum(1 for records in hash_to_records.values() if len(records) > 1)
        total_duplicate_records = sum(len(records) - 1 for records in hash_to_records.values() if len(records) > 1)

        print(f"   Unique content hashes: {len(hash_to_records)}")
        print(f"   Content duplicates: {content_duplicates} groups")
        print(f"   Total duplicate records: {total_duplicate_records}")

        conn.close()

        print("\n" + "="*70)
        print("✅ ANALYSIS COMPLETE")
        print("="*70)

        return {
            'law_duplicates': law_duplicates,
            'case_duplicates': case_duplicates,
            'content_duplicates': total_duplicate_records
        }

    def deduplicate_database(self, dry_run=True):
        """Remove duplicates from database"""
        print("\n" + "="*70)
        print("🧹 DATABASE DEDUPLICATION")
        print("="*70)
        print(f"Mode: {'DRY RUN (no changes)' if dry_run else 'LIVE (will modify DB)'}")
        print("="*70)

        if not dry_run:
            # Backup database
            backup_path = self.backup_dir / f"legal_db_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
            print(f"\n📦 Creating database backup: {backup_path}")
            shutil.copy2(self.legal_db, backup_path)
            print(f"   ✓ Backup created")

        conn = sqlite3.connect(self.legal_db)
        cursor = conn.cursor()

        # Deduplicate court decisions by case_number (keep newest)
        print(f"\n⚖️  Deduplicating court decisions...")

        cursor.execute("""
            SELECT case_number, COUNT(*) as cnt
            FROM court_decisions WHERE full_text IS NOT NULL
            GROUP BY case_number HAVING cnt > 1
        """)

        duplicate_cases = cursor.fetchall()
        print(f"   Found {len(duplicate_cases)} case numbers with duplicates")

        removed_count = 0
        for case_num, cnt in duplicate_cases:
            # Get all records for this case_number, ordered by crawled_at DESC
            cursor.execute("""
                SELECT id, crawled_at FROM court_decisions
                WHERE case_number = ? AND full_text IS NOT NULL
                ORDER BY crawled_at DESC
            """, (case_num,))

            records = cursor.fetchall()
            if len(records) <= 1:
                continue

            # Keep first (newest), remove rest
            keep_id = records[0][0]
            remove_ids = [r[0] for r in records[1:]]

            print(f"   {case_num}: keeping ID {keep_id}, removing {len(remove_ids)} duplicates")

            if not dry_run:
                cursor.execute(f"""
                    DELETE FROM court_decisions
                    WHERE id IN ({','.join('?' * len(remove_ids))})
                """, remove_ids)
                removed_count += len(remove_ids)

        # Deduplicate by content hash
        print(f"\n🔐 Deduplicating by content hash...")

        cursor.execute("""
            SELECT id, case_number, full_text, crawled_at
            FROM court_decisions WHERE full_text IS NOT NULL
        """)

        hash_to_records = defaultdict(list)
        for row in cursor.fetchall():
            doc_id, case_num, text, crawled = row
            content_hash = self.compute_content_hash(text)
            hash_to_records[content_hash].append({
                'id': doc_id,
                'case_number': case_num,
                'crawled_at': crawled
            })

        hash_removed_count = 0
        for content_hash, records in hash_to_records.items():
            if len(records) <= 1:
                continue

            # Sort by crawled_at (newest first)
            records.sort(key=lambda x: x['crawled_at'] or '', reverse=True)

            keep_id = records[0]['id']
            remove_ids = [r['id'] for r in records[1:]]

            print(f"   Hash {content_hash[:16]}...: keeping ID {keep_id}, removing {len(remove_ids)}")

            if not dry_run:
                cursor.execute(f"""
                    DELETE FROM court_decisions
                    WHERE id IN ({','.join('?' * len(remove_ids))})
                """, remove_ids)
                hash_removed_count += len(remove_ids)

        if not dry_run:
            conn.commit()
            print(f"\n✅ Removed {removed_count + hash_removed_count} duplicate records")
        else:
            print(f"\n🔍 Would remove {removed_count + hash_removed_count} duplicate records")

        conn.close()

        print("\n" + "="*70)
        print("✅ DATABASE DEDUPLICATION COMPLETE")
        print("="*70)

    def analyze_rag_duplicates(self):
        """Analyze duplicates in RAG metadata"""
        print("\n" + "="*70)
        print("🔍 ANALYZING RAG DUPLICATES")
        print("="*70)

        metadata_path = self.rag_dir / "metadata.json"

        if not metadata_path.exists():
            print("   ❌ RAG metadata not found")
            return

        with open(metadata_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            metadata = data['metadata']

        print(f"\n📊 RAG Stats:")
        print(f"   Total chunks: {len(metadata)}")

        # Check for duplicate chunk_ids
        chunk_ids = [m['chunk_id'] for m in metadata]
        unique_chunk_ids = set(chunk_ids)

        print(f"   Unique chunk IDs: {len(unique_chunk_ids)}")
        print(f"   Duplicate chunk IDs: {len(chunk_ids) - len(unique_chunk_ids)}")

        # Check for duplicate source documents
        law_numbers = set()
        case_numbers = set()

        for m in metadata:
            if m['document_type'] == 'law':
                law_numbers.add(m.get('law_number'))
            elif m['document_type'] == 'court_decision':
                case_numbers.add(m.get('case_number'))

        print(f"\n📋 Source documents in RAG:")
        print(f"   Unique laws: {len(law_numbers)}")
        print(f"   Unique court decisions: {len(case_numbers)}")

        print("\n" + "="*70)
        print("✅ RAG ANALYSIS COMPLETE")
        print("="*70)

    def vacuum_database(self):
        """Vacuum database to reclaim space after deletion"""
        print("\n🗜️  Vacuuming database to reclaim space...")

        conn = sqlite3.connect(self.legal_db)
        conn.execute("VACUUM")
        conn.close()

        print("   ✓ Database vacuumed")


def main():
    """Main function"""
    import argparse

    parser = argparse.ArgumentParser(
        description='Almquist Deduplication Tool',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Analyze duplicates (read-only)
  python3 almquist_deduplication_tool.py --analyze

  # Deduplicate database (dry-run)
  python3 almquist_deduplication_tool.py --deduplicate-db --dry-run

  # Deduplicate database (live)
  python3 almquist_deduplication_tool.py --deduplicate-db

  # Analyze RAG duplicates
  python3 almquist_deduplication_tool.py --analyze-rag

  # Full cleanup (analyze + deduplicate + vacuum)
  python3 almquist_deduplication_tool.py --full-cleanup
        """
    )

    parser.add_argument('--analyze', action='store_true',
                        help='Analyze database for duplicates')
    parser.add_argument('--deduplicate-db', action='store_true',
                        help='Deduplicate database')
    parser.add_argument('--analyze-rag', action='store_true',
                        help='Analyze RAG for duplicates')
    parser.add_argument('--dry-run', action='store_true',
                        help='Dry run (show what would be done)')
    parser.add_argument('--full-cleanup', action='store_true',
                        help='Full cleanup (analyze + deduplicate + vacuum)')
    parser.add_argument('--vacuum', action='store_true',
                        help='Vacuum database to reclaim space')

    args = parser.parse_args()

    deduplicator = AlmquistDeduplicator()

    if args.full_cleanup:
        deduplicator.analyze_db_duplicates()
        deduplicator.deduplicate_database(dry_run=False)
        deduplicator.vacuum_database()
        deduplicator.analyze_db_duplicates()  # Re-analyze to confirm
    elif args.analyze:
        deduplicator.analyze_db_duplicates()
    elif args.deduplicate_db:
        deduplicator.deduplicate_database(dry_run=args.dry_run)
        if not args.dry_run and args.vacuum:
            deduplicator.vacuum_database()
    elif args.analyze_rag:
        deduplicator.analyze_rag_duplicates()
    elif args.vacuum:
        deduplicator.vacuum_database()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
