#!/usr/bin/env python3
"""
Diagnostic script to inspect NALUS search results structure
"""
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service
import time

options = Options()
options.add_argument('--headless')
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')

service = Service('/snap/bin/geckodriver')
driver = webdriver.Firefox(service=service, options=options)

try:
    print("🔍 Loading NALUS and submitting search...")
    driver.get("https://nalus.usoud.cz")
    time.sleep(3)

    # Fill in date range for 2024
    date_from = driver.find_element(By.ID, "ctl00_MainContent_decidedFrom")
    date_to = driver.find_element(By.ID, "ctl00_MainContent_decidedTo")

    date_from.clear()
    date_from.send_keys("1.1.2024")

    date_to.clear()
    date_to.send_keys("31.12.2024")

    print("📅 Submitting search for 2024...")
    search_button = driver.find_element(By.ID, "ctl00_MainContent_but_search")
    search_button.click()

    time.sleep(8)  # Wait for results to load

    # Save results page
    print("\n💾 Saving results page source...")
    with open('/tmp/nalus_results_page.html', 'w', encoding='utf-8') as f:
        f.write(driver.page_source)
    print("   Saved to: /tmp/nalus_results_page.html")

    # Check for various table structures
    print("\n📊 Looking for result tables...")

    # Try different table selectors
    tables = driver.find_elements(By.TAG_NAME, "table")
    print(f"\n   Found {len(tables)} tables total")

    for idx, table in enumerate(tables):
        table_class = table.get_attribute('class') or 'NO-CLASS'
        table_id = table.get_attribute('id') or 'NO-ID'
        rows = table.find_elements(By.TAG_NAME, "tr")
        print(f"\n   Table {idx+1}:")
        print(f"     ID: {table_id}")
        print(f"     Class: {table_class}")
        print(f"     Rows: {len(rows)}")

        # Show first few rows if they contain links
        if rows:
            for row_idx, row in enumerate(rows[:3]):
                links = row.find_elements(By.TAG_NAME, "a")
                if links:
                    print(f"       Row {row_idx+1}: {len(links)} links")
                    for link in links[:2]:
                        href = link.get_attribute('href') or 'NO-HREF'
                        text = link.text[:50] or 'NO-TEXT'
                        print(f"         - {text} -> {href[:80]}")

    # Try CSS selectors mentioned in original code
    print("\n🔗 Checking for decision links...")

    selectors = [
        "table.searchResultsTable tr",
        "a[href*='GetText.aspx']",
        "table tr a",
        "div.results a",
        "table.results tr"
    ]

    for selector in selectors:
        try:
            elements = driver.find_elements(By.CSS_SELECTOR, selector)
            print(f"   {selector}: {len(elements)} found")
        except:
            print(f"   {selector}: ERROR")

    # Look for any error messages or "no results" text
    print("\n⚠️  Checking for messages...")
    body_text = driver.find_element(By.TAG_NAME, "body").text

    keywords = ["výsledek", "nenalezen", "žádné", "chyba", "error", "nalezeno"]
    for keyword in keywords:
        if keyword.lower() in body_text.lower():
            print(f"   Found keyword '{keyword}' in page")
            # Print surrounding context
            idx = body_text.lower().find(keyword.lower())
            context = body_text[max(0, idx-50):min(len(body_text), idx+100)]
            print(f"   Context: ...{context}...")

finally:
    driver.quit()
    print("\n✅ Inspection complete!")
