# MAJ Monitor - Ovládání

## ✓ Nainstalováno

Monitor je **aktivní** a zobrazuje **všechny aktivity** z CDB (ne jen Claude CLI).

## 🎮 Rychlé připojení

```bash
# Připojit se k monitoru všech aktivit
screen -r maj_all_monitor

# Nebo:
~/maj-monitor-control.sh attach
```

## 📋 Control Skript

```bash
# Status - zobrazí běžící monitory
~/maj-monitor-control.sh status

# Spustit monitor VŠECH aktivit (default)
~/maj-monitor-control.sh start

# Spustit monitor JEN Claude CLI sessions
~/maj-monitor-control.sh start claude

# Zastavit
~/maj-monitor-control.sh stop

# Restart
~/maj-monitor-control.sh restart

# Připojit se
~/maj-monitor-control.sh attach
```

## ⌨️ Klávesy v monitoru

**Hlavní zobrazení:**
- `↑/↓` nebo `j/k` - Navigace mezi komponenty
- `Enter` nebo `d` - Detail view komponenty
- `q` - Quit

**Detail view:**
- `↑/↓` nebo `j/k` - Scroll
- `ESC` nebo `q` - Zpět

**Screen:**
- `Ctrl+A D` - Odpojit (monitor běží dál)

## 📊 Co monitor zobrazuje

Monitor zobrazuje **VŠECHNY komponenty** z CDB za posledních 24 hodin:

- `●` = aktivní (< 5 min)
- `○` = neaktivní
- Component name
- Čas poslední aktivity
- Typ poslední události
- Počet událostí

**Příklad komponent:**
- `network_rag_monitor` - RAG network monitoring
- `almquist-pro-backend` - Backend aktivity
- `claude-code` - Claude CLI interakce
- `cdb_to_rag_upload` - Upload do RAG
- atd.

## 🔄 Automatické spuštění

Monitor se spustí automaticky při startu systému (crontab @reboot).

Ověření:
```bash
crontab -l | grep maj
```

## 📁 Soubory

- **All Activities Monitor:** `/home/puzik/maj-all-activities-monitor.py`
- **Claude CLI Monitor:** `/home/puzik/maj-cli-monitor-interactive.py`
- **Control Script:** `/home/puzik/maj-monitor-control.sh`
- **Database:** `/home/puzik/almquist-central-log/almquist.db`
- **README:** `/home/puzik/MAJ_MONITOR_README.md`

## 🐛 Troubleshooting

**Monitor neběží:**
```bash
~/maj-monitor-control.sh start
```

**Monitor zamrznul:**
```bash
~/maj-monitor-control.sh restart
```

**Zobrazit všechny běžící screen sessions:**
```bash
screen -list
```

## 🔀 Přepnutí mezi monitory

**Monitor všech aktivit (default):**
```bash
~/maj-monitor-control.sh stop
~/maj-monitor-control.sh start all
screen -r maj_all_monitor
```

**Monitor jen Claude CLI:**
```bash
~/maj-monitor-control.sh stop
~/maj-monitor-control.sh start claude
screen -r maj_monitor
```

---

**Created:** 2025-11-30
**Status:** ✓ Aktivní - zobrazuje VŠECHNY komponenty z CDB
**Updated:** 2025-11-30 17:43 - Přepnuto na all-activities monitor
