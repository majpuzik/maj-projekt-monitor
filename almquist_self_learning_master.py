#!/usr/bin/env python3
"""
ALMQUIST RAG - Self-Learning Master Script
Orchestruje celý self-learning cyklus
Spouští se jako cron job každé pondělí v 2:00
"""

import sys
from datetime import datetime
from pathlib import Path

# Import našich modulů
from almquist_query_logger import AlmquistQueryLogger
from almquist_gap_detector import AlmquistGapDetector
from almquist_external_scraper import AlmquistExternalScraper

class AlmquistSelfLearningMaster:
    """Master orchestrátor self-learning procesu"""

    def __init__(self):
        self.logger = AlmquistQueryLogger()
        self.gap_detector = AlmquistGapDetector()
        self.external_scraper = AlmquistExternalScraper()

        self.log_file = Path("/home/puzik/almquist_self_learning.log")
        self.report = []

    def log(self, message, level="INFO"):
        """Logging"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_msg = f"[{timestamp}] [{level}] {message}"
        self.report.append(log_msg)
        print(log_msg)

    def step1_analyze_queries(self):
        """Krok 1: Analýza uživatelských dotazů"""
        self.log("\n" + "="*70)
        self.log("KROK 1: ANALÝZA UŽIVATELSKÝCH DOTAZŮ")
        self.log("="*70)

        # Get stats
        stats = self.logger.get_stats(days=7)

        self.log(f"Total queries (7 days): {stats['total_queries']}")
        self.log(f"Avg retrieval score: {stats['avg_best_score']:.3f}")
        self.log(f"Low quality queries: {stats['low_quality_count']}")
        self.log(f"Thumbs up rate: {stats['thumbs_up_rate']*100:.1f}%")
        self.log(f"Avg rating: {stats['avg_rating']:.2f}/5")

        # Check if enough data
        if stats['total_queries'] < 10:
            self.log("⚠️  Málo dotazů pro analýzu", level="WARN")
            return False

        if stats['low_quality_count'] < 5:
            self.log("✅ Většina dotazů má dobrou kvalitu")
            return False

        self.log(f"✓ Nalezeno {stats['low_quality_count']} low-quality dotazů pro analýzu")
        return True

    def step2_detect_gaps(self):
        """Krok 2: Detekce gaps"""
        self.log("\n" + "="*70)
        self.log("KROK 2: DETEKCE GAPS V RAG DATABÁZI")
        self.log("="*70)

        try:
            gaps = self.gap_detector.detect_gaps(min_queries_per_cluster=2)

            if not gaps:
                self.log("✅ Žádné gaps detekovány")
                return []

            self.log(f"✓ Detekováno {len(gaps)} gaps")

            # Top 3 gaps
            for i, gap in enumerate(gaps[:3], 1):
                self.log(f"  {i}. [{gap.get('profession', 'N/A')}] {gap['topic']}")
                self.log(f"     Queries: {gap['query_count']}, Score: {gap['avg_score']:.3f}")

            return gaps

        except Exception as e:
            self.log(f"✗ Chyba při detekci gaps: {e}", level="ERROR")
            return []

    def step3_scrape_external(self):
        """Krok 3: Scraping externích zdrojů"""
        self.log("\n" + "="*70)
        self.log("KROK 3: SCRAPING EXTERNÍCH ZDROJŮ")
        self.log("="*70)

        try:
            findings = self.external_scraper.scrape_all()

            self.log(f"✓ Nalezeno {len(findings)} relevantních zdrojů")

            # By source
            by_source = {}
            for finding in findings:
                source = finding.get('url', '').split('/')[2] if finding.get('url') else 'unknown'
                by_source[source] = by_source.get(source, 0) + 1

            for source, count in by_source.items():
                self.log(f"  {source}: {count}")

            return findings

        except Exception as e:
            self.log(f"✗ Chyba při scrapingu: {e}", level="ERROR")
            return []

    def step4_generate_suggestions(self, gaps, findings):
        """Krok 4: Generování návrhů na nové chunks"""
        self.log("\n" + "="*70)
        self.log("KROK 4: GENEROVÁNÍ NÁVRHŮ NA NOVÉ CHUNKS")
        self.log("="*70)

        if not gaps:
            self.log("⚠️  Žádné gaps k řešení", level="WARN")
            return []

        suggestions = []

        for gap in gaps[:5]:  # Top 5 gaps
            # Find relevant external sources
            relevant_sources = [
                f for f in findings
                if f.get('profession_id') == gap.get('profession')
            ]

            suggestion = {
                'topic': gap['topic'],
                'profession_id': gap.get('profession'),
                'query_count': gap['query_count'],
                'external_sources_count': len(relevant_sources),
                'status': 'pending_human_review'
            }

            suggestions.append(suggestion)

            self.log(f"✓ Návrh pro gap: {gap['topic']}")
            self.log(f"  Profese: {gap.get('profession')}")
            self.log(f"  External sources: {len(relevant_sources)}")

        self.log(f"\n✓ Vygenerováno {len(suggestions)} návrhů")

        # V produkci: zde by LLM generoval actual chunks
        # Pro teď jen logujeme návrhy

        return suggestions

    def step5_save_report(self):
        """Krok 5: Uložení reportu"""
        self.log("\n" + "="*70)
        self.log("KROK 5: ULOŽENÍ REPORTU")
        self.log("="*70)

        report_content = "\n".join(self.report)

        # Append to log file
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write("\n\n" + report_content + "\n")

        self.log(f"✓ Report uložen: {self.log_file}")

    def run_weekly_cycle(self):
        """Spustit celý týdenní self-learning cyklus"""
        self.log("\n" + "╔" + "="*68 + "╗")
        self.log("║" + " "*15 + "ALMQUIST RAG - SELF-LEARNING CYCLE" + " "*19 + "║")
        self.log("╚" + "="*68 + "╝")

        try:
            # Step 1: Analyze queries
            has_data = self.step1_analyze_queries()

            # Step 2: Detect gaps
            gaps = self.step2_detect_gaps() if has_data else []

            # Step 3: Scrape external
            findings = self.step3_scrape_external()

            # Step 4: Generate suggestions
            suggestions = self.step4_generate_suggestions(gaps, findings)

            # Step 5: Save report
            self.step5_save_report()

            # Summary
            self.log("\n" + "="*70)
            self.log("✅ SELF-LEARNING CYCLE COMPLETED")
            self.log("="*70)
            self.log(f"Gaps detected: {len(gaps)}")
            self.log(f"External findings: {len(findings)}")
            self.log(f"Suggestions generated: {len(suggestions)}")
            self.log("="*70)

            return True

        except Exception as e:
            self.log(f"✗ CRITICAL ERROR: {e}", level="ERROR")
            import traceback
            self.log(traceback.format_exc(), level="ERROR")
            return False


def main():
    """Hlavní funkce"""
    master = AlmquistSelfLearningMaster()
    success = master.run_weekly_cycle()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
