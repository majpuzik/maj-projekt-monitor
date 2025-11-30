#!/usr/bin/env python3
"""
ALMQUIST Legal Court Decisions Crawler
Crawls court decisions from Czech courts (NS, ÚS, NSS)
"""

import sqlite3
import requests
from bs4 import BeautifulSoup
import time
from datetime import datetime
import json
import re
import shutil
import sys
import os
sys.path.append(os.path.dirname(__file__))
from almquist_resource_monitor import ResourceMonitor

class CourtDecisionsCrawler:
    """Crawler for Czech court decisions"""

    def __init__(self, db_path="/home/puzik/almquist_legal_sources.db"):
        self.db_path = db_path
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'ALMQUIST Legal RAG Bot/1.0 (Educational Purpose)'
        })
        self.pause_between_requests = 5  # 5 seconds between requests (reduced from 30)
        self.resource_monitor = ResourceMonitor(
            cpu_limit=80,
            disk_limit=90,
            mem_limit=85,
            gpu_limit=80
        )

    def crawl_nsoud_listing(self, max_pages=5):
        """Crawl listing of decisions from Nejvyšší soud"""
        print("\n⚖️  Crawling Nejvyšší soud (sbirka.nsoud.cz)")
        print(f"   Max pages: {max_pages}")

        base_url = "https://sbirka.nsoud.cz"
        archive_base = "https://sbirka.nsoud.cz/nove-vydana-rozhodnuti-ve-sbirce"
        decisions_found = []

        # Use archive pagination (supports up to ~1,328 pages!)
        for page_num in range(1, max_pages + 1):
            if page_num == 1:
                url = archive_base + "/"
            else:
                url = f"{archive_base}/strana/{page_num}/"

            print(f"\n   Page {page_num}: {url}")

            try:
                response = self.session.get(url, timeout=30)
                response.raise_for_status()

                soup = BeautifulSoup(response.text, 'html.parser')

                # Find all decision links
                # Pattern: <a href="https://sbirka.nsoud.cz/sbirka/XXXXX/">
                links = soup.find_all('a', href=re.compile(r'/sbirka/\d+/'))

                page_decisions = []
                for link in links:
                    href = link.get('href')
                    if not href or '/sbirka/' not in href:
                        continue

                    # Extract decision ID from URL
                    match = re.search(r'/sbirka/(\d+)/', href)
                    if not match:
                        continue

                    decision_id = match.group(1)
                    full_url = href if href.startswith('http') else base_url + href

                    # Extract info from link text
                    link_text = link.get_text(strip=True)

                    # Parse: "Rozsudek Nejvyššího soudu ze dne 23. 5. 2024, sp. zn. 33 Cdo 2889/2023, ECLI:..."
                    decision_info = {
                        'decision_id': decision_id,
                        'url': full_url,
                        'link_text': link_text
                    }

                    # Extract date
                    date_match = re.search(r'ze dne (\d{1,2}\.\s*\d{1,2}\.\s*\d{4})', link_text)
                    if date_match:
                        decision_info['decision_date_raw'] = date_match.group(1).replace(' ', '')

                    # Extract case number (sp. zn. / sen. zn.)
                    case_match = re.search(r'(?:sp\.|sen\.)\s*zn\.\s*([^\,]+)', link_text)
                    if case_match:
                        decision_info['case_number'] = case_match.group(1).strip()

                    # Extract ECLI
                    ecli_match = re.search(r'ECLI:([^\s]+)', link_text)
                    if ecli_match:
                        decision_info['ecli'] = 'ECLI:' + ecli_match.group(1).strip()

                    # Extract decision type
                    if 'Rozsudek' in link_text:
                        decision_info['decision_type'] = 'rozsudek'
                    elif 'Usnesení' in link_text:
                        decision_info['decision_type'] = 'usneseni'
                    elif 'Stanovisko' in link_text:
                        decision_info['decision_type'] = 'stanovisko'

                    page_decisions.append(decision_info)

                print(f"      Found {len(page_decisions)} decisions")
                decisions_found.extend(page_decisions)

                # Check resources (CPU, GPU, Disk, Memory)
                if not self.resource_monitor.check_all(verbose=False):
                    print(f"   ⚠️  Stopping crawl due to resource limits")
                    break

                # Be nice to server
                if page_num < max_pages:
                    print(f"      ⏸️  Pausing {self.pause_between_requests} seconds...")
                    time.sleep(self.pause_between_requests)

            except Exception as e:
                print(f"      ✗ Error on page {page_num}: {e}")
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

            # Extract full text
            # Main content is typically in entry-content or article
            content_div = soup.find('div', class_='entry-content') or soup.find('article')

            if not content_div:
                # Try table-based layout
                content_div = soup.find('table')

            full_text = ""
            summary = ""
            keywords = []
            affected_laws = []

            if content_div:
                # Extract právní věta (summary)
                legal_sentence = content_div.find('td', string=re.compile(r'Právní věta'))
                if legal_sentence:
                    summary_td = legal_sentence.find_next('td')
                    if summary_td:
                        summary = summary_td.get_text(strip=True)

                # Extract keywords/tags
                tags_section = soup.find_all('a', rel='tag')
                keywords = [tag.get_text(strip=True) for tag in tags_section if tag.get_text(strip=True)]

                # Extract full text
                full_text = content_div.get_text(separator='\n\n', strip=True)

                # Try to extract affected laws from text
                law_pattern = re.compile(r'\d+/\d{4}\s+Sb\.')
                affected_laws = list(set(law_pattern.findall(full_text)))

            decision_info['full_text'] = full_text[:500000]  # Limit to 500k chars (increased from 50k)
            decision_info['summary'] = summary[:10000] if summary else ""  # Increased from 5k
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
                # Parse Czech date format: "23.5.2024"
                date_str = decision_info['decision_date_raw']
                parts = date_str.split('.')
                if len(parts) == 3:
                    day, month, year = parts
                    decision_date = f"{year}-{month.zfill(2)}-{day.zfill(2)}"
            except:
                pass

        # Check if decision already exists (by ECLI or case number)
        ecli = decision_info.get('ecli')
        case_number = decision_info.get('case_number')

        cursor.execute('''
        SELECT id FROM court_decisions
        WHERE ecli = ? OR case_number = ?
        ''', (ecli, case_number))

        existing = cursor.fetchone()

        if existing:
            # Update existing
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
            # Insert new
            cursor.execute('''
            INSERT INTO court_decisions (
                case_number, court_level, court_name,
                decision_type, decision_date, ecli,
                legal_area, affected_laws, keywords,
                summary, full_text, source_url
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                decision_info.get('case_number', 'Unknown'),
                'supreme',
                'Nejvyšší soud',
                decision_info.get('decision_type'),
                decision_date,
                decision_info.get('ecli'),
                'obcanske',  # Default, could be refined
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

    def crawl_nsoud_decisions(self, max_pages=5, max_details=20):
        """Crawl Nejvyšší soud decisions (listing + details)"""
        print("=" * 70)
        print("⚖️  NEJVYŠŠÍ SOUD CRAWLER")
        print("=" * 70)

        # Get listing
        decisions = self.crawl_nsoud_listing(max_pages=max_pages)

        if not decisions:
            print("\n⚠️  No decisions found")
            return

        # Limit to max_details for this run
        decisions = decisions[:max_details]

        print(f"\n📥 Crawling details for {len(decisions)} decisions...")

        success_count = 0
        failed_count = 0

        for i, decision_info in enumerate(decisions, 1):
            print(f"\n[{i}/{len(decisions)}] {decision_info.get('case_number', 'Unknown')}")
            print(f"   URL: {decision_info['url']}")

            # Crawl detail
            if self.crawl_decision_detail(decision_info):
                # Save to database
                decision_id = self.save_decision(decision_info)
                print(f"   ✓ Saved (ID: {decision_id})")
                print(f"   ✓ Text length: {len(decision_info.get('full_text', ''))} chars")
                print(f"   ✓ Keywords: {len(json.loads(decision_info.get('keywords', '[]')))}")
                success_count += 1
            else:
                failed_count += 1

            # Check resources every 10 decisions
            if i % 10 == 0 and not self.resource_monitor.check_all(verbose=False):
                print(f"\n⚠️  Stopping detail crawl due to resource limits")
                break

            # Be nice to server - pause between detail requests
            if i < len(decisions):
                time.sleep(self.pause_between_requests)

        # Log crawl
        self.log_crawl('nsoud_sbirka', 'court_decision', 'success', len(decisions), success_count)

        # Summary
        print("\n" + "=" * 70)
        print("✅ NEJVYŠŠÍ SOUD CRAWL COMPLETED")
        print("=" * 70)
        print(f"Success: {success_count}/{len(decisions)}")
        print(f"Failed:  {failed_count}/{len(decisions)}")
        print("=" * 70)

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

    def show_stats(self):
        """Show database statistics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        print("\n📊 Court Decisions Database Statistics:")

        # Total decisions
        cursor.execute('SELECT COUNT(*) FROM court_decisions')
        total = cursor.fetchone()[0]
        print(f"\n  Total decisions: {total}")

        # By court level
        cursor.execute('''
        SELECT court_level, COUNT(*)
        FROM court_decisions
        GROUP BY court_level
        ORDER BY COUNT(*) DESC
        ''')
        courts = cursor.fetchall()
        if courts:
            print("\n  By court level:")
            for court, count in courts:
                print(f"    {court}: {count}")

        # By decision type
        cursor.execute('''
        SELECT decision_type, COUNT(*)
        FROM court_decisions
        GROUP BY decision_type
        ORDER BY COUNT(*) DESC
        ''')
        types = cursor.fetchall()
        if types:
            print("\n  By decision type:")
            for dtype, count in types:
                print(f"    {dtype}: {count}")

        # In RAG
        cursor.execute('SELECT COUNT(*) FROM court_decisions WHERE added_to_rag = 1')
        in_rag = cursor.fetchone()[0]
        print(f"\n  Added to RAG: {in_rag}/{total}")

        conn.close()


def main():
    """Main function"""
    crawler = CourtDecisionsCrawler()

    # Show initial resource status
    print(f"\n{'='*70}")
    print(f"⚖️  NEJVYŠŠÍ SOUD - DAILY CRAWLER")
    print(f"{'='*70}")
    crawler.resource_monitor.print_status()

    # Crawl Nejvyšší soud - DAILY INCREMENTAL CRAWL
    # Crawl 5 pages (~100 decisions) per day to avoid long-running jobs
    # Will auto-stop if resources reach limits (CPU 80%, Disk 90%, Mem 85%, GPU 80%)
    print(f"\n🎯 TARGET: Daily incremental crawl (5 pages, ~50 decisions)")
    print(f"⏸️  Pause between requests: {crawler.pause_between_requests} seconds")
    print(f"📊 Resource limits: CPU 80%, Disk 90%, Memory 85%, GPU 80%")
    print(f"⏱️  Estimated time: ~{(50 * crawler.pause_between_requests) // 60} minutes")

    crawler.crawl_nsoud_decisions(max_pages=5, max_details=50)

    # Show final stats
    crawler.show_stats()
    print(f"\n✅ Daily crawl completed")
    crawler.resource_monitor.print_status()


if __name__ == "__main__":
    main()
