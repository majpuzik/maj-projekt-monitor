#!/usr/bin/env python3
"""
ALMQUIST Full NSS (Nejvyšší správní soud) Crawler
Crawls ALL decisions from Supreme Administrative Court (2003-2025)
"""

import sqlite3
import requests
from bs4 import BeautifulSoup
import time
from datetime import datetime
import json
import re

class FullNSSCrawler:
    """Full crawler for NSS decisions"""

    def __init__(self, db_path="/home/puzik/almquist_legal_sources.db"):
        self.db_path = db_path
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'ALMQUIST Legal RAG Bot/1.0 (Educational Purpose)'
        })
        self.pause_between_requests = 3
        self.years_to_crawl = range(2003, 2026)  # NSS existuje od 2003

    def get_decisions_from_year(self, year):
        """Get all decisions from a specific year by iterating through issues"""
        print(f"\n📅 Year {year}")

        all_decisions = []

        # NSS has 12 issues per year (monthly)
        for issue in range(1, 13):
            url = f"https://sbirka.nssoud.cz/cz/{year}-{issue}"
            print(f"   Issue {issue}/12: {url}")

            try:
                response = self.session.get(url, timeout=30)
                response.raise_for_status()
                soup = BeautifulSoup(response.text, 'html.parser')

                # Find all decision links
                # Pattern: href="/cz/TITLE.pNUMBER.html"
                links = soup.find_all('a', href=re.compile(r'\.p\d+\.html'))

                issue_decisions = []
                for link in links:
                    href = link.get('href')

                    # Skip if not a decision link
                    if not href or '.p' not in href:
                        continue

                    full_url = f"https://sbirka.nssoud.cz{href}" if href.startswith('/') else href

                    # Extract decision number from URL
                    match = re.search(r'\.p(\d+)\.html', href)
                    decision_id = match.group(1) if match else None

                    # Extract case number from link text or href
                    decision_text = link.get_text(strip=True)

                    # Try to find case number in text
                    case_match = re.search(r'(\d+\s+[A-Za-z]+\s+\d+/\d{4})', decision_text)
                    if case_match:
                        case_number = case_match.group(1)
                    else:
                        case_number = f"NSS-p{decision_id}"

                    issue_decisions.append({
                        'url': full_url,
                        'decision_id': decision_id,
                        'case_number': case_number,
                        'year': year,
                        'issue': issue,
                        'link_text': decision_text
                    })

                print(f"      Found {len(issue_decisions)} decisions")
                all_decisions.extend(issue_decisions)

                time.sleep(1)  # Brief pause between issues

            except Exception as e:
                print(f"      ✗ Error on issue {issue}: {e}")
                # Don't break - try next issue

        print(f"   ✓ Total for year {year}: {len(all_decisions)} decisions")
        return all_decisions

    def crawl_decision_detail(self, decision_info):
        """Crawl detail of single NSS decision"""
        try:
            response = self.session.get(decision_info['url'], timeout=30)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')

            # Remove scripts, styles
            for element in soup(['script', 'style', 'nav', 'header', 'footer']):
                element.decompose()

            # Extract full text from main content
            content = soup.find('div', class_='dokument') or soup.find('article') or soup.find('main')

            full_text = ""
            if content:
                full_text = content.get_text(separator='\n\n', strip=True)

            if not full_text:
                body = soup.find('body')
                if body:
                    full_text = body.get_text(separator='\n\n', strip=True)

            # Extract decision date
            decision_date = None
            date_match = re.search(r'(\d{1,2})\.\s*(\d{1,2})\.\s*(\d{4})', full_text[:500])
            if date_match:
                day, month, year = date_match.groups()
                decision_date = f"{year}-{month.zfill(2)}-{day.zfill(2)}"

            # Extract affected laws
            law_pattern = re.compile(r'\d+/\d{4}\s+Sb\.')
            affected_laws = list(set(law_pattern.findall(full_text)))

            # Determine decision type
            decision_type = 'rozsudek' if 'rozsudek' in full_text.lower()[:1000] else 'usneseni'

            decision_info['full_text'] = full_text[:500000]
            decision_info['decision_date'] = decision_date
            decision_info['decision_type'] = decision_type
            decision_info['affected_laws'] = json.dumps(affected_laws, ensure_ascii=False)

            return True

        except Exception as e:
            print(f"      ✗ Error: {e}")
            return False

    def save_decision(self, decision_info):
        """Save NSS decision to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        case_number = decision_info['case_number']

        cursor.execute('SELECT id FROM court_decisions WHERE case_number = ?', (case_number,))
        existing = cursor.fetchone()

        if existing:
            cursor.execute('''
            UPDATE court_decisions SET
                decision_type = ?,
                decision_date = ?,
                full_text = ?,
                affected_laws = ?,
                source_url = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            ''', (
                decision_info.get('decision_type'),
                decision_info.get('decision_date'),
                decision_info.get('full_text', ''),
                decision_info.get('affected_laws', '[]'),
                decision_info['url'],
                existing[0]
            ))
            decision_id = existing[0]
        else:
            cursor.execute('''
            INSERT INTO court_decisions (
                case_number, court_level, court_name,
                decision_type, decision_date,
                legal_area, affected_laws,
                full_text, source_url
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                case_number,
                'administrative',
                'Nejvyšší správní soud',
                decision_info.get('decision_type'),
                decision_info.get('decision_date'),
                'spravni',
                decision_info.get('affected_laws', '[]'),
                decision_info.get('full_text', ''),
                decision_info['url']
            ))
            decision_id = cursor.lastrowid

        conn.commit()
        conn.close()
        return decision_id

    def log_crawl(self, source, source_type, status, items_found, items_added):
        """Log crawl to history"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
        INSERT INTO crawl_history (source, source_type, status, items_found, items_added)
        VALUES (?, ?, ?, ?, ?)
        ''', (source, source_type, status, items_found, items_added))

        conn.commit()
        conn.close()

    def crawl_all_nss(self):
        """Crawl ALL NSS decisions"""
        print("=" * 70)
        print("⚖️  ALMQUIST FULL NSS CRAWLER")
        print("=" * 70)
        print(f"\nYears: {min(self.years_to_crawl)}-{max(self.years_to_crawl)}")
        print(f"Estimated decisions: {len(self.years_to_crawl) * 500} (~500/year avg)")
        print(f"Estimated time: {len(self.years_to_crawl) * 500 * 3 / 3600:.1f} hours")

        total_found = 0
        total_success = 0
        total_failed = 0

        for year in self.years_to_crawl:
            print(f"\n{'='*70}")
            print(f"YEAR {year}")
            print(f"{'='*70}")

            decisions = self.get_decisions_from_year(year)
            total_found += len(decisions)

            if not decisions:
                continue

            year_success = 0
            year_failed = 0

            for i, decision_info in enumerate(decisions, 1):
                print(f"\n[{i}/{len(decisions)}] {decision_info['case_number']}")
                print(f"   URL: {decision_info['url']}")

                if self.crawl_decision_detail(decision_info):
                    decision_id = self.save_decision(decision_info)
                    print(f"   ✓ Saved (ID: {decision_id})")
                    year_success += 1
                    total_success += 1
                else:
                    year_failed += 1
                    total_failed += 1

                time.sleep(self.pause_between_requests)

                # Progress report every 50
                if i % 50 == 0:
                    print(f"\n   📊 Progress: {i}/{len(decisions)} ({i/len(decisions)*100:.1f}%)")

            print(f"\n{'='*70}")
            print(f"YEAR {year} COMPLETE")
            print(f"Success: {year_success}/{len(decisions)}")
            print(f"{'='*70}")

            self.log_crawl(f'nss_full_{year}', 'court_decision', 'success', len(decisions), year_success)

        print(f"\n{'='*70}")
        print(f"✅ FULL NSS CRAWL COMPLETED")
        print(f"{'='*70}")
        print(f"Total found:   {total_found:,}")
        print(f"Total success: {total_success:,}")
        print(f"Total failed:  {total_failed:,}")
        print(f"{'='*70}")


def main():
    crawler = FullNSSCrawler()
    crawler.crawl_all_nss()


if __name__ == "__main__":
    main()
