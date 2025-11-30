# ALMQUIST RAG - Automatická Aktualizace (Cron Job)

Systém pro automatickou noční aktualizaci RAG databáze z oficiálních českých zdrojů.

## 📁 Struktura

```
/home/puzik/
├── almquist_sources_scraper.py      # Web scraper pro oficiální zdroje
├── almquist_rag_updater.py          # Hlavní updater (detekce změn, integrace)
├── almquist_rag_cron.sh             # Wrapper pro cron
├── almquist_rag_updater.log         # Log všech aktualizací (JSON)
├── almquist_rag_cron.log            # Cron výstup (text)
├── almquist_rag_updates.json        # Aktuální scraped data
├── almquist_rag_notification.json   # Poslední notifikace
└── almquist_rag_backups/            # Zálohy před každou aktualizací
    └── ALMQUIST_RAG_PROFILY_backup_YYYYMMDD_HHMMSS.json
```

## ⏰ Cron Job Setup

### Přidat cron job:

```bash
crontab -e
```

### Přidat řádek:

```cron
# ALMQUIST RAG - Automatická aktualizace každou noc ve 3:00
0 3 * * * /home/puzik/almquist_rag_cron.sh
```

### Alternativní časy:

```cron
# Každou noc ve 2:00
0 2 * * * /home/puzik/almquist_rag_cron.sh

# Každou noc ve 4:00
0 4 * * * /home/puzik/almquist_rag_cron.sh

# Každou neděli ve 3:00 (týdenní aktualizace)
0 3 * * 0 /home/puzik/almquist_rag_cron.sh

# Každý 1. den v měsíci ve 3:00 (měsíční aktualizace)
0 3 1 * * /home/puzik/almquist_rag_cron.sh
```

### Ověřit crontab:

```bash
crontab -l | grep almquist
```

## 🔍 Monitorování

### Zkontrolovat cron log:

```bash
tail -f /home/puzik/almquist_rag_cron.log
```

### Zkontrolovat update log:

```bash
cat /home/puzik/almquist_rag_updater.log | python3 -m json.tool | less
```

### Poslední aktualizace:

```bash
cat /home/puzik/almquist_rag_updater.log | python3 -c "
import json, sys
logs = json.load(sys.stdin)
if logs:
    last = logs[-1]
    print(f\"Timestamp: {last['timestamp']}\")
    print(f\"Změn: {last['changes_count']}\")
    if last['changes']:
        print('\\nZměny:')
        for c in last['changes']:
            print(f\"  - {c['type']}: {c.get('profession', 'N/A')} {c['old_value']} → {c['new_value']}\")
"
```

### Zkontrolovat notifikace:

```bash
cat /home/puzik/almquist_rag_notification.json | python3 -m json.tool
```

## 🧪 Testovací Spuštění

Před nastavením cronu otestujte manuálně:

```bash
# Spustit celý update proces
/home/puzik/almquist_rag_cron.sh

# Nebo přímo updater
python3 /home/puzik/almquist_rag_updater.py

# Nebo jen scraper
python3 /home/puzik/almquist_sources_scraper.py
```

## 🔄 Proces Aktualizace

1. **Záloha** - Vytvoří zálohu současné RAG databáze
2. **Scraping** - Stáhne aktuální data z oficiálních zdrojů:
   - czso.cz (statistiky příjmů)
   - cssz.cz (minimální zálohy sociálního pojištění)
   - vzp.cz (minimální zdravotní pojištění)
   - financnisprava.cz (DPH sazby, termíny)
   - cak.cz (příspěvky advokátů)
   - lkcr.cz (příspěvky lékařů)
   - kdpcr.cz (příspěvky daňových poradců)

3. **Detekce změn** - Porovná scraped data s existující databází
4. **Aplikace změn** - Aktualizuje JSON databázi
5. **Re-generování embeddings** - Vytvoří nové vector embeddings
6. **Notifikace** - Uloží notifikaci o změnách
7. **Log** - Uloží detailní log aktualizace

## 📊 Sledované Změny

### Automaticky detekované:

- ✅ Minimální zálohy ČSSZ (sociální pojištění)
- ✅ Minimální pojistné zdravotní pojišťovny
- ✅ Sazby DPH
- ✅ Příspěvky komorám (ČAK, LKCR, KDP ČR)
- ✅ Termíny a deadlines

### Manuální kontrola nutná:

- ⚠️ Legislativní změny (nové zákony)
- ⚠️ Nové požadavky pro profese
- ⚠️ Změny v procesech registrace
- ⚠️ Nové povinnosti

## 🚨 Troubleshooting

### Cron job se nespouští:

```bash
# Zkontrolovat cron service
systemctl status cron

# Zkontrolovat crontab syntax
crontab -l

# Zkontrolovat oprávnění
ls -la /home/puzik/almquist_rag_cron.sh
```

### Scraping selhává:

```bash
# Zkontrolovat internet připojení
ping -c 3 czso.cz

# Zkontrolovat timeout
# Upravit timeout v almquist_sources_scraper.py (řádek response.get(url, timeout=10))

# Spustit scraper manuálně s debug výstupem
python3 /home/puzik/almquist_sources_scraper.py
```

### Embeddings se negenerují:

```bash
# Zkontrolovat volnou paměť
free -h

# Zkontrolovat GPU
nvidia-smi

# Spustit manuálně
python3 /home/puzik/create_rag_embeddings.py
```

## 🔔 Notifikace

### Email notifikace (volitelné):

Upravit `send_notification()` v `almquist_rag_updater.py`:

```python
import smtplib
from email.mime.text import MIMEText

def send_email_notification(self):
    msg = MIMEText(json.dumps(self.changes_made, indent=2))
    msg['Subject'] = f"ALMQUIST RAG Update: {len(self.changes_made)} změn"
    msg['From'] = "rag-updater@almquist.local"
    msg['To'] = "admin@example.com"

    with smtplib.SMTP('localhost') as s:
        s.send_message(msg)
```

### Slack notifikace (volitelné):

```python
import requests

def send_slack_notification(self):
    webhook_url = "https://hooks.slack.com/services/YOUR/WEBHOOK/URL"

    message = {
        "text": f"🔄 ALMQUIST RAG Update: {len(self.changes_made)} změn",
        "attachments": [{
            "color": "good",
            "fields": [
                {"title": change['type'], "value": f"{change['old_value']} → {change['new_value']}", "short": True}
                for change in self.changes_made
            ]
        }]
    }

    requests.post(webhook_url, json=message)
```

## 📝 Zálohy

Zálohy se ukládají před každou aktualizací do:

```
/home/puzik/almquist_rag_backups/
```

### Obnovení ze zálohy:

```bash
# Zobrazit zálohy
ls -lth /home/puzik/almquist_rag_backups/

# Obnovit ze zálohy
cp /home/puzik/almquist_rag_backups/ALMQUIST_RAG_PROFILY_backup_20251129_030000.json \
   /home/puzik/ALMQUIST_RAG_PROFILY.json

# Re-generovat embeddings
python3 /home/puzik/create_rag_embeddings.py
```

### Automatické čištění starých záloh:

Přidat do crontab:

```cron
# Smazat zálohy starší než 30 dní (každý den v 4:00)
0 4 * * * find /home/puzik/almquist_rag_backups/ -name "*.json" -mtime +30 -delete
```

## 🎯 Best Practices

1. **Testuj před nasazením** - Vždy otestuj manuálně před nastavením cronu
2. **Monitoruj logy** - Pravidelně kontroluj logy pro chyby
3. **Zálohy** - Udržuj zálohy alespoň 30 dní
4. **Notifikace** - Nastavit email/Slack notifikace pro kritické změny
5. **Frekvence** - Denní update může být moc častý, týdenní je doporučeno
6. **Kontrola** - I s automatizací, manuální kontrola změn je důležitá

## 📅 Doporučená Frekvence

| Zdroj | Frekvence změn | Doporučená kontrola |
|-------|----------------|---------------------|
| ČSSZ (minimální zálohy) | Ročně (1. ledna) | Týdně v lednu, měsíčně jinak |
| VZP (zdravotní pojištění) | Ročně (1. ledna) | Týdně v lednu, měsíčně jinak |
| Finanční správa (DPH) | Velmi zřídka | Měsíčně |
| ČAK (příspěvky) | Ročně | Měsíčně |
| LKCR (příspěvky) | Ročně | Měsíčně |
| ČSÚ (statistiky) | Čtvrtletně | Měsíčně |

**Doporučení**: Spouštět **každou neděli ve 3:00** (týdenní frekvence)

## ✅ Instalace

```bash
# 1. Nastavit oprávnění
chmod +x /home/puzik/almquist_rag_cron.sh
chmod +x /home/puzik/almquist_rag_updater.py
chmod +x /home/puzik/almquist_sources_scraper.py

# 2. Vytvořit adresáře
mkdir -p /home/puzik/almquist_rag_backups

# 3. Testovací spuštění
/home/puzik/almquist_rag_cron.sh

# 4. Zkontrolovat výstup
cat /home/puzik/almquist_rag_cron.log

# 5. Přidat do crontab
crontab -e
# Přidat: 0 3 * * 0 /home/puzik/almquist_rag_cron.sh

# 6. Ověřit
crontab -l
```

---

**Created**: 2025-11-29
**Status**: Production Ready ✅
**Cron Schedule**: Každou neděli ve 3:00
