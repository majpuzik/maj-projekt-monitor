# 🚨 DGS SPARK INCIDENT REPORT
## Memory Freeze & Recovery Analysis

**Datum:** 2025-11-17  
**Systém:** DGS Spark (Nvidia Jetson Orin AGX) - 192.168.10.200  
**Status:** ✅ RESOLVED

---

## 📋 Shrnutí

DGS Spark zamrzl kvůli memory leaku v `ingestion.py` skriptu, který zpracovával RAG knowledge base. Proces použil **121GB RAM** a způsobil, že systém byl nepoužitelný. Linux OOM Killer proces automaticky zabil a systém se zotavil.

---

## ⏱️ Timeline

| Čas | Událost |
|-----|---------|
| 15:37 | `ingestion.py` spuštěn |
| 15:54 | První pokus o SSH připojení - timeout |
| 16:32:39 | **OOM Killer zabil proces** |
| 16:52 | Systém se zotavil, SSH funguje |
| 17:54 | Analýza dokončena, opravy nasazeny |

---

## 🔍 Root Cause

### Problém
`ingestion.py` načítal všechny PDF chunky do RAM najednou bez batch processingu.

### Čísla
- **RAM použito:** 121GB / 119GB
- **SWAP použito:** 11GB / 15GB  
- **Load average:** 125+ (normál: 0.3)
- **Zpracovávaný soubor:** alquist_5.0.pdf (5.2MB)

### Technické detaily
Viz: `/home/puzik/almqist/rag/MEMORY_LEAK_ANALYSIS.md`

---

## ✅ Řešení

### 1. Opravený script
**Soubor:** `/home/puzik/almqist/rag/ingestion_fixed.py`

**Použití:**
\`\`\`bash
cd /home/puzik/almqist/rag
python3 ingestion_fixed.py
\`\`\`

**Změny:**
- ✅ Batch processing (50 chunků najednou)
- ✅ Explicit garbage collection
- ✅ Memory cleanup mezi batchi
- ✅ Progress reporting

### 2. Memory Monitoring
**Soubor:** `/home/puzik/monitor_memory.sh`

**Spustit monitoring:**
\`\`\`bash
# V novém terminálu:
/home/puzik/monitor_memory.sh

# Nebo na pozadí:
nohup /home/puzik/monitor_memory.sh &

# Logy:
tail -f /var/log/memory_alerts.log
\`\`\`

**Co dělá:**
- Kontroluje RAM každých 60s
- Alarmuje při >80% RAM usage
- Loguje top 5 memory-hungry procesů

### 3. Preventivní opatření

**Systemd service s limity (volitelné):**
\`\`\`bash
# Vytvoř /etc/systemd/system/ingestion.service
sudo nano /etc/systemd/system/ingestion.service

# Obsah:
[Unit]
Description=Alquist RAG Ingestion
After=network.target

[Service]
Type=simple
User=puzik
WorkingDirectory=/home/puzik/almqist/rag
ExecStart=/usr/bin/python3 ingestion_fixed.py
MemoryMax=64G
MemoryHigh=48G
CPUQuota=200%
Restart=on-failure

[Install]
WantedBy=multi-user.target

# Reload & enable:
sudo systemctl daemon-reload
sudo systemctl enable ingestion.service
sudo systemctl start ingestion.service
\`\`\`

---

## 📊 Aktuální stav systému

\`\`\`
Uptime: 1 day, 21 hours
Load: 0.20 (normální)
RAM: 4.2GB / 119GB (zdravé)
SWAP: 8.8GB / 15GB (postupně se uvolňuje)
\`\`\`

---

## 🎯 Doporučení do budoucna

1. **Vždy používej opravený script:**
   - ✅ `ingestion_fixed.py`
   - ❌ `ingestion.py` (DEPRECATED)

2. **Spusť memory monitoring:**
   - `nohup /home/puzik/monitor_memory.sh &`

3. **Před velkými úlohami:**
   - Zkontroluj dostupnou RAM: `free -h`
   - Spusť menší test nejdřív
   - Sleduj `htop` během běhu

4. **Nastav systemd limity** (viz výše)

5. **Pravidelně kontroluj logy:**
   - `/var/log/memory_alerts.log`
   - `journalctl -u ingestion.service`

---

## 📁 Vytvořené soubory

| Soubor | Popis |
|--------|-------|
| `/home/puzik/almqist/rag/ingestion_fixed.py` | Opravený ingestion script |
| `/home/puzik/almqist/rag/MEMORY_LEAK_ANALYSIS.md` | Technická analýza |
| `/home/puzik/monitor_memory.sh` | Memory monitoring script |
| `/home/puzik/DGS_SPARK_INCIDENT_REPORT.md` | Tento report |

---

## ✅ Checklist

- [x] Identifikován problém (memory leak)
- [x] Vytvořen opravený script
- [x] Vytvořen memory monitoring
- [x] Dokumentace vytvořena
- [x] Systém stabilní
- [ ] **TODO:** Spustit monitoring na pozadí
- [ ] **TODO:** Otestovat opravený script
- [ ] **TODO:** Nastav systemd limity (volitelné)

---

**Vytvořeno:** 2025-11-17 17:54  
**Autor:** AI Analysis (Claude)  
**Status:** ✅ INCIDENT RESOLVED
