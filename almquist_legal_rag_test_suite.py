#!/usr/bin/env python3
"""
ALMQUIST Legal RAG - Test Suite
Comprehensive testing of legal RAG search quality
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

from almquist_legal_rag_integration import LegalRAGIntegration
import json
from datetime import datetime

class LegalRAGTestSuite:
    """Comprehensive test suite for Legal RAG"""

    def __init__(self):
        self.rag = LegalRAGIntegration()
        self.test_queries = {
            # Civil law queries
            'civil': [
                'dědictví',
                'kupní smlouva',
                'výživné',
                'rozvod manželství',
                'vlastnické právo',
                'věcné břemeno'
            ],
            # Criminal law queries
            'criminal': [
                'trestný čin krádeže',
                'vražda',
                'přečin',
                'zločin',
                'trestní odpovědnost',
                'podmíněný trest'
            ],
            # Commercial law queries
            'commercial': [
                'obchodní korporace',
                'společnost s ručením omezeným',
                'insolvence',
                'úpadek',
                'konkurz',
                'valná hromada'
            ],
            # Administrative law queries
            'administrative': [
                'správní řízení',
                'správní trestání',
                'přestupek',
                'odvolání',
                'kasační stížnost',
                'obnova řízení'
            ],
            # Labor law queries
            'labor': [
                'pracovní smlouva',
                'výpověď',
                'odstupné',
                'dovolená',
                'mzda',
                'pracovní doba'
            ],
            # Tax law queries
            'tax': [
                'daň z příjmů',
                'DPH',
                'daňové přiznání',
                'daňová kontrola',
                'penále',
                'odpočet daně'
            ],
            # Court decisions queries
            'court_decisions': [
                'rozsudek nejvyššího soudu',
                'nález ústavního soudu',
                'usnesení',
                'ECLI',
                'právní věta',
                'dovolání'
            ]
        }

    def run_single_query(self, query, top_k=3):
        """Run single query and return results"""
        try:
            results = self.rag.search(query, top_k=top_k)
            return {
                'query': query,
                'status': 'success',
                'results_count': len(results),
                'top_result': results[0] if results else None,
                'results': results
            }
        except Exception as e:
            return {
                'query': query,
                'status': 'error',
                'error': str(e)
            }

    def run_category_tests(self, category, queries):
        """Run all queries in a category"""
        print(f"\n{'='*70}")
        print(f"📋 Testing category: {category.upper()}")
        print(f"{'='*70}")

        results = []
        for i, query in enumerate(queries, 1):
            print(f"\n[{i}/{len(queries)}] Query: '{query}'")
            result = self.run_single_query(query, top_k=3)

            if result['status'] == 'success':
                if result['results_count'] > 0:
                    top = result['top_result']
                    print(f"   ✓ Top result: {top['metadata'].get('law_name') or top['metadata'].get('case_number', 'Unknown')}")
                    print(f"   ✓ Score: {top['score']:.3f}")
                    print(f"   ✓ Type: {top['metadata'].get('document_type', 'unknown')}")

                    # Summarize all results
                    for j, res in enumerate(result['results'][:3], 1):
                        doc_type = res['metadata'].get('document_type', 'unknown')
                        if doc_type == 'law':
                            doc_id = res['metadata'].get('law_name', 'Unknown')
                        else:
                            doc_id = res['metadata'].get('case_number', 'Unknown')
                        print(f"      {j}. [{doc_id}] (score: {res['score']:.3f})")
                else:
                    print(f"   ⚠️  No results found")
            else:
                print(f"   ✗ Error: {result['error']}")

            results.append(result)

        return results

    def run_all_tests(self):
        """Run all test categories"""
        print("="*70)
        print("🧪 ALMQUIST LEGAL RAG - COMPREHENSIVE TEST SUITE")
        print("="*70)
        print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        all_results = {}

        for category, queries in self.test_queries.items():
            category_results = self.run_category_tests(category, queries)
            all_results[category] = category_results

        # Summary
        self.print_summary(all_results)

        return all_results

    def print_summary(self, all_results):
        """Print test summary"""
        print("\n" + "="*70)
        print("📊 TEST SUMMARY")
        print("="*70)

        total_queries = 0
        total_success = 0
        total_with_results = 0
        total_errors = 0

        category_stats = {}

        for category, results in all_results.items():
            success = sum(1 for r in results if r['status'] == 'success')
            with_results = sum(1 for r in results if r['status'] == 'success' and r['results_count'] > 0)
            errors = sum(1 for r in results if r['status'] == 'error')

            category_stats[category] = {
                'total': len(results),
                'success': success,
                'with_results': with_results,
                'errors': errors
            }

            total_queries += len(results)
            total_success += success
            total_with_results += with_results
            total_errors += errors

        print(f"\nOverall:")
        print(f"  Total queries:        {total_queries}")
        print(f"  Successful:           {total_success} ({total_success/total_queries*100:.1f}%)")
        print(f"  With results:         {total_with_results} ({total_with_results/total_queries*100:.1f}%)")
        print(f"  Errors:               {total_errors}")

        print(f"\nBy category:")
        for category, stats in category_stats.items():
            print(f"\n  {category:20s}:")
            print(f"    Queries:            {stats['total']}")
            print(f"    With results:       {stats['with_results']}/{stats['total']} ({stats['with_results']/stats['total']*100:.1f}%)")

        # Quality metrics
        print(f"\n{'─'*70}")
        print("🎯 QUALITY METRICS")
        print(f"{'─'*70}")

        # Calculate average scores for successful queries
        all_scores = []
        for category, results in all_results.items():
            for result in results:
                if result['status'] == 'success' and result['results_count'] > 0:
                    all_scores.append(result['top_result']['score'])

        if all_scores:
            print(f"  Average top score:    {sum(all_scores)/len(all_scores):.3f}")
            print(f"  Max score:            {max(all_scores):.3f}")
            print(f"  Min score:            {min(all_scores):.3f}")

        print("="*70)

    def test_specific_legal_scenarios(self):
        """Test specific legal scenarios"""
        print("\n" + "="*70)
        print("🎯 SPECIFIC LEGAL SCENARIO TESTS")
        print("="*70)

        scenarios = [
            {
                'name': 'Dědictví a pozůstalost',
                'query': 'jak funguje dědění bez závěti',
                'expected_type': 'law',
                'expected_category': 'civil'
            },
            {
                'name': 'Krádež a trestní odpovědnost',
                'query': 'jaký trest hrozí za krádež',
                'expected_type': 'law',
                'expected_category': 'criminal'
            },
            {
                'name': 'Výpověď z pracovního poměru',
                'query': 'jak zaměstnavatel může dát výpověď',
                'expected_type': 'law',
                'expected_category': 'labor'
            },
            {
                'name': 'DPH a daňová povinnost',
                'query': 'kdy vzniká povinnost registrace k DPH',
                'expected_type': 'law',
                'expected_category': 'tax'
            },
            {
                'name': 'Soudní rozhodnutí',
                'query': 'nejvyšší soud kupní smlouva',
                'expected_type': 'court_decision',
                'expected_category': None
            }
        ]

        for i, scenario in enumerate(scenarios, 1):
            print(f"\n[{i}/{len(scenarios)}] {scenario['name']}")
            print(f"   Query: '{scenario['query']}'")

            result = self.run_single_query(scenario['query'], top_k=5)

            if result['status'] == 'success' and result['results_count'] > 0:
                top = result['top_result']
                doc_type = top['metadata'].get('document_type', 'unknown')
                category = top['metadata'].get('category', 'unknown')

                print(f"   ✓ Score: {top['score']:.3f}")
                print(f"   ✓ Type: {doc_type} (expected: {scenario['expected_type']})")

                if doc_type == 'law':
                    print(f"   ✓ Law: {top['metadata'].get('law_name', 'Unknown')}")
                    print(f"   ✓ Category: {category} (expected: {scenario['expected_category']})")
                else:
                    print(f"   ✓ Case: {top['metadata'].get('case_number', 'Unknown')}")
                    print(f"   ✓ Court: {top['metadata'].get('court_name', 'Unknown')}")

                # Check if result matches expectations
                if doc_type == scenario['expected_type']:
                    print(f"   ✅ Type match!")
                else:
                    print(f"   ⚠️  Type mismatch (got {doc_type}, expected {scenario['expected_type']})")

                # Show preview
                text_preview = top['text'][:200] + "..." if len(top['text']) > 200 else top['text']
                print(f"   Preview: {text_preview}")
            else:
                print(f"   ✗ No results or error")

        print("\n" + "="*70)


def main():
    """Main function"""
    suite = LegalRAGTestSuite()

    # Run comprehensive tests
    suite.run_all_tests()

    # Run specific scenario tests
    suite.test_specific_legal_scenarios()

    print("\n✅ Test suite completed")


if __name__ == "__main__":
    main()
