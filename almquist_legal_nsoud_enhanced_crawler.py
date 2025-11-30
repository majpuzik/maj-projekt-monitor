#!/usr/bin/env python3
"""
ALMQUIST Legal - Enhanced Nejvyšší Soud Crawler
Crawls more decisions by using sequential ID approach
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

from almquist_legal_court_decisions_crawler import CourtDecisionsCrawler
import time

class EnhancedNSCrawler(CourtDecisionsCrawler):
    """Enhanced NS crawler with ID-range support"""

    def crawl_by_id_range(self, start_id=24840, count=50):
        """
        Crawl decisions by sequential sbírkové číslo
        NS decisions have sequential IDs, so we can crawl them directly
        """
        print(f"\n📥 Crawling by ID range: {start_id} down to {start_id - count + 1}")

        success_count = 0
        failed_count = 0
        decisions_found = []

        for i in range(count):
            decision_id = start_id - i
            url = f"https://sbirka.nsoud.cz/sbirka/{decision_id}/"

            print(f"\n[{i+1}/{count}] ID: {decision_id}")
            print(f"   URL: {url}")

            decision_info = {
                'decision_id': str(decision_id),
                'url': url
            }

            # Try to crawl detail
            try:
                if self.crawl_decision_detail(decision_info):
                    # Check if we got actual content
                    if decision_info.get('case_number') and len(decision_info.get('full_text', '')) > 100:
                        # Save to database
                        db_id = self.save_decision(decision_info)
                        print(f"   ✓ Saved (DB ID: {db_id})")
                        print(f"   ✓ Case: {decision_info.get('case_number', 'N/A')}")
                        print(f"   ✓ Type: {decision_info.get('decision_type', 'N/A')}")
                        print(f"   ✓ Text: {len(decision_info.get('full_text', ''))} chars")
                        success_count += 1
                        decisions_found.append(decision_info)
                    else:
                        print(f"   ⚠️  Empty or invalid content")
                        failed_count += 1
                else:
                    print(f"   ✗ Failed (possibly 404 or restricted)")
                    failed_count += 1
            except Exception as e:
                print(f"   ✗ Error: {e}")
                failed_count += 1

            time.sleep(1.5)  # Be nice to server

        # Log crawl
        self.log_crawl('nsoud_sbirka_enhanced', 'court_decision', 'success', count, success_count)

        return decisions_found, success_count, failed_count

    def run_enhanced_crawl(self, start_id=24840, count=50):
        """Main enhanced crawl function"""
        print("=" * 70)
        print("⚖️  NEJVYŠŠÍ SOUD - ENHANCED CRAWLER")
        print("=" * 70)
        print(f"Target: {count} decisions")
        print(f"ID range: {start_id} → {start_id - count + 1}")

        decisions, success, failed = self.crawl_by_id_range(start_id=start_id, count=count)

        # Summary
        print("\n" + "=" * 70)
        print("✅ ENHANCED NS CRAWL COMPLETED")
        print("=" * 70)
        print(f"Attempted: {count}")
        print(f"Success:   {success} ({success/count*100:.1f}%)")
        print(f"Failed:    {failed} ({failed/count*100:.1f}%)")
        print("=" * 70)

        return decisions


def main():
    """Main function - crawl 50 decisions"""
    crawler = EnhancedNSCrawler()

    # Crawl 50 recent decisions
    # Start from ID 24840 (latest known) and go backwards
    decisions = crawler.run_enhanced_crawl(start_id=24840, count=50)

    # Show stats
    crawler.show_stats()

    print(f"\n✅ Crawled {len(decisions)} new decisions")


if __name__ == "__main__":
    main()
