#!/usr/bin/env python3
"""
ALMQUIST Legal - NSS Crawler
Crawls decisions from Nejvyšší správní soud (vyhledavac.nssoud.cz, sbirka.nssoud.cz)
"""

import sqlite3
import requests
from bs4 import BeautifulSoup
import time
from datetime import datetime
import json
import re

class NSSCrawler:
    """Crawler for Nejvyšší správní soud decisions"""

    def __init__(self, db_path="/home/puzik/almquist_legal_sources.db"):
        self.db_path = db_path
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'ALMQUIST Legal RAG Bot/1.0 (Educational Purpose)'
        })

    def crawl_nss_sbirka(self, max_results=30):
        """Crawl NSS Sbírka rozhodnutí"""
        print("\n⚖️  Crawling Nejvyšší správní soud (sbirka.nssoud.cz)")
        print(f"   Max results: {max_results}")

        base_url = "https://sbirka.nssoud.cz"
        decisions_found = []

        try:
            response = self.session.get(base_url, timeout=30)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'html.parser')

            # Look for decision links
            # NSS typically has links with case numbers (e.g., "1 As 123/2024")
            links = soup.find_all('a', href=True)

            for link in links:
                href = link.get('href')
                text = link.get_text(strip=True)

                # Look for case number pattern (e.g., "1 As 123/2024")
                case_match = re.search(r'\d+\s+[A-Z][a-z]+\s+\d+/\d{4}', text)

                if case_match and ('/sbirka/' in href or '/rozhodnuti/' in href):
                    full_url = href if href.startswith('http') else base_url + href

                    decision_info = {
                        'url': full_url,
                        'case_number': case_match.group(0),
                        'link_text': text
                    }

                    # Try to extract date
                    date_match = re.search(r'(\d{1,2}\.\s*\d{1,2}\.\s*\d{4})', text)
                    if date_match:
                        decision_info['decision_date_raw'] = date_match.group(1).replace(' ', '')

                    decisions_found.append(decision_info)

                    if len(decisions_found) >= max_results:
                        break

            print(f"   ✓ Found {len(decisions_found)} decisions")
            return decisions_found

        except Exception as e:
            print(f"   ✗ Error crawling NSS: {e}")
            return []

    def save_decision(self, decision_info):
        """Save NSS decision to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        case_number = decision_info.get('case_number', 'Unknown')

        # Check if decision already exists
        cursor.execute('''
        SELECT id FROM court_decisions
        WHERE case_number = ? AND court_level = 'administrative'
        ''', (case_number,))

        existing = cursor.fetchone()

        if existing:
            print(f"   ⚠️  Decision {case_number} already exists")
            conn.close()
            return existing[0]

        # Parse date
        decision_date = None
        if 'decision_date_raw' in decision_info:
            try:
                date_str = decision_info['decision_date_raw']
                parts = date_str.split('.')
                if len(parts) == 3:
                    day, month, year = parts
                    decision_date = f"{year}-{month.zfill(2)}-{day.zfill(2)}"
            except:
                pass

        # Insert new decision
        cursor.execute('''
        INSERT INTO court_decisions (
            case_number, court_level, court_name,
            decision_type, decision_date,
            legal_area, summary, full_text, source_url
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            case_number,
            'administrative',
            'Nejvyšší správní soud',
            decision_info.get('decision_type', 'rozsudek'),
            decision_date,
            'spravni',
            decision_info.get('summary', ''),
            decision_info.get('full_text', ''),
            decision_info.get('url', '')
        ))

        decision_id = cursor.lastrowid
        conn.commit()
        conn.close()

        return decision_id

    def crawl_nss_decisions(self, max_results=30):
        """Main crawl function for NSS"""
        print("=" * 70)
        print("⚖️  NEJVYŠŠÍ SPRÁVNÍ SOUD CRAWLER")
        print("=" * 70)

        # Get decisions from Sbírka
        decisions = self.crawl_nss_sbirka(max_results=max_results)

        if not decisions:
            print("\n⚠️  NSS crawler needs enhancement")

            # Create sample entries
            print("\n   Creating sample NSS decision entries for testing...")
            sample_decisions = [
                {
                    'case_number': '1 As 100/2024',
                    'decision_type': 'rozsudek',
                    'decision_date': '2024-11-15',
                    'legal_area': 'spravni',
                    'summary': 'Ukázkový rozsudek NSS (placeholder)',
                    'full_text': 'Toto je ukázkový záznam pro demonstraci struktury. V produkci by zde byl plný text rozsudku NSS.',
                    'url': 'https://sbirka.nssoud.cz'
                },
                {
                    'case_number': '2 Ads 50/2024',
                    'decision_type': 'rozsudek',
                    'decision_date': '2024-10-20',
                    'legal_area': 'spravni',
                    'summary': 'Ukázkový rozsudek NSS v daňové věci (placeholder)',
                    'full_text': 'Toto je ukázkový záznam pro demonstraci struktury. V produkci by zde byl plný text rozsudku NSS.',
                    'url': 'https://sbirka.nssoud.cz'
                }
            ]

            success_count = 0
            for decision in sample_decisions:
                decision_id = self.save_decision(decision)
                if decision_id:
                    print(f"   ✓ Created sample: {decision['case_number']} (ID: {decision_id})")
                    success_count += 1

            print("\n" + "=" * 70)
            print("⚠️  NSS CRAWLER - SAMPLE DATA CREATED")
            print("=" * 70)
            print(f"Sample decisions: {success_count}")
            print("\nNote: For production, enhance NSS crawler with:")
            print("  - Better parsing of sbirka.nssoud.cz")
            print("  - or vyhledavac.nssoud.cz API access")
            print("=" * 70)
            return

        # Save found decisions
        success_count = 0
        for decision in decisions:
            decision_id = self.save_decision(decision)
            if decision_id:
                print(f"   ✓ Saved: {decision.get('case_number', 'Unknown')} (ID: {decision_id})")
                success_count += 1

        print("\n" + "=" * 70)
        print("✅ NSS CRAWL COMPLETED")
        print("=" * 70)
        print(f"Success: {success_count}/{len(decisions)}")
        print("=" * 70)


def main():
    """Main function"""
    crawler = NSSCrawler()
    crawler.crawl_nss_decisions(max_results=30)


if __name__ == "__main__":
    main()
