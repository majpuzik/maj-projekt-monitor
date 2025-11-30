#!/usr/bin/env python3
"""
Diagnostic script to inspect NALUS form structure
"""
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.common.by import By
import time

options = Options()
options.add_argument('--headless')
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')

service = Service('/snap/bin/geckodriver')
driver = webdriver.Firefox(service=service, options=options)

try:
    print("🔍 Loading NALUS homepage...")
    driver.get("https://nalus.usoud.cz")
    time.sleep(5)  # Wait for page to load

    print("\n📋 ALL INPUT ELEMENTS:")
    print("=" * 80)
    inputs = driver.find_elements(By.TAG_NAME, "input")
    for inp in inputs:
        elem_id = inp.get_attribute('id') or 'NO-ID'
        elem_name = inp.get_attribute('name') or 'NO-NAME'
        elem_type = inp.get_attribute('type') or 'NO-TYPE'
        elem_class = inp.get_attribute('class') or 'NO-CLASS'
        print(f"ID: {elem_id}")
        print(f"  Name: {elem_name}")
        print(f"  Type: {elem_type}")
        print(f"  Class: {elem_class}")
        print("-" * 40)

    print("\n🔘 ALL BUTTON ELEMENTS:")
    print("=" * 80)
    buttons = driver.find_elements(By.TAG_NAME, "button")
    for btn in buttons:
        elem_id = btn.get_attribute('id') or 'NO-ID'
        elem_name = btn.get_attribute('name') or 'NO-NAME'
        elem_text = btn.text or 'NO-TEXT'
        print(f"ID: {elem_id}")
        print(f"  Name: {elem_name}")
        print(f"  Text: {elem_text}")
        print("-" * 40)

    print("\n📝 ALL SELECT ELEMENTS:")
    print("=" * 80)
    selects = driver.find_elements(By.TAG_NAME, "select")
    for sel in selects:
        elem_id = sel.get_attribute('id') or 'NO-ID'
        elem_name = sel.get_attribute('name') or 'NO-NAME'
        print(f"ID: {elem_id}")
        print(f"  Name: {elem_name}")
        print("-" * 40)

    # Save page source for analysis
    print("\n💾 Saving page source...")
    with open('/tmp/nalus_page_source.html', 'w', encoding='utf-8') as f:
        f.write(driver.page_source)
    print("   Saved to: /tmp/nalus_page_source.html")

finally:
    driver.quit()
    print("\n✅ Inspection complete!")
