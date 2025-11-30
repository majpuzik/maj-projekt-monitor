#!/usr/bin/env python3
"""
ALMQUIST RAG - Sources Scraper
Automatické scrapování oficiálních českých zdrojů pro aktualizaci RAG databáze
"""

import requests
from bs4 import BeautifulSoup
import json
import re
from datetime import datetime
from pathlib import Path
import time

class AlmquistSourcesScraper:
    """Scraper pro oficiální české zdroje"""

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36'
        })
        self.updates = []
        self.log = []

    def log_info(self, message):
        """Log zprávy"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_msg = f"[{timestamp}] {message}"
        self.log.append(log_msg)
        print(log_msg)

    def scrape_cssz_rates(self):
        """Scrape ČSSZ - minimální zálohy na sociální pojištění"""
        self.log_info("📊 Scraping ČSSZ - minimální zálohy...")

        try:
            url = "https://www.cssz.cz/minimalni-zalohy-na-pojistne"
            response = self.session.get(url, timeout=10)

            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')

                # Hledat aktuální sazby (2025)
                text = soup.get_text()

                # Extrahovat minimální zálohu
                pattern = r'(?:minimální záloha|minimální měsíční záloha).*?(\d{1,2}[\s]?\d{3}).*?Kč'
                matches = re.findall(pattern, text, re.IGNORECASE)

                if matches:
                    min_payment = int(matches[0].replace(' ', ''))
                    current_year = datetime.now().year

                    update = {
                        'source': 'cssz.cz',
                        'type': 'social_insurance',
                        'data': {
                            'min_monthly_payment': min_payment,
                            'year': current_year,
                            'deadline': '20. den následujícího měsíce'
                        },
                        'scraped_at': datetime.now().isoformat(),
                        'url': url
                    }

                    self.updates.append(update)
                    self.log_info(f"   ✓ Minimální záloha OSVČ: {min_payment} Kč ({current_year})")
                    return update

        except Exception as e:
            self.log_info(f"   ✗ Chyba při scrapingu ČSSZ: {e}")

        return None

    def scrape_health_insurance_rates(self):
        """Scrape VZP - minimální pojistné"""
        self.log_info("🏥 Scraping VZP - zdravotní pojištění...")

        try:
            url = "https://www.vzp.cz/platci/informace/platby-pojistneho"
            response = self.session.get(url, timeout=10)

            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                text = soup.get_text()

                # Hledat minimální pojistné
                pattern = r'(?:minimální.*?pojistné|OSVČ.*?minimální).*?(\d{1,2}[\s]?\d{3}).*?Kč'
                matches = re.findall(pattern, text, re.IGNORECASE)

                if matches:
                    min_payment = int(matches[0].replace(' ', ''))
                    current_year = datetime.now().year

                    update = {
                        'source': 'vzp.cz',
                        'type': 'health_insurance',
                        'data': {
                            'min_monthly_payment': min_payment,
                            'year': current_year,
                            'percentage': 13.5,
                            'deadline': '8. den následujícího měsíce'
                        },
                        'scraped_at': datetime.now().isoformat(),
                        'url': url
                    }

                    self.updates.append(update)
                    self.log_info(f"   ✓ Minimální pojistné OSVČ: {min_payment} Kč ({current_year})")
                    return update

        except Exception as e:
            self.log_info(f"   ✗ Chyba při scrapingu VZP: {e}")

        return None

    def scrape_financial_administration(self):
        """Scrape Finanční správa - DPH sazby, termíny"""
        self.log_info("💰 Scraping Finanční správa - DPH...")

        try:
            url = "https://www.financnisprava.cz/cs/dane/danove-tiskopisy-a-zakladni-informace/dph"
            response = self.session.get(url, timeout=10)

            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                text = soup.get_text()

                # Hledat základní sazbu DPH
                pattern = r'(?:základní sazba|standardní sazba).*?(\d+)\s*%'
                matches = re.findall(pattern, text, re.IGNORECASE)

                if matches:
                    vat_rate = int(matches[0])

                    update = {
                        'source': 'financnisprava.cz',
                        'type': 'vat',
                        'data': {
                            'standard_rate': vat_rate,
                            'reduced_rates': [12, 0],  # Snížené sazby
                            'deadline_monthly': '25. den následujícího měsíce',
                            'tax_return_deadline': '1. duben následujícího roku'
                        },
                        'scraped_at': datetime.now().isoformat(),
                        'url': url
                    }

                    self.updates.append(update)
                    self.log_info(f"   ✓ Základní sazba DPH: {vat_rate}%")
                    return update

        except Exception as e:
            self.log_info(f"   ✗ Chyba při scrapingu Finanční správy: {e}")

        return None

    def scrape_czso_statistics(self):
        """Scrape ČSÚ - statistiky příjmů"""
        self.log_info("📈 Scraping ČSÚ - statistiky příjmů...")

        try:
            # ČSÚ má komplexní API, použijeme zjednodušený přístup
            url = "https://www.czso.cz/csu/czso/prace_a_mzdy_prace"
            response = self.session.get(url, timeout=10)

            if response.status_code == 200:
                update = {
                    'source': 'czso.cz',
                    'type': 'statistics',
                    'data': {
                        'note': 'Statistiky se aktualizují čtvrtletně',
                        'last_check': datetime.now().isoformat()
                    },
                    'scraped_at': datetime.now().isoformat(),
                    'url': url
                }

                self.updates.append(update)
                self.log_info(f"   ✓ ČSÚ statistiky zkontrolovány")
                return update

        except Exception as e:
            self.log_info(f"   ✗ Chyba při scrapingu ČSÚ: {e}")

        return None

    def scrape_cak_fees(self):
        """Scrape ČAK - příspěvky advokátů"""
        self.log_info("⚖️  Scraping ČAK - příspěvky advokátů...")

        try:
            url = "https://www.cak.cz/scripts/detail.php?id=16690"
            response = self.session.get(url, timeout=10)

            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                text = soup.get_text()

                # Hledat měsíční příspěvek
                pattern = r'(?:měsíční příspěvek).*?(\d+).*?Kč'
                matches = re.findall(pattern, text, re.IGNORECASE)

                if matches:
                    monthly_fee = int(matches[0])

                    update = {
                        'source': 'cak.cz',
                        'type': 'chamber_fees',
                        'profession': 'advokat',
                        'data': {
                            'monthly_fee': monthly_fee,
                            'insurance_requirement': 25000,
                            'year': datetime.now().year
                        },
                        'scraped_at': datetime.now().isoformat(),
                        'url': url
                    }

                    self.updates.append(update)
                    self.log_info(f"   ✓ Měsíční příspěvek ČAK: {monthly_fee} Kč")
                    return update

        except Exception as e:
            self.log_info(f"   ✗ Chyba při scrapingu ČAK: {e}")

        return None

    def scrape_all(self):
        """Scrape všechny zdroje"""
        self.log_info("\n" + "="*70)
        self.log_info("ALMQUIST RAG - Automatická aktualizace ze zdrojů")
        self.log_info("="*70 + "\n")

        sources = [
            self.scrape_cssz_rates,
            self.scrape_health_insurance_rates,
            self.scrape_financial_administration,
            self.scrape_czso_statistics,
            self.scrape_cak_fees
        ]

        for scraper in sources:
            try:
                scraper()
                time.sleep(2)  # Být slušný k serverům
            except Exception as e:
                self.log_info(f"✗ Chyba při scrapingu: {e}")

        self.log_info(f"\n✅ Scraping dokončen. Nalezeno {len(self.updates)} aktualizací.")
        return self.updates

    def save_updates(self, filepath="/home/puzik/almquist_rag_updates.json"):
        """Uložit aktualizace"""
        output = {
            'updates': self.updates,
            'log': self.log,
            'scraped_at': datetime.now().isoformat(),
            'total_updates': len(self.updates)
        }

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(output, f, indent=2, ensure_ascii=False)

        self.log_info(f"\n💾 Aktualizace uloženy do: {filepath}")
        return filepath


def main():
    scraper = AlmquistSourcesScraper()
    updates = scraper.scrape_all()
    scraper.save_updates()

    return updates


if __name__ == "__main__":
    main()
