#!/usr/bin/env python3
"""
ALMQUIST Justice.cz API Crawler
Crawls ALL Czech courts via official rozhodnuti.justice.cz API
Includes resource monitoring (CPU, GPU, Disk, Memory)
"""

import requests
import sqlite3
import time
import json
from datetime import datetime, timedelta
import sys
import os
sys.path.append(os.path.dirname(__file__))
from almquist_resource_monitor import ResourceMonitor


class JusticeAPICrawler:
    """Crawler for rozhodnuti.justice.cz REST API"""

    def __init__(self, db_path="/home/puzik/almquist_legal_sources.db"):
        self.db_path = db_path
        self.api_base = "https://rozhodnuti.justice.cz/api/opendata"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'ALMQUIST Legal RAG Bot/1.1 (Educational Purpose)'
        })
        self.pause_between_requests = 30  # 30 seconds
        self.resource_monitor = ResourceMonitor(
            cpu_limit=80,
            disk_limit=90,
            mem_limit=85,
            gpu_limit=80
        )

    def get_available_years(self):
        """Get all available years from API"""
        try:
            response = self.session.get(self.api_base, timeout=30)
            response.raise_for_status()
            years_data = response.json()
            return years_data
        except Exception as e:
            print(f"✗ Error getting years: {e}")
            return []

    def get_months(self, year):
        """Get all months for a year"""
        try:
            url = f"{self.api_base}/{year}"
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"✗ Error getting months for {year}: {e}")
            return []

    def get_days(self, year, month):
        """Get all days for a month"""
        try:
            url = f"{self.api_base}/{year}/{month}"
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"✗ Error getting days for {year}/{month}: {e}")
            return []

    def get_decisions(self, year, month, day, page=0):
        """Get decisions for a specific day (paginated)"""
        try:
            url = f"{self.api_base}/{year}/{month}/{day}?page={page}"
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"✗ Error getting decisions for {year}/{month}/{day} page {page}: {e}")
            return None

    def get_decision_detail(self, decision_url):
        """Get full text of decision"""
        try:
            response = self.session.get(decision_url, timeout=30)
            response.raise_for_status()
            return response.text
        except Exception as e:
            print(f"✗ Error getting decision detail: {e}")
            return None

    def save_decision(self, decision_data, full_text=None):
        """Save decision to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Parse court level from court name
        court_name = decision_data.get('soud', '')
        if 'Vrchní' in court_name:
            court_level = 'appellate'
        elif 'Krajský' in court_name:
            court_level = 'regional'
        elif 'Okresní' in court_name:
            court_level = 'district'
        elif 'Nejvyšší správní' in court_name:
            court_level = 'administrative'
        elif 'Nejvyšší' in court_name:
            court_level = 'supreme'
        elif 'Ústavní' in court_name:
            court_level = 'constitutional'
        else:
            court_level = 'other'

        # Parse decision type from case number
        case_number = decision_data.get('jednaciCislo', '')
        if ' C ' in case_number:
            decision_type = 'rozsudek'
        elif ' Tz ' in case_number or ' T ' in case_number:
            decision_type = 'rozsudek'
        else:
            decision_type = 'usneseni'

        # Check if already exists
        ecli = decision_data.get('ecli')
        cursor.execute('SELECT id FROM court_decisions WHERE ecli = ?', (ecli,))
        existing = cursor.fetchone()

        if existing:
            # Update
            cursor.execute('''
            UPDATE court_decisions SET
                case_number = ?,
                court_level = ?,
                court_name = ?,
                decision_type = ?,
                decision_date = ?,
                ecli = ?,
                keywords = ?,
                affected_laws = ?,
                summary = ?,
                full_text = ?,
                source_url = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            ''', (
                case_number,
                court_level,
                court_name,
                decision_type,
                decision_data.get('datumVydani'),
                ecli,
                json.dumps(decision_data.get('klicovaSlova', []), ensure_ascii=False),
                json.dumps(decision_data.get('zminenaUstanoveni', []), ensure_ascii=False),
                decision_data.get('predmetRizeni', ''),
                full_text or '',
                decision_data.get('odkaz', ''),
                existing[0]
            ))
            decision_id = existing[0]
        else:
            # Insert
            cursor.execute('''
            INSERT INTO court_decisions (
                case_number, court_level, court_name,
                decision_type, decision_date, ecli,
                keywords, affected_laws, summary, full_text, source_url
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                case_number,
                court_level,
                court_name,
                decision_type,
                decision_data.get('datumVydani'),
                ecli,
                json.dumps(decision_data.get('klicovaSlova', []), ensure_ascii=False),
                json.dumps(decision_data.get('zminenaUstanoveni', []), ensure_ascii=False),
                decision_data.get('predmetRizeni', ''),
                full_text or '',
                decision_data.get('odkaz', '')
            ))
            decision_id = cursor.lastrowid

        conn.commit()
        conn.close()
        return decision_id

    def crawl_year(self, year, max_decisions=None):
        """Crawl all decisions for a specific year"""
        print(f"\n{'='*70}")
        print(f"📅 Crawling year: {year}")
        print(f"{'='*70}")

        decisions_count = 0
        saved_count = 0

        # Get months
        months_data = self.get_months(year)
        if not months_data:
            return 0, 0

        for month_info in months_data:
            month = month_info['mesic']
            print(f"\n  📆 Month: {year}/{month} ({month_info['pocet']} decisions)")

            # Get days
            days_data = self.get_days(year, month)
            if not days_data:
                continue

            for day_info in days_data:
                day = day_info['den']
                count = day_info['pocet']

                print(f"    📄 Day: {year}/{month}/{day} ({count} decisions)")

                # Calculate pages (100 per page)
                total_pages = (count // 100) + (1 if count % 100 > 0 else 0)

                for page in range(total_pages):
                    # Check resources
                    if not self.resource_monitor.check_all(verbose=False):
                        print(f"\n⚠️  Resource limits reached, stopping crawl")
                        return decisions_count, saved_count

                    # Check max_decisions limit
                    if max_decisions and decisions_count >= max_decisions:
                        print(f"\n✓ Reached max decisions limit: {max_decisions}")
                        return decisions_count, saved_count

                    # Get decisions for this page
                    page_data = self.get_decisions(year, month, day, page)
                    if not page_data or 'items' not in page_data:
                        continue

                    items = page_data['items']
                    print(f"      Page {page}/{total_pages-1}: {len(items)} decisions")

                    for item in items:
                        # Save decision (metadata only for now, full text optional)
                        try:
                            decision_id = self.save_decision(item)
                            saved_count += 1
                            decisions_count += 1

                            if decisions_count % 100 == 0:
                                print(f"      ✓ Progress: {decisions_count} decisions processed")

                        except Exception as e:
                            print(f"      ✗ Error saving decision: {e}")

                    # Pause between requests
                    if page < total_pages - 1 or day_info != days_data[-1]:
                        time.sleep(self.pause_between_requests)

        return decisions_count, saved_count

    def crawl_recent(self, days_back=30, max_decisions=None):
        """Crawl recent decisions (last N days)"""
        print(f"\n{'='*70}")
        print(f"📅 Crawling recent {days_back} days")
        print(f"{'='*70}")

        decisions_count = 0
        saved_count = 0

        today = datetime.now()

        for i in range(days_back):
            date = today - timedelta(days=i)
            year = date.year
            month = date.month
            day = date.day

            # Check resources
            if not self.resource_monitor.check_all(verbose=False):
                print(f"\n⚠️  Resource limits reached")
                return decisions_count, saved_count

            # Check limit
            if max_decisions and decisions_count >= max_decisions:
                return decisions_count, saved_count

            print(f"\n  📄 Crawling {year}/{month}/{day}")

            page = 0
            while True:
                page_data = self.get_decisions(year, month, day, page)
                if not page_data or 'items' not in page_data or not page_data['items']:
                    break

                items = page_data['items']
                print(f"    Page {page}: {len(items)} decisions")

                for item in items:
                    try:
                        decision_id = self.save_decision(item)
                        saved_count += 1
                        decisions_count += 1
                    except Exception as e:
                        print(f"    ✗ Error: {e}")

                page += 1
                time.sleep(self.pause_between_requests)

        return decisions_count, saved_count


def main():
    """Main function - crawl ALL available years"""
    crawler = JusticeAPICrawler()

    print(f"\n{'='*70}")
    print(f"⚖️  JUSTICE.CZ API - COMPLETE CRAWLER")
    print(f"{'='*70}")
    crawler.resource_monitor.print_status()

    # Get available years
    print(f"\n🔍 Fetching available years...")
    years_data = crawler.get_available_years()

    if not years_data:
        print("✗ No years data available")
        return

    print(f"\n📊 Available data:")
    for year_info in years_data:
        print(f"   {year_info['rok']}: {year_info['pocet']:,} decisions")

    # Crawl from newest to oldest
    years_data_sorted = sorted(years_data, key=lambda x: x['rok'], reverse=True)

    total_crawled = 0
    total_saved = 0

    for year_info in years_data_sorted:
        year = year_info['rok']
        count = year_info['pocet']

        print(f"\n{'='*70}")
        print(f"Starting year {year} ({count:,} decisions)")
        print(f"{'='*70}")

        year_crawled, year_saved = crawler.crawl_year(year, max_decisions=None)
        total_crawled += year_crawled
        total_saved += year_saved

        print(f"\n✓ Year {year} complete: {year_crawled} crawled, {year_saved} saved")
        print(f"✓ Total progress: {total_crawled:,} crawled, {total_saved:,} saved")

        crawler.resource_monitor.print_status()

    print(f"\n{'='*70}")
    print(f"✅ CRAWL COMPLETE")
    print(f"{'='*70}")
    print(f"Total crawled: {total_crawled:,}")
    print(f"Total saved:   {total_saved:,}")
    print(f"{'='*70}")


if __name__ == "__main__":
    main()
