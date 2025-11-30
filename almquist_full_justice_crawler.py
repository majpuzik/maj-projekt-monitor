#!/usr/bin/env python3
"""
ALMQUIST Full Justice.cz API Crawler
Crawls ALL decisions from rozhodnuti.justice.cz OpenData API
Covers: Vrchní soudy, Krajské soudy, vybraná Okresní rozhodnutí
Total: ~546,000 decisions (2020-2024)
"""

import sqlite3
import requests
import time
from datetime import datetime
import json
import re

class FullJusticeCrawler:
    """Full crawler for rozhodnuti.justice.cz OpenData API"""

    def __init__(self, db_path="/home/puzik/almquist_legal_sources.db"):
        self.db_path = db_path
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'ALMQUIST Legal RAG Bot/1.0 (Educational Purpose)',
            'Accept': 'application/json'
        })
        self.base_url = "https://rozhodnuti.justice.cz/api/opendata"
        self.pause_between_requests = 2  # Be gentle with API

    def init_database(self):
        """Initialize database with proper schema"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Court decisions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS court_decisions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                case_number TEXT UNIQUE,
                court_name TEXT,
                decision_date DATE,
                publication_date DATE,
                author TEXT,
                ecli TEXT,
                subject TEXT,
                keywords TEXT,
                legal_provisions TEXT,
                full_text TEXT,
                summary TEXT,
                url TEXT,
                source TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        conn.commit()
        conn.close()

    def get_years(self):
        """Get all available years from API"""
        try:
            response = self.session.get(self.base_url, timeout=30)
            response.raise_for_status()
            years_data = response.json()

            years = [(item['rok'], item['pocet']) for item in years_data]
            print(f"📊 Found {len(years)} years with total decisions")
            for year, count in years:
                print(f"   {year}: {count:,} decisions")

            return years
        except Exception as e:
            print(f"✗ Error getting years: {e}")
            return []

    def get_months(self, year):
        """Get all months for a specific year"""
        try:
            url = f"{self.base_url}/{year}"
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            months_data = response.json()

            return [(item['mesic'], item['pocet']) for item in months_data]
        except Exception as e:
            print(f"   ✗ Error getting months for {year}: {e}")
            return []

    def get_days(self, year, month):
        """Get all days for a specific year/month"""
        try:
            url = f"{self.base_url}/{year}/{month}"
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            days_data = response.json()

            return [(item['datum'], item['pocet']) for item in days_data]
        except Exception as e:
            print(f"      ✗ Error getting days for {year}/{month}: {e}")
            return []

    def get_decisions_for_day(self, year, month, day, page=0, page_size=100):
        """Get all decisions for a specific day (paginated)"""
        try:
            url = f"{self.base_url}/{year}/{month}/{day}"
            params = {'pageNumber': page, 'pageSize': page_size}

            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()

            return data
        except Exception as e:
            print(f"         ✗ Error getting decisions for {year}/{month}/{day}: {e}")
            return None

    def get_decision_detail(self, doc_uuid):
        """Get detailed decision document"""
        try:
            url = f"https://rozhodnuti.justice.cz/api/finaldoc/{doc_uuid}"
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"            ✗ Error getting detail for {doc_uuid}: {e}")
            return None

    def save_decision(self, decision_metadata, decision_detail):
        """Save decision to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            # Extract UUID from odkaz URL
            uuid_match = re.search(r'([a-f0-9\-]{36})', decision_metadata.get('odkaz', ''))
            doc_uuid = uuid_match.group(1) if uuid_match else None

            # Build full text from detail
            full_text_parts = []
            if decision_detail:
                if decision_detail.get('verdictText'):
                    full_text_parts.append(f"VÝROK:\n{decision_detail['verdictText']}")
                if decision_detail.get('justificationText'):
                    full_text_parts.append(f"\nODŮVODNĚNÍ:\n{decision_detail['justificationText']}")

            full_text = "\n\n".join(full_text_parts) if full_text_parts else None

            # Build summary from metadata
            summary_parts = []
            if decision_metadata.get('predmetRizeni'):
                summary_parts.append(f"Předmět: {decision_metadata['predmetRizeni']}")
            if decision_metadata.get('klicovaSlova'):
                keywords = ', '.join(decision_metadata['klicovaSlova'])
                summary_parts.append(f"Klíčová slova: {keywords}")

            summary = "\n".join(summary_parts) if summary_parts else None

            # Prepare data
            case_number = decision_metadata.get('jednaciCislo')
            court_name = decision_metadata.get('soud')
            decision_date = decision_metadata.get('datumVydani')
            publication_date = decision_metadata.get('datumZverejneni')
            author = decision_metadata.get('autor')
            ecli = decision_metadata.get('ecli')
            subject = decision_metadata.get('predmetRizeni')
            keywords = json.dumps(decision_metadata.get('klicovaSlova', []))
            legal_provisions = json.dumps(decision_metadata.get('zminenaUstanoveni', []))
            url = f"https://rozhodnuti.justice.cz/detail/{doc_uuid}" if doc_uuid else decision_metadata.get('odkaz')

            cursor.execute('''
                INSERT OR IGNORE INTO court_decisions
                (case_number, court_name, decision_date, publication_date, author,
                 ecli, subject, keywords, legal_provisions, full_text, summary, url, source)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (case_number, court_name, decision_date, publication_date, author,
                  ecli, subject, keywords, legal_provisions, full_text, summary, url,
                  'rozhodnuti.justice.cz'))

            conn.commit()

            # Get ID of inserted/existing record
            cursor.execute('SELECT id FROM court_decisions WHERE case_number = ?', (case_number,))
            result = cursor.fetchone()
            decision_id = result[0] if result else None

            return decision_id

        except Exception as e:
            print(f"            ✗ Error saving decision: {e}")
            return None
        finally:
            conn.close()

    def crawl_all(self):
        """Crawl all decisions from all years"""
        print("🚀 Starting FULL Justice.cz OpenData Crawler")
        print("=" * 60)

        self.init_database()

        # Get all years
        years = self.get_years()

        total_processed = 0
        total_saved = 0

        for year, year_count in years:
            print(f"\n📅 YEAR {year} ({year_count:,} decisions)")
            print("-" * 60)

            # Get months for this year
            months = self.get_months(year)

            for month, month_count in months:
                print(f"\n   📆 Month {year}/{month:02d} ({month_count:,} decisions)")

                # Get days for this month
                days = self.get_days(year, month)

                for day_date, day_count in days:
                    print(f"\n      📅 {day_date} ({day_count} decisions)")

                    # Get decisions for this day (handle pagination)
                    page = 0
                    while True:
                        result = self.get_decisions_for_day(year, month, int(day_date.split('-')[2]), page)

                        if not result or not result.get('items'):
                            break

                        items = result['items']
                        total_pages = result.get('totalPages', 1)

                        print(f"         Page {page + 1}/{total_pages}: {len(items)} decisions")

                        # Process each decision
                        for idx, decision in enumerate(items, 1):
                            case_num = decision.get('jednaciCislo', 'Unknown')
                            court = decision.get('soud', 'Unknown')

                            # Extract UUID
                            uuid_match = re.search(r'([a-f0-9\-]{36})', decision.get('odkaz', ''))
                            doc_uuid = uuid_match.group(1) if uuid_match else None

                            if not doc_uuid:
                                print(f"            [{idx}/{len(items)}] {case_num} - No UUID, skipping")
                                continue

                            # Check if already exists
                            conn = sqlite3.connect(self.db_path)
                            cursor = conn.cursor()
                            cursor.execute('SELECT id FROM court_decisions WHERE case_number = ?', (case_num,))
                            exists = cursor.fetchone()
                            conn.close()

                            if exists:
                                print(f"            [{idx}/{len(items)}] {case_num} - Already exists (ID: {exists[0]})")
                                total_processed += 1
                                continue

                            # Get decision detail
                            detail = self.get_decision_detail(doc_uuid)

                            # Save to database
                            decision_id = self.save_decision(decision, detail)

                            if decision_id:
                                text_len = len(detail.get('verdictText', '') + detail.get('justificationText', '')) if detail else 0
                                print(f"            [{idx}/{len(items)}] ✓ {case_num} - {court}")
                                print(f"                Saved (ID: {decision_id}), text length: {text_len:,} chars")
                                total_saved += 1
                            else:
                                print(f"            [{idx}/{len(items)}] ✗ {case_num} - Failed to save")

                            total_processed += 1

                            # Rate limiting
                            time.sleep(self.pause_between_requests)

                        # Check if there are more pages
                        if page + 1 >= total_pages:
                            break

                        page += 1
                        time.sleep(1)  # Brief pause between pages

                # Summary after each month
                print(f"\n   ✓ Month {year}/{month:02d} complete")
                print(f"   Total processed so far: {total_processed:,}")
                print(f"   Total saved so far: {total_saved:,}")

        print("\n" + "=" * 60)
        print(f"🎉 CRAWLER COMPLETE!")
        print(f"   Total processed: {total_processed:,}")
        print(f"   Total saved: {total_saved:,}")
        print(f"   Database: {self.db_path}")

if __name__ == "__main__":
    crawler = FullJusticeCrawler()
    crawler.crawl_all()
