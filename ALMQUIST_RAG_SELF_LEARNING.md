# ALMQUIST RAG - Self-Learning Systém

Automatické průběžné učení a vylepšování RAG databáze na základě reálného použití.

## 🎯 Koncept

**Základní myšlenka**: Systém se učí z každého dotazu uživatele a automaticky identifikuje mezery v pokrytí, navrhuje nové chunky a obohacuje databázi.

## 📊 Zdroje Učení

### 1. **Primární zdroj: Uživatelské dotazy (Almquist Pro Web)**

```
User Query → RAG Search → LLM Response → User Feedback → Learning Loop
```

**Co logujeme:**
- ✅ Kompletní dotaz uživatele
- ✅ Profese uživatele (pokud známá)
- ✅ Top-K retrieved chunks (které chunky RAG vrátil)
- ✅ Similarity scores
- ✅ Finální odpověď LLM
- ✅ User feedback (👍/👎, rating 1-5, follow-up questions)
- ✅ Timestamp, session ID

**Metriky úspěšnosti:**
- **Answer Quality Score** = user rating (1-5)
- **Retrieval Success** = similarity score top-1 chunk (>0.5 = dobrý)
- **User Satisfaction** = thumbs up/down ratio
- **Follow-up Rate** = % dotazů s follow-up (nižší = lepší)

### 2. **Sekundární zdroj: České online komunity**

#### A) **Reddit - r/podnikani, r/czech**
```python
Sources:
- r/podnikani (živnostníci, podnikatelé)
- r/czech (obecné české téma)
- r/pravnirady (právní dotazy)
```

**Scraping strategie:**
- Sledovat TOP posts týdně
- Filtrovat podle keywords: "živnost", "daňové přiznání", "OSVČ", "DPH", "pojištění"
- Extrahovat časté problémy a otázky

#### B) **Facebook skupiny**
```
Skupiny:
- "Živnostníci a podnikatelé v ČR" (~50K členů)
- "IT Freelanceři ČR" (~15K členů)
- "Lékaři v soukromé praxi" (~8K členů)
- "Daně a účetnictví pro začátečníky" (~30K členů)
```

**Přístup:**
- Manuální review (Facebook API je omezené)
- Scraping weekly top questions
- Identifikace pain points

#### C) **Fóra a weby**
```
- podnikatel.cz/diskuze
- penize.cz/diskuze
- finance.cz/diskuze
- lkcr.cz/forum (lékaři)
```

### 3. **Terciární zdroj: Změny v legislativě**

**Automatické sledování:**
- Finanční správa - nové vyhlášky
- ČSSZ - změny sazeb
- Komory (ČAK, LKCR, KDP) - nové požadavky
- ČSÚ - nové statistiky

## 🏗️ Architektura Self-Learning Systému

```
┌─────────────────────────────────────────────────────────────────┐
│                    ALMQUIST RAG ECOSYSTEM                       │
└─────────────────────────────────────────────────────────────────┘

┌──────────────┐
│  User Query  │
└──────┬───────┘
       │
       v
┌──────────────────────────────────────────────────────────────┐
│  1. QUERY LOGGER                                             │
│     - Log query, user, timestamp                             │
│     - Store in queries.db                                    │
└──────┬───────────────────────────────────────────────────────┘
       │
       v
┌──────────────────────────────────────────────────────────────┐
│  2. RAG RETRIEVAL (existing)                                 │
│     - Embedding query                                        │
│     - FAISS search → Top-K chunks                            │
└──────┬───────────────────────────────────────────────────────┘
       │
       v
┌──────────────────────────────────────────────────────────────┐
│  3. LLM RESPONSE (existing)                                  │
│     - Generate answer from retrieved context                 │
└──────┬───────────────────────────────────────────────────────┘
       │
       v
┌──────────────────────────────────────────────────────────────┐
│  4. USER FEEDBACK                                            │
│     - 👍/👎 buttons                                          │
│     - Rating 1-5 stars                                       │
│     - Optional comment                                       │
│     - "Was this helpful?" → Yes/No/Partial                   │
└──────┬───────────────────────────────────────────────────────┘
       │
       v
┌──────────────────────────────────────────────────────────────┐
│  5. FEEDBACK ANALYZER (nightly)                              │
│     - Aggregate daily feedback                               │
│     - Calculate success metrics                              │
│     - Identify low-quality responses                         │
└──────┬───────────────────────────────────────────────────────┘
       │
       v
┌──────────────────────────────────────────────────────────────┐
│  6. GAP DETECTOR                                             │
│     - Cluster unanswered/low-score queries                   │
│     - Identify missing topics                                │
│     - Detect profession-specific gaps                        │
└──────┬───────────────────────────────────────────────────────┘
       │
       v
┌──────────────────────────────────────────────────────────────┐
│  7. CONTENT SUGGESTER                                        │
│     - Search external sources (Reddit, forums)               │
│     - Scrape official sources for missing topics             │
│     - Generate draft chunks using LLM                        │
│     - Rank by importance/frequency                           │
└──────┬───────────────────────────────────────────────────────┘
       │
       v
┌──────────────────────────────────────────────────────────────┐
│  8. HUMAN REVIEW (weekly)                                    │
│     - Review suggested chunks                                │
│     - Approve/Reject/Edit                                    │
│     - Assign to profession profile                           │
└──────┬───────────────────────────────────────────────────────┘
       │
       v
┌──────────────────────────────────────────────────────────────┐
│  9. AUTO-ENRICHMENT                                          │
│     - Add approved chunks to RAG JSON                        │
│     - Re-generate embeddings                                 │
│     - Update FAISS index                                     │
│     - Deploy new version                                     │
└──────────────────────────────────────────────────────────────┘
```

## 📦 Databázové Schéma

### `queries.db`

```sql
-- Všechny uživatelské dotazy
CREATE TABLE queries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    session_id TEXT,
    user_id TEXT,
    profession_id TEXT,  -- zivnostnik_obecny, it_freelancer, etc.
    query_text TEXT NOT NULL,
    query_embedding BLOB,  -- vector embedding dotazu

    -- RAG retrieval
    top_chunks_ids TEXT,  -- JSON array chunk IDs
    top_chunks_scores TEXT,  -- JSON array similarity scores
    best_score REAL,

    -- LLM response
    response_text TEXT,
    response_time_ms INTEGER,

    -- User feedback
    feedback_type TEXT,  -- thumbs_up, thumbs_down, rating
    feedback_value INTEGER,  -- 1-5 for rating
    feedback_comment TEXT,
    follow_up_query_id INTEGER,  -- ID následného dotazu

    -- Flags
    is_answered BOOLEAN DEFAULT 1,
    needs_review BOOLEAN DEFAULT 0,
    is_low_quality BOOLEAN DEFAULT 0
);

-- Gaps v pokrytí
CREATE TABLE coverage_gaps (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    detected_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    topic_cluster TEXT,  -- "elektronická evidence tržeb"
    profession_id TEXT,
    query_count INTEGER,  -- kolik dotazů k tomuto tématu
    avg_score REAL,  -- průměrný retrieval score (nízký = gap)
    status TEXT,  -- detected, in_progress, resolved
    suggested_chunk_id INTEGER
);

-- Navržené nové chunks
CREATE TABLE suggested_chunks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    topic TEXT,
    profession_id TEXT,
    chunk_type TEXT,  -- pain_points, use_cases, obligations, etc.

    -- Zdrojové dotazy
    source_query_ids TEXT,  -- JSON array query IDs

    -- Navržený obsah
    suggested_text TEXT,
    confidence_score REAL,

    -- External sources
    external_sources TEXT,  -- JSON array URLs

    -- Human review
    status TEXT,  -- pending, approved, rejected, edited
    reviewed_by TEXT,
    reviewed_at DATETIME,
    final_text TEXT,

    -- Integration
    integrated_at DATETIME,
    chunk_id TEXT  -- ID v RAG databázi
);

-- External sources monitoring
CREATE TABLE external_sources (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_type TEXT,  -- reddit, facebook, forum
    source_url TEXT,
    scraped_at DATETIME,
    content TEXT,
    keywords TEXT,
    relevance_score REAL,
    processed BOOLEAN DEFAULT 0
);
```

## 🔍 Gap Detection Algoritmus

### Fáze 1: Identifikace low-quality responses

```python
Low Quality Query =
    (best_retrieval_score < 0.4) OR
    (user_feedback == thumbs_down) OR
    (user_rating <= 2) OR
    (follow_up_query_count >= 2)
```

### Fáze 2: Clustering podobných dotazů

```python
# Embedovat všechny low-quality queries
embeddings = [q.query_embedding for q in low_quality_queries]

# K-means clustering
from sklearn.cluster import DBSCAN
clusters = DBSCAN(eps=0.3, min_samples=3).fit(embeddings)

# Pro každý cluster:
for cluster in clusters:
    # Extrahovat common topic
    topic = extract_topic(cluster.queries)

    # Identifikovat gap
    if not exists_in_rag(topic):
        gaps.append({
            'topic': topic,
            'query_count': len(cluster.queries),
            'profession': most_common_profession(cluster.queries)
        })
```

### Fáze 3: Prioritizace gaps

```python
Gap Priority Score =
    (query_frequency * 10) +
    (profession_coverage_score * 5) +
    (external_mentions * 3) +
    (recency_bonus)
```

## 🤖 Automatické Generování Chunks

### Strategie A: LLM-based generation

```python
prompt = f"""
Na základě těchto uživatelských dotazů:
{queries_in_cluster}

A těchto externích zdrojů:
{reddit_posts + forum_discussions}

Vytvoř informativní chunk pro RAG databázi:

Profese: {profession_name}
Typ chunku: {chunk_type}
Téma: {detected_topic}

Format:
Profese: {profession_name}
{chunk_type_description}

{structured_information}

Požadavky:
- Fakticky přesné (čerpej z oficiálních zdrojů)
- České terminologie
- Konkrétní částky, deadlines, kroky
- Max 300 slov
"""

chunk = llm.generate(prompt)
```

### Strategie B: Template-based extraction

```python
# Pro obligations chunk
template = {
    'monthly': [
        {'type': '...', 'amount': ..., 'deadline': '...'}
    ],
    'annual': [
        {'type': '...', 'deadline': '...'}
    ]
}

# Extrahovat z official sources
data = scrape_and_fill_template(sources, template)
chunk = format_chunk(data, profession, 'obligations')
```

## 📈 Metriky Self-Learning Systému

### KPIs Dashboard

```
┌─────────────────────────────────────────────────────────────┐
│  ALMQUIST RAG - Self-Learning Dashboard                    │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  📊 RETRIEVAL QUALITY (Last 7 days)                        │
│     Average Top-1 Score:     0.68  (▲ +0.05 vs last week) │
│     Queries with score >0.5: 78%   (▲ +3%)                │
│     Low-quality queries:     145   (▼ -12)                │
│                                                             │
│  👍 USER SATISFACTION                                       │
│     Thumbs up rate:          84%   (▲ +2%)                 │
│     Average rating:          4.1/5 (▲ +0.2)               │
│     Follow-up rate:          18%   (▼ -3%)                │
│                                                             │
│  🔍 COVERAGE GAPS                                          │
│     Active gaps:             23                            │
│     New this week:           5                             │
│     Resolved this week:      8                             │
│                                                             │
│  📝 CONTENT SUGGESTIONS                                     │
│     Pending review:          12 chunks                     │
│     Approved this week:      7 chunks                      │
│     Integrated this week:    5 chunks                      │
│                                                             │
│  🌐 EXTERNAL SOURCES                                       │
│     Reddit posts scraped:    234 (this week)              │
│     Forum threads:           89                            │
│     Relevant findings:       43                            │
│                                                             │
│  📈 RAG GROWTH                                             │
│     Total chunks:            35 → 47 (+12 this month)     │
│     Professions covered:     5                             │
│     Total size:              160 KB → 215 KB              │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## 🔄 Weekly Self-Learning Cycle

### **Neděle 3:00** - Automatic Updates (existing)
- Scraping official sources
- Detect rate changes
- Update existing chunks

### **Pondělí 2:00** - Gap Detection
```bash
python3 almquist_gap_detector.py
# Output: detected_gaps_YYYYMMDD.json
```

### **Úterý 2:00** - External Sources Scraping
```bash
python3 almquist_external_scraper.py
# Scrape Reddit, forums
# Output: external_findings_YYYYMMDD.json
```

### **Středa 2:00** - Content Suggestion
```bash
python3 almquist_content_suggester.py
# Generate chunk suggestions
# Output: suggested_chunks_YYYYMMDD.json
```

### **Čtvrtek** - Human Review
```
→ Admin reviews suggested chunks
→ Approve/Reject/Edit in web interface
```

### **Pátek 2:00** - Auto-Integration
```bash
python3 almquist_auto_integrator.py
# Integrate approved chunks
# Re-generate embeddings
# Deploy
```

## 🎓 Konkrétní Use Cases

### Use Case 1: Detekce nové legislativy

```
Week 1:
- Uživatelé se ptají: "Co je to FIDI?" (Finanční Identita)
- RAG nemá data → low retrieval scores
- Gap detector identifikuje cluster

Week 2:
- External scraper najde diskuze na financnisprava.cz
- Content suggester vytvoří draft chunk o FIDI

Week 3:
- Admin schválí chunk
- Chunk integrován do profese "zivnostnik_obecny"
- Příští dotazy o FIDI → high retrieval score ✅
```

### Use Case 2: Profession-specific pain point

```
Queries:
- "Jak vyřešit problém s EET u lékaře?"
- "EET pro zdravotní služby - musím?"
- "Výjimka z EET pro soukromou praxi"

Gap Detection:
- Cluster: "EET pro lékaře"
- Profession: soukromy_lekar
- Current coverage: None

Content Suggestion:
- Scrape LKCR.cz stanovisko k EET
- Generate chunk type: pain_points
- Add to soukromy_lekar profile

Result:
- New chunk added
- Topic "EET" now covered
- Future queries answered correctly
```

### Use Case 3: Regional differences

```
Queries:
- "Kolik platí OSVČ v Praze?"
- "Je jiné pojištění v Brně?"
- "Regionální rozdíly v nákladech"

Observation:
- Existing data has regional income differences
- Missing: regional differences in costs

Suggestion:
- Add regional cost data
- Enhance chunks with local specifics
```

## 🛡️ Quality Control

### Automatické kontroly:

```python
def validate_suggested_chunk(chunk):
    checks = []

    # 1. Factual accuracy (compare with official sources)
    if not cite_official_source(chunk):
        checks.append("⚠️ Missing official source citation")

    # 2. No hallucination (verify all numbers)
    if contains_unverified_numbers(chunk):
        checks.append("⚠️ Contains unverified data")

    # 3. Language quality (Czech grammar)
    if grammar_errors(chunk) > 2:
        checks.append("⚠️ Grammar issues")

    # 4. Duplication (similarity with existing chunks)
    if max_similarity_with_existing(chunk) > 0.85:
        checks.append("⚠️ Too similar to existing chunk")

    # 5. Length (not too short, not too long)
    if not (100 < word_count(chunk) < 400):
        checks.append("⚠️ Length out of range")

    return checks
```

### Human-in-the-loop:

```
Každý suggested chunk:
→ Projde automatickými kontrolami
→ Admin dostane report
→ Zelená (all checks passed) = auto-approve
→ Žlutá (minor issues) = review required
→ Červená (major issues) = reject
```

## 🚀 Implementační Fáze

### **Fáze 1: Query Logging (Week 1)**
- ✅ Vytvořit queries.db
- ✅ Integrovat logging do Almquist Pro backend
- ✅ Přidat feedback buttons do frontendu

### **Fáze 2: Feedback Analysis (Week 2)**
- ✅ Nightly feedback analyzer
- ✅ Dashboard pro metriky
- ✅ Email reports

### **Fáze 3: Gap Detection (Week 3)**
- ✅ Clustering algoritmus
- ✅ Topic extraction
- ✅ Gap prioritization

### **Fáze 4: External Scraping (Week 4)**
- ✅ Reddit scraper
- ✅ Forum scraper
- ✅ Relevance filtering

### **Fáze 5: Content Suggestion (Week 5)**
- ✅ LLM-based chunk generation
- ✅ Validation pipeline
- ✅ Human review interface

### **Fáze 6: Auto-Integration (Week 6)**
- ✅ Approved chunks → JSON
- ✅ Re-embedding
- ✅ Deployment

## 📊 Expected Impact

### Po 3 měsících:

```
Metriky:
  Retrieval quality: 0.68 → 0.82 (+20%)
  User satisfaction: 84% → 92% (+8pp)
  Coverage gaps: 23 → 5 (-78%)
  Total chunks: 35 → 85 (+143%)

ROI:
  Manual chunk creation: 2 hours/chunk
  Auto-suggestion: 15 min review/chunk
  Time saved: 87.5%
```

### Po 6 měsících:

```
  Total chunks: 85 → 150
  Professions: 5 → 8 (přidány: architekti, inženýři, realitní makléři)
  User queries handled: 95%+ bez eskalace
  Self-learning cycles: 24 (weekly)
```

---

**Conclusion:**

Self-learning systém transformuje Almquist RAG z **statické databáze** na **živý, evolving knowledge base** který se učí z každé interakce a průběžně zlepšuje.

**Klíčové výhody:**
1. 🎯 **Zero manual effort** po initial setupu
2. 📈 **Continuous improvement** based on real usage
3. 🔍 **Proactive gap detection** before users complain
4. 🌐 **Community-driven** content from forums/Reddit
5. ✅ **Quality control** through validation pipeline

**Next Steps:**
→ Implementovat Query Logger (Week 1)
→ Dashboard pro monitoring (Week 2)
→ Gap Detector (Week 3)

---

**Created**: 2025-11-29
**Status**: Design Complete - Ready for Implementation
