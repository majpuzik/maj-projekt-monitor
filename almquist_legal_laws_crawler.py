#!/usr/bin/env python3
"""
ALMQUIST Legal Laws Crawler
Crawls Czech laws from zakonyprolidi.cz
"""

import sqlite3
import requests
from bs4 import BeautifulSoup
import time
import hashlib
from datetime import datetime
import json
import re

class LegalLawsCrawler:
    """Crawler for Czech laws"""

    def __init__(self, db_path="/home/puzik/almquist_legal_sources.db"):
        self.db_path = db_path
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'ALMQUIST Legal RAG Bot/1.0 (Educational Purpose)'
        })

        # Priority laws to crawl
        self.priority_laws = [
            # Civil law
            {
                'number': '89/2012',
                'name': 'Občanský zákoník',
                'category': 'civil',
                'law_type': 'zakon'
            },
            {
                'number': '99/1963',
                'name': 'Občanský soudní řád',
                'category': 'civil',
                'law_type': 'zakon'
            },
            {
                'number': '292/2013',
                'name': 'Zákon o zvláštních řízeních soudních',
                'category': 'civil',
                'law_type': 'zakon'
            },
            # Commercial law
            {
                'number': '90/2012',
                'name': 'Zákon o obchodních korporacích',
                'category': 'commercial',
                'law_type': 'zakon'
            },
            {
                'number': '182/2006',
                'name': 'Zákon o úpadku a způsobech jeho řešení (insolvenční zákon)',
                'category': 'commercial',
                'law_type': 'zakon'
            },
            # Criminal law
            {
                'number': '40/2009',
                'name': 'Trestní zákoník',
                'category': 'criminal',
                'law_type': 'zakon'
            },
            {
                'number': '141/1961',
                'name': 'Trestní řád',
                'category': 'criminal',
                'law_type': 'zakon'
            },
            {
                'number': '218/2003',
                'name': 'Zákon o odpovědnosti mládeže',
                'category': 'criminal',
                'law_type': 'zakon'
            },
            # Administrative law
            {
                'number': '500/2004',
                'name': 'Správní řád',
                'category': 'administrative',
                'law_type': 'zakon'
            },
            {
                'number': '150/2002',
                'name': 'Soudní řád správní',
                'category': 'administrative',
                'law_type': 'zakon'
            },
            {
                'number': '200/1990',
                'name': 'Zákon o přestupcích',
                'category': 'administrative',
                'law_type': 'zakon'
            },
            # Labor law
            {
                'number': '262/2006',
                'name': 'Zákoník práce',
                'category': 'labor',
                'law_type': 'zakon'
            },
            {
                'number': '435/2004',
                'name': 'Zákon o zaměstnanosti',
                'category': 'labor',
                'law_type': 'zakon'
            },
            # Constitutional law
            {
                'number': '1/1993',
                'name': 'Ústava České republiky',
                'category': 'constitutional',
                'law_type': 'zakon'
            },
            {
                'number': '2/1993',
                'name': 'Listina základních práv a svobod',
                'category': 'constitutional',
                'law_type': 'zakon'
            },
            {
                'number': '182/1993',
                'name': 'Zákon o Ústavním soudu',
                'category': 'constitutional',
                'law_type': 'zakon'
            },
            # Tax law
            {
                'number': '235/2004',
                'name': 'Zákon o dani z přidané hodnoty',
                'category': 'tax',
                'law_type': 'zakon'
            },
            {
                'number': '586/1992',
                'name': 'Zákon o daních z příjmů',
                'category': 'tax',
                'law_type': 'zakon'
            },
            {
                'number': '280/2009',
                'name': 'Daňový řád',
                'category': 'tax',
                'law_type': 'zakon'
            },
            # Property & Registration
            {
                'number': '256/2013',
                'name': 'Zákon o katastru nemovitostí (katastrální zákon)',
                'category': 'property',
                'law_type': 'zakon'
            },
            {
                'number': '304/2013',
                'name': 'Zákon o veřejných rejstřících',
                'category': 'commercial',
                'law_type': 'zakon'
            },
            # Family law
            {
                'number': '94/1963',
                'name': 'Zákon o rodině',
                'category': 'civil',
                'law_type': 'zakon'
            },
            # Intellectual property
            {
                'number': '121/2000',
                'name': 'Autorský zákon',
                'category': 'intellectual_property',
                'law_type': 'zakon'
            },
            {
                'number': '441/2003',
                'name': 'Zákon o ochranných známkách',
                'category': 'intellectual_property',
                'law_type': 'zakon'
            },
        ]

    def crawl_law(self, law_info):
        """Crawl single law from zakonyprolidi.cz"""
        law_number = law_info['number']
        # URL format: /cs/[year]-[number] (e.g., 89/2012 -> /cs/2012-89)
        number, year = law_number.split('/')
        url = f"https://www.zakonyprolidi.cz/cs/{year}-{number}"

        print(f"\n📜 Crawling: {law_info['name']} ({law_number})")
        print(f"   URL: {url}")

        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'html.parser')

            # Extract law text - improved extraction
            law_text = ""

            # Remove script, style, and navigation elements
            for element in soup(['script', 'style', 'nav', 'header', 'footer', 'aside', 'iframe', 'noscript']):
                element.decompose()

            # Remove ads and promotional content
            for element in soup.find_all(['div', 'section'], class_=re.compile(r'(ad|promo|banner|subscribe|newsletter)', re.I)):
                element.decompose()

            # Try to find main law content - zakonyprolidi.cz specific
            # Look for article or main content area
            content_div = (
                soup.find('article') or
                soup.find('div', {'id': 'zakon'}) or
                soup.find('div', {'class': 'zakon'}) or
                soup.find('div', {'id': 'content'}) or
                soup.find('main')
            )

            if content_div:
                # Get clean text
                law_text = content_div.get_text(separator='\n\n', strip=True)

                # Remove common boilerplate phrases
                boilerplate = [
                    r'Vyčkejte chviličku.*?Web bez reklam',
                    r'Předplatné PLUS.*?Více funkcí',
                    r'Cookies.*?souhlasíte',
                    r'Přihlášení.*?Registrace',
                ]

                for pattern in boilerplate:
                    law_text = re.sub(pattern, '', law_text, flags=re.DOTALL | re.IGNORECASE)

                # Clean up excessive whitespace
                law_text = re.sub(r'\n{3,}', '\n\n', law_text)
                law_text = law_text.strip()

            # If no structured content found, get full page text
            if not law_text:
                body = soup.find('body')
                if body:
                    law_text = body.get_text(separator='\n\n', strip=True)

            # Extract metadata
            effective_from = self._extract_date(soup, 'effective_from')
            effective_to = self._extract_date(soup, 'effective_to')

            # Save to database
            law_data = {
                'law_number': f"{law_number} Sb.",
                'law_name': law_info['name'],
                'law_type': law_info['law_type'],
                'category': law_info['category'],
                'full_text': law_text[:500000],  # Limit to 500k chars (increased from 50k)
                'effective_from': effective_from,
                'effective_to': effective_to,
                'last_amendment': None,
                'source_url': url
            }

            law_id = self.save_law(law_data)

            print(f"   ✓ Crawled successfully (ID: {law_id})")
            print(f"   ✓ Text length: {len(law_text)} chars")

            # Log crawl
            self.log_crawl('zakonyprolidi_web', 'law', 'success', 1, 1)

            return law_id

        except Exception as e:
            print(f"   ✗ Error: {e}")
            self.log_crawl('zakonyprolidi_web', 'law', 'failed', 0, 0, str(e))
            return None

    def _extract_date(self, soup, date_type):
        """Extract effective date from page"""
        # This is a placeholder - actual implementation depends on page structure
        # zakonyprolidi.cz doesn't always have structured dates visible
        return None

    def save_law(self, law_data):
        """Save law to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Check if law already exists
        cursor.execute('SELECT id FROM laws WHERE law_number = ?', (law_data['law_number'],))
        existing = cursor.fetchone()

        if existing:
            # Update existing
            cursor.execute('''
            UPDATE laws SET
                law_name = ?,
                law_type = ?,
                category = ?,
                full_text = ?,
                effective_from = ?,
                effective_to = ?,
                last_amendment = ?,
                source_url = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE law_number = ?
            ''', (
                law_data['law_name'],
                law_data['law_type'],
                law_data['category'],
                law_data['full_text'],
                law_data['effective_from'],
                law_data['effective_to'],
                law_data['last_amendment'],
                law_data['source_url'],
                law_data['law_number']
            ))
            law_id = existing[0]
        else:
            # Insert new
            cursor.execute('''
            INSERT INTO laws (
                law_number, law_name, law_type, category,
                full_text, effective_from, effective_to,
                last_amendment, source_url
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                law_data['law_number'],
                law_data['law_name'],
                law_data['law_type'],
                law_data['category'],
                law_data['full_text'],
                law_data['effective_from'],
                law_data['effective_to'],
                law_data['last_amendment'],
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

    def crawl_all_priority_laws(self):
        """Crawl all priority laws"""
        print("=" * 70)
        print("🏛️  ALMQUIST LEGAL LAWS CRAWLER")
        print("=" * 70)
        print(f"\nCrawling {len(self.priority_laws)} priority laws from zakonyprolidi.cz")

        success_count = 0
        failed_count = 0

        for i, law_info in enumerate(self.priority_laws, 1):
            print(f"\n[{i}/{len(self.priority_laws)}]", end=" ")
            law_id = self.crawl_law(law_info)

            if law_id:
                success_count += 1
            else:
                failed_count += 1

            # Be nice to the server
            time.sleep(2)

        # Summary
        print("\n" + "=" * 70)
        print("✅ CRAWL COMPLETED")
        print("=" * 70)
        print(f"Success: {success_count}/{len(self.priority_laws)}")
        print(f"Failed:  {failed_count}/{len(self.priority_laws)}")
        print("=" * 70)

    def show_stats(self):
        """Show database statistics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        print("\n📊 Laws Database Statistics:")

        # Total laws
        cursor.execute('SELECT COUNT(*) FROM laws')
        total = cursor.fetchone()[0]
        print(f"\n  Total laws: {total}")

        # By category
        cursor.execute('''
        SELECT category, COUNT(*)
        FROM laws
        GROUP BY category
        ORDER BY COUNT(*) DESC
        ''')
        categories = cursor.fetchall()
        if categories:
            print("\n  By category:")
            for cat, count in categories:
                print(f"    {cat}: {count}")

        # Text stats
        cursor.execute('''
        SELECT
            AVG(LENGTH(full_text)) as avg_length,
            MAX(LENGTH(full_text)) as max_length,
            MIN(LENGTH(full_text)) as min_length
        FROM laws
        WHERE full_text IS NOT NULL
        ''')
        length_stats = cursor.fetchone()
        if length_stats and length_stats[0]:
            print(f"\n  Text statistics:")
            print(f"    Average length: {int(length_stats[0]):,} chars")
            print(f"    Max length: {int(length_stats[1]):,} chars")
            print(f"    Min length: {int(length_stats[2]):,} chars")

        # In RAG
        cursor.execute('SELECT COUNT(*) FROM laws WHERE added_to_rag = 1')
        in_rag = cursor.fetchone()[0]
        print(f"\n  Added to RAG: {in_rag}/{total}")

        conn.close()


def main():
    """Main function"""
    crawler = LegalLawsCrawler()

    # Crawl priority laws
    crawler.crawl_all_priority_laws()

    # Show stats
    crawler.show_stats()


if __name__ == "__main__":
    main()
