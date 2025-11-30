#!/usr/bin/env python3
"""
ALMQUIST Full Laws Crawler
Crawls ALL Czech laws from zakonyprolidi.cz (1945-2025)
Designed for long-running 24h+ operation
"""

import sqlite3
import requests
from bs4 import BeautifulSoup
import time
from datetime import datetime
import json
import re
import sys
import os

class FullLawsCrawler:
    """Full crawler for ALL Czech laws"""

    def __init__(self, db_path="/home/puzik/almquist_legal_sources.db"):
        self.db_path = db_path
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'ALMQUIST Legal RAG Bot/1.0 (Educational Purpose)'
        })
        self.pause_between_requests = 2  # 2 seconds between requests
        self.years_to_crawl = range(1993, 2026)  # 1993-2025 (since ČR independence)

    def get_laws_from_year(self, year):
        """Get all law URLs from a specific year"""
        url = f"https://www.zakonyprolidi.cz/cs/rocnik/{year}"
        print(f"\n📅 Year {year}: {url}")

        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')

            # Find all law links: /cs/YYYY-NUMBER
            pattern = re.compile(rf'/cs/{year}-\d+')
            links = soup.find_all('a', href=pattern)

            law_urls = []
            for link in links:
                href = link.get('href')
                # Only include laws with REF_OK class (valid, active laws)
                if 'REF_OK' in link.get('class', []) or 'REF_DEL' in link.get('class', []):
                    law_number = href.replace('/cs/', '').replace('-', '/')
                    law_name = link.get('title', '') or link.get_text(strip=True)

                    law_urls.append({
                        'url': f"https://www.zakonyprolidi.cz{href}",
                        'law_number': f"{law_number} Sb.",
                        'law_name': law_name,
                        'year': year
                    })

            print(f"   Found {len(law_urls)} laws")
            return law_urls

        except Exception as e:
            print(f"   ✗ Error: {e}")
            return []

    def crawl_law_detail(self, law_info):
        """Crawl detail of single law"""
        print(f"\n📜 {law_info['law_number']} - {law_info['law_name']}")
        print(f"   URL: {law_info['url']}")

        try:
            response = self.session.get(law_info['url'], timeout=30)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')

            # Remove script, style, and navigation elements
            for element in soup(['script', 'style', 'nav', 'header', 'footer', 'aside', 'iframe', 'noscript']):
                element.decompose()

            # Remove ads and promotional content
            for element in soup.find_all(['div', 'section'], class_=re.compile(r'(ad|promo|banner|subscribe|newsletter)', re.I)):
                element.decompose()

            # Try to find main law content
            content_div = (
                soup.find('article') or
                soup.find('div', {'id': 'zakon'}) or
                soup.find('div', {'class': 'zakon'}) or
                soup.find('div', {'id': 'content'}) or
                soup.find('main')
            )

            law_text = ""
            if content_div:
                law_text = content_div.get_text(separator='\n\n', strip=True)

                # Remove common boilerplate
                boilerplate = [
                    r'Vyčkejte chviličku.*?Web bez reklam',
                    r'Předplatné PLUS.*?Více funkcí',
                    r'Cookies.*?souhlasíte',
                    r'Přihlášení.*?Registrace',
                ]
                for pattern in boilerplate:
                    law_text = re.sub(pattern, '', law_text, flags=re.DOTALL | re.IGNORECASE)

                law_text = re.sub(r'\n{3,}', '\n\n', law_text).strip()

            if not law_text:
                body = soup.find('body')
                if body:
                    law_text = body.get_text(separator='\n\n', strip=True)

            # Categorize law
            category = self._categorize_law(law_info['law_name'], law_text)

            # Save to database
            law_data = {
                'law_number': law_info['law_number'],
                'law_name': law_info['law_name'],
                'law_type': 'zakon',
                'category': category,
                'full_text': law_text[:500000],
                'source_url': law_info['url']
            }

            law_id = self.save_law(law_data)
            print(f"   ✓ Saved (ID: {law_id}), length: {len(law_text):,} chars")

            return True

        except Exception as e:
            print(f"   ✗ Error: {e}")
            return False

    def _categorize_law(self, name, text):
        """Categorize law based on name/content"""
        name_lower = name.lower()

        if any(x in name_lower for x in ['občansk', 'rodina', 'manželství']):
            return 'civil'
        elif any(x in name_lower for x in ['trestn', 'kriminal']):
            return 'criminal'
        elif any(x in name_lower for x in ['obchodní', 'korporac', 'účetní', 'insolvenc']):
            return 'commercial'
        elif any(x in name_lower for x in ['daň', 'daňov', 'dph']):
            return 'tax'
        elif any(x in name_lower for x in ['správní', 'přestupk']):
            return 'administrative'
        elif any(x in name_lower for x in ['práce', 'zaměstnan', 'mzd']):
            return 'labor'
        elif any(x in name_lower for x in ['ústav', 'listina', 'základní práv']):
            return 'constitutional'
        elif any(x in name_lower for x in ['katastr', 'nemovit', 'staveb']):
            return 'property'
        elif any(x in name_lower for x in ['autor', 'patent', 'známk', 'ochran']):
            return 'intellectual_property'
        else:
            return 'other'

    def save_law(self, law_data):
        """Save law to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('SELECT id FROM laws WHERE law_number = ?', (law_data['law_number'],))
        existing = cursor.fetchone()

        if existing:
            cursor.execute('''
            UPDATE laws SET
                law_name = ?,
                law_type = ?,
                category = ?,
                full_text = ?,
                source_url = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE law_number = ?
            ''', (
                law_data['law_name'],
                law_data['law_type'],
                law_data['category'],
                law_data['full_text'],
                law_data['source_url'],
                law_data['law_number']
            ))
            law_id = existing[0]
        else:
            cursor.execute('''
            INSERT INTO laws (
                law_number, law_name, law_type, category,
                full_text, source_url
            ) VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                law_data['law_number'],
                law_data['law_name'],
                law_data['law_type'],
                law_data['category'],
                law_data['full_text'],
                law_data['source_url']
            ))
            law_id = cursor.lastrowid

        conn.commit()
        conn.close()
        return law_id

    def log_crawl(self, source, source_type, status, items_found, items_added, error_message=None):
        """Log crawl to history"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
        INSERT INTO crawl_history (source, source_type, status, items_found, items_added, error_message)
        VALUES (?, ?, ?, ?, ?, ?)
        ''', (source, source_type, status, items_found, items_added, error_message))

        conn.commit()
        conn.close()

    def crawl_all_laws(self):
        """Crawl ALL laws from all years"""
        print("=" * 70)
        print("🏛️  ALMQUIST FULL LAWS CRAWLER")
        print("=" * 70)
        print(f"\nYears: {min(self.years_to_crawl)}-{max(self.years_to_crawl)}")
        print(f"Estimated laws: {len(self.years_to_crawl) * 300} (~300/year avg)")
        print(f"Estimated time: {len(self.years_to_crawl) * 300 * 2 / 3600:.1f} hours")
        print(f"Pause between requests: {self.pause_between_requests}s")

        total_laws_found = 0
        total_laws_crawled = 0
        total_laws_failed = 0

        for year in self.years_to_crawl:
            print(f"\n{'='*70}")
            print(f"YEAR {year}")
            print(f"{'='*70}")

            # Get all laws from year
            laws = self.get_laws_from_year(year)
            total_laws_found += len(laws)

            if not laws:
                continue

            # Crawl each law
            year_success = 0
            year_failed = 0

            for i, law_info in enumerate(laws, 1):
                print(f"\n[{i}/{len(laws)}]", end=" ")

                if self.crawl_law_detail(law_info):
                    year_success += 1
                    total_laws_crawled += 1
                else:
                    year_failed += 1
                    total_laws_failed += 1

                # Pause between requests
                time.sleep(self.pause_between_requests)

                # Progress report every 50 laws
                if i % 50 == 0:
                    print(f"\n   📊 Progress: {i}/{len(laws)} ({i/len(laws)*100:.1f}%)")
                    print(f"   ✓ Success: {year_success}, ✗ Failed: {year_failed}")

            # Year summary
            print(f"\n{'='*70}")
            print(f"YEAR {year} COMPLETE")
            print(f"Success: {year_success}/{len(laws)}")
            print(f"Failed:  {year_failed}/{len(laws)}")
            print(f"{'='*70}")

            # Log year crawl
            self.log_crawl(
                f'zakonyprolidi_full_{year}',
                'law',
                'success',
                len(laws),
                year_success
            )

        # Final summary
        print(f"\n{'='*70}")
        print(f"✅ FULL CRAWL COMPLETED")
        print(f"{'='*70}")
        print(f"Total laws found:   {total_laws_found:,}")
        print(f"Total laws crawled: {total_laws_crawled:,}")
        print(f"Total laws failed:  {total_laws_failed:,}")
        print(f"Success rate:       {total_laws_crawled/total_laws_found*100:.1f}%")
        print(f"{'='*70}")


def main():
    """Main function"""
    crawler = FullLawsCrawler()
    crawler.crawl_all_laws()


if __name__ == "__main__":
    main()
