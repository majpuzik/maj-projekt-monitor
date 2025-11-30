#!/usr/bin/env python3
"""
ALMQUIST RAG - Automatic Updater
Automatická aktualizace RAG databáze z oficiálních zdrojů
Spouští se jako cron job každou noc
"""

import json
import subprocess
from pathlib import Path
from datetime import datetime
import difflib
import sys

class AlmquistRAGUpdater:
    """Automatický updater RAG databáze"""

    def __init__(self):
        self.rag_json = Path("/home/puzik/ALMQUIST_RAG_PROFILY.json")
        self.updates_file = Path("/home/puzik/almquist_rag_updates.json")
        self.log_file = Path("/home/puzik/almquist_rag_updater.log")
        self.backup_dir = Path("/home/puzik/almquist_rag_backups")
        self.backup_dir.mkdir(exist_ok=True)

        self.changes_made = []
        self.log_messages = []

    def log(self, message, level="INFO"):
        """Logging"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_msg = f"[{timestamp}] [{level}] {message}"
        self.log_messages.append(log_msg)
        print(log_msg)

    def backup_current_rag(self):
        """Záloha současné RAG databáze"""
        self.log("📦 Vytvářím zálohu současné RAG databáze...")

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = self.backup_dir / f"ALMQUIST_RAG_PROFILY_backup_{timestamp}.json"

        if self.rag_json.exists():
            with open(self.rag_json, 'r', encoding='utf-8') as f:
                data = json.load(f)

            with open(backup_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            self.log(f"   ✓ Záloha uložena: {backup_path}")
            return backup_path
        else:
            self.log("   ✗ RAG databáze neexistuje!", level="ERROR")
            return None

    def run_scraper(self):
        """Spustí web scraper"""
        self.log("\n🕷️  Spouštím web scraper...")

        try:
            result = subprocess.run(
                ["python3", "/home/puzik/almquist_sources_scraper.py"],
                capture_output=True,
                text=True,
                timeout=300
            )

            if result.returncode == 0:
                self.log("   ✓ Scraper dokončen úspěšně")
                return True
            else:
                self.log(f"   ✗ Scraper selhal: {result.stderr}", level="ERROR")
                return False

        except Exception as e:
            self.log(f"   ✗ Chyba při spuštění scraperu: {e}", level="ERROR")
            return False

    def load_updates(self):
        """Načte aktualizace ze scraperu"""
        self.log("\n📥 Načítám aktualizace...")

        if not self.updates_file.exists():
            self.log("   ⚠ Soubor s aktualizacemi neexistuje", level="WARN")
            return []

        with open(self.updates_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            updates = data.get('updates', [])

        self.log(f"   ✓ Načteno {len(updates)} aktualizací")
        return updates

    def detect_changes(self, updates):
        """Detekuje změny oproti současné databázi"""
        self.log("\n🔍 Detekuji změny...")

        with open(self.rag_json, 'r', encoding='utf-8') as f:
            current_data = json.load(f)

        changes = []

        for update in updates:
            update_type = update['type']
            source = update['source']

            if update_type == 'social_insurance':
                # Kontrola změny minimálních záloh ČSSZ
                new_amount = update['data']['min_monthly_payment']
                new_year = update['data']['year']

                # Projít všechny profese a zkontrolovat sociální pojištění
                for prof in current_data['professions']:
                    if 'recurring_obligations' in prof:
                        for obligation in prof['recurring_obligations'].get('monthly', []):
                            if 'Sociální pojištění' in obligation.get('type', ''):
                                current_amount = obligation.get('amount')

                                # Pokud je amount číslo (ne string)
                                if isinstance(current_amount, int):
                                    if current_amount != new_amount:
                                        changes.append({
                                            'type': 'social_insurance_rate_change',
                                            'profession': prof['name'],
                                            'old_value': current_amount,
                                            'new_value': new_amount,
                                            'year': new_year,
                                            'source': source
                                        })

            elif update_type == 'health_insurance':
                # Kontrola změny minimálního zdravotního pojištění
                new_amount = update['data']['min_monthly_payment']
                new_year = update['data']['year']

                for prof in current_data['professions']:
                    if 'recurring_obligations' in prof:
                        for obligation in prof['recurring_obligations'].get('monthly', []):
                            if 'Zdravotní pojištění' in obligation.get('type', ''):
                                current_amount = obligation.get('amount')

                                if isinstance(current_amount, int):
                                    if current_amount != new_amount:
                                        changes.append({
                                            'type': 'health_insurance_rate_change',
                                            'profession': prof['name'],
                                            'old_value': current_amount,
                                            'new_value': new_amount,
                                            'year': new_year,
                                            'source': source
                                        })

            elif update_type == 'chamber_fees':
                # Kontrola změny příspěvků komorám
                profession = update.get('profession')
                new_fee = update['data']['monthly_fee']

                for prof in current_data['professions']:
                    if profession in prof['id']:
                        if 'recurring_obligations' in prof:
                            for obligation in prof['recurring_obligations'].get('monthly', []):
                                if 'Příspěvky' in obligation.get('type', ''):
                                    current_fee = obligation.get('amount')

                                    if isinstance(current_fee, int) and current_fee != new_fee:
                                        changes.append({
                                            'type': 'chamber_fee_change',
                                            'profession': prof['name'],
                                            'old_value': current_fee,
                                            'new_value': new_fee,
                                            'source': source
                                        })

        self.log(f"   ✓ Detekováno {len(changes)} změn")

        for change in changes:
            self.log(f"      • {change['type']}: {change.get('profession', 'N/A')} "
                    f"{change['old_value']} → {change['new_value']}")

        return changes

    def apply_changes(self, changes):
        """Aplikuje změny do RAG databáze"""
        if not changes:
            self.log("\n✅ Žádné změny k aplikaci")
            return False

        self.log(f"\n🔧 Aplikuji {len(changes)} změn...")

        with open(self.rag_json, 'r', encoding='utf-8') as f:
            data = json.load(f)

        for change in changes:
            change_type = change['type']

            if change_type == 'social_insurance_rate_change':
                new_value = change['new_value']
                year = change['year']

                for prof in data['professions']:
                    if prof['name'] == change['profession']:
                        for obligation in prof['recurring_obligations'].get('monthly', []):
                            if 'Sociální pojištění' in obligation.get('type', ''):
                                obligation['amount'] = new_value
                                obligation['year'] = year
                                self.log(f"   ✓ Aktualizováno: {prof['name']} - Sociální pojištění: {new_value} Kč")

            elif change_type == 'health_insurance_rate_change':
                new_value = change['new_value']
                year = change['year']

                for prof in data['professions']:
                    if prof['name'] == change['profession']:
                        for obligation in prof['recurring_obligations'].get('monthly', []):
                            if 'Zdravotní pojištění' in obligation.get('type', ''):
                                obligation['amount'] = new_value
                                obligation['year'] = year
                                self.log(f"   ✓ Aktualizováno: {prof['name']} - Zdravotní pojištění: {new_value} Kč")

            elif change_type == 'chamber_fee_change':
                new_value = change['new_value']

                for prof in data['professions']:
                    if prof['name'] == change['profession']:
                        for obligation in prof['recurring_obligations'].get('monthly', []):
                            if 'Příspěvky' in obligation.get('type', ''):
                                obligation['amount'] = new_value
                                self.log(f"   ✓ Aktualizováno: {prof['name']} - Příspěvky: {new_value} Kč")

        # Aktualizovat timestamp
        data['last_updated'] = datetime.now().strftime("%Y-%m-%d")

        # Uložit aktualizovaná data
        with open(self.rag_json, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        self.log(f"   ✓ Databáze aktualizována")
        self.changes_made = changes
        return True

    def regenerate_embeddings(self):
        """Re-generuje vector embeddings"""
        self.log("\n🧠 Re-generuji vector embeddings...")

        try:
            result = subprocess.run(
                ["python3", "/home/puzik/create_rag_embeddings.py"],
                capture_output=True,
                text=True,
                timeout=600
            )

            if result.returncode == 0:
                self.log("   ✓ Embeddings re-generovány úspěšně")
                return True
            else:
                self.log(f"   ✗ Re-generování embeddings selhalo: {result.stderr}", level="ERROR")
                return False

        except Exception as e:
            self.log(f"   ✗ Chyba při re-generování embeddings: {e}", level="ERROR")
            return False

    def save_log(self):
        """Uloží log"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        log_entry = {
            'timestamp': timestamp,
            'changes_count': len(self.changes_made),
            'changes': self.changes_made,
            'log': self.log_messages
        }

        # Append k existujícímu logu
        if self.log_file.exists():
            with open(self.log_file, 'r', encoding='utf-8') as f:
                try:
                    logs = json.load(f)
                except:
                    logs = []
        else:
            logs = []

        logs.append(log_entry)

        # Udržovat max 30 dnů logů
        if len(logs) > 30:
            logs = logs[-30:]

        with open(self.log_file, 'w', encoding='utf-8') as f:
            json.dump(logs, f, indent=2, ensure_ascii=False)

        self.log(f"\n💾 Log uložen do: {self.log_file}")

    def send_notification(self):
        """Pošle notifikaci pokud byly změny"""
        if not self.changes_made:
            return

        self.log("\n📧 Vytvářím notifikaci...")

        notification = {
            'timestamp': datetime.now().isoformat(),
            'subject': f"ALMQUIST RAG Update: {len(self.changes_made)} změn",
            'changes': self.changes_made,
            'summary': f"Automatická aktualizace RAG databáze našla a aplikovala {len(self.changes_made)} změn."
        }

        # Uložit notifikaci do souboru
        notif_file = Path("/home/puzik/almquist_rag_notification.json")
        with open(notif_file, 'w', encoding='utf-8') as f:
            json.dump(notification, f, indent=2, ensure_ascii=False)

        self.log(f"   ✓ Notifikace uložena: {notif_file}")

        # V budoucnu: poslat email nebo Slack notifikaci

    def run_full_update(self):
        """Hlavní funkce - spustí celý update proces"""
        self.log("\n" + "="*70)
        self.log("ALMQUIST RAG - AUTOMATICKÁ AKTUALIZACE")
        self.log("="*70)

        # 1. Záloha
        backup = self.backup_current_rag()
        if not backup:
            self.log("Chyba při záloze, končím.", level="ERROR")
            return False

        # 2. Scraping
        if not self.run_scraper():
            self.log("Scraping selhal, končím.", level="ERROR")
            return False

        # 3. Načíst aktualizace
        updates = self.load_updates()
        if not updates:
            self.log("Žádné aktualizace k zpracování")
            self.save_log()
            return True

        # 4. Detekce změn
        changes = self.detect_changes(updates)

        # 5. Aplikace změn
        if changes:
            if self.apply_changes(changes):
                # 6. Re-generování embeddings
                self.regenerate_embeddings()

                # 7. Notifikace
                self.send_notification()

        # 8. Uložit log
        self.save_log()

        self.log("\n" + "="*70)
        self.log("✅ AKTUALIZACE DOKONČENA")
        self.log("="*70)

        return True


def main():
    updater = AlmquistRAGUpdater()
    success = updater.run_full_update()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
