#!/usr/bin/env python3
"""
ALMQUIST RAG - External Sources Scraper
Scraping relevantních informací z Reddit, fór a komunit
"""

import requests
from bs4 import BeautifulSoup
import json
import sqlite3
import time
from datetime import datetime, timedelta
import re

class AlmquistExternalScraper:
    """Scraper pro externí zdroje (Reddit, fóra)"""

    def __init__(self, db_path="/home/puzik/almquist_queries.db"):
        self.db_path = db_path
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36'
        })

        # Keywords pro filtrování
        self.keywords = {
            'zivnostnik_obecny': [
                'živnost', 'OSVČ', 'živnostník', 'podnikatel', 'daňové přiznání',
                'DPH', 'sociální pojištění', 'zdravotní pojištění', 'zálohy'
            ],
            'it_freelancer': [
                'freelancer', 'IT freelancer', 'OSVČ IT', 'fakturace', 'time tracking',
                'reverse charge', 'zahraniční klienti', 'trade license'
            ],
            'soukromy_lekar': [
                'soukromý lékař', 'privátní praxe', 'ordinace', 'zdravotní pojišťovna',
                'vykazování výkonů', 'IZIP', 'CŽV', 'lékař OSVČ'
            ],
            'advokat': [
                'advokát', 'ČAK', 'advokátní komora', 'právník OSVČ', 'právnická kancelář'
            ],
            'ucetni_danovy_poradce': [
                'daňový poradce', 'účetní', 'KDP ČR', 'vedení účetnictví', 'daňová evidence'
            ]
        }

    def scrape_reddit(self, subreddit='podnikani', time_filter='week', limit=25):
        """Scrape Reddit - nové posty"""
        print(f"🔍 Scraping Reddit: r/{subreddit}...")

        try:
            # Reddit JSON API (no auth needed for public posts)
            url = f"https://www.reddit.com/r/{subreddit}/top.json"
            params = {'t': time_filter, 'limit': limit}

            response = self.session.get(url, params=params, timeout=10)

            if response.status_code != 200:
                print(f"   ✗ Reddit API error: {response.status_code}")
                return []

            data = response.json()
            posts = []

            for post in data['data']['children']:
                post_data = post['data']

                # Extract relevant info
                posts.append({
                    'title': post_data['title'],
                    'selftext': post_data.get('selftext', ''),
                    'url': f"https://reddit.com{post_data['permalink']}",
                    'score': post_data['score'],
                    'num_comments': post_data['num_comments'],
                    'created_utc': post_data['created_utc']
                })

            print(f"   ✓ Nalezeno {len(posts)} postů")
            return posts

        except Exception as e:
            print(f"   ✗ Chyba: {e}")
            return []

    def scrape_podnikatel_cz_forum(self, limit=20):
        """Scrape podnikatel.cz diskuze"""
        print("🔍 Scraping podnikatel.cz/diskuze...")

        try:
            url = "https://www.podnikatel.cz/diskuze/"
            response = self.session.get(url, timeout=10)

            if response.status_code != 200:
                print(f"   ✗ HTTP {response.status_code}")
                return []

            soup = BeautifulSoup(response.text, 'html.parser')

            # Find discussion threads (structure může být různá, needs update)
            threads = soup.find_all('div', class_=re.compile('thread|discussion'))[:limit]

            posts = []
            for thread in threads:
                title_elem = thread.find('a')
                if title_elem:
                    posts.append({
                        'title': title_elem.text.strip(),
                        'url': title_elem.get('href', ''),
                        'source': 'podnikatel.cz'
                    })

            print(f"   ✓ Nalezeno {len(posts)} vláken")
            return posts

        except Exception as e:
            print(f"   ✗ Chyba: {e}")
            return []

    def calculate_relevance(self, text, profession_id):
        """Spočítat relevanci textu pro danou profesi"""
        if not profession_id or profession_id not in self.keywords:
            return 0.0

        keywords = self.keywords[profession_id]
        text_lower = text.lower()

        # Count keyword matches
        matches = sum(1 for kw in keywords if kw.lower() in text_lower)

        # Normalize
        relevance_score = min(matches / 3.0, 1.0)  # Max 1.0 if 3+ keywords

        return relevance_score

    def filter_by_keywords(self, posts, profession_id=None):
        """Filtrovat posty podle keywords"""
        filtered = []

        for post in posts:
            text = post.get('title', '') + ' ' + post.get('selftext', '')

            # Calculate relevance for each profession
            if profession_id:
                relevance = self.calculate_relevance(text, profession_id)
                if relevance > 0.3:  # Threshold
                    post['relevance_score'] = relevance
                    post['profession_id'] = profession_id
                    filtered.append(post)
            else:
                # Check all professions
                best_score = 0.0
                best_profession = None

                for prof_id in self.keywords:
                    score = self.calculate_relevance(text, prof_id)
                    if score > best_score:
                        best_score = score
                        best_profession = prof_id

                if best_score > 0.3:
                    post['relevance_score'] = best_score
                    post['profession_id'] = best_profession
                    filtered.append(post)

        return filtered

    def save_to_database(self, posts, source_type):
        """Uložit do databáze"""
        if not posts:
            return

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        for post in posts:
            content = json.dumps(post, ensure_ascii=False)
            keywords = ', '.join(self.keywords.get(post.get('profession_id', ''), []))

            cursor.execute('''
            INSERT INTO external_sources (
                source_type, source_url, content, keywords,
                relevance_score, processed
            ) VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                source_type,
                post.get('url', ''),
                content,
                keywords,
                post.get('relevance_score', 0.0),
                0  # Not processed yet
            ))

        conn.commit()
        conn.close()

        print(f"   💾 Uloženo {len(posts)} relevantních zdrojů")

    def scrape_all(self):
        """Scrape všechny zdroje"""
        print("\n" + "="*70)
        print("🕷️  ALMQUIST EXTERNAL SCRAPER")
        print("="*70)

        all_findings = []

        # 1. Reddit - r/podnikani
        print("\n1. Reddit - r/podnikani")
        reddit_posts = self.scrape_reddit('podnikani', time_filter='week', limit=25)
        filtered_reddit = self.filter_by_keywords(reddit_posts)
        print(f"   ✓ Relevantních: {len(filtered_reddit)}/{len(reddit_posts)}")
        self.save_to_database(filtered_reddit, 'reddit_podnikani')
        all_findings.extend(filtered_reddit)
        time.sleep(2)

        # 2. Reddit - r/czech (broader)
        print("\n2. Reddit - r/czech")
        reddit_czech = self.scrape_reddit('czech', time_filter='week', limit=50)
        filtered_czech = self.filter_by_keywords(reddit_czech)
        print(f"   ✓ Relevantních: {len(filtered_czech)}/{len(reddit_czech)}")
        self.save_to_database(filtered_czech, 'reddit_czech')
        all_findings.extend(filtered_czech)
        time.sleep(2)

        # 3. Podnikatel.cz forum
        print("\n3. Podnikatel.cz diskuze")
        forum_posts = self.scrape_podnikatel_cz_forum(limit=20)
        filtered_forum = self.filter_by_keywords(forum_posts)
        print(f"   ✓ Relevantních: {len(filtered_forum)}/{len(forum_posts)}")
        self.save_to_database(filtered_forum, 'forum_podnikatel_cz')
        all_findings.extend(filtered_forum)

        # Summary
        print("\n" + "="*70)
        print(f"✅ Celkem nalezeno {len(all_findings)} relevantních zdrojů")

        # By profession
        by_prof = {}
        for finding in all_findings:
            prof = finding.get('profession_id', 'unknown')
            by_prof[prof] = by_prof.get(prof, 0) + 1

        print("\nPo profesích:")
        for prof, count in sorted(by_prof.items(), key=lambda x: x[1], reverse=True):
            print(f"  {prof}: {count}")

        print("="*70)

        return all_findings

    def get_unprocessed_sources(self, limit=50):
        """Získat nezpracované zdroje"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute('''
        SELECT * FROM external_sources
        WHERE processed = 0
        ORDER BY relevance_score DESC, scraped_at DESC
        LIMIT ?
        ''', (limit,))

        sources = []
        for row in cursor.fetchall():
            sources.append(dict(row))

        conn.close()
        return sources

    def mark_as_processed(self, source_id):
        """Označit zdroj jako zpracovaný"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
        UPDATE external_sources
        SET processed = 1
        WHERE id = ?
        ''', (source_id,))

        conn.commit()
        conn.close()


def main():
    """Hlavní funkce"""
    scraper = AlmquistExternalScraper()

    # Scrape all sources
    findings = scraper.scrape_all()

    # Save summary
    if findings:
        summary_path = f"/home/puzik/external_findings_{datetime.now().strftime('%Y%m%d')}.json"
        with open(summary_path, 'w', encoding='utf-8') as f:
            json.dump(findings, f, indent=2, ensure_ascii=False)
        print(f"\n💾 Summary saved: {summary_path}")

    # Show unprocessed
    print("\n📋 Nezpracované zdroje v databázi:")
    unprocessed = scraper.get_unprocessed_sources(limit=10)
    for source in unprocessed:
        print(f"  [{source['source_type']}] {source['relevance_score']:.2f} - {source['source_url'][:60]}...")


if __name__ == "__main__":
    main()
