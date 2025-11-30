# Claude CLI Logging v2 - Two-Phase Logging with Crash Recovery

## Přehled

Vylepšený logging systém pro Claude CLI s ochranou proti ztrátě dat při pádu systému.

### Klíčové vylepšení v2:

1. **Two-Phase Logging** - Zápis na 2x:
   - **PHASE 1 (PENDING):** Okamžitý zápis promptu při ENTER
   - **PHASE 2 (COMPLETED):** Update s akcemi po dokončení

2. **Crash Recovery** - Automatická detekce nedokončených promptů:
   - Kontrola při startu Claude CLI
   - Interaktivní nástroj pro opakování promptů
   - Možnost označit prompty jako abandoned

3. **Robustnost** - Žádná ztráta dat:
   - Prompt je uložen okamžitě (pending)
   - Pokud systém spadne → prompt zůstane v CDB
   - Uživatel může prompt zkopírovat a opakovat

---

## Komponenty

### 1. Logger v2 (`claude_activity_logger_v2.py`)

**Two-Phase Logging:**

```
User: [presses ENTER]
  → Logger: PHASE 1 - Write prompt to CDB (status: pending)
  
Claude: [executes actions]
  
User: [presses ENTER again]
  → Logger: PHASE 2 - Update previous event (status: completed)
               + PHASE 1 - Write new prompt (status: pending)
```

**Start:**
```bash
~/claude-logger-control.sh start
```

**Database Schema:**
```sql
-- Event lifecycle:
-- 1. INSERT with status='pending' when prompt received
-- 2. UPDATE to status='completed' when actions logged
-- 3. If crash → status stays 'pending'
```

### 2. Crash Recovery (`claude_crash_recovery.py`)

**Auto-check mode (startup hook):**
```bash
python3 ~/claude_crash_recovery.py --auto
```

Zobrazí varování, pokud existují pending prompty.

**Interactive mode:**
```bash
python3 ~/claude_crash_recovery.py
# nebo
~/claude-logger-control.sh recovery
```

**Interactive flow:**
1. Zobrazí všechny pending prompty
2. Umožní uživateli:
   - Zkopírovat a opakovat prompt
   - Označit jako abandoned (skip)
   - Nechat pending pro později (quit)

### 3. Claude CLI Wrapper (`claude-cli-with-recovery`)

Wrapper, který automaticky kontroluje pending prompty před startem.

**Usage:**
```bash
# Místo:
claude

# Použij:
~/claude-cli-with-recovery
```

**Setup alias (doporučeno):**
```bash
echo "alias claude='~/claude-cli-with-recovery'" >> ~/.bashrc
source ~/.bashrc
```

### 4. Control Script (`claude-logger-control.sh`)

Centrální správa loggeru.

**Commands:**
```bash
~/claude-logger-control.sh start          # Spustit logger
~/claude-logger-control.sh stop           # Zastavit
~/claude-logger-control.sh restart        # Restart
~/claude-logger-control.sh status         # Status
~/claude-logger-control.sh attach         # Připojit se
~/claude-logger-control.sh check-pending  # Zkontrolovat pending
~/claude-logger-control.sh recovery       # Interaktivní recovery
```

---

## Instalace a Setup

### Krok 1: Nasazení souborů

```bash
# Soubory už jsou v /home/puzik:
ls -lh ~/claude_activity_logger_v2.py
ls -lh ~/claude_crash_recovery.py
ls -lh ~/claude-cli-with-recovery
ls -lh ~/claude-logger-control.sh
```

### Krok 2: Spustit logger

```bash
~/claude-logger-control.sh start
```

### Krok 3: Setup auto-start (optional)

```bash
crontab -e
# Přidat:
@reboot sleep 15 && screen -dmS claude_logger_v2 python3 /home/puzik/claude_activity_logger_v2.py
```

### Krok 4: Setup Claude CLI wrapper (doporučeno)

```bash
echo "alias claude='~/claude-cli-with-recovery'" >> ~/.bashrc
source ~/.bashrc
```

Nyní při každém spuštění `claude` se automaticky zkontrolují pending prompty.

---

## Usage Scenarios

### Scenario 1: Normální provoz (bez crash)

```
1. User: "najdi všechny python soubory"
   → Logger: CREATE event #100 (status: pending)

2. Claude: [runs Glob, Read, etc.]

3. User: "zkomprimuj je do zip"
   → Logger: UPDATE event #100 (status: completed, actions: [Glob, Read])
            CREATE event #101 (status: pending)

4. Claude: [runs Bash to create zip]

5. User: [další prompt]
   → Logger: UPDATE event #101 (status: completed)
            ...
```

**Result:** Všechny události mají status `completed`.

### Scenario 2: System crash

```
1. User: "vytvoř nový projekt Django"
   → Logger: CREATE event #200 (status: pending)

2. Claude: [starts creating files...]

3. CRASH! (power loss, kernel panic, etc.)

4. [System reboot]

5. User: spustí Claude CLI
   → Wrapper: Zkontroluje CDB
   → Nalezen event #200 (status: pending)
   → Zobrazí varování

6. User: spustí recovery
   → python3 ~/claude_crash_recovery.py

7. Recovery zobrazí:
   ================================================================================
   ⚠️  CRASH RECOVERY: Incomplete Prompts Detected
   ================================================================================
   
   #1 - Event ID: 200
        Time: 2025-11-30 18:00:15
        Prompt: vytvoř nový projekt Django
   
   Your choice: 1

8. Recovery zobrazí full prompt:
   ================================================================================
   📋 PROMPT TO RETRY (Event #200)
   ================================================================================
   
   vytvoř nový projekt Django
   
   ================================================================================
   
   📝 Instructions:
     1. Copy the prompt above
     2. Paste it into your Claude CLI
     3. Press ENTER to retry
   
   Did you retry this prompt? (y/n/skip):

9. User: zkopíruje, spustí v Claude CLI, zadá 'y'
   → Event #200 se označí jako abandoned
   → Nový event #201 (pending) se vytvoří pro retry
```

**Result:** Žádná ztráta dat. Uživatel může opakovat nedokončenou práci.

### Scenario 3: Multiple crashes

```
Pokud systém spadne vícekrát, v CDB může být více pending events.
Recovery tool zobrazí všechny a umožní je zpracovat postupně.
```

---

## Database Schema

### Events table (relevant columns)

```sql
CREATE TABLE events (
    id INTEGER PRIMARY KEY,
    event_type TEXT,              -- 'claude_prompt'
    component TEXT,               -- 'claude-code'
    status TEXT,                  -- 'pending' | 'completed' | 'abandoned'
    metadata TEXT,                -- JSON with prompt, actions, etc.
    timestamp DATETIME
);
```

### Event statuses

- **pending:** Prompt byl zapsán, ale akce ještě nebyly dokončeny
- **completed:** Prompt + akce úspěšně zalogováno
- **abandoned:** Uživatel se rozhodl neopakovat (skip) nebo prompt byl duplicitní

### Query examples

```sql
-- Find all pending prompts
SELECT * FROM events
WHERE component = 'claude-code'
  AND event_type = 'claude_prompt'
  AND status = 'pending';

-- Find completed interactions from today
SELECT * FROM events
WHERE component = 'claude-code'
  AND status = 'completed'
  AND date(timestamp) = date('now');

-- Count by status
SELECT status, COUNT(*) FROM events
WHERE component = 'claude-code'
GROUP BY status;
```

---

## Troubleshooting

### Logger neběží
```bash
~/claude-logger-control.sh status
~/claude-logger-control.sh start
```

### Pending prompty se hromadí
```bash
# Interaktivní cleanup:
~/claude-logger-control.sh recovery

# Nebo ručně v CDB:
sqlite3 /home/puzik/almquist-central-log/almquist.db \
  "UPDATE events SET status='abandoned' WHERE status='pending' AND component='claude-code';"
```

### Logger loguje duplicity
```bash
# Zkontroluj, jestli neběží více instancí:
screen -list | grep claude_logger
```

### Recovery tool nefunguje
```bash
# Ověř přístup k CDB:
sqlite3 /home/puzik/almquist-central-log/almquist.db ".tables"

# Zkontroluj pending prompty ručně:
sqlite3 /home/puzik/almquist-central-log/almquist.db \
  "SELECT id, timestamp, status FROM events WHERE status='pending' LIMIT 5;"
```

---

## Porovnání v1 vs v2

| Feature | v1 (claude_activity_logger.py) | v2 (claude_activity_logger_v2.py) |
|---------|--------------------------------|-----------------------------------|
| Logging strategy | Single-phase (na konci) | Two-phase (pending → completed) |
| Crash protection | ❌ Žádná | ✅ Prompt uložen okamžitě |
| Data loss risk | ⚠️ Vysoké (při crash) | ✅ Žádné |
| Recovery tool | ❌ Ne | ✅ Ano |
| Status tracking | completed only | pending/completed/abandoned |

**Doporučení:** Používat v2 pro produkční nasazení.

---

## Files & Locations

```
/home/puzik/
├── claude_activity_logger_v2.py        # Logger v2 (two-phase)
├── claude_crash_recovery.py            # Recovery tool
├── claude-cli-with-recovery            # Wrapper s auto-check
├── claude-logger-control.sh            # Control script
└── CLAUDE_LOGGING_V2_README.md         # This file

/home/puzik/almquist-central-log/
└── almquist.db                         # Central Database

Screen sessions:
- claude_logger_v2                      # Running logger
```

---

## Changelog

### v2.0 (2025-11-30)

**Added:**
- Two-phase logging (pending → completed)
- Crash recovery tool
- Claude CLI wrapper with auto-check
- Control script with recovery commands
- Status tracking (pending/completed/abandoned)

**Changed:**
- Event_type: `claude_interaction` → `claude_prompt`
- Status field now required and tracked
- Prompt logged immediately (not delayed)

**Fixed:**
- Data loss on system crash
- No way to retry incomplete interactions

**Migration from v1:**
```bash
# Stop v1 logger
screen -S claude_logger -X quit

# Start v2 logger
~/claude-logger-control.sh start

# Setup alias for wrapper
echo "alias claude='~/claude-cli-with-recovery'" >> ~/.bashrc
```

---

## License & Credits

**Created:** 2025-11-30  
**Author:** Claude Code (Sonnet 4.5)  
**Database:** Almquist Central Log (CDB)  
**Status:** ✓ Production ready

---

## Quick Reference

### Start everything
```bash
~/claude-logger-control.sh start
echo "alias claude='~/claude-cli-with-recovery'" >> ~/.bashrc
```

### Check for incomplete work
```bash
~/claude-logger-control.sh check-pending
```

### Interactive recovery
```bash
~/claude-logger-control.sh recovery
```

### View logs
```bash
~/claude-logger-control.sh attach
# Ctrl+A D to detach
```

---

**Pro více informací, viz dokumentace v CDB:**
```bash
sqlite3 /home/puzik/almquist-central-log/almquist.db \
  "SELECT * FROM events WHERE component='claude-logging-v2' ORDER BY id DESC LIMIT 1;"
```
