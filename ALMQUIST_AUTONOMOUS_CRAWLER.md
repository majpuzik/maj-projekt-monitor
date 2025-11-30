# ALMQUIST RAG - Autonomní Web Crawler

Inteligentní crawler který průběžně monitoruje české oficiální weby, detekuje změny, hodnotí zdroje a autonomně objevuje nové relevantní zdroje.

## 🎯 Koncept

**Základní myšlenka**: Systém funguje jako autonomní research agent - nejen pasivně scrape-uje známé weby, ale aktivně hledá nové zdroje, hodnotí jejich kvalitu a priority.

## 🏗️ Architektura

```
┌─────────────────────────────────────────────────────────────────┐
│           ALMQUIST AUTONOMOUS WEB CRAWLER SYSTEM                │
└─────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────┐
│  1. SOURCE REGISTRY                                          │
│     - Database všech známých zdrojů                          │
│     - Quality scores, priority, crawl frequency              │
│     - Change detection history                               │
└──────┬───────────────────────────────────────────────────────┘
       │
       v
┌──────────────────────────────────────────────────────────────┐
│  2. PRIORITY QUEUE                                           │
│     - Které weby crawlovat jako první                        │
│     - Dynamická prioritizace podle:                          │
│       • Quality score                                        │
│       • Update frequency                                     │
│       • Last crawl time                                      │
│       • Profession relevance                                 │
└──────┬───────────────────────────────────────────────────────┘
       │
       v
┌──────────────────────────────────────────────────────────────┐
│  3. INTELLIGENT CRAWLER                                      │
│     - Respektuje robots.txt                                  │
│     - Rate limiting (být slušný)                             │
│     - JavaScript rendering (Selenium pro SPA)                │
│     - Content extraction (BeautifulSoup)                     │
│     - Structured data parsing                                │
└──────┬───────────────────────────────────────────────────────┘
       │
       v
┌──────────────────────────────────────────────────────────────┐
│  4. CHANGE DETECTOR                                          │
│     - Diff detection (co se změnilo)                         │
│     - Semantic change analysis (je to důležitá změna?)       │
│     - Trigger alerts for important changes                   │
└──────┬───────────────────────────────────────────────────────┘
       │
       v
┌──────────────────────────────────────────────────────────────┐
│  5. CONTENT ANALYZER                                         │
│     - Extract structured information                         │
│     - Identify: amounts, dates, deadlines, processes         │
│     - Map to profession profiles                             │
│     - Generate chunks for RAG                                │
└──────┬───────────────────────────────────────────────────────┘
       │
       v
┌──────────────────────────────────────────────────────────────┐
│  6. SOURCE SCORER                                            │
│     - Quality metrics:                                       │
│       • Information density                                  │
│       • Authority (*.gov.cz > blog)                          │
│       • Freshness (last updated)                             │
│       • RAG contribution (kolik chunks vygenerovalo)         │
│     - Update crawl priority based on scores                  │
└──────┬───────────────────────────────────────────────────────┘
       │
       v
┌──────────────────────────────────────────────────────────────┐
│  7. LINK DISCOVERY AGENT                                     │
│     - Extract all links from crawled pages                   │
│     - Filter relevant domains (.gov.cz, .cz official)        │
│     - Relevance scoring (keywords, context)                  │
│     - Add new sources to registry                            │
│     - Autonomous expansion of knowledge base                 │
└──────┬───────────────────────────────────────────────────────┘
       │
       v
┌──────────────────────────────────────────────────────────────┐
│  8. RAG INTEGRATION                                          │
│     - Convert discovered info → RAG chunks                   │
│     - Update existing chunks with new data                   │
│     - Trigger embedding regeneration                         │
└──────────────────────────────────────────────────────────────┘
```

## 📦 Databázové Schéma

### `sources_registry.db`

```sql
-- Registry všech známých zdrojů
CREATE TABLE sources (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    url TEXT UNIQUE NOT NULL,
    domain TEXT,
    source_type TEXT,  -- government, chamber, forum, news

    -- Metadata
    title TEXT,
    description TEXT,
    language TEXT DEFAULT 'cs',

    -- Discovery
    discovered_at DATETIME,
    discovered_by TEXT,  -- crawler, manual, link_discovery
    parent_source_id INTEGER,  -- pokud discovered from another source

    -- Crawling
    last_crawled_at DATETIME,
    crawl_frequency_hours INTEGER DEFAULT 168,  -- default weekly
    next_crawl_at DATETIME,
    crawl_count INTEGER DEFAULT 0,

    -- Status
    is_active BOOLEAN DEFAULT 1,
    is_whitelisted BOOLEAN DEFAULT 0,  -- trusted sources
    is_blacklisted BOOLEAN DEFAULT 0,

    -- Scores
    quality_score REAL DEFAULT 0.5,  -- 0.0 - 1.0
    information_density REAL,  -- chunks per page
    authority_score REAL,  -- .gov.cz = 1.0, blog = 0.3
    freshness_score REAL,  -- jak často se updatuje
    rag_contribution_score REAL,  -- kolik užitečných chunks vygenerovalo

    -- Profession relevance
    profession_relevance TEXT,  -- JSON: {"zivnostnik": 0.8, "lekar": 0.2}

    FOREIGN KEY (parent_source_id) REFERENCES sources(id)
);

-- Historie crawlingu
CREATE TABLE crawl_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_id INTEGER NOT NULL,
    crawled_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    -- Status
    status TEXT,  -- success, failed, timeout, blocked
    http_status INTEGER,

    -- Content
    content_hash TEXT,  -- MD5 hash pro change detection
    content_length INTEGER,

    -- Extraction
    chunks_extracted INTEGER DEFAULT 0,
    links_found INTEGER DEFAULT 0,

    -- Performance
    response_time_ms INTEGER,

    FOREIGN KEY (source_id) REFERENCES sources(id)
);

-- Detekované změny
CREATE TABLE content_changes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_id INTEGER NOT NULL,
    detected_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    -- Change details
    change_type TEXT,  -- new_content, updated_content, deleted_content
    change_summary TEXT,

    -- Semantic analysis
    is_significant BOOLEAN,  -- je to důležitá změna?
    affected_professions TEXT,  -- JSON array

    -- Content
    old_content TEXT,
    new_content TEXT,
    diff_text TEXT,

    -- Processing
    processed BOOLEAN DEFAULT 0,
    rag_chunks_generated INTEGER DEFAULT 0,

    FOREIGN KEY (source_id) REFERENCES sources(id)
);

-- Discovered links (kandidáti na nové zdroje)
CREATE TABLE discovered_links (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    url TEXT UNIQUE NOT NULL,
    discovered_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    discovered_from_source_id INTEGER,

    -- Analysis
    relevance_score REAL,  -- 0.0 - 1.0
    context_text TEXT,  -- text kolem linku
    anchor_text TEXT,

    -- Status
    status TEXT DEFAULT 'pending',  -- pending, approved, rejected, crawled
    reviewed_by TEXT,
    reviewed_at DATETIME,

    -- If approved → becomes source
    promoted_to_source_id INTEGER,

    FOREIGN KEY (discovered_from_source_id) REFERENCES sources(id),
    FOREIGN KEY (promoted_to_source_id) REFERENCES sources(id)
);

-- Extracted information (před RAG integrací)
CREATE TABLE extracted_info (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_id INTEGER NOT NULL,
    extracted_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    -- Content
    info_type TEXT,  -- amount, deadline, process, requirement
    content TEXT,
    structured_data TEXT,  -- JSON

    -- Metadata
    profession_id TEXT,
    confidence_score REAL,

    -- RAG integration
    integrated_to_rag BOOLEAN DEFAULT 0,
    rag_chunk_id TEXT,

    FOREIGN KEY (source_id) REFERENCES sources(id)
);
```

## 🌐 Seed Sources (Iniciální zdroje)

### Tier 1: Vládní a státní instituce (.gov.cz)

```python
SEED_SOURCES = {
    # Daně a finance
    'financnisprava.cz': {
        'name': 'Finanční správa',
        'priority': 'critical',
        'crawl_frequency': 24,  # každý den
        'sections': [
            '/cs/dane',
            '/cs/danove-tiskopisy',
            '/cs/aktualni-informace'
        ],
        'authority_score': 1.0
    },

    # Sociální zabezpečení
    'cssz.cz': {
        'name': 'ČSSZ',
        'priority': 'critical',
        'crawl_frequency': 24,
        'sections': [
            '/minimalni-zalohy',
            '/socialni-pojisteni-osvc',
            '/aktualne'
        ],
        'authority_score': 1.0
    },

    # Zdravotní pojištění
    'vzp.cz': {
        'name': 'VZP',
        'priority': 'high',
        'crawl_frequency': 168,  # týdně
        'sections': [
            '/platci/informace/platby-pojistneho',
            '/aktuality'
        ],
        'authority_score': 0.9
    },

    # Práce
    'mpsv.cz': {
        'name': 'Ministerstvo práce a sociálních věcí',
        'priority': 'high',
        'crawl_frequency': 168,
        'sections': [
            '/web/cz/legislativa',
            '/web/cz/podnikani'
        ],
        'authority_score': 1.0
    },

    # Živnostenské podnikání
    'businessinfo.cz': {
        'name': 'BusinessInfo.cz',
        'priority': 'medium',
        'crawl_frequency': 168,
        'sections': [
            '/cs/clanky',
            '/cs/prakticke-rady'
        ],
        'authority_score': 0.8
    },

    # Komory
    'cak.cz': {
        'name': 'Česká advokátní komora',
        'priority': 'high',
        'crawl_frequency': 168,
        'sections': [
            '/scripts/search.asp',
            '/aktuality'
        ],
        'authority_score': 0.95,
        'profession': 'advokat'
    },

    'lkcr.cz': {
        'name': 'Lékařská komora ČR',
        'priority': 'high',
        'crawl_frequency': 168,
        'sections': [
            '/aktuality',
            '/legislativa'
        ],
        'authority_score': 0.95,
        'profession': 'soukromy_lekar'
    },

    'kdpcr.cz': {
        'name': 'Komora daňových poradců ČR',
        'priority': 'high',
        'crawl_frequency': 168,
        'sections': [
            '/pro-cleny',
            '/legislativa'
        ],
        'authority_score': 0.95,
        'profession': 'ucetni_danovy_poradce'
    },

    # Zákony
    'zakonyprolidi.cz': {
        'name': 'Zákony pro lidi',
        'priority': 'medium',
        'crawl_frequency': 168,
        'sections': [
            '/cs/aktualni',
            '/cs/nove-predpisy'
        ],
        'authority_score': 0.85
    }
}
```

## 🔍 Source Scoring Algoritmus

```python
def calculate_quality_score(source):
    """
    Quality Score = weighted average of:
    - Authority (40%)
    - Information Density (25%)
    - Freshness (20%)
    - RAG Contribution (15%)
    """

    # 1. Authority Score (domain trust)
    authority = get_authority_score(source.domain)
    # .gov.cz = 1.0, .cz chambers = 0.9, established sites = 0.7, blogs = 0.3

    # 2. Information Density
    if source.crawl_count > 0:
        avg_chunks = source.total_chunks_extracted / source.crawl_count
        # Normalize: 5 chunks/page = 1.0, 0 chunks = 0.0
        density = min(avg_chunks / 5.0, 1.0)
    else:
        density = 0.5  # default

    # 3. Freshness Score
    if source.last_updated:
        days_since_update = (now - source.last_updated).days
        # Fresh (0-7 days) = 1.0, stale (>90 days) = 0.2
        freshness = max(1.0 - (days_since_update / 90.0), 0.2)
    else:
        freshness = 0.5

    # 4. RAG Contribution
    if source.chunks_in_rag > 0:
        # How many chunks from this source are in RAG
        contribution = min(source.chunks_in_rag / 10.0, 1.0)
    else:
        contribution = 0.0

    # Weighted average
    quality_score = (
        authority * 0.40 +
        density * 0.25 +
        freshness * 0.20 +
        contribution * 0.15
    )

    return quality_score

def get_authority_score(domain):
    """Authority based on domain"""
    if domain.endswith('.gov.cz'):
        return 1.0
    elif domain in ['cak.cz', 'lkcr.cz', 'kdpcr.cz', 'czso.cz']:
        return 0.95
    elif domain in ['businessinfo.cz', 'zakonyprolidi.cz']:
        return 0.85
    elif domain.endswith('.cz'):
        return 0.6  # General Czech domain
    else:
        return 0.3  # International or unknown
```

## 🎯 Dynamic Crawl Frequency

```python
def calculate_next_crawl(source):
    """
    Adaptivní crawl frequency podle:
    - Quality score (vyšší = častěji)
    - Update frequency (často se mění = častěji crawl)
    - Last significant change
    """

    base_frequency = 168  # 1 týden (hours)

    # Adjust by quality
    if source.quality_score > 0.8:
        base_frequency = 24  # denně pro high-quality
    elif source.quality_score > 0.6:
        base_frequency = 72  # 3 dny

    # Adjust by update frequency
    if source.avg_days_between_changes < 7:
        base_frequency = min(base_frequency, 24)  # denně
    elif source.avg_days_between_changes < 30:
        base_frequency = min(base_frequency, 72)  # 3 dny

    # Critical sources - always daily
    if source.is_whitelisted or source.authority_score >= 0.95:
        base_frequency = 24

    return base_frequency
```

## 🔗 Autonomous Link Discovery

### Strategie 1: From Crawled Pages

```python
def discover_links_from_page(page_content, source_url):
    """
    Extract všechny linky z crawled page
    Filter podle relevance
    """
    soup = BeautifulSoup(page_content, 'html.parser')

    discovered = []

    for link in soup.find_all('a', href=True):
        href = link['href']

        # Make absolute URL
        full_url = urljoin(source_url, href)

        # Filter criteria
        if not is_potentially_relevant(full_url, link):
            continue

        # Extract context
        context = extract_context(link, soup)
        anchor_text = link.get_text(strip=True)

        # Score relevance
        relevance = score_link_relevance(full_url, anchor_text, context)

        if relevance > 0.3:  # threshold
            discovered.append({
                'url': full_url,
                'anchor_text': anchor_text,
                'context': context,
                'relevance_score': relevance
            })

    return discovered

def is_potentially_relevant(url, link):
    """Quick filters"""
    # Must be Czech domain or government
    if not ('.cz' in url or '.gov' in url):
        return False

    # Skip common irrelevant pages
    skip_patterns = [
        '/kontakt', '/cookie', '/gdpr', '/rss',
        '.pdf', '.jpg', '.png', '.zip'
    ]
    if any(pattern in url.lower() for pattern in skip_patterns):
        return False

    return True

def score_link_relevance(url, anchor_text, context):
    """
    Score 0.0 - 1.0 based on:
    - Keywords in URL
    - Keywords in anchor text
    - Keywords in surrounding context
    """
    keywords = [
        'živnost', 'daň', 'pojištění', 'OSVČ', 'podnikání',
        'zákon', 'vyhláška', 'legislativa', 'povinnost',
        'registrace', 'přiznání', 'evidence'
    ]

    score = 0.0
    text = f"{url} {anchor_text} {context}".lower()

    # Count keyword matches
    matches = sum(1 for kw in keywords if kw.lower() in text)
    score = min(matches / 5.0, 1.0)  # 5+ keywords = 1.0

    # Bonus for official domains
    if '.gov.cz' in url or 'komora' in url:
        score = min(score + 0.2, 1.0)

    return score
```

### Strategie 2: Search Engine Discovery

```python
def discover_sources_via_search(query, profession_id):
    """
    Use Google/Bing to find new sources

    Example queries:
    - "živnostenské podnikání postup 2025 site:.gov.cz"
    - "advokát registrace povinnosti site:.cak.cz"
    """

    # Google Custom Search API
    # Or DuckDuckGo (no API key needed)

    results = search_web(query, num_results=20)

    discovered = []
    for result in results:
        # Filter by domain authority
        if not is_trustworthy_domain(result['url']):
            continue

        discovered.append({
            'url': result['url'],
            'title': result['title'],
            'snippet': result['snippet'],
            'discovered_by': 'search_engine',
            'profession_id': profession_id,
            'relevance_score': 0.7  # from search = probably relevant
        })

    return discovered
```

## 🔄 Change Detection

```python
def detect_changes(source_id, new_content):
    """
    Detect what changed since last crawl
    """
    # Get last crawl
    last_crawl = get_last_successful_crawl(source_id)
    if not last_crawl:
        return {'type': 'new_source', 'significant': True}

    old_content = last_crawl.content

    # Quick check: content hash
    new_hash = hashlib.md5(new_content.encode()).hexdigest()
    if new_hash == last_crawl.content_hash:
        return {'type': 'no_change', 'significant': False}

    # Detailed diff
    diff = compute_diff(old_content, new_content)

    # Semantic analysis: is this important?
    is_significant = analyze_significance(diff)

    return {
        'type': 'content_updated',
        'significant': is_significant,
        'diff_summary': summarize_diff(diff),
        'changed_sections': extract_changed_sections(diff)
    }

def analyze_significance(diff):
    """
    Is this a significant change?

    Significant = obsahuje:
    - Změny čísel (částky, sazby)
    - Nové deadlines
    - Nové požadavky/povinnosti
    - Legislativní změny
    """
    significant_patterns = [
        r'\d+\s*Kč',  # částky v Kč
        r'\d+\s*%',   # procenta
        r'20\d{2}',   # roky
        r'deadline|termín|lhůta',
        r'nový|nová|nové',
        r'změna|aktualizace',
        r'povinnost|požadavek',
        r'zákon|vyhláška'
    ]

    diff_text = str(diff).lower()

    matches = sum(1 for pattern in significant_patterns
                  if re.search(pattern, diff_text))

    # 3+ matches = significant
    return matches >= 3
```

## 📊 Dashboard Metriky

```
┌─────────────────────────────────────────────────────────────┐
│  ALMQUIST AUTONOMOUS CRAWLER - Dashboard                   │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  📚 SOURCE REGISTRY                                         │
│     Total sources:          247                            │
│     Active:                 235                            │
│     Government (.gov.cz):   45                             │
│     Chambers:               8                              │
│     High quality (>0.8):    67                             │
│                                                             │
│  🕷️  CRAWLING ACTIVITY (Last 7 days)                       │
│     Pages crawled:          1,234                          │
│     Successful:             1,189 (96.4%)                  │
│     Failed:                 45                             │
│     Avg response time:      834ms                          │
│                                                             │
│  🔍 CHANGE DETECTION                                        │
│     Content changes:        23                             │
│     Significant changes:    7                              │
│     Awaiting review:        3                              │
│     Auto-integrated:        4                              │
│                                                             │
│  🔗 LINK DISCOVERY                                          │
│     New links found:        156 (this week)                │
│     High relevance (>0.7):  34                             │
│     Pending review:         12                             │
│     Promoted to sources:    8                              │
│                                                             │
│  📈 RAG CONTRIBUTION                                        │
│     Chunks extracted:       45 (this week)                 │
│     Integrated to RAG:      38                             │
│     Updated existing:       12                             │
│                                                             │
│  ⭐ TOP SOURCES (by quality score)                         │
│     1. financnisprava.cz       0.98                        │
│     2. cssz.cz                 0.96                        │
│     3. cak.cz                  0.94                        │
│     4. lkcr.cz                 0.93                        │
│     5. zakonyprolidi.cz        0.89                        │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## 🚀 Implementační Fáze

### Week 1: Core Infrastructure
- ✅ Database schema
- ✅ Seed sources initialization
- ✅ Basic crawler (requests + BeautifulSoup)

### Week 2: Quality & Scoring
- ✅ Source scoring system
- ✅ Dynamic crawl frequency
- ✅ Priority queue

### Week 3: Change Detection
- ✅ Content diffing
- ✅ Significance analysis
- ✅ Alert system

### Week 4: Link Discovery
- ✅ Link extraction from pages
- ✅ Relevance scoring
- ✅ Autonomous discovery

### Week 5: Content Extraction
- ✅ Structured data extraction
- ✅ Profession mapping
- ✅ Chunk generation

### Week 6: Integration
- ✅ RAG integration
- ✅ Dashboard
- ✅ Monitoring & alerts

## 🔐 Safety & Ethics

### Robots.txt Compliance
```python
from urllib.robotparser import RobotFileParser

def can_crawl(url):
    rp = RobotFileParser()
    rp.set_url(f"{get_base_url(url)}/robots.txt")
    rp.read()
    return rp.can_fetch("*", url)
```

### Rate Limiting
```python
# Max 1 request per second per domain
# Max 10 concurrent domains
# Exponential backoff on errors
```

### Respect Terms of Service
- Never scrape behind login (pokud není explicitně povoleno)
- Never DDoS (rate limiting)
- Cache aggressively (minimize requests)

---

**Created**: 2025-11-29
**Status**: Architecture Complete - Ready for Implementation
