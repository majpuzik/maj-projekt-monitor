#!/usr/bin/env python3
"""
ALMQUIST Legal - Ústavní Soud Crawler
Crawls decisions from Constitutional Court (nalus.usoud.cz)
"""

import sqlite3
import requests
from bs4 import BeautifulSoup
import time
from datetime import datetime
import json
import re

class UstavniSoudCrawler:
    """Crawler for Ústavní soud decisions"""

    def __init__(self, db_path="/home/puzik/almquist_legal_sources.db"):
        self.db_path = db_path
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'ALMQUIST Legal RAG Bot/1.0 (Educational Purpose)'
        })

    def crawl_usoud_search(self, max_results=30):
        """Crawl ÚS decisions via search interface"""
        print("\n⚖️  Crawling Ústavní soud (nalus.usoud.cz)")
        print(f"   Max results: {max_results}")

        # NALUS search URL - we'll try to get recent decisions
        base_url = "https://nalus.usoud.cz"
        search_url = f"{base_url}/Search/Search.aspx"

        decisions_found = []

        try:
            # First, get the search page to understand structure
            response = self.session.get(base_url, timeout=30)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'html.parser')

            # Look for recent decisions links
            # NALUS typically has links to decisions in format: /Search/GetText.aspx?...
            links = soup.find_all('a', href=re.compile(r'GetText\.aspx'))

            if not links:
                # Try finding table with decisions
                tables = soup.find_all('table')
                for table in tables:
                    rows = table.find_all('tr')
                    for row in rows:
                        cells = row.find_all('td')
                        if len(cells) >= 2:
                            # Look for case number pattern (Pl. ÚS, I. ÚS, etc.)
                            for cell in cells:
                                text = cell.get_text(strip=True)
                                if re.search(r'(?:Pl\.|I\.|II\.|III\.|IV\.)\s*ÚS', text):
                                    # Found a decision reference
                                    link = cell.find('a')
                                    if link and link.get('href'):
                                        href = link.get('href')
                                        full_url = href if href.startswith('http') else base_url + href

                                        decision_info = {
                                            'url': full_url,
                                            'case_number': text,
                                            'link_text': row.get_text(strip=True)
                                        }
                                        decisions_found.append(decision_info)

            # If still nothing, create sample decisions from known recent IDs
            if not decisions_found:
                print("   ⚠️  Could not parse decision listing, using fallback approach")
                # For now, we'll just note that ÚS requires more sophisticated approach
                # possibly using their search API or Selenium
                return []

            print(f"   ✓ Found {len(decisions_found)} decisions")
            return decisions_found[:max_results]

        except Exception as e:
            print(f"   ✗ Error crawling ÚS: {e}")
            return []

    def save_decision(self, decision_info, court_name="Ústavní soud"):
        """Save ÚS decision to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        case_number = decision_info.get('case_number', 'Unknown')

        # Check if decision already exists
        cursor.execute('''
        SELECT id FROM court_decisions
        WHERE case_number = ? AND court_level = 'constitutional'
        ''', (case_number,))

        existing = cursor.fetchone()

        if existing:
            print(f"   ⚠️  Decision {case_number} already exists")
            conn.close()
            return existing[0]

        # Parse date if available
        decision_date = decision_info.get('decision_date')

        # Insert new decision
        cursor.execute('''
        INSERT INTO court_decisions (
            case_number, court_level, court_name,
            decision_type, decision_date,
            legal_area, summary, full_text, source_url
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            case_number,
            'constitutional',
            court_name,
            decision_info.get('decision_type', 'nalez'),
            decision_date,
            decision_info.get('legal_area', 'ustavni'),
            decision_info.get('summary', ''),
            decision_info.get('full_text', ''),
            decision_info.get('url', '')
        ))

        decision_id = cursor.lastrowid
        conn.commit()
        conn.close()

        return decision_id

    def crawl_usoud_decisions(self, max_results=30):
        """Main crawl function for ÚS"""
        print("=" * 70)
        print("⚖️  ÚSTAVNÍ SOUD CRAWLER")
        print("=" * 70)

        # Get decisions
        decisions = self.crawl_usoud_search(max_results=max_results)

        if not decisions:
            print("\n⚠️  ÚS crawler needs enhancement - website requires more sophisticated approach")
            print("   Recommendation: Use Selenium/Playwright or find API")

            # Create a few sample entries for demonstration
            print("\n   Creating sample ÚS decision entries for testing...")
            sample_decisions = [
                {
                    'case_number': 'Pl. ÚS 1/24',
                    'decision_type': 'nalez',
                    'decision_date': '2024-11-01',
                    'legal_area': 'ustavni',
                    'summary': 'Ukázkový nález Ústavního soudu (placeholder)',
                    'full_text': 'Toto je ukázkový záznam pro demonstraci struktury. V produkci by zde byl plný text nálezu Ústavního soudu.',
                    'url': 'https://nalus.usoud.cz'
                },
                {
                    'case_number': 'I. ÚS 500/24',
                    'decision_type': 'usneseni',
                    'decision_date': '2024-10-15',
                    'legal_area': 'ustavni',
                    'summary': 'Ukázkové usnesení Ústavního soudu (placeholder)',
                    'full_text': 'Toto je ukázkový záznam pro demonstraci struktury. V produkci by zde byl plný text usnesení Ústavního soudu.',
                    'url': 'https://nalus.usoud.cz'
                }
            ]

            success_count = 0
            for decision in sample_decisions:
                decision_id = self.save_decision(decision)
                if decision_id:
                    print(f"   ✓ Created sample: {decision['case_number']} (ID: {decision_id})")
                    success_count += 1

            print("\n" + "=" * 70)
            print("⚠️  ÚS CRAWLER - SAMPLE DATA CREATED")
            print("=" * 70)
            print(f"Sample decisions: {success_count}")
            print("\nNote: For production, implement full ÚS crawler with:")
            print("  - Selenium/Playwright for JavaScript rendering")
            print("  - or NALUS API access if available")
            print("=" * 70)
            return

        # Process found decisions
        success_count = 0
        for decision in decisions:
            decision_id = self.save_decision(decision)
            if decision_id:
                print(f"   ✓ Saved: {decision.get('case_number', 'Unknown')} (ID: {decision_id})")
                success_count += 1

        print("\n" + "=" * 70)
        print("✅ ÚSTAVNÍ SOUD CRAWL COMPLETED")
        print("=" * 70)
        print(f"Success: {success_count}/{len(decisions)}")
        print("=" * 70)


def main():
    """Main function"""
    crawler = UstavniSoudCrawler()
    crawler.crawl_usoud_decisions(max_results=30)


if __name__ == "__main__":
    main()
