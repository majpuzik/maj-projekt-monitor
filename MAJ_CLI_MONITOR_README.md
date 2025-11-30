# MAJ CLI Monitor

Real-time monitor pro sledování Claude CLI aktivit z Central Database.

## 🚀 Funkce

- ✅ **Real-time monitoring** všech Claude CLI sessions
- ✅ **Minimální zobrazení** - session ID, poslední aktivita, prompt, tool
- ✅ **Detail view** - kompletní historie session s možností kopírování
- ✅ **Export** - export session do JSON
- ✅ **Filtrování** - podle času, typu akce
- ✅ **Cross-platform** - Linux x86, Linux ARM64 (DGX), macOS ARM64 (M1/M2/M4)
- ✅ **Autostart** - systemd service (Linux) / LaunchAgent (macOS)

## 📦 Instalace

```bash
# Automatická instalace (vyžaduje sudo pro autostart)
./install-maj-monitor.sh

# Manuální spuštění
python3 maj-cli-monitor.py                    # Simple mode
python3 maj-cli-monitor-interactive.py        # Interactive mode

# Ve screen (doporučeno)
screen -dmS maj_monitor python3 maj-cli-monitor.py
screen -r maj_monitor                          # Připojit se
```

## ⌨️ Ovládání (Interactive Mode)

```
↑/↓ nebo j/k    - Navigace mezi sessions
ENTER nebo d    - Detail view
c               - Kopírovat do clipboard
e               - Export session do JSON
q nebo ESC      - Quit / Zpět
```

## 📊 Co monitor ukazuje

### Hlavní view
```
#  Session   Last Activity       Last Prompt              Tool    Count
●  ea5a22f4  16:52:28 (2m ago)  a bude to platit...      Edit    15
○  f3853e30  15:34:12 (1h ago)  podivej se do cdb...     Bash    8
```

**Indikátor:**
- `●` = Aktivní (poslední aktivita < 5 min)
- `○` = Neaktivní

### Detail view
```
Session: ea5a22f4-3c28-4343-a2ab-57e80eb726d1
================================================================================

[2025-11-30 16:52:28] USER PROMPT
  → a bude to platit generelne pro vsechny me claude cli?

[2025-11-30 16:52:30] TOOL: TodoWrite

[2025-11-30 16:52:31] TOOL: Bash
  → Cmd: cat ~/.claude/settings.json

[2025-11-30 16:52:35] TOOL: Edit
  → File: /home/puzik/.claude/settings.local.json
```

## 🔧 Běžící services

```bash
# Zobrazit všechny běžící monitory
screen -ls

# Připojit se k monitoru
screen -r maj_monitor

# Odpojit (monitor běží dál)
Ctrl+A, D

# Zastavit monitor
screen -S maj_monitor -X quit
```

## 📂 Soubory

```
~/maj-cli-monitor.py                    # Simple real-time monitor
~/maj-cli-monitor-interactive.py       # Interactive TUI monitor
~/install-maj-monitor.sh                # Installer script
~/.claude/hooks/activity_logger.py      # Hook handler (automatický logging)
/tmp/maj-cli-monitor.service            # Systemd service template
```

## 🔍 SQL dotazy

```bash
# Poslední Claude aktivity
sqlite3 /home/puzik/almquist-central-log/almquist.db \
  "SELECT timestamp, event_type,
   json_extract(metadata, '$.tool') as tool,
   json_extract(metadata, '$.prompt') as prompt
   FROM events
   WHERE component='claude-code'
   ORDER BY timestamp DESC LIMIT 20;"

# Statistiky podle session
sqlite3 /home/puzik/almquist-central-log/almquist.db \
  "SELECT
   json_extract(metadata, '$.session_id') as session,
   COUNT(*) as actions,
   MIN(timestamp) as start_time,
   MAX(timestamp) as last_time
   FROM events
   WHERE component='claude-code'
   GROUP BY session
   ORDER BY last_time DESC;"

# Export session do JSON
sqlite3 /home/puzik/almquist-central-log/almquist.db \
  "SELECT json_object(
     'timestamp', timestamp,
     'event_type', event_type,
     'metadata', metadata
   ) FROM events
   WHERE component='claude-code'
   AND json_extract(metadata, '$.session_id') = 'YOUR_SESSION_ID'
   ORDER BY timestamp DESC;" > session_export.json
```

## 🐛 Troubleshooting

### Monitor nevidí události

```bash
# Zkontroluj že hooks fungují
cat ~/.claude/settings.local.json | grep -A10 hooks

# Zkontroluj CDB
sqlite3 /home/puzik/almquist-central-log/almquist.db \
  "SELECT COUNT(*) FROM events WHERE component='claude-code';"

# Zkontroluj log hook handleru
ls -la ~/.claude/hooks/activity_logger.py
```

### Autostart nefunguje

**Linux:**
```bash
# Zkontroluj systemd service
systemctl status maj-cli-monitor
journalctl -u maj-cli-monitor -f

# Restart service
sudo systemctl restart maj-cli-monitor
```

**macOS:**
```bash
# Zkontroluj LaunchAgent
launchctl list | grep cli-monitor
tail -f /tmp/maj-cli-monitor.log

# Reload
launchctl unload ~/Library/LaunchAgents/com.majpuzik.cli-monitor.plist
launchctl load ~/Library/LaunchAgents/com.majpuzik.cli-monitor.plist
```

## 📈 Performance

- **Dotaz frekvence**: Každé 2 sekundy
- **Databáze load**: ~1-5ms per query
- **Memory usage**: ~20-30 MB
- **CPU usage**: <1%

## 🔐 Data Retention

- Events starší než 24h se neobjevují v monitoru
- Ale zůstávají v CDB pro historické analýzy
- Manual cleanup: `sqlite3 almquist.db "DELETE FROM events WHERE timestamp < datetime('now', '-30 days');"`

---

**Author**: Auto-generated for MAJ Puzik
**Platform**: DGX-SPARK, Mac Mini M4, Mac
**Version**: 1.0
