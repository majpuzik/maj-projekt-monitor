#!/usr/bin/env python3
"""
ALMQUIST Import Constitutional Court Dataset (Zenodo 2024)
Imports 96,271 decisions from Czech Constitutional Court (1993-2023)
Source: https://zenodo.org/records/11618008
"""

import sqlite3
import csv
import json
from datetime import datetime
import sys

# Increase CSV field size limit for large text fields
csv.field_size_limit(sys.maxsize)

class ConstitutionalCourtImporter:
    """Import Czech Constitutional Court dataset into Almquist DB"""

    def __init__(self, db_path="/home/puzik/almquist_legal_sources.db"):
        self.db_path = db_path
        self.csv_path_metadata = "ccc_database/csv/ccc_metadata.csv"
        self.csv_path_texts = "ccc_database/csv/ccc_texts.csv"

    def init_database(self):
        """Ensure court_decisions table exists"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Check if source column exists, if not add it
        cursor.execute("PRAGMA table_info(court_decisions)")
        columns = [col[1] for col in cursor.fetchall()]

        if 'source' not in columns:
            print("Adding 'source' column to court_decisions table")
            cursor.execute('ALTER TABLE court_decisions ADD COLUMN source TEXT')
            conn.commit()

        conn.close()

    def load_texts(self):
        """Load all texts into memory dictionary (doc_id -> text)"""
        print("📖 Loading texts from CSV...")
        texts = {}

        with open(self.csv_path_texts, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            count = 0
            for row in reader:
                doc_id = row['doc_id']
                text = row['text']
                texts[doc_id] = text
                count += 1

                if count % 10000 == 0:
                    print(f"   Loaded {count:,} texts...")

        print(f"✓ Loaded {len(texts):,} texts into memory")
        return texts

    def import_decisions(self):
        """Import all decisions with texts"""
        print("🚀 Starting Constitutional Court import")
        print("=" * 60)

        self.init_database()

        # Load texts first
        texts_dict = self.load_texts()

        print("\n📊 Importing decisions...")

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        imported = 0
        skipped = 0
        errors = 0

        with open(self.csv_path_metadata, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)

            for idx, row in enumerate(reader, 1):
                if idx % 1000 == 0:
                    print(f"   Processed {idx:,} / 96,271 - Imported: {imported:,}, Skipped: {skipped:,}")

                try:
                    doc_id = row['doc_id']  # ECLI - use as unique ID
                    case_number = row['case_id']  # Real case ID (e.g., "Pl.ÚS 43/23")
                    decision_date = row['date_decision'] if row['date_decision'] != 'NA' else None

                    # Get full text
                    full_text = texts_dict.get(doc_id, '')

                    # Build summary from metadata
                    summary_parts = []
                    if row.get('type_decision'):
                        summary_parts.append(f"Typ: {row['type_decision']}")
                    if row.get('type_proceedings'):
                        summary_parts.append(f"Řízení: {row['type_proceedings']}")
                    if row.get('type_verdict'):
                        summary_parts.append(f"Výrok: {row['type_verdict']}")
                    if row.get('popular_name') and row['popular_name'] != 'NA':
                        summary_parts.append(f"Název: {row['popular_name']}")

                    summary = "\n".join(summary_parts) if summary_parts else None

                    # Prepare subject/keywords
                    subject = row.get('subject_proceedings', '')
                    keywords = row.get('subject_register', '')

                    # URL
                    url = row.get('url_address', '')

                    # Check if already exists by ECLI
                    cursor.execute('SELECT id FROM court_decisions WHERE ecli = ?',
                                   (doc_id,))
                    exists = cursor.fetchone()

                    if exists:
                        skipped += 1
                        continue

                    # Insert
                    cursor.execute('''
                        INSERT INTO court_decisions
                        (case_number, court_level, court_name, decision_date, ecli,
                         keywords, full_text, summary, source_url, source)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        case_number,
                        'Ústavní soud',  # court_level
                        'Ústavní soud',  # court_name
                        decision_date,
                        doc_id,  # ECLI
                        f"{keywords}\n{subject}" if keywords and subject else (keywords or subject or ''),
                        full_text[:500000] if full_text else None,  # Limit to 500k chars
                        summary,
                        url,
                        'usoud.cz'
                    ))

                    imported += 1

                    # Commit every 1000 records
                    if imported % 1000 == 0:
                        conn.commit()

                except Exception as e:
                    errors += 1
                    if errors < 10:  # Only print first 10 errors
                        print(f"   ✗ Error on row {idx}: {e}")

        conn.commit()
        conn.close()

        print("\n" + "=" * 60)
        print(f"🎉 IMPORT COMPLETE!")
        print(f"   Imported: {imported:,}")
        print(f"   Skipped (duplicates): {skipped:,}")
        print(f"   Errors: {errors:,}")
        print(f"   Database: {self.db_path}")

if __name__ == "__main__":
    importer = ConstitutionalCourtImporter()
    importer.import_decisions()
