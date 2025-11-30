#!/usr/bin/env python3
"""
ALMQUIST NALUS Crawler for 2024-2025
Crawls recent Constitutional Court decisions missing from Zenodo dataset
"""

import sqlite3
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service
import time
from datetime import datetime
import re

class NALUSRecentCrawler:
    """Selenium crawler for NALUS 2024-2025 decisions"""

    def __init__(self, db_path="/home/puzik/almquist_legal_sources.db"):
        self.db_path = db_path
        self.base_url = "https://nalus.usoud.cz"

        # Setup headless Firefox
        options = Options()
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')

        service = Service('/snap/bin/geckodriver')
        self.driver = webdriver.Firefox(service=service, options=options)
        self.wait = WebDriverWait(self.driver, 20)

    def search_by_year(self, year):
        """Search for all decisions from a specific year"""
        print(f"\n📅 Searching for {year} decisions...")

        try:
            self.driver.get(self.base_url)
            time.sleep(3)

            # Find date fields and set year range
            # Correct NALUS element IDs (discovered via inspection)
            date_from = self.driver.find_element(By.ID, "ctl00_MainContent_decidedFrom")
            date_to = self.driver.find_element(By.ID, "ctl00_MainContent_decidedTo")

            # Set date range for full year (format: d.m.yyyy)
            date_from.clear()
            date_from.send_keys(f"1.1.{year}")

            date_to.clear()
            date_to.send_keys(f"31.12.{year}")

            time.sleep(1)

            # Submit search
            search_button = self.driver.find_element(By.ID, "ctl00_MainContent_but_search")
            search_button.click()

            time.sleep(8)  # Wait for results to load

            # Get decision links from results
            decisions = []

            # NALUS uses ResultDetail.aspx, not GetText.aspx
            # Results are paginated, so we need to iterate through pages
            page = 1
            max_pages = 200  # Limit to prevent infinite loops (3712 results / ~20 per page = ~186 pages)

            while page <= max_pages:
                print(f"      Page {page}...")

                # Find all decision links on current page
                decision_links = self.driver.find_elements(By.CSS_SELECTOR, "a[href*='ResultDetail.aspx']")

                if not decision_links:
                    print(f"      No more results on page {page}")
                    break

                # Extract decision info from each link
                for link in decision_links:
                    try:
                        url = link.get_attribute('href')
                        case_text = link.text.strip()

                        # Filter out navigation links (they don't have case numbers)
                        if case_text and 'ÚS' in case_text:
                            # Remove the " #1" or similar suffix that NALUS adds
                            case_number = case_text.split('#')[0].strip()

                            # Avoid duplicates
                            if not any(d['case_number'] == case_number for d in decisions):
                                decisions.append({
                                    'url': url,
                                    'case_number': case_number,
                                    'year': year
                                })
                    except:
                        continue

                # Try to go to next page
                try:
                    # Look for "next page" link or specific page number
                    next_page_link = self.driver.find_element(By.LINK_TEXT, str(page + 1))
                    next_page_link.click()
                    time.sleep(3)
                    page += 1
                except:
                    # No more pages
                    print(f"      Reached last page ({page})")
                    break

            print(f"   Found {len(decisions)} decisions for {year}")
            return decisions

        except Exception as e:
            print(f"   ✗ Error searching {year}: {e}")
            return []

    def crawl_decision_detail(self, decision_info):
        """Get full text of a decision"""
        try:
            self.driver.get(decision_info['url'])
            time.sleep(2)

            # Get full text from page
            body = self.driver.find_element(By.TAG_NAME, "body")
            full_text = body.text

            # Try to extract ECLI if present
            ecli_match = re.search(r'ECLI:CZ:US:\d+:[^\s]+', full_text)
            ecli = ecli_match.group(0) if ecli_match else None

            return {
                'case_number': decision_info['case_number'],
                'ecli': ecli,
                'full_text': full_text[:500000],  # Limit to 500k
                'url': decision_info['url'],
                'year': decision_info['year']
            }

        except Exception as e:
            print(f"      ✗ Error crawling {decision_info['case_number']}: {e}")
            return None

    def save_decision(self, decision):
        """Save decision to database"""
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
                return False  # Already exists

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
            print(f"         ✗ Error saving: {e}")
            conn.close()
            return False

    def crawl_years(self, years=[2024, 2025]):
        """Crawl decisions from specified years"""
        print("🚀 Starting NALUS 2024-2025 Crawler")
        print("=" * 60)

        total_found = 0
        total_saved = 0

        for year in years:
            # Search for decisions
            decisions = self.search_by_year(year)
            total_found += len(decisions)

            # Crawl each decision
            for idx, dec_info in enumerate(decisions, 1):
                print(f"   [{idx}/{len(decisions)}] {dec_info['case_number']}")

                # Get detail
                decision = self.crawl_decision_detail(dec_info)

                if decision:
                    # Save to DB
                    if self.save_decision(decision):
                        print(f"      ✓ Saved")
                        total_saved += 1
                    else:
                        print(f"      - Already exists")

                time.sleep(2)  # Be gentle with server

        print("\n" + "=" * 60)
        print(f"🎉 CRAWLER COMPLETE!")
        print(f"   Found: {total_found}")
        print(f"   Saved: {total_saved}")

        self.driver.quit()

if __name__ == "__main__":
    crawler = NALUSRecentCrawler()
    crawler.crawl_years([2024, 2025])
