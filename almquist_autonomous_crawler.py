#!/usr/bin/env python3
"""
ALMQUIST RAG - Autonomous Web Crawler
Inteligentní crawler pro průběžné monitorování českých oficiálních webů
"""

import psycopg2
import psycopg2.extras
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from urllib.robotparser import RobotFileParser
import hashlib
import time
import re
from datetime import datetime, timedelta
from pathlib import Path
import json

class AlmquistAutonomousCrawler:
    """Autonomní web crawler s prioritní frontou a source scoring"""

    def __init__(self, db_url="postgresql://almquist_user:almquist_secure_password_2025@localhost:5432/almquist_db"):
        self.db_url = db_url
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'AlmquistBot/1.0 (+https://almquist.cz/bot)'
        })

        # Rate limiting
        self.min_delay_seconds = 1.0  # Minimum 1 second between requests
        self.last_request_time = {}  # Per domain

        self.init_database()

    def init_database(self):
        """Inicializace databáze"""
        conn = psycopg2.connect(self.db_url)
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

        # Sources registry (already exists in PostgreSQL, skip if exists)
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS autonomous_sources (
            id SERIAL PRIMARY KEY,
            url TEXT UNIQUE NOT NULL,
            domain TEXT,
            source_type TEXT,

            title TEXT,
            description TEXT,

            discovered_at TIMESTAMP,
            discovered_by TEXT,
            parent_source_id INTEGER,

            last_crawled_at TIMESTAMP,
            crawl_frequency_hours INTEGER DEFAULT 168,
            next_crawl_at TIMESTAMP,
            crawl_count INTEGER DEFAULT 0,

            is_active BOOLEAN DEFAULT true,
            is_whitelisted BOOLEAN DEFAULT false,

            quality_score REAL DEFAULT 0.5,
            information_density REAL,
            authority_score REAL,
            freshness_score REAL,

            profession_relevance TEXT,

            FOREIGN KEY (parent_source_id) REFERENCES autonomous_sources(id)
        )
        ''')

        # Crawl history
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS autonomous_crawl_history (
            id SERIAL PRIMARY KEY,
            source_id INTEGER NOT NULL,
            crawled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

            status TEXT,
            http_status INTEGER,

            content_hash TEXT,
            content_length INTEGER,

            chunks_extracted INTEGER DEFAULT 0,
            links_found INTEGER DEFAULT 0,

            response_time_ms INTEGER,

            FOREIGN KEY (source_id) REFERENCES autonomous_sources(id)
        )
        ''')

        # Content changes
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS autonomous_content_changes (
            id SERIAL PRIMARY KEY,
            source_id INTEGER NOT NULL,
            detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

            change_type TEXT,
            change_summary TEXT,
            is_significant BOOLEAN,

            affected_professions TEXT,

            processed BOOLEAN DEFAULT false,

            FOREIGN KEY (source_id) REFERENCES autonomous_sources(id)
        )
        ''')

        # Discovered links
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS autonomous_discovered_links (
            id SERIAL PRIMARY KEY,
            url TEXT UNIQUE NOT NULL,
            discovered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            discovered_from_source_id INTEGER,

            relevance_score REAL,
            context_text TEXT,
            anchor_text TEXT,

            status TEXT DEFAULT 'pending',
            promoted_to_source_id INTEGER,

            FOREIGN KEY (discovered_from_source_id) REFERENCES autonomous_sources(id),
            FOREIGN KEY (promoted_to_source_id) REFERENCES autonomous_sources(id)
        )
        ''')

        # Extracted information chunks
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS autonomous_extracted_info (
            id SERIAL PRIMARY KEY,
            source_id INTEGER NOT NULL,
            extracted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

            text_content TEXT,
            chunk_type TEXT,
            relevance_score REAL,

            profession_relevance TEXT,

            added_to_rag BOOLEAN DEFAULT false,
            rag_chunk_id TEXT,

            FOREIGN KEY (source_id) REFERENCES autonomous_sources(id)
        )
        ''')

        conn.commit()
        conn.close()

    def seed_initial_sources(self):
        """Nasadit iniciální zdroje"""
        print("🌱 Seeding initial sources...")

        seed_sources = [
            {
                'url': 'https://www.financnisprava.cz/cs/dane',
                'title': 'Finanční správa - Daně',
                'source_type': 'government',
                'authority_score': 1.0,
                'crawl_frequency_hours': 24,
                'is_whitelisted': True
            },
            {
                'url': 'https://www.cssz.cz/web/cz/povinne-pojisteni-osvc',
                'title': 'ČSSZ - Povinné pojištění OSVČ',
                'source_type': 'government',
                'authority_score': 1.0,
                'crawl_frequency_hours': 24,
                'is_whitelisted': True
            },
            {
                'url': 'https://www.vzp.cz/platci/osoby-samostatne-vydelecne-cinne',
                'title': 'VZP - OSVČ',
                'source_type': 'health_insurance',
                'authority_score': 0.9,
                'crawl_frequency_hours': 168
            },
            {
                'url': 'https://www.cak.cz/scripts/search.asp',
                'title': 'ČAK - Česká advokátní komora',
                'source_type': 'chamber',
                'authority_score': 0.95,
                'crawl_frequency_hours': 168,
                'profession_relevance': json.dumps({'advokat': 1.0})
            },
            {
                'url': 'https://www.lkcr.cz',
                'title': 'LKCR - Lékařská komora ČR',
                'source_type': 'chamber',
                'authority_score': 0.95,
                'crawl_frequency_hours': 168,
                'profession_relevance': json.dumps({'soukromy_lekar': 1.0})
            },
            {
                'url': 'https://www.kdpcr.cz',
                'title': 'KDP ČR - Komora daňových poradců',
                'source_type': 'chamber',
                'authority_score': 0.95,
                'crawl_frequency_hours': 168,
                'profession_relevance': json.dumps({'ucetni_danovy_poradce': 1.0})
            },
            {
                'url': 'https://www.zakonyprolidi.cz/cs/aktualni',
                'title': 'Zákony pro lidi - Aktuální',
                'source_type': 'legal',
                'authority_score': 0.85,
                'crawl_frequency_hours': 168
            },
            {
                'url': 'https://www.businessinfo.cz/cs/clanky',
                'title': 'BusinessInfo.cz - Články',
                'source_type': 'info_portal',
                'authority_score': 0.8,
                'crawl_frequency_hours': 168
            }
        ]

        conn = psycopg2.connect(self.db_url)
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

        for source in seed_sources:
            domain = urlparse(source['url']).netloc

            try:
                cursor.execute('''
                INSERT INTO autonomous_sources (
                    url, domain, title, source_type,
                    authority_score, crawl_frequency_hours,
                    is_whitelisted, profession_relevance,
                    discovered_at, discovered_by,
                    next_crawl_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ''', (
                    source['url'],
                    domain,
                    source['title'],
                    source['source_type'],
                    source['authority_score'],
                    source['crawl_frequency_hours'],
                    source.get('is_whitelisted', False),
                    source.get('profession_relevance'),
                    datetime.now(),
                    'seed',
                    datetime.now()  # Crawl immediately
                ))
            except Exception as e:
                print(f"   ✗ Error seeding {source['url']}: {e}")

        conn.commit()
        conn.close()

        print(f"   ✓ Seeded {len(seed_sources)} initial sources")

    def can_crawl(self, url):
        """Check robots.txt compliance"""
        try:
            parsed = urlparse(url)
            robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"

            rp = RobotFileParser()
            rp.set_url(robots_url)
            rp.read()

            return rp.can_fetch("*", url)
        except:
            # If can't check robots.txt, allow (be permissive)
            return True

    def rate_limit_delay(self, domain):
        """Implement rate limiting per domain"""
        now = time.time()
        last_time = self.last_request_time.get(domain, 0)

        time_since_last = now - last_time

        if time_since_last < self.min_delay_seconds:
            sleep_time = self.min_delay_seconds - time_since_last
            time.sleep(sleep_time)

        self.last_request_time[domain] = time.time()

    def crawl_source(self, source_id):
        """Crawl jednoho zdroje"""
        conn = psycopg2.connect(self.db_url)
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

        cursor.execute('SELECT * FROM autonomous_sources WHERE id = %s', (source_id,))
        source = dict(cursor.fetchone())

        url = source['url']
        domain = source['domain']

        print(f"\n🕷️  Crawling: {url}")

        # Check robots.txt
        if not self.can_crawl(url):
            print(f"   ✗ Robots.txt disallows crawling")
            self._log_crawl(source_id, 'blocked', None, None)
            conn.close()
            return None

        # Rate limiting
        self.rate_limit_delay(domain)

        # Crawl
        start_time = time.time()

        try:
            response = self.session.get(url, timeout=10)
            response_time_ms = int((time.time() - start_time) * 1000)

            if response.status_code != 200:
                print(f"   ✗ HTTP {response.status_code}")
                self._log_crawl(source_id, 'failed', response.status_code, response_time_ms)
                conn.close()
                return None

            content = response.text
            content_hash = hashlib.md5(content.encode()).hexdigest()
            content_length = len(content)

            print(f"   ✓ Downloaded {content_length} bytes in {response_time_ms}ms")

            # Detect changes
            change_detected = self._detect_changes(source_id, content, content_hash)

            # Extract links
            links_found = self._discover_links(source_id, content, url)

            # Extract information from content
            source_type = source.get('source_type', 'unknown')
            profession_relevance = source.get('profession_relevance')
            chunks_extracted, extracted_data = self._extract_information(
                content, source_type, profession_relevance
            )

            if chunks_extracted > 0:
                print(f"   📊 Extracted {chunks_extracted} relevant chunks")
                # Store extracted data (could be saved to database or RAG directly)
                self._store_extracted_chunks(source_id, extracted_data)

            # Log successful crawl
            self._log_crawl(
                source_id, 'success', 200, response_time_ms,
                content_hash, content_length, chunks_extracted, links_found
            )

            # Update source
            self._update_source_after_crawl(source_id, source['crawl_frequency_hours'])

            conn.close()

            return {
                'status': 'success',
                'change_detected': change_detected,
                'links_found': links_found
            }

        except requests.Timeout:
            print(f"   ✗ Timeout")
            self._log_crawl(source_id, 'timeout', None, None)
            conn.close()
            return None

        except Exception as e:
            print(f"   ✗ Error: {e}")
            self._log_crawl(source_id, 'error', None, None)
            conn.close()
            return None

    def _detect_changes(self, source_id, content, content_hash):
        """Detect změny od posledního crawlu"""
        conn = psycopg2.connect(self.db_url)
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

        # Get last successful crawl
        cursor.execute('''
        SELECT content_hash FROM autonomous_crawl_history
        WHERE source_id = %s AND status = 'success'
        ORDER BY crawled_at DESC
        LIMIT 1
        ''', (source_id,))

        row = cursor.fetchone()

        if not row:
            # First crawl
            conn.close()
            return False

        last_hash = row[0]

        if content_hash == last_hash:
            # No change
            conn.close()
            return False

        # Change detected!
        print(f"   🔍 Content change detected")

        # Analyze significance (simplified for now)
        is_significant = self._analyze_significance(content)

        cursor.execute('''
        INSERT INTO autonomous_content_changes (
            source_id, detected_at, change_type,
            is_significant, processed
        ) VALUES (%s, %s, %s, %s, %s)
        ''', (
            source_id,
            datetime.now(),
            'content_updated',
            is_significant,
            False
        ))

        conn.commit()
        conn.close()

        return True

    def _analyze_significance(self, content):
        """Je to významná změna?"""
        # Look for significant patterns
        significant_patterns = [
            r'\d+\s*Kč',  # částky
            r'\d+\s*%',   # procenta
            r'20\d{2}',   # roky
            r'(deadline|termín|lhůta)',
            r'(nový|nová|nové|změna|aktualizace)',
            r'(povinnost|požadavek|registrace)'
        ]

        content_lower = content.lower()
        matches = sum(1 for pattern in significant_patterns
                     if re.search(pattern, content_lower))

        # 3+ matches = significant
        return matches >= 3

    def _extract_information(self, content, source_type, profession_relevance=None):
        """
        Extrahuje strukturované informace z HTML obsahu
        Returns: (chunks_extracted, extracted_data[])
        """
        soup = BeautifulSoup(content, 'html.parser')

        # Remove script and style elements
        for script in soup(["script", "style", "nav", "footer", "header"]):
            script.decompose()

        extracted_chunks = []

        # Extract text content in paragraphs and headings
        text_elements = []
        for elem in soup.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'li', 'td']):
            text = elem.get_text(strip=True)
            if len(text) > 30:  # Ignore short snippets
                text_elements.append(text)

        # Pattern-based extraction
        for text in text_elements:
            chunk_info = self._analyze_text_chunk(text, source_type, profession_relevance)

            if chunk_info and chunk_info['relevance_score'] > 0.3:
                extracted_chunks.append(chunk_info)

        return len(extracted_chunks), extracted_chunks

    def _analyze_text_chunk(self, text, source_type, profession_relevance):
        """Analyzuje text chunk a určí relevanci"""

        # Keywords by category
        financial_keywords = ['kč', 'platba', 'záloha', 'pojistné', 'daň', 'dph', 'sazba', 'tarif']
        legal_keywords = ['zákon', 'vyhláška', 'paragraf', '§', 'povinnost', 'nárok', 'právo']
        deadline_keywords = ['termín', 'lhůta', 'do', 'nejpozději', 'deadline']
        process_keywords = ['postup', 'návod', 'jak', 'kroky', 'formulář', 'registrace']

        text_lower = text.lower()

        # Score relevance
        relevance = 0.0
        chunk_type = 'general'

        # Check for amounts
        if re.search(r'\d+\s*(kč|korun|%|procent)', text_lower):
            relevance += 0.3
            chunk_type = 'financial_info'

        # Check for legal references
        if re.search(r'(zákon|vyhláška|§\s*\d+|paragrafu)', text_lower):
            relevance += 0.25
            chunk_type = 'legal_reference'

        # Check for deadlines
        if any(kw in text_lower for kw in deadline_keywords):
            relevance += 0.2
            if chunk_type == 'general':
                chunk_type = 'deadline'

        # Check for processes
        if any(kw in text_lower for kw in process_keywords):
            relevance += 0.15
            if chunk_type == 'general':
                chunk_type = 'process'

        # Keyword density
        all_keywords = financial_keywords + legal_keywords + deadline_keywords + process_keywords
        keyword_count = sum(1 for kw in all_keywords if kw in text_lower)
        relevance += min(keyword_count * 0.05, 0.3)

        # Bonus for government sources
        if source_type in ['government', 'chamber']:
            relevance *= 1.2

        # Normalize to 0-1
        relevance = min(relevance, 1.0)

        if relevance < 0.3:
            return None

        return {
            'text': text[:500],  # Limit length
            'chunk_type': chunk_type,
            'relevance_score': relevance,
            'profession_relevance': profession_relevance,
            'extracted_at': datetime.now().isoformat()
        }

    def _store_extracted_chunks(self, source_id, extracted_data):
        """Uložit extrahované chunks do databáze"""
        if not extracted_data:
            return

        conn = psycopg2.connect(self.db_url)
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

        for chunk in extracted_data:
            cursor.execute('''
            INSERT INTO autonomous_extracted_info (
                source_id, extracted_at, text_content, chunk_type,
                relevance_score, profession_relevance, added_to_rag
            ) VALUES (%s, %s, %s, %s, %s, %s, %s)
            ''', (
                source_id,
                datetime.now(),
                chunk['text'],
                chunk['chunk_type'],
                chunk['relevance_score'],
                chunk.get('profession_relevance'),
                False  # Not yet added to RAG
            ))

        conn.commit()
        conn.close()

    def _discover_links(self, source_id, content, base_url):
        """Discover nové linky z crawled page"""
        soup = BeautifulSoup(content, 'html.parser')

        links_found = 0
        conn = psycopg2.connect(self.db_url)
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

        for link in soup.find_all('a', href=True):
            href = link['href']

            # Make absolute URL
            full_url = urljoin(base_url, href)

            # Quick filter
            if not self._is_potentially_relevant(full_url):
                continue

            # Extract context
            anchor_text = link.get_text(strip=True)
            context = self._extract_context(link, soup)

            # Score relevance
            relevance = self._score_link_relevance(full_url, anchor_text, context)

            if relevance > 0.3:  # Threshold
                try:
                    cursor.execute('''
                    INSERT INTO autonomous_discovered_links (
                        url, discovered_at, discovered_from_source_id,
                        relevance_score, context_text, anchor_text,
                        status
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                    ''', (
                        full_url,
                        datetime.now(),
                        source_id,
                        relevance,
                        context[:500],  # Limit context length
                        anchor_text[:200],
                        'pending'
                    ))
                    links_found += 1
                except:
                    pass  # Duplicate, skip

        conn.commit()
        conn.close()

        if links_found > 0:
            print(f"   🔗 Discovered {links_found} new relevant links")

        return links_found

    def _is_potentially_relevant(self, url):
        """Quick filter pro relevanci"""
        # Must be Czech domain or government
        if not ('.cz' in url or '.gov' in url):
            return False

        # Skip common irrelevant patterns
        skip_patterns = [
            '/kontakt', '/cookie', '/gdpr', '/rss', '/feed',
            '.pdf', '.jpg', '.png', '.zip', '.doc',
            'facebook.com', 'twitter.com', 'linkedin.com'
        ]

        url_lower = url.lower()
        if any(pattern in url_lower for pattern in skip_patterns):
            return False

        return True

    def _extract_context(self, link, soup):
        """Extract text kolem linku"""
        # Get parent paragraph or div
        parent = link.find_parent(['p', 'div', 'section', 'article'])
        if parent:
            return parent.get_text(strip=True)[:500]
        return ""

    def _score_link_relevance(self, url, anchor_text, context):
        """Score relevance 0.0 - 1.0"""
        keywords = [
            'živnost', 'daň', 'pojištění', 'osvč', 'podnikání',
            'zákon', 'vyhláška', 'legislativa', 'povinnost',
            'registrace', 'přiznání', 'evidence', 'formulář'
        ]

        text = f"{url} {anchor_text} {context}".lower()

        # Count keyword matches
        matches = sum(1 for kw in keywords if kw in text)
        score = min(matches / 5.0, 1.0)

        # Bonus for official domains
        if '.gov.cz' in url or 'komora' in url:
            score = min(score + 0.2, 1.0)

        return score

    def _log_crawl(self, source_id, status, http_status, response_time_ms,
                   content_hash=None, content_length=None,
                   chunks_extracted=0, links_found=0):
        """Log crawl attempt"""
        conn = psycopg2.connect(self.db_url)
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

        cursor.execute('''
        INSERT INTO autonomous_crawl_history (
            source_id, crawled_at, status, http_status,
            content_hash, content_length,
            chunks_extracted, links_found, response_time_ms
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        ''', (
            source_id,
            datetime.now(),
            status,
            http_status,
            content_hash,
            content_length,
            chunks_extracted,
            links_found,
            response_time_ms
        ))

        # Update crawl count
        cursor.execute('''
        UPDATE autonomous_sources
        SET crawl_count = crawl_count + 1,
            last_crawled_at = %s
        WHERE id = %s
        ''', (datetime.now(), source_id))

        conn.commit()
        conn.close()

    def _update_source_after_crawl(self, source_id, crawl_frequency_hours):
        """Update next_crawl_at"""
        conn = psycopg2.connect(self.db_url)
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

        next_crawl = datetime.now() + timedelta(hours=crawl_frequency_hours)

        cursor.execute('''
        UPDATE autonomous_sources
        SET next_crawl_at = %s
        WHERE id = %s
        ''', (next_crawl, source_id))

        conn.commit()
        conn.close()

    def get_sources_to_crawl(self, limit=10):
        """Get sources ready to crawl (prioritní fronta)"""
        conn = psycopg2.connect(self.db_url)
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

        cursor.execute('''
        SELECT * FROM autonomous_sources
        WHERE is_active = true
        AND (next_crawl_at IS NULL OR next_crawl_at <= %s)
        ORDER BY
            is_whitelisted DESC,
            quality_score DESC,
            next_crawl_at ASC
        LIMIT %s
        ''', (datetime.now(), limit))

        sources = [dict(row) for row in cursor.fetchall()]
        conn.close()

        return sources

    def calculate_quality_score(self, source_id):
        """
        Výpočet quality score podle 4-faktorového algoritmu:
        - Authority (40%): Důvěryhodnost zdroje (.gov.cz = 1.0, blog = 0.3)
        - Info Density (25%): Kolik užitečných chunků na stránku
        - Freshness (20%): Jak často se aktualizuje
        - RAG Contribution (15%): Kolik chunků skutečně v RAG
        """
        conn = psycopg2.connect(self.db_url)
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

        # Get source data
        cursor.execute('SELECT * FROM autonomous_sources WHERE id = %s', (source_id,))
        source = dict(cursor.fetchone())

        # 1. Authority Score (40%) - already set manually
        authority = source.get('authority_score', 0.5)

        # 2. Info Density (25%) - chunks per successful crawl
        cursor.execute('''
        SELECT AVG(chunks_extracted) as avg_chunks
        FROM autonomous_crawl_history
        WHERE source_id = %s AND status = 'success'
        ''', (source_id,))

        row = cursor.fetchone()
        avg_chunks = float(row['avg_chunks']) if row and row['avg_chunks'] else 0.0

        # Normalize: 5+ chunks = perfect score
        info_density = min(avg_chunks / 5.0, 1.0)

        # 3. Freshness (20%) - update frequency
        cursor.execute('''
        SELECT COUNT(*) as change_count
        FROM autonomous_content_changes
        WHERE source_id = %s AND detected_at > NOW() - INTERVAL '30 days'
        ''', (source_id,))

        row = cursor.fetchone()
        recent_changes = row['change_count'] if row else 0

        # Normalize: 4+ changes/month = very fresh
        freshness = min(recent_changes / 4.0, 1.0)

        # 4. RAG Contribution (15%) - chunks actually in RAG
        # TODO: Implement when RAG integration is done
        # For now, use placeholder based on chunks extracted
        rag_contribution = min(avg_chunks / 10.0, 1.0)

        # Weighted average
        quality_score = (
            authority * 0.40 +
            info_density * 0.25 +
            freshness * 0.20 +
            rag_contribution * 0.15
        )

        # Update database
        cursor.execute('''
        UPDATE autonomous_sources
        SET quality_score = %s,
            information_density = %s,
            freshness_score = %s
        WHERE id = %s
        ''', (quality_score, info_density, freshness, source_id))

        conn.commit()
        conn.close()

        return quality_score

    def update_all_quality_scores(self):
        """Přepočítat quality scores pro všechny zdroje"""
        conn = psycopg2.connect(self.db_url)
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

        cursor.execute('SELECT id FROM autonomous_sources WHERE is_active = true')
        source_ids = [row[0] for row in cursor.fetchall()]
        conn.close()

        print(f"📊 Updating quality scores for {len(source_ids)} sources...")

        for source_id in source_ids:
            score = self.calculate_quality_score(source_id)
            print(f"   Source {source_id}: {score:.3f}")

    def run_crawl_cycle(self, max_sources=10):
        """Spustit jeden crawl cycle"""
        print("\n" + "="*70)
        print("🕷️  ALMQUIST AUTONOMOUS CRAWLER - Crawl Cycle")
        print("="*70)

        sources = self.get_sources_to_crawl(limit=max_sources)

        if not sources:
            print("\n✅ No sources ready to crawl")
            return

        print(f"\n📋 Found {len(sources)} sources to crawl")

        results = {
            'success': 0,
            'failed': 0,
            'changes_detected': 0,
            'links_discovered': 0
        }

        for source in sources:
            result = self.crawl_source(source['id'])

            if result:
                results['success'] += 1
                if result.get('change_detected'):
                    results['changes_detected'] += 1
                results['links_discovered'] += result.get('links_found', 0)
            else:
                results['failed'] += 1

            # Be nice - delay between sources
            time.sleep(2)

        # Update quality scores after crawling
        print("\n📊 Updating quality scores...")
        for source in sources:
            if source['id'] in [s['id'] for s in sources]:  # Only update crawled sources
                self.calculate_quality_score(source['id'])

        print("\n" + "="*70)
        print("CRAWL CYCLE SUMMARY")
        print("="*70)
        print(f"✓ Successful:         {results['success']}")
        print(f"✗ Failed:             {results['failed']}")
        print(f"🔍 Changes detected:   {results['changes_detected']}")
        print(f"🔗 New links found:    {results['links_discovered']}")
        print("="*70)


def main():
    """Main function"""
    crawler = AlmquistAutonomousCrawler()

    # Seed sources if empty
    print("Checking sources...")
    conn = psycopg2.connect(crawler.db_url)
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cursor.execute('SELECT COUNT(*) FROM autonomous_sources')
    count = cursor.fetchone()[0]
    conn.close()

    if count == 0:
        crawler.seed_initial_sources()

    # Run crawl cycle
    crawler.run_crawl_cycle(max_sources=5)


if __name__ == "__main__":
    main()
