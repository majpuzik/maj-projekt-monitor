# ALMQUIST Autonomous System - CDB Logging

**Automatické logování všech RAG updatů do Central Database**

---

## 📝 Přehled

Systém automaticky loguje každé přidání chunks do RAG v rámci denního běhu (5:00 AM).

---

## 🎯 Co se loguje

Každý den, když RAG Integration přidá nové chunks, vytvoří se CDB event s:

- **Zdroj:** Odkud byl chunk stažen (ČAK, LKCR, KDP ČR, Finanční správa...)
- **Profese:** Pro koho je obsah relevantní (advokat, soukromy_lekar, ucetni_danovy_poradce...)
- **Typy chunks:** Jaký typ obsahu (legal_reference, deadline, financial_info, process)
- **Počty:** Kolik chunks každého typu
- **Score:** Průměrná kvalita (relevance score)

---

## 📊 Formát Logu

### Metadata String:

```
RAG auto-update | Added X chunks | Source → Profession | type:count | avg_score:X.XX
```

### Příklad:

```
RAG auto-update | Added 3 chunks |
LKCR - Lékařská komora ČR → soukromy_lekar | legal_reference:2 | avg_score:0.66 |
ČAK - Česká advokátní komora → advokat | deadline:1 | avg_score:0.60
```

---

## 🤖 Kdy se loguje

**Automaticky každý den:**

```
04:00 → Crawler crawluje weby, extrahuje chunks
05:00 → RAG Integration:
        1. Filtruje chunks (relevance ≥ 0.6)
        2. Přidává do RAG
        3. Generuje embeddings
        4. Aktualizuje FAISS
        5. ✅ LOGUJE DO CDB
```

---

## 💾 CDB Event Detail

**Event Type:** `improvement`
**System:** `almquist`
**Version:** `rag-auto-add-YYYYMMDD` (datum běhu)
**Status:** `completed`

---

## 📈 Příklady Logů

### Příklad 1: Jeden zdroj, jeden typ

```
Event ID: 147
Type: improvement
Version: rag-auto-add-20251129
Metadata: RAG auto-update | Added 1 chunks |
          ČAK - Česká advokátní komora → advokat | deadline:1 | avg_score:0.60
```

### Příklad 2: Více zdrojů, různé typy

```
Event ID: 148
Type: improvement
Version: rag-auto-add-20251130
Metadata: RAG auto-update | Added 5 chunks |
          LKCR - Lékařská komora ČR → soukromy_lekar | legal_reference:3, deadline:1 | avg_score:0.72 |
          KDP ČR - Komora daňových poradců → ucetni_danovy_poradce | financial_info:1 | avg_score:0.65
```

### Příklad 3: Žádné nové chunks

```
(Žádný CDB event - loguje se pouze když jsou chunks přidány)
```

---

## 🔍 Jak Najít Logy

### V CDB:

```bash
# Zobrazit poslední RAG updates
sqlite3 /home/puzik/almquist-central-log/[database].db \
  "SELECT * FROM events WHERE version LIKE 'rag-auto-add-%'
   ORDER BY timestamp DESC LIMIT 10;"
```

### V Cron Logu:

```bash
# Kontrola RAG integration logu
tail -f /home/puzik/almquist_rag_integration_cron.log

# Hledat CDB log entries
grep "Logged to CDB" /home/puzik/almquist_rag_integration_cron.log
```

---

## 📊 Analytika

### Sledované Metriky:

1. **Počet chunks denně** - kolik nového obsahu přibývá
2. **Zdroje** - které weby přispívají nejvíce
3. **Profese** - pro které skupiny se obsah přidává
4. **Typy obsahu** - jaký typ informací převažuje
5. **Kvalita** - průměrné relevance score

### Příklad Analýzy:

```
Týden 1 (29.11 - 05.12):
- Celkem přidáno: 15 chunks
- Top zdroj: LKCR (8 chunks, avg 0.71)
- Top profese: soukromy_lekar (8 chunks)
- Top typ: legal_reference (9 chunks)
- Průměrná kvalita: 0.67
```

---

## 🎯 Výhody CDB Logging

### 1. **Viditelnost**
- Přesně víš, co se přidává do RAG
- Žádné "black box" operace

### 2. **Audit Trail**
- Kompletní historie všech změn
- Možnost zpětného dohledání

### 3. **Analytics**
- Trendy v obsahu
- Identifikace nejhodnotnějších zdrojů

### 4. **Debugging**
- Snadné ověření, že systém funguje
- Rychlá detekce problémů

### 5. **Reporting**
- Automatické reporty o růstu RAG
- Metriky pro management

---

## 🔧 Implementace

### Kód (v `almquist_crawler_rag_integration.py`):

```python
def log_to_cdb(self, chunks_added):
    """Logovat přidané chunks do CDB"""
    if not chunks_added:
        return

    # Seskupit podle zdroje a typu
    by_source_type = {}
    for chunk in chunks_added:
        source = chunk.get('source_title', 'Unknown')
        chunk_type = chunk.get('chunk_type', 'unknown')
        profession = self._extract_profession(chunk.get('profession_relevance'))
        score = chunk.get('relevance_score', 0.0)

        key = (source, profession)
        if key not in by_source_type:
            by_source_type[key] = {'types': {}, 'scores': []}

        by_source_type[key]['types'][chunk_type] = \
            by_source_type[key]['types'].get(chunk_type, 0) + 1
        by_source_type[key]['scores'].append(score)

    # Sestavit metadata string
    metadata_parts = []
    for (source, profession), data in by_source_type.items():
        types_str = ', '.join([f"{t}:{c}" for t, c in data['types'].items()])
        avg_score = sum(data['scores']) / len(data['scores'])
        metadata_parts.append(
            f"{source} → {profession} | {types_str} | avg_score:{avg_score:.2f}"
        )

    metadata = f"RAG auto-update | Added {len(chunks_added)} chunks | " + \
               " | ".join(metadata_parts)

    # Volat maj-almquist-log
    subprocess.run([
        '/home/puzik/almquist-central-log/maj-almquist-log',
        'event', 'improvement', 'almquist',
        f'rag-auto-add-{datetime.now().strftime("%Y%m%d")}',
        '--status', 'completed',
        '--metadata', metadata
    ], check=True, capture_output=True, text=True)
```

### Volání (v `run_integration`):

```python
# Save
if added_count > 0:
    print(f"\n3️⃣ Saving updated RAG system...")
    self.save_rag_system()

    # Log to CDB
    print(f"\n4️⃣ Logging to CDB...")
    self.log_to_cdb(added_chunks)  # ← Automatické logování
```

---

## ✅ Status

**Implementováno:** 2025-11-29
**Status:** ✅ Production Ready
**GitHub:** Commit `adbc93c`
**CDB Event:** ID=148

---

## 📚 Související Dokumentace

- `README.md` - Hlavní dokumentace
- `ALMQUIST_AUTONOMOUS_SYSTEM_COMPLETE.md` - Kompletní přehled
- `ALMQUIST_CRAWLER_SETUP.md` - Setup guide

---

**🎉 Kompletní viditelnost do autonomního systému!**
