#!/usr/bin/env python3
"""
Limited test of NALUS crawler - first 3 pages only
"""
import sqlite3
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service
import time
import re

class NALUSLimitedTest:
    def __init__(self):
        self.db_path = "/home/puzik/almquist_legal_sources.db"
        options = Options()
        options.add_argument('--headless')
        service = Service('/snap/bin/geckodriver')
        self.driver = webdriver.Firefox(service=service, options=options)

    def search_2024(self, max_pages=3):
        """Search for 2024 decisions - limited pages"""
        print("📅 Searching for 2024 decisions (first 3 pages)...")
        self.driver.get("https://nalus.usoud.cz")
        time.sleep(3)

        # Fill search form
        date_from = self.driver.find_element(By.ID, "ctl00_MainContent_decidedFrom")
        date_to = self.driver.find_element(By.ID, "ctl00_MainContent_decidedTo")
        date_from.clear()
        date_from.send_keys("1.1.2024")
        date_to.clear()
        date_to.send_keys("31.12.2024")

        search_button = self.driver.find_element(By.ID, "ctl00_MainContent_but_search")
        search_button.click()
        time.sleep(8)

        # Collect decisions from first few pages
        decisions = []
        page = 1

        while page <= max_pages:
            print(f"   Page {page}...")

            decision_links = self.driver.find_elements(By.CSS_SELECTOR, "a[href*='ResultDetail.aspx']")
            if not decision_links:
                break

            for link in decision_links:
                url = link.get_attribute('href')
                text = link.text.strip()
                if text and 'ÚS' in text:
                    case_number = text.split('#')[0].strip()
                    if not any(d['case_number'] == case_number for d in decisions):
                        decisions.append({
                            'url': url,
                            'case_number': case_number,
                            'year': 2024
                        })

            # Next page
            if page < max_pages:
                try:
                    next_link = self.driver.find_element(By.LINK_TEXT, str(page + 1))
                    next_link.click()
                    time.sleep(3)
                    page += 1
                except:
                    break
            else:
                break

        print(f"   Found {len(decisions)} decisions")
        return decisions

    def crawl_detail(self, dec_info):
        """Get full text from ResultDetail page"""
        try:
            self.driver.get(dec_info['url'])
            time.sleep(2)

            # Get full text from page body
            body = self.driver.find_element(By.TAG_NAME, "body")
            full_text = body.text

            # Try to extract ECLI
            ecli_match = re.search(r'ECLI:CZ:US:\d+:[^\s]+', full_text)
            ecli = ecli_match.group(0) if ecli_match else None

            return {
                'case_number': dec_info['case_number'],
                'ecli': ecli,
                'full_text': full_text[:500000],
                'url': dec_info['url'],
                'year': dec_info['year']
            }
        except Exception as e:
            print(f"      ✗ Error: {e}")
            return None

    def save_decision(self, decision):
        """Save to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            # Check if exists
            if decision['ecli']:
                cursor.execute('SELECT id FROM court_decisions WHERE ecli = ?', (decision['ecli'],))
            else:
                cursor.execute('SELECT id FROM court_decisions WHERE case_number = ? AND source = ?',
                               (decision['case_number'], 'usoud.cz'))

            if cursor.fetchone():
                conn.close()
                return False

            # Insert
            cursor.execute('''
                INSERT INTO court_decisions
                (case_number, court_level, court_name, ecli, full_text, source_url, source)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                decision['case_number'],
                'Ústavní soud',
                'Ústavní soud',
                decision['ecli'],
                decision['full_text'],
                decision['url'],
                'usoud.cz'
            ))

            conn.commit()
            conn.close()
            return True

        except Exception as e:
            print(f"         ✗ Save error: {e}")
            conn.close()
            return False

    def run_test(self):
        print("🚀 NALUS Limited Test (3 pages)")
        print("=" * 60)

        try:
            decisions = self.search_2024(max_pages=3)

            saved = 0
            for idx, dec in enumerate(decisions[:10], 1):  # Test first 10
                print(f"   [{idx}/10] {dec['case_number']}")

                detail = self.crawl_detail(dec)
                if detail:
                    if self.save_decision(detail):
                        print(f"      ✓ Saved")
                        saved += 1
                    else:
                        print(f"      - Already exists")

                time.sleep(2)

            print("\n" + "=" * 60)
            print(f"✅ TEST COMPLETE")
            print(f"   Found: {len(decisions)}")
            print(f"   Tested: 10")
            print(f"   Saved: {saved}")

        finally:
            self.driver.quit()

if __name__ == "__main__":
    test = NALUSLimitedTest()
    test.run_test()
