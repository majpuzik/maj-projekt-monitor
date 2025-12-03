# 🤖 MAJ-PROJEKT-MONITOR

**Comprehensive Project Lifecycle Management System**

Automatizovaný systém pro kompletní správu životního cyklu softwarových projektů od zrození až po produkci.

---

## 📋 Obsah

- [Přehled](#přehled)
- [Funkce](#funkce)
- [Architektura](#architektura)
- [Instalace](#instalace)
- [Použití](#použití)
- [Databázová struktura](#databázová-struktura)
- [API](#api)
- [Bot - Autonomní režim](#bot---autonomní-režim)
- [GUI Dashboard](#gui-dashboard)
- [Integrace s Claude CLI](#integrace-s-claude-cli)
- [Bodovací systém](#bodovací-systém)
- [Bezpečnost](#bezpečnost)

---

## 🎯 Přehled

MAJ-PROJEKT-MONITOR je komplexní systém, který:

1. **Sleduje celý životní cyklus projektů** - od plánování až po produkci
2. **Automaticky analyzuje kvalitu** - kód, testy, dokumentace, bezpečnost
3. **Řídí testy** - spouští, vyhodnocuje a reportuje výsledky
4. **Boduje kvalitu** - 0-100% professional quality scoring
5. **Autonomně pracuje** - bot provádí všechny úkony samostatně
6. **Vizualizuje průběh** - real-time GUI dashboard s grafy
7. **Integruje s nástroji** - GitHub, Claude CLI, centrální databáze

---

## ✨ Funkce

### Core Funkce

- ✅ **Centrální databáze (CDB)** - všechna data projektu na jednom místě
- ✅ **Automatické záznamy** - Claude CLI automaticky zapisuje průběh
- ✅ **Hodinová analýza** - pravidelné vyhodnocování stavu projektů
- ✅ **Bodovací systém** - sledování dosažení 100% profesionální kvality
- ✅ **Autonomní bot** - samostatné provádění úkonů
- ✅ **Real-time GUI** - živé sledování průběhu
- ✅ **GitHub integrace** - synchronizace s repozitáři
- ✅ **Fázový management** - automatické přechody mezi fázemi

### Monitorování

- 📊 **Plánování** - požadavky, scope, timeline
- 🎨 **Design** - architektura, schéma, API
- 💻 **Programování** - kód, testy, review
- 🧪 **Testování** - unit, integration, e2e, security
- 🔍 **Review** - kvalita, dokumentace, audit
- 🚀 **Deployment** - nasazení, skripty, backup
- 🏭 **Produkce** - monitoring, feedback, opravy

### Kvalita

- **Code Quality** - statická analýza, best practices
- **Test Coverage** - procento pokrytí testy
- **Documentation** - README, docstrings, docs/
- **Security** - bezpečnostní testy, CVE scan
- **Performance** - výkonnostní metriky
- **Maintainability** - udržovatelnost kódu

---

## 🏗️ Architektura

```
┌─────────────────────────────────────────────────────────────┐
│                    MAJ-PROJEKT-MONITOR                       │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐  │
│  │              │    │              │    │              │  │
│  │   Core       │◄───│   Bot        │◄───│   Web GUI    │  │
│  │   System     │    │   (Auto)     │    │   Dashboard  │  │
│  │              │    │              │    │              │  │
│  └──────┬───────┘    └──────┬───────┘    └──────┬───────┘  │
│         │                   │                   │           │
│         └───────────────────┴───────────────────┘           │
│                             │                                │
│                    ┌────────▼────────┐                       │
│                    │                  │                       │
│                    │  Central DB      │                       │
│                    │  (CDB)           │                       │
│                    │                  │                       │
│                    └────────┬─────────┘                       │
│                             │                                │
├─────────────────────────────┼─────────────────────────────┤
│                             │                                │
│  ┌──────────────┐    ┌─────▼──────┐    ┌──────────────┐  │
│  │  Claude CLI  │───►│  Events    │◄───│  GitHub      │  │
│  │  Integration │    │  System    │    │  Integration │  │
│  └──────────────┘    └────────────┘    └──────────────┘  │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

### Komponenty

1. **maj-projekt-monitor.py** - Core systém
   - Databázové operace
   - Project management
   - API rozhraní

2. **maj-projekt-monitor-bot.py** - Autonomní bot
   - Hodinová analýza
   - Automatické testy
   - Kvalitní hodnocení
   - Fázové přechody
   - Auto-fixes

3. **maj-projekt-monitor-web.py** - GUI Dashboard
   - Real-time monitoring
   - Grafy a vizualizace
   - WebSocket updates
   - Interaktivní ovládání

4. **maj-projekt-monitor-control.sh** - Control script
   - Start/stop služeb
   - Status monitoring
   - Logs management

---

## 📦 Instalace

### Požadavky

- Python 3.8+
- SQLite3
- Flask
- Flask-SocketIO
- Schedule
- psutil

### Kroky

```bash
# 1. Install dependencies
pip3 install flask flask-socketio schedule psutil

# 2. Make control script executable
chmod +x /home/puzik/maj-projekt-monitor-control.sh

# 3. Initialize database
python3 /home/puzik/maj-projekt-monitor.py

# 4. Start system
/home/puzik/maj-projekt-monitor-control.sh start
```

### Instalace jako služba

Pro automatické spuštění při startu systému:

```bash
# Vytvořit systemd service
sudo tee /etc/systemd/system/maj-projekt-monitor.service << EOF
[Unit]
Description=MAJ-PROJEKT-MONITOR - Project Lifecycle Manager
After=network.target

[Service]
Type=forking
User=puzik
WorkingDirectory=/home/puzik
ExecStart=/home/puzik/maj-projekt-monitor-control.sh start
ExecStop=/home/puzik/maj-projekt-monitor-control.sh stop
Restart=on-failure

[Install]
WantedBy=multi-user.target
EOF

# Enable and start
sudo systemctl enable maj-projekt-monitor
sudo systemctl start maj-projekt-monitor
```

---

## 🚀 Použití

### 1. Vytvoření nového projektu

```bash
# Interaktivně
./maj-projekt-monitor-control.sh create

# Přímo z CLI
python3 maj-projekt-monitor.py create "My Project" /path/to/project \
    --description "Project description" \
    --github "https://github.com/user/repo" \
    --customer "Customer Name" \
    --environment "production"
```

### 2. Skenování projektových souborů

```bash
python3 maj-projekt-monitor.py scan PROJECT_ID
```

### 3. Spuštění analýzy

```bash
# Jedna analýza
python3 maj-projekt-monitor.py analyze PROJECT_ID

# Analýza všech projektů
./maj-projekt-monitor-control.sh analyze
```

### 4. Zobrazení stavu

```bash
# Status projektu
python3 maj-projekt-monitor.py status PROJECT_ID

# Status systému
./maj-projekt-monitor-control.sh status
```

### 5. Práce s botem

```bash
# Spustit bota (autonomní režim)
./maj-projekt-monitor-control.sh bot

# Jednorázová analýza
python3 maj-projekt-monitor-bot.py --once

# Analyzovat specifický projekt
python3 maj-projekt-monitor-bot.py --analyze PROJECT_ID

# Spustit testy
python3 maj-projekt-monitor-bot.py --test PROJECT_ID

# Zkontrolovat kvalitu
python3 maj-projekt-monitor-bot.py --quality PROJECT_ID
```

### 6. Web dashboard

```bash
# Spustit dashboard
./maj-projekt-monitor-control.sh web

# Přístup: http://IP:5050
```

---

## 🗄️ Databázová struktura

### Tabulky v CDB

#### `projects`
Základní informace o projektech

| Sloupec | Typ | Popis |
|---------|-----|-------|
| id | INTEGER | Primary key |
| name | TEXT | Název projektu (unique) |
| description | TEXT | Popis |
| phase | TEXT | Aktuální fáze |
| created_at | TEXT | Datum vytvoření |
| updated_at | TEXT | Datum poslední aktualizace |
| github_repo | TEXT | GitHub URL |
| local_path | TEXT | Lokální cesta |
| customer | TEXT | Zákazník |
| environment | TEXT | Prostředí |
| quality_score | REAL | Celkové skóre kvality |
| status | TEXT | Status (active/archived) |

#### `project_programs`
Programy/skripty v projektu

| Sloupec | Typ | Popis |
|---------|-----|-------|
| id | INTEGER | Primary key |
| project_id | INTEGER | Foreign key |
| name | TEXT | Název souboru |
| path | TEXT | Relativní cesta |
| language | TEXT | Programovací jazyk |
| lines_of_code | INTEGER | Počet řádků |
| complexity_score | REAL | Skóre složitosti |
| last_modified | TEXT | Datum modifikace |
| git_hash | TEXT | Git commit hash |

#### `project_tests`
Záznamy testů

| Sloupec | Typ | Popis |
|---------|-----|-------|
| id | INTEGER | Primary key |
| project_id | INTEGER | Foreign key |
| program_id | INTEGER | Foreign key (optional) |
| test_name | TEXT | Název testu |
| test_type | TEXT | Typ (unit/integration/e2e/security) |
| status | TEXT | Výsledek (passed/failed/skipped) |
| started_at | TEXT | Začátek |
| completed_at | TEXT | Konec |
| duration_seconds | REAL | Trvání |
| error_message | TEXT | Chybová zpráva |
| coverage_percent | REAL | Procento pokrytí |

#### `project_todos`
TODO položky

| Sloupec | Typ | Popis |
|---------|-----|-------|
| id | INTEGER | Primary key |
| project_id | INTEGER | Foreign key |
| task | TEXT | Popis úkolu |
| status | TEXT | Status (todo/in_progress/done/blocked) |
| priority | INTEGER | Priorita (1-10) |
| created_at | TEXT | Vytvoření |
| updated_at | TEXT | Aktualizace |
| completed_at | TEXT | Dokončení |
| assigned_to | TEXT | Přiřazeno (claude-bot/human) |

#### `project_quality_scores`
Skóre kvality

| Sloupec | Typ | Popis |
|---------|-----|-------|
| id | INTEGER | Primary key |
| project_id | INTEGER | Foreign key |
| metric | TEXT | Metrika |
| score | REAL | Skóre |
| max_score | REAL | Maximum |
| calculated_at | TEXT | Čas výpočtu |
| details | TEXT | JSON detaily |

#### `project_analysis`
Hodinové analýzy

| Sloupec | Typ | Popis |
|---------|-----|-------|
| id | INTEGER | Primary key |
| project_id | INTEGER | Foreign key |
| analysis_time | TEXT | Čas analýzy |
| phase | TEXT | Fáze projektu |
| todos_completed | INTEGER | Dokončené TODO |
| todos_remaining | INTEGER | Zbývající TODO |
| tests_passed | INTEGER | Úspěšné testy |
| tests_failed | INTEGER | Neúspěšné testy |
| quality_score | REAL | Skóre kvality |
| issues_found | INTEGER | Nalezené problémy |
| recommendations | TEXT | JSON doporučení |
| progress_percent | REAL | Procento dokončení |

#### `project_deployments`
Nasazení

| Sloupec | Typ | Popis |
|---------|-----|-------|
| id | INTEGER | Primary key |
| project_id | INTEGER | Foreign key |
| environment | TEXT | Prostředí |
| version | TEXT | Verze |
| deployed_at | TEXT | Čas nasazení |
| deployed_by | TEXT | Kdo nasadil |
| status | TEXT | Status |
| rollback_available | BOOLEAN | Možnost rollbacku |
| notes | TEXT | Poznámky |

#### `project_security_tests`
Bezpečnostní testy

| Sloupec | Typ | Popis |
|---------|-----|-------|
| id | INTEGER | Primary key |
| project_id | INTEGER | Foreign key |
| test_type | TEXT | Typ testu |
| severity | TEXT | Závažnost |
| finding | TEXT | Nález |
| status | TEXT | Status |
| found_at | TEXT | Nalezeno |
| fixed_at | TEXT | Opraveno |

#### `project_git_commits`
Git commity

| Sloupec | Typ | Popis |
|---------|-----|-------|
| id | INTEGER | Primary key |
| project_id | INTEGER | Foreign key |
| commit_hash | TEXT | Hash commitu |
| author | TEXT | Autor |
| message | TEXT | Commit message |
| timestamp | TEXT | Čas |
| files_changed | INTEGER | Změněné soubory |
| lines_added | INTEGER | Přidané řádky |
| lines_deleted | INTEGER | Odebrané řádky |

---

## 🔌 API

### REST Endpoints

#### GET `/api/projects`
Získat všechny projekty

**Response:**
```json
{
  "projects": [
    {
      "id": 1,
      "name": "My Project",
      "phase": "development",
      "quality_score": 85.5,
      ...
    }
  ]
}
```

#### GET `/api/project/<id>`
Detail projektu

**Response:**
```json
{
  "project": { ... },
  "programs": [ ... ],
  "tests": [ ... ],
  "todos": [ ... ],
  "quality_scores": [ ... ],
  "recent_analyses": [ ... ]
}
```

#### GET `/api/project/<id>/analysis?hours=24`
Historie analýz

#### GET `/api/project/<id>/quality`
Metriky kvality

#### GET `/api/project/<id>/tests`
Výsledky testů

#### GET `/api/project/<id>/todos`
TODO seznam

#### GET `/api/project/<id>/structure`
Struktura projektu

#### GET `/api/overview`
Přehled systému

#### GET `/api/bot/status`
Status bota

### WebSocket Events

#### Client → Server

- `analyze_project` - Spustit analýzu projektu

#### Server → Client

- `project_update` - Aktualizace dat projektů (každých 5 sekund)
- `analysis_complete` - Analýza dokončena
- `error` - Chyba

---

## 🤖 Bot - Autonomní režim

Bot pracuje samostatně a provádí:

### Každou hodinu (60 min)
- ✅ Analýza všech aktivních projektů
- ✅ Vyhodnocení kvalitního stavu
- ✅ Kontrola fázových přechodů
- ✅ Generování doporučení
- ✅ Reportování problémů

### Každých 30 minut
- ✅ Spuštění testů
- ✅ Vyhodnocení výsledků
- ✅ Záznam do CDB

### Každé 2 hodiny (120 min)
- ✅ Hodnocení kvality kódu
- ✅ Kontrola dokumentace
- ✅ Bezpečnostní kontrola
- ✅ Výpočet celkového skóre

### Automatické akce

Bot automaticky:
- 📝 Vytváří TODO položky pro nové fáze
- 🔄 Přesouvá projekty mezi fázemi (když jsou splněny požadavky)
- 🔧 Pokouší se o automatické opravy běžných problémů
- 📊 Generuje statusové reporty
- 🚨 Upozorňuje na problémy

---

## 📊 GUI Dashboard

### Funkce

- **Real-time monitoring** - živé aktualizace každých 5 sekund
- **Color-coded status** - zelená/žlutá/červená signalizace
- **Interactive charts** - Chart.js grafy
- **Project cards** - přehledné karty projektů
- **Quality visualization** - vizualizace kvality
- **Progress tracking** - sledování postupu
- **Activity log** - log aktivit
- **Bot status** - stav bota

### Přístup

```bash
# Spustit dashboard
./maj-projekt-monitor-control.sh web

# Otevřít v prohlížeči
http://192.168.10.200:5050
```

### Barvy statusu

- 🟢 **Zelená** - Vše OK (quality ≥ 90%)
- 🟡 **Žlutá** - Varování (quality 60-89%)
- 🔴 **Červená** - Problém (quality < 60%)

---

## 🔗 Integrace s Claude CLI

### Automatické logování

Při použití Claude CLI se automaticky zapisuje do CDB:

```python
# V Claude CLI scriptech:
import sqlite3
from datetime import datetime

def log_to_cdb(component, event_type, details):
    conn = sqlite3.connect('/home/puzik/almquist-central-log/almquist.db')
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO events (timestamp, component, event_type, details)
        VALUES (?, ?, ?, ?)
    """, (
        datetime.now().isoformat(),
        component,
        event_type,
        json.dumps(details)
    ))
    conn.commit()
    conn.close()

# Použití:
log_to_cdb('maj-projekt-monitor', 'test_started', {
    'project_id': 1,
    'test_name': 'test_login'
})
```

---

## 📈 Bodovací systém

### Kvalitní metriky (0-100%)

#### Code Quality (0-100)
- Kontrola best practices
- TODO/FIXME count
- Debug print statements
- Code complexity

#### Test Coverage (0-100)
- Procento pokrytí testy
- Test/code ratio
- Test types diversity

#### Documentation (0-100)
- README.md existence (30%)
- docs/ directory (20%)
- Docstrings (50%)

#### Security (0-100)
- No hardcoded secrets
- No known vulnerabilities
- Secure defaults

### Celkové skóre

```
Overall Quality = (Code Quality + Test Coverage + Documentation + Security) / 4
```

### Fázové požadavky

- **Planning**: ≥ 50%
- **Design**: ≥ 60%
- **Development**: ≥ 70%
- **Testing**: ≥ 80%
- **Review**: ≥ 90%
- **Deployment**: ≥ 95%
- **Production**: 100%

---

## 🔒 Bezpečnost

### Ochrana dat

- Databáze pouze v lokálním filesystému
- Žádné citlivé údaje v logách
- API bez autentizace (pouze lokální síť)

### Doporučení

Pro produkci:
- Přidat autentizaci k Web GUI
- HTTPS pro dashboard
- Firewall rules
- Backup databáze

---

## 📝 Příklady

### Kompletní workflow

```bash
# 1. Start systému
./maj-projekt-monitor-control.sh start

# 2. Vytvoření projektu
./maj-projekt-monitor-control.sh create
# Input: name, path, description, etc.

# 3. Skenování
python3 maj-projekt-monitor.py scan 1

# 4. První analýza
python3 maj-projekt-monitor.py analyze 1

# 5. Bot se postará o zbytek automaticky
# - Hodinové analýzy
# - Testy
# - Kvalitní hodnocení
# - Fázové přechody

# 6. Sledování v GUI
# http://192.168.10.200:5050

# 7. Status check
./maj-projekt-monitor-control.sh status
```

---

## 🐛 Troubleshooting

### Bot se nespustí
```bash
# Check logs
tail -f ~/logs/maj-projekt-monitor-bot.log

# Check dependencies
pip3 install -r requirements.txt
```

### Web dashboard nedostupný
```bash
# Check if running
./maj-projekt-monitor-control.sh status

# Check port
ss -tulpn | grep 5050

# Check firewall
sudo ufw allow 5050
```

### Databáze nedostupná
```bash
# Check CDB path
ls -la /home/puzik/almquist-central-log/almquist.db

# Reinitialize
python3 maj-projekt-monitor.py
```

---

## 📞 Support

**Author**: Claude + Maj
**Date**: 2025-12-03
**Version**: 1.0.0

Pro otázky a problémy:
- Check logs: `~/logs/maj-projekt-monitor-*.log`
- Run status: `./maj-projekt-monitor-control.sh status`
- Review CDB: `sqlite3 ~/almquist-central-log/almquist.db`

---

## 🎯 Další vývoj

### Plánované funkce

- [ ] NER-based code analysis
- [ ] AI-powered auto-fixes
- [ ] Multi-language support
- [ ] Docker integration
- [ ] Slack/Email notifications
- [ ] Advanced security scanning
- [ ] Performance profiling
- [ ] Cost tracking
- [ ] Team collaboration features

---

**Enjoy MAJ-PROJEKT-MONITOR! 🚀**
