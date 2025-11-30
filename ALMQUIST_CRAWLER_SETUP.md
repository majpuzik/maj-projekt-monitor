# ALMQUIST AUTONOMOUS CRAWLER - Setup & Usage

## Přehled

Autonomní web crawler, který:
- **Crawluje** oficiální české weby (Finanční správa, ČSSZ, VZP, komory)
- **Hodnotí** kvalitu zdrojů podle 4 faktorů
- **Extrahuje** strukturované informace z HTML
- **Objevuje** nové relevantní zdroje autonomně
- **Detekuje** významné změny v obsahu

## Architektura

### Databáze: `almquist_sources.db`

**5 tabulek:**

1. **sources** - Registry všech zdrojů
   - URL, doména, typ zdroje
   - Quality score, authority, info density, freshness
   - Crawl frequency, next crawl time
   - Profession relevance

2. **crawl_history** - Historie všech crawlů
   - Status, HTTP kód, response time
   - Content hash, délka
   - Počet extrahovaných chunks a linků

3. **content_changes** - Detekované změny
   - Typ změny, je významná?
   - Affected professions
   - Processed status

4. **discovered_links** - Objevené linky
   - URL, relevance score
   - Anchor text, kontext
   - Status (pending/promoted)

5. **extracted_info** - Extrahované chunks
   - Text obsah, typ chunku
   - Relevance score
   - Added to RAG status

## Quality Scoring Algorithm

```python
Quality Score =
  Authority (40%) +       # .gov.cz = 1.0, blog = 0.3
  Info Density (25%) +    # chunks extrahované na stránku (5+ = 1.0)
  Freshness (20%) +       # změny za měsíc (4+ = 1.0)
  RAG Contribution (15%)  # chunks skutečně v RAG
```

**Výsledky:**
- LKCR: 0.78 (10 chunks, vysoká info density)
- ČAK: 0.575 (3 chunks, dobrá kvalita)
- Finanční správa: 0.4 (vysoká autorita, ale 0 chunks zatím)

## Content Extraction

**Typy chunků:**
- `financial_info` - Částky, platby, sazby (relevance +0.3)
- `legal_reference` - Zákony, vyhlášky, § (relevance +0.25)
- `deadline` - Termíny, lhůty (relevance +0.2)
- `process` - Postupy, návody, formuláře (relevance +0.15)

**Threshold:** Relevance > 0.3 → uloženo do databáze

**Bonus:** Government/chamber sources → relevance × 1.2

## Link Discovery

**Relevance scoring:**
```python
score = min(keyword_matches / 5.0, 1.0)

# Bonus for official domains
if '.gov.cz' in url or 'komora' in url:
    score += 0.2
```

**Keywords:** živnost, daň, pojištění, osvč, podnikání, komora, registr...

**Výsledky:**
- 67 links discovered from KDP ČR
- Relevance 0.4-0.6
- Nejlepší: "Daňové tiskopisy" (0.6), "Legislativa a metodika" (0.6)

## Change Detection

**Mechanismus:**
1. MD5 hash obsahu
2. Porovnání s předchozím crawlem
3. Semantic analysis významnosti

**Významná změna = 3+ patterns:**
- Částky (\\d+ Kč, %)
- Datumy (20\\d{2})
- Termíny (deadline, lhůta)
- Změny (nový, změna, aktualizace)
- Povinnosti (povinnost, požadavek)

## Cron Setup

**Frekvence:** Denně v 4:00 AM

```bash
# Crontab entry
0 4 * * * /home/puzik/almquist_autonomous_crawler_cron.sh

# Log
/home/puzik/almquist_crawler_cron.log

# Auto-rotace při 50,000+ řádcích
```

## Seed Sources

| URL | Authority | Profession | Frequency |
|-----|-----------|------------|-----------|
| financnisprava.cz/cs/dane | 1.0 | all | 24h |
| cssz.cz/povinne-pojisteni-osvc | 1.0 | all | 24h |
| vzp.cz/platci/osvc | 0.9 | all | 168h |
| cak.cz | 0.95 | advokat | 168h |
| lkcr.cz | 0.95 | soukromy_lekar | 168h |
| kdpcr.cz | 0.95 | ucetni_danovy_poradce | 168h |
| zakonyprolidi.cz/cs/aktualni | 0.85 | all | 168h |
| businessinfo.cz/cs/clanky | 0.8 | all | 168h |

## Použití

### Manuální spuštění

```bash
cd /home/puzik
python3 almquist_autonomous_crawler.py
```

### Kontrola výsledků

```bash
# Zobrazit quality scores
sqlite3 almquist_sources.db \
  "SELECT title, quality_score, information_density, authority_score
   FROM sources ORDER BY quality_score DESC;"

# Extrahované chunks
sqlite3 almquist_sources.db \
  "SELECT chunk_type, COUNT(*), AVG(relevance_score)
   FROM extracted_info GROUP BY chunk_type;"

# Discovered links
sqlite3 almquist_sources.db \
  "SELECT url, relevance_score FROM discovered_links
   WHERE status='pending' ORDER BY relevance_score DESC LIMIT 20;"

# Content changes
sqlite3 almquist_sources.db \
  "SELECT s.title, cc.detected_at, cc.is_significant
   FROM content_changes cc JOIN sources s ON cc.source_id = s.id
   WHERE cc.processed = 0;"
```

### Monitoring logu

```bash
# Real-time
tail -f /home/puzik/almquist_crawler_cron.log

# Poslední běh
tail -100 /home/puzik/almquist_crawler_cron.log
```

## Workflow

```
1. Get sources to crawl (priority queue)
   ↓ (order by: whitelisted, quality_score, next_crawl_at)

2. For each source:
   a. Check robots.txt compliance
   b. Rate limiting (1 req/sec per domain)
   c. Download content
   d. Detect changes (MD5 hash)
   e. Extract information (pattern-based)
   f. Discover links (relevance scoring)
   g. Log crawl history
   h. Update source metadata
   ↓

3. Update quality scores
   - Calculate info_density, freshness
   - Apply 4-factor weighted formula
   - Update database
   ↓

4. Summary report
```

## Performance

**Současný stav:**
- ✓ 8 seed sources
- ✓ 3/5 successful crawls (2× 404 - URL fixes pending)
- ✓ 13 chunks extracted (LKCR: 10, ČAK: 3)
- ✓ 67 links discovered
- ✓ Response times: 83-945ms

**Expected at scale:**
- 50+ sources
- 1000+ chunks/month
- 500+ discovered links/month
- 95%+ crawl success rate

## Next Steps

### 1. Fix 404 URLs
- ČSSZ: Find correct OSVČ page
- VZP: Find correct OSVČ page

### 2. RAG Integration
- Auto-add high-quality chunks (score > 0.7)
- Generate embeddings
- Update FAISS index

### 3. Human Review Interface
- Dashboard pro review discovered links
- Promote relevant links to sources
- Review extracted chunks before RAG

### 4. Enhanced Extraction
- LLM-based extraction (GPT-4/Claude)
- Structured data extraction (amounts, dates, laws)
- Multi-page crawling for detailed info

### 5. Monitoring & Alerts
- Email notifications for significant changes
- Quality score trends
- Failed crawl alerts

## Troubleshooting

**Crawler fails:**
```bash
# Check cron log
tail -50 /home/puzik/almquist_crawler_cron.log

# Test manually
python3 /home/puzik/almquist_autonomous_crawler.py

# Check database
sqlite3 almquist_sources.db "SELECT * FROM sources WHERE is_active = 1;"
```

**No chunks extracted:**
- Check source HTML structure
- Verify keywords in _analyze_text_chunk()
- Lower relevance threshold (current: 0.3)

**Too many discovered links:**
- Increase relevance threshold (current: 0.3 → 0.5)
- Improve keyword filtering
- Add domain blacklist

## Konfigurace

### Crawl Frequency

```python
# V seed_sources:
'crawl_frequency_hours': 24  # Daily
'crawl_frequency_hours': 168  # Weekly
```

### Relevance Thresholds

```python
# Content extraction (line ~446)
if chunk_info and chunk_info['relevance_score'] > 0.3:  # Default

# Link discovery (line ~593)
if relevance > 0.3:  # Threshold
```

### Rate Limiting

```python
# Between sources (line ~854)
time.sleep(2)  # 2 seconds between sources

# Per domain: 1 request/second (enforced via session)
```

## License & Credits

**ALMQUIST Autonomous Crawler**
Version: 1.0
Date: 2025-11-29
Author: ALMQUIST Team

Součást ALMQUIST RAG Self-Learning Ecosystem.
