#!/usr/bin/env python3
"""Quick test of NALUS crawler - just first page"""
import sys
sys.path.insert(0, '/home/puzik')
from almquist_nalus_2024_2025_crawler import NALUSRecentCrawler

crawler = NALUSRecentCrawler()

# Override max_pages to test just first 2 pages
print("Testing decision finding on first 2 pages...")

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service
import time

options = Options()
options.add_argument('--headless')

service = Service('/snap/bin/geckodriver')
driver = webdriver.Firefox(service=service, options=options)

try:
    driver.get("https://nalus.usoud.cz")
    time.sleep(3)

    # Search for 2024
    date_from = driver.find_element(By.ID, "ctl00_MainContent_decidedFrom")
    date_to = driver.find_element(By.ID, "ctl00_MainContent_decidedTo")
    date_from.clear()
    date_from.send_keys("1.1.2024")
    date_to.clear()
    date_to.send_keys("31.12.2024")

    search_button = driver.find_element(By.ID, "ctl00_MainContent_but_search")
    search_button.click()
    time.sleep(8)

    # Test finding decisions on page 1
    decisions = []
    decision_links = driver.find_elements(By.CSS_SELECTOR, "a[href*='ResultDetail.aspx']")

    print(f"\nFound {len(decision_links)} total links with ResultDetail.aspx")

    for link in decision_links[:10]:  # Just first 10
        url = link.get_attribute('href')
        text = link.text.strip()
        if text and 'ÚS' in text:
            case_number = text.split('#')[0].strip()
            print(f"  ✓ {case_number} -> {url[:80]}...")
            decisions.append(case_number)

    print(f"\n✅ Successfully extracted {len(decisions)} case numbers from page 1")

finally:
    driver.quit()
