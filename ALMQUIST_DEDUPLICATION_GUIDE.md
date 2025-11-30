# 🧹 ALMQUIST DEDUPLICATION GUIDE

## 📋 PŘEHLED

Kompletní systém pro prevenci a odstranění duplicitních dokumentů v RAG systému.

---

## 🔍 ANALÝZA SOUČASNÉHO STAVU

### Databáze Statistiky (2025-11-30)

| Typ | Total | Unique | Duplicity | Metoda |
|-----|-------|--------|-----------|--------|
| **Zákony** | 1,038 | 1,038 | 0 | ✅ case_number |
| **Soudní rozhodnutí (ID)** | 94,260 | 92,115 | 2,145 | ⚠️ case_number |
| **Soudní rozhodnutí (Content)** | 94,260 | 94,212 | 48 | ✅ SHA256 hash |

### Klíčová zjištění:

1. **Žádné duplicity v zákonech** ✅
2. **2,145 "duplicit" podle case_number** - často různé verze téhož rozhodnutí (opravy, aktualizace)
3. **Jen 48 skutečných duplicit** - identický obsah (content hash)

---

## 🛡️ STRATEGIE DEDUPLIKACE

### 1. Prevence (Merger s Content Hash)

**Upgraded Merger** `/home/puzik/almquist_rag_merger.py`:
- ✅ Kontroluje document ID (law_number, case_number)
- ✅ Kontroluje SHA256 content hash
- ✅ Ukládá content_hash do RAG metadata
- ✅ Blokuje duplicity v rámci jednoho batch merge

**Příklad:**
```python
# Stará verze (jen ID)
if doc_id not in existing_ids:
    add_document()

# Nová verze (ID + content hash)
if doc_id not in existing_ids and content_hash not in existing_hashes:
    add_document()
```

### 2. Detekce (Deduplication Tool)

**Nástroj:** `/home/puzik/almquist_deduplication_tool.py`

**Funkce:**
- Analyzuje databázi na duplicity (ID i content hash)
- Detekuje duplicity v RAG metadata
- Vyčistí databázi (ponechá nejnovější verzi)
- Vacuum databáze pro uvolnění místa
- Automatické zálohy před úpravami

---

## 🚀 POUŽITÍ

### 1. Analýza Duplicit (Read-Only)

```bash
# Rychlá analýza databáze
python3 /home/puzik/almquist_deduplication_tool.py --analyze
```

**Output:**
```
📋 LAWS: 1038 total, 1038 unique, 0 duplicates
⚖️  COURT DECISIONS: 94260 total, 92115 unique, 2145 duplicates
🔐 CONTENT HASH: 94212 unique, 47 groups, 48 duplicates
```

### 2. Analýza RAG Duplicit

```bash
# Zkontrolovat RAG metadata na duplicity
python3 /home/puzik/almquist_deduplication_tool.py --analyze-rag
```

### 3. Vyčištění Databáze (Dry-Run)

```bash
# Ukázat co by bylo vymazáno (bez změn)
python3 /home/puzik/almquist_deduplication_tool.py --deduplicate-db --dry-run
```

### 4. Skutečné Vyčištění Databáze

```bash
# VAROVÁNÍ: Mění databázi! (vytváří zálohu)
python3 /home/puzik/almquist_deduplication_tool.py --deduplicate-db
```

**Proces:**
1. ✅ Vytvoří zálohu databáze
2. 🔍 Najde duplicity podle case_number (ponechá nejnovější)
3. 🔐 Najde duplicity podle content hash (ponechá nejnovější)
4. 🗑️ Smaže duplicitní záznamy
5. ✅ Commit změn

### 5. Full Cleanup (All-in-One)

```bash
# Kompletní vyčištění: analyze → deduplicate → vacuum → re-analyze
python3 /home/puzik/almquist_deduplication_tool.py --full-cleanup
```

**Kroky:**
1. Analýza PŘED
2. Deduplikace
3. Vacuum (uvolnění místa)
4. Analýza PO (ověření)

### 6. Vacuum Databáze

```bash
# Uvolnit místo po smazání záznamů
python3 /home/puzik/almquist_deduplication_tool.py --vacuum
```

---

## 🔄 AUTOMATIZACE

### Cron Job pro Pravidelné Čištění

**Možnost 1: Měsíční vyčištění**

```bash
# Přidat do crontabu
crontab -e
```

```cron
# Full cleanup první den v měsíci ve 3:00
0 3 1 * * /home/puzik/miniconda3/bin/python3 /home/puzik/almquist_deduplication_tool.py --full-cleanup >> /home/puzik/logs/deduplication.log 2>&1
```

**Možnost 2: Týdenní analýza**

```cron
# Analýza každé pondělí v 1:00
0 1 * * 1 /home/puzik/miniconda3/bin/python3 /home/puzik/almquist_deduplication_tool.py --analyze >> /home/puzik/logs/deduplication_analysis.log 2>&1
```

---

## 📊 OČEKÁVANÉ VÝSLEDKY

### Před Deduplikací:

```
Database size: ~45 MB
Court decisions: 94,260 records
Duplicates: 2,145 (by ID), 48 (by content)
```

### Po Deduplikaci:

```
Database size: ~44 MB (úspora ~1 MB)
Court decisions: 94,212 records
Duplicates: 0
```

### RAG Impact:

Merger s content hash **automaticky blokuje** duplicity:
- ✅ Nové duplicity se **nepřidají** do RAG
- ✅ Existující RAG zůstává čistý
- ✅ Úspora storage a compute

---

## 🛡️ BEZPEČNOST

### Automatické Zálohy:

**Database Backup:**
```
/home/puzik/almquist_rag_backups/
└── legal_db_backup_20251130_174500.db
```

**RAG Backup (před merge):**
```
/home/puzik/almquist_rag_backups/
└── legal_rag_backup_20251130_180000/
    ├── embeddings.npy
    ├── faiss_index.bin
    └── metadata.json
```

### Restore z Backup:

```bash
# Obnovit databázi
cp /home/puzik/almquist_rag_backups/legal_db_backup_*.db \
   /home/puzik/almquist_legal_sources.db

# Obnovit RAG
cp -r /home/puzik/almquist_rag_backups/legal_rag_backup_*/* \
      /home/puzik/almquist_legal_rag/
```

---

## 🔬 DETEKCE METODY

### 1. Document ID Check (Fast)

```python
existing_ids = set()
for meta in existing_metadata:
    if meta['document_type'] == 'law':
        existing_ids.add(f"law_{meta['law_number']}")
    elif meta['document_type'] == 'court_decision':
        existing_ids.add(f"case_{meta['case_number']}")

if doc_id not in existing_ids:
    # Not a duplicate by ID
```

**Výhody:**
- ⚡ Velmi rychlé (O(1) lookup)
- 🎯 Detekuje duplicitní case_number

**Nevýhody:**
- ⚠️ Může označit různé verze jako duplicity
- ⚠️ Nedetekuje obsah-duplicity s různými ID

### 2. Content Hash Check (Precise)

```python
def compute_content_hash(text: str) -> str:
    return hashlib.sha256(text.encode('utf-8')).hexdigest()

existing_hashes = set()
for doc in documents:
    content_hash = compute_content_hash(doc['text'])
    if content_hash not in existing_hashes:
        # Not a duplicate by content
        existing_hashes.add(content_hash)
```

**Výhody:**
- ✅ 100% přesné (identický obsah = duplicita)
- ✅ Detekuje různá ID ale stejný obsah
- ✅ Umožňuje různé verze téhož rozhodnutí

**Nevýhody:**
- 🐌 Pomalejší (musí hashovat celý text)
- 💾 Vyšší paměťová náročnost

### 3. Kombinovaný Přístup (Doporučeno)

```python
# Merger používá OBA
if doc_id not in existing_ids and content_hash not in existing_hashes:
    add_document()
    existing_ids.add(doc_id)
    existing_hashes.add(content_hash)
```

**Výhody:**
- ⚡ Rychlé (ID check je O(1))
- ✅ Přesné (content hash je 100%)
- 🛡️ Dvojitá ochrana

---

## 📈 METRIKY & MONITORING

### Logy:

```bash
# Sledovat deduplikační logy
tail -f /home/puzik/logs/deduplication.log

# Sledovat merge logy (content hash v akci)
tail -f /home/puzik/logs/almquist_rag_merge.log
```

### Statistiky:

```bash
# Počet záznamů v databázi
sqlite3 /home/puzik/almquist_legal_sources.db \
  "SELECT COUNT(*) FROM court_decisions WHERE full_text IS NOT NULL"

# Počet unique case_numbers
sqlite3 /home/puzik/almquist_legal_sources.db \
  "SELECT COUNT(DISTINCT case_number) FROM court_decisions WHERE full_text IS NOT NULL"

# Velikost databáze
ls -lh /home/puzik/almquist_legal_sources.db
```

---

## 🎯 BEST PRACTICES

### 1. Pravidelná Analýza

```bash
# Týdenní check
python3 /home/puzik/almquist_deduplication_tool.py --analyze
```

### 2. Měsíční Cleanup

```bash
# První den v měsíci
python3 /home/puzik/almquist_deduplication_tool.py --full-cleanup
```

### 3. Před Velkým Merge

```bash
# Vyčistit PŘED merge velkého množství dat
python3 /home/puzik/almquist_deduplication_tool.py --deduplicate-db
python3 /home/puzik/almquist_rag_merger.py
```

### 4. Po Změně Crawlerů

```bash
# Když se změní crawler logika
python3 /home/puzik/almquist_deduplication_tool.py --analyze
```

---

## 🔧 TROUBLESHOOTING

### Problém: "Too many duplicates"

**Řešení:**
```bash
# 1. Analyzovat
python3 /home/puzik/almquist_deduplication_tool.py --analyze

# 2. Vyčistit databázi
python3 /home/puzik/almquist_deduplication_tool.py --full-cleanup

# 3. Rebuild RAG (pokud potřeba)
# RAG merger automaticky vynechá duplicity s content hash
```

### Problém: "Database growing too fast"

**Příčina:** Crawlery ukládají duplicity

**Řešení:**
```bash
# 1. Vypnout crawlery dočasně
# 2. Vyčistit databázi
python3 /home/puzik/almquist_deduplication_tool.py --full-cleanup

# 3. Zkontrolovat crawler logiku
# 4. Restart crawlerů
```

### Problém: "RAG queries returning duplicate results"

**Kontrola:**
```bash
# Analyzovat RAG metadata
python3 /home/puzik/almquist_deduplication_tool.py --analyze-rag
```

**Řešení:** RAG rebuild (pokud jsou duplicity v metadata)

---

## 📚 SOUBORY

| Soubor | Popis |
|--------|-------|
| `almquist_deduplication_tool.py` | Deduplikační nástroj |
| `almquist_rag_merger.py` | Merger s content hash prevencí |
| `almquist_legal_sources.db` | Databáze (může obsahovat duplicity) |
| `almquist_legal_rag/metadata.json` | RAG metadata (s content_hash) |

---

## ✅ ZÁVĚR

**Systém deduplikace je kompletní:**

1. ✅ **Prevence** - Merger blokuje duplicity pomocí content hash
2. ✅ **Detekce** - Deduplication tool analyzuje databázi i RAG
3. ✅ **Odstranění** - Automatické vyčištění s backup
4. ✅ **Monitoring** - Logy a statistiky
5. ✅ **Automatizace** - Cron jobs pro pravidelné čištění

**Doporučení:**
- Spustit `--full-cleanup` jednou měsíčně
- Sledovat logy pravidelně
- Nechat merger s content hash prevencí aktivní (již je)

---

*Dokument vytvořen: 2025-11-30*
*Status: ✅ Production Ready*
