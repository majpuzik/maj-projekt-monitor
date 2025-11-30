#!/usr/bin/env python3
"""
ALMQUIST Full Court Decisions Crawler
Crawls ALL court decisions from Czech courts
Designed for long-running 24h+ operation with thousands of decisions
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

class FullCourtCrawler:
    """Full crawler for ALL Czech court decisions"""

    def __init__(self, db_path="/home/puzik/almquist_legal_sources.db"):
        self.db_path = db_path
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'ALMQUIST Legal RAG Bot/1.0 (Educational Purpose)'
        })
        self.pause_between_requests = 3  # 3 seconds between requests

    def crawl_nsoud_listing(self, max_pages=1000):
        """Crawl listing of decisions from Nejvyšší soud - FULL ARCHIVE"""
        print("\n⚖️  Crawling Nejvyšší soud (sbirka.nsoud.cz) - FULL ARCHIVE")
        print(f"   Max pages: {max_pages}")

        base_url = "https://sbirka.nsoud.cz"
        archive_base = "https://sbirka.nsoud.cz/nove-vydana-rozhodnuti-ve-sbirce"
        decisions_found = []

        for page_num in range(1, max_pages + 1):
            if page_num == 1:
                url = archive_base + "/"
            else:
                url = f"{archive_base}/strana/{page_num}/"

            print(f"\n   Page {page_num}/{max_pages}: {url}")

            try:
                response = self.session.get(url, timeout=30)
                response.raise_for_status()

                soup = BeautifulSoup(response.text, 'html.parser')

                # Find all decision links
                links = soup.find_all('a', href=re.compile(r'/sbirka/\d+/'))

                page_decisions = []
                for link in links:
                    href = link.get('href')
                    if not href or '/sbirka/' not in href:
                        continue

                    match = re.search(r'/sbirka/(\d+)/', href)
                    if not match:
                        continue

                    decision_id = match.group(1)
                    full_url = href if href.startswith('http') else base_url + href
                    link_text = link.get_text(strip=True)

                    decision_info = {
                        'decision_id': decision_id,
                        'url': full_url,
                        'link_text': link_text
                    }

                    # Extract metadata
                    date_match = re.search(r'ze dne (\d{1,2}\.\s*\d{1,2}\.\s*\d{4})', link_text)
                    if date_match:
                        decision_info['decision_date_raw'] = date_match.group(1).replace(' ', '')

                    case_match = re.search(r'(?:sp\.|sen\.)\s*zn\.\s*([^\,]+)', link_text)
                    if case_match:
                        decision_info['case_number'] = case_match.group(1).strip()

                    ecli_match = re.search(r'ECLI:([^\s]+)', link_text)
                    if ecli_match:
                        decision_info['ecli'] = 'ECLI:' + ecli_match.group(1).strip()

                    if 'Rozsudek' in link_text:
                        decision_info['decision_type'] = 'rozsudek'
                    elif 'Usnesení' in link_text:
                        decision_info['decision_type'] = 'usneseni'
                    elif 'Stanovisko' in link_text:
                        decision_info['decision_type'] = 'stanovisko'

                    page_decisions.append(decision_info)

                print(f"      Found {len(page_decisions)} decisions")
                decisions_found.extend(page_decisions)

                # Check if last page (no decisions found)
                if len(page_decisions) == 0:
                    print(f"      No more decisions - stopping at page {page_num}")
                    break

                # Progress report every 10 pages
                if page_num % 10 == 0:
                    print(f"\n   📊 Progress: Page {page_num}, Total decisions: {len(decisions_found)}")

                # Pause between pages
                time.sleep(self.pause_between_requests)

            except Exception as e:
                print(f"      ✗ Error on page {page_num}: {e}")
                if page_num > 10:  # Allow errors on early pages, but stop if we're deep
                    break

        print(f"\n   ✓ Total decisions found: {len(decisions_found)}")
        return decisions_found

    def crawl_decision_detail(self, decision_info):
        """Crawl detail of single decision"""
        url = decision_info['url']

        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'html.parser')

            # Extract content
            content_div = soup.find('div', class_='entry-content') or soup.find('article') or soup.find('table')

            full_text = ""
            summary = ""
            keywords = []
            affected_laws = []

            if content_div:
                # Legal sentence (summary)
                legal_sentence = content_div.find('td', string=re.compile(r'Právní věta'))
                if legal_sentence:
                    summary_td = legal_sentence.find_next('td')
                    if summary_td:
                        summary = summary_td.get_text(strip=True)

                # Keywords
                tags_section = soup.find_all('a', rel='tag')
                keywords = [tag.get_text(strip=True) for tag in tags_section if tag.get_text(strip=True)]

                # Full text
                full_text = content_div.get_text(separator='\n\n', strip=True)

                # Affected laws
                law_pattern = re.compile(r'\d+/\d{4}\s+Sb\.')
                affected_laws = list(set(law_pattern.findall(full_text)))

            decision_info['full_text'] = full_text[:500000]
            decision_info['summary'] = summary[:10000] if summary else ""
            decision_info['keywords'] = json.dumps(keywords, ensure_ascii=False)
            decision_info['affected_laws'] = json.dumps(affected_laws, ensure_ascii=False)

            return True

        except Exception as e:
            print(f"      ✗ Error crawling detail: {e}")
            return False

    def save_decision(self, decision_info):
        """Save decision to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

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

        ecli = decision_info.get('ecli')
        case_number = decision_info.get('case_number', 'Unknown')

        cursor.execute('SELECT id FROM court_decisions WHERE ecli = ? OR case_number = ?', (ecli, case_number))
        existing = cursor.fetchone()

        if existing:
            cursor.execute('''
            UPDATE court_decisions SET
                decision_type = ?,
                decision_date = ?,
                summary = ?,
                full_text = ?,
                keywords = ?,
                affected_laws = ?,
                source_url = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            ''', (
                decision_info.get('decision_type'),
                decision_date,
                decision_info.get('summary', ''),
                decision_info.get('full_text', ''),
                decision_info.get('keywords', '[]'),
                decision_info.get('affected_laws', '[]'),
                decision_info['url'],
                existing[0]
            ))
            decision_id = existing[0]
        else:
            cursor.execute('''
            INSERT INTO court_decisions (
                case_number, court_level, court_name,
                decision_type, decision_date, ecli,
                legal_area, affected_laws, keywords,
                summary, full_text, source_url
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                case_number,
                'supreme',
                'Nejvyšší soud',
                decision_info.get('decision_type'),
                decision_date,
                decision_info.get('ecli'),
                'obcanske',
                decision_info.get('affected_laws', '[]'),
                decision_info.get('keywords', '[]'),
                decision_info.get('summary', ''),
                decision_info.get('full_text', ''),
                decision_info['url']
            ))
            decision_id = cursor.lastrowid

        conn.commit()
        conn.close()

        return decision_id

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

    def crawl_all_decisions(self, max_pages=1000):
        """Crawl ALL Nejvyšší soud decisions"""
        print("=" * 70)
        print("⚖️  ALMQUIST FULL COURT DECISIONS CRAWLER")
        print("=" * 70)
        print(f"\nTarget: Nejvyšší soud full archive")
        print(f"Max pages: {max_pages}")
        print(f"Estimated decisions: {max_pages * 20} (~20/page avg)")
        print(f"Estimated time: {max_pages * 20 * 3 / 3600:.1f} hours")
        print(f"Pause between requests: {self.pause_between_requests}s")

        # Get listing
        decisions = self.crawl_nsoud_listing(max_pages=max_pages)

        if not decisions:
            print("\n⚠️  No decisions found")
            return

        print(f"\n📥 Crawling details for {len(decisions)} decisions...")

        success_count = 0
        failed_count = 0

        for i, decision_info in enumerate(decisions, 1):
            print(f"\n[{i}/{len(decisions)}] {decision_info.get('case_number', 'Unknown')}")
            print(f"   URL: {decision_info['url']}")

            # Crawl detail
            if self.crawl_decision_detail(decision_info):
                decision_id = self.save_decision(decision_info)
                print(f"   ✓ Saved (ID: {decision_id})")
                print(f"   ✓ Text length: {len(decision_info.get('full_text', ''))}")
                success_count += 1
            else:
                failed_count += 1

            # Pause between decisions
            time.sleep(self.pause_between_requests)

            # Progress report every 100 decisions
            if i % 100 == 0:
                print(f"\n   📊 Progress: {i}/{len(decisions)} ({i/len(decisions)*100:.1f}%)")
                print(f"   ✓ Success: {success_count}, ✗ Failed: {failed_count}")

                # Log intermediate progress
                self.log_crawl('nsoud_full_archive', 'court_decision', 'in_progress', i, success_count)

        # Log final crawl
        self.log_crawl('nsoud_full_archive', 'court_decision', 'success', len(decisions), success_count)

        # Summary
        print("\n" + "=" * 70)
        print("✅ FULL COURT DECISIONS CRAWL COMPLETED")
        print("=" * 70)
        print(f"Total decisions found: {len(decisions):,}")
        print(f"Success: {success_count:,}/{len(decisions):,}")
        print(f"Failed:  {failed_count:,}/{len(decisions):,}")
        print(f"Success rate: {success_count/len(decisions)*100:.1f}%")
        print("=" * 70)


def main():
    """Main function"""
    crawler = FullCourtCrawler()

    # Crawl up to 1000 pages (up to 20,000 decisions)
    # This will run for ~16 hours at 3s/request
    crawler.crawl_all_decisions(max_pages=1000)


if __name__ == "__main__":
    main()
