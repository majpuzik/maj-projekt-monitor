#!/usr/bin/env python3
"""
ALMQUIST ALEXA PRIZE COMPREHENSIVE TEST SUITE
Kompletní test suite pro porovnání RAG systémů
Inspirováno Alexa Prize Socialbot Grand Challenge metrikami
"""

import sys
import time
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any
import json
import statistics

# Import both old and new RAG systems
from almquist_universal_rag_with_llm import AlmquistUniversalRAG


class AlexaPrizeTestSuite:
    """
    Comprehensive test suite based on Alexa Prize metrics

    Metrics:
    - Relevance: How relevant are the search results?
    - Coherence: How coherent is the generated answer?
    - Informativeness: How informative is the response?
    - Helpfulness: How helpful is the answer to the user?
    - Engagement: Would the user continue the conversation?
    """

    def __init__(self):
        self.test_queries = self._load_test_queries()
        self.results = {
            'old_system': [],  # Without LLM
            'new_system': []   # With LLM
        }

    def _load_test_queries(self) -> Dict[str, List[Dict[str, Any]]]:
        """Load comprehensive test queries across all domains"""
        return {
            'legal_civil': [
                {
                    'query': 'Jaké jsou podmínky pro uzavření kupní smlouvy?',
                    'category': 'civil_law',
                    'difficulty': 'easy',
                    'expected_type': 'law'
                },
                {
                    'query': 'Jak funguje dědění bez závěti v České republice?',
                    'category': 'civil_law',
                    'difficulty': 'medium',
                    'expected_type': 'law'
                },
                {
                    'query': 'Jaké jsou podmínky pro uzavření manželství?',
                    'category': 'civil_law',
                    'difficulty': 'easy',
                    'expected_type': 'law'
                },
                {
                    'query': 'Co je to věcné břemeno a jak se zřizuje?',
                    'category': 'civil_law',
                    'difficulty': 'medium',
                    'expected_type': 'law'
                },
            ],
            'legal_criminal': [
                {
                    'query': 'Jaký trest hrozí za krádež podle trestního zákoníku?',
                    'category': 'criminal_law',
                    'difficulty': 'easy',
                    'expected_type': 'law'
                },
                {
                    'query': 'Jaký je rozdíl mezi přečinem a zločinem?',
                    'category': 'criminal_law',
                    'difficulty': 'medium',
                    'expected_type': 'law'
                },
                {
                    'query': 'Co je podmíněný trest a kdy jej soud může uložit?',
                    'category': 'criminal_law',
                    'difficulty': 'medium',
                    'expected_type': 'law'
                },
            ],
            'legal_labor': [
                {
                    'query': 'Jaké jsou zákonné důvody pro výpověď ze strany zaměstnavatele?',
                    'category': 'labor_law',
                    'difficulty': 'medium',
                    'expected_type': 'law'
                },
                {
                    'query': 'Kolik dní dovolené mi náleží podle zákoníku práce?',
                    'category': 'labor_law',
                    'difficulty': 'easy',
                    'expected_type': 'law'
                },
                {
                    'query': 'Jaká je minimální mzda v České republice?',
                    'category': 'labor_law',
                    'difficulty': 'easy',
                    'expected_type': 'law'
                },
                {
                    'query': 'Kdy vzniká nárok na odstupné?',
                    'category': 'labor_law',
                    'difficulty': 'medium',
                    'expected_type': 'law'
                },
            ],
            'legal_commercial': [
                {
                    'query': 'Jaké jsou základní povinnosti jednatelů s.r.o.?',
                    'category': 'commercial_law',
                    'difficulty': 'medium',
                    'expected_type': 'law'
                },
                {
                    'query': 'Co je to insolvenční řízení?',
                    'category': 'commercial_law',
                    'difficulty': 'medium',
                    'expected_type': 'law'
                },
                {
                    'query': 'Jaké jsou podmínky pro svolání valné hromady?',
                    'category': 'commercial_law',
                    'difficulty': 'hard',
                    'expected_type': 'law'
                },
            ],
            'legal_administrative': [
                {
                    'query': 'Jaké jsou lhůty pro podání odvolání ve správním řízení?',
                    'category': 'administrative_law',
                    'difficulty': 'medium',
                    'expected_type': 'law'
                },
                {
                    'query': 'Co je to správní trestání?',
                    'category': 'administrative_law',
                    'difficulty': 'medium',
                    'expected_type': 'law'
                },
            ],
            'legal_tax': [
                {
                    'query': 'Kdy vzniká povinnost registrace k DPH?',
                    'category': 'tax_law',
                    'difficulty': 'medium',
                    'expected_type': 'law'
                },
                {
                    'query': 'Jaké jsou sazby daně z příjmů fyzických osob?',
                    'category': 'tax_law',
                    'difficulty': 'easy',
                    'expected_type': 'law'
                },
            ],
            'legal_court_decisions': [
                {
                    'query': 'Jaká jsou nejdůležitější rozhodnutí Nejvyššího soudu o kupní smlouvě?',
                    'category': 'court_decisions',
                    'difficulty': 'hard',
                    'expected_type': 'court_decision'
                },
                {
                    'query': 'Jaké jsou nálezy Ústavního soudu k ochraně soukromí?',
                    'category': 'court_decisions',
                    'difficulty': 'hard',
                    'expected_type': 'court_decision'
                },
            ],
            'conversational': [
                {
                    'query': 'Pomoz mi, prosím. Chci se rozvést, ale nevím jak na to.',
                    'category': 'conversational',
                    'difficulty': 'medium',
                    'expected_type': 'law'
                },
                {
                    'query': 'Můj zaměstnavatel mi nechce vyplatit mzdu. Co mám dělat?',
                    'category': 'conversational',
                    'difficulty': 'medium',
                    'expected_type': 'law'
                },
                {
                    'query': 'Dostal jsem výpověď. Je to legální?',
                    'category': 'conversational',
                    'difficulty': 'medium',
                    'expected_type': 'law'
                },
            ]
        }

    def rate_relevance(self, results: List[Dict], query_meta: Dict) -> float:
        """
        Rate search result relevance (0-5 scale)

        Criteria:
        - Do results match expected document type?
        - Are top results highly relevant?
        - Are scores sufficiently high?
        """
        if not results:
            return 0.0

        score = 0.0

        # Check top result score (max 2 points)
        top_score = results[0]['score']
        if top_score > 0.8:
            score += 2.0
        elif top_score > 0.6:
            score += 1.5
        elif top_score > 0.4:
            score += 1.0

        # Check if type matches expected (max 2 points)
        expected_type = query_meta.get('expected_type')
        if expected_type:
            top_type = results[0]['metadata'].get('document_type')
            if top_type == expected_type:
                score += 2.0
            else:
                score += 0.5  # At least something was found

        # Check result diversity (max 1 point)
        unique_sources = len(set(r['metadata'].get('law_name', r['metadata'].get('case_number', '')) for r in results[:5]))
        if unique_sources >= 3:
            score += 1.0
        elif unique_sources >= 2:
            score += 0.5

        return min(score, 5.0)

    def rate_coherence(self, answer: str) -> float:
        """
        Rate answer coherence (0-5 scale)

        Criteria:
        - Is answer well-structured?
        - Does it flow logically?
        - Is Czech grammar correct?
        """
        if not answer or answer.startswith("LLM"):
            return 0.0

        score = 5.0

        # Basic checks
        if len(answer) < 50:
            score -= 2.0  # Too short

        if len(answer) > 1000:
            score -= 0.5  # Potentially too verbose

        # Check for complete sentences
        if not answer.strip().endswith(('.', '!', '?')):
            score -= 0.5

        # Check for structure indicators
        structure_indicators = ['protože', 'ale', 'také', 'například', 'pokud', 'tedy']
        if any(ind in answer.lower() for ind in structure_indicators):
            score = min(score + 0.5, 5.0)

        return max(score, 0.0)

    def rate_informativeness(self, answer: str, sources: List[Dict]) -> float:
        """
        Rate answer informativeness (0-5 scale)

        Criteria:
        - Does answer cite specific sources?
        - Does it provide concrete information?
        - Does it include relevant details?
        """
        if not answer or answer.startswith("LLM"):
            return 0.0

        score = 2.0  # Base score for having an answer

        # Check for source citations
        law_indicators = ['zákon', 'zákoník', '§', 'odstavec', 'paragraf']
        if any(ind in answer.lower() for ind in law_indicators):
            score += 1.5

        # Check for specific references
        if any(char.isdigit() for char in answer):  # Contains numbers (likely § references)
            score += 0.5

        # Check answer length (informativeness proxy)
        if 100 <= len(answer) <= 500:
            score += 1.0
        elif len(answer) > 500:
            score += 0.5

        return min(score, 5.0)

    def rate_helpfulness(self, answer: str, query: str) -> float:
        """
        Rate answer helpfulness (0-5 scale)

        Criteria:
        - Does answer directly address the question?
        - Is it actionable?
        - Would it help the user?
        """
        if not answer or answer.startswith("LLM"):
            return 0.0

        score = 3.0  # Base score

        # Check if answer addresses question keywords
        query_words = set(query.lower().split())
        answer_words = set(answer.lower().split())
        overlap = len(query_words & answer_words) / len(query_words) if query_words else 0

        if overlap > 0.3:
            score += 1.0
        elif overlap > 0.2:
            score += 0.5

        # Check for actionable language
        actionable_words = ['musíte', 'můžete', 'měli byste', 'je třeba', 'je nutné']
        if any(word in answer.lower() for word in actionable_words):
            score += 1.0

        return min(score, 5.0)

    def test_system(
        self,
        rag_dir: str,
        use_llm: bool,
        system_name: str
    ) -> List[Dict[str, Any]]:
        """Test a RAG system with all queries"""

        print(f"\n{'='*70}")
        print(f"🧪 TESTING: {system_name}")
        print(f"   RAG dir: {rag_dir}")
        print(f"   LLM enabled: {use_llm}")
        print(f"{'='*70}\n")

        # Initialize system
        try:
            rag = AlmquistUniversalRAG(
                rag_dir=rag_dir,
                domain="legal",
                use_llm=use_llm
            )
        except Exception as e:
            print(f"❌ Failed to initialize RAG: {e}")
            return []

        all_results = []
        query_count = sum(len(queries) for queries in self.test_queries.values())
        current = 0

        for category, queries in self.test_queries.items():
            print(f"\n📋 Category: {category}")
            print(f"{'─'*70}")

            for query_meta in queries:
                current += 1
                query = query_meta['query']

                print(f"\n[{current}/{query_count}] {query}")

                # Run query
                start_time = time.time()
                try:
                    result = rag.query(
                        query,
                        top_k=5,
                        generate_answer=use_llm
                    )
                    query_time = time.time() - start_time

                    # Calculate metrics
                    relevance = self.rate_relevance(
                        result['search_results'],
                        query_meta
                    )

                    if use_llm and 'generated_answer' in result:
                        answer = result['generated_answer']
                        coherence = self.rate_coherence(answer)
                        informativeness = self.rate_informativeness(
                            answer,
                            result['sources']
                        )
                        helpfulness = self.rate_helpfulness(answer, query)
                        engagement = (coherence + informativeness + helpfulness) / 3
                    else:
                        answer = None
                        coherence = 0.0
                        informativeness = 0.0
                        helpfulness = 0.0
                        engagement = 0.0

                    # Store result
                    test_result = {
                        'query': query,
                        'category': category,
                        'difficulty': query_meta['difficulty'],
                        'search_results_count': len(result['search_results']),
                        'answer': answer,
                        'query_time': query_time,
                        'metrics': {
                            'relevance': relevance,
                            'coherence': coherence,
                            'informativeness': informativeness,
                            'helpfulness': helpfulness,
                            'engagement': engagement
                        },
                        'raw_result': result
                    }

                    all_results.append(test_result)

                    # Print metrics
                    print(f"   ⏱️  Time: {query_time:.2f}s")
                    print(f"   📊 Metrics:")
                    print(f"      Relevance:        {relevance:.2f}/5.0")
                    if use_llm:
                        print(f"      Coherence:        {coherence:.2f}/5.0")
                        print(f"      Informativeness:  {informativeness:.2f}/5.0")
                        print(f"      Helpfulness:      {helpfulness:.2f}/5.0")
                        print(f"      Engagement:       {engagement:.2f}/5.0")
                        if answer:
                            answer_preview = answer[:150] + "..." if len(answer) > 150 else answer
                            print(f"   💡 Answer: {answer_preview}")

                except Exception as e:
                    print(f"   ❌ Error: {e}")
                    all_results.append({
                        'query': query,
                        'category': category,
                        'error': str(e),
                        'metrics': {
                            'relevance': 0.0,
                            'coherence': 0.0,
                            'informativeness': 0.0,
                            'helpfulness': 0.0,
                            'engagement': 0.0
                        }
                    })

        return all_results

    def compare_systems(
        self,
        results_old: List[Dict],
        results_new: List[Dict]
    ):
        """Generate detailed comparison report"""

        print(f"\n\n{'='*70}")
        print("📊 COMPREHENSIVE COMPARISON REPORT")
        print(f"{'='*70}\n")

        # Calculate aggregate metrics
        def calc_stats(results, metric):
            values = [r['metrics'][metric] for r in results if 'metrics' in r]
            if not values:
                return {'mean': 0, 'median': 0, 'min': 0, 'max': 0}
            return {
                'mean': statistics.mean(values),
                'median': statistics.median(values),
                'min': min(values),
                'max': max(values)
            }

        metrics = ['relevance', 'coherence', 'informativeness', 'helpfulness', 'engagement']

        print("="*70)
        print("OVERALL METRICS COMPARISON")
        print("="*70)
        print(f"{'Metric':<20} {'OLD (no LLM)':<20} {'NEW (with LLM)':<20} {'Improvement':<15}")
        print("─"*70)

        improvements = {}

        for metric in metrics:
            old_stats = calc_stats(results_old, metric)
            new_stats = calc_stats(results_new, metric)

            improvement = ((new_stats['mean'] - old_stats['mean']) / old_stats['mean'] * 100) if old_stats['mean'] > 0 else 0
            improvements[metric] = improvement

            print(f"{metric.capitalize():<20} {old_stats['mean']:>6.2f} ±{old_stats['median']:>4.2f}      {new_stats['mean']:>6.2f} ±{new_stats['median']:>4.2f}      {improvement:>+6.1f}%")

        # Performance comparison
        print(f"\n{'='*70}")
        print("PERFORMANCE COMPARISON")
        print(f"{'='*70}")

        old_times = [r.get('query_time', 0) for r in results_old if 'query_time' in r]
        new_times = [r.get('query_time', 0) for r in results_new if 'query_time' in r]

        if old_times and new_times:
            print(f"{'Metric':<30} {'OLD':<15} {'NEW':<15}")
            print("─"*60)
            print(f"{'Avg query time':<30} {statistics.mean(old_times):>7.2f}s       {statistics.mean(new_times):>7.2f}s")
            print(f"{'Median query time':<30} {statistics.median(old_times):>7.2f}s       {statistics.median(new_times):>7.2f}s")
            print(f"{'Max query time':<30} {max(old_times):>7.2f}s       {max(new_times):>7.2f}s")

        # Category breakdown
        print(f"\n{'='*70}")
        print("CATEGORY BREAKDOWN")
        print(f"{'='*70}")

        categories = set(r['category'] for r in results_new if 'category' in r)

        for category in sorted(categories):
            old_cat = [r for r in results_old if r.get('category') == category]
            new_cat = [r for r in results_new if r.get('category') == category]

            if old_cat and new_cat:
                old_eng = statistics.mean([r['metrics']['engagement'] for r in old_cat])
                new_eng = statistics.mean([r['metrics']['engagement'] for r in new_cat])
                improvement = ((new_eng - old_eng) / old_eng * 100) if old_eng > 0 else 0

                print(f"\n{category}:")
                print(f"  OLD engagement: {old_eng:.2f}/5.0")
                print(f"  NEW engagement: {new_eng:.2f}/5.0")
                print(f"  Improvement:    {improvement:+.1f}%")

        # Summary
        print(f"\n{'='*70}")
        print("✅ SUMMARY")
        print(f"{'='*70}")

        non_zero_improvements = [v for v in improvements.values() if v != 0]
        avg_improvement = statistics.mean(non_zero_improvements) if non_zero_improvements else 0.0

        print(f"\n📈 Average improvement across all metrics: {avg_improvement:+.1f}%")
        print(f"\n🏆 Best improvements:")
        for metric, improvement in sorted(improvements.items(), key=lambda x: x[1], reverse=True)[:3]:
            print(f"   {metric.capitalize():<20} {improvement:+.1f}%")

        print(f"\n{'='*70}\n")

        return {
            'improvements': improvements,
            'avg_improvement': avg_improvement,
            'old_stats': {m: calc_stats(results_old, m) for m in metrics},
            'new_stats': {m: calc_stats(results_new, m) for m in metrics}
        }

    def save_results(self, results_old, results_new, comparison):
        """Save results to JSON"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"/home/puzik/almquist_alexa_test_results_{timestamp}.json"

        output = {
            'timestamp': datetime.now().isoformat(),
            'test_info': {
                'total_queries': len(results_old),
                'categories': list(self.test_queries.keys())
            },
            'results': {
                'old_system': results_old,
                'new_system': results_new
            },
            'comparison': comparison
        }

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output, f, indent=2, ensure_ascii=False)

        print(f"💾 Results saved to: {output_file}")


def main():
    """Run comprehensive tests"""

    print("\n" + "="*70)
    print("🚀 ALMQUIST ALEXA PRIZE COMPREHENSIVE TEST SUITE")
    print("="*70)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*70)

    suite = AlexaPrizeTestSuite()

    # Test OLD system (without LLM)
    results_old = suite.test_system(
        rag_dir="/home/puzik/almquist_legal_rag",
        use_llm=False,
        system_name="OLD SYSTEM (Search Only, No LLM)"
    )

    # Test NEW system (with LLM)
    results_new = suite.test_system(
        rag_dir="/home/puzik/almquist_legal_rag",
        use_llm=True,
        system_name="NEW SYSTEM (Search + LLM Generation)"
    )

    # Compare and generate report
    comparison = suite.compare_systems(results_old, results_new)

    # Save results
    suite.save_results(results_old, results_new, comparison)

    print("\n✅ Comprehensive test suite completed!")
    print(f"Finished: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


if __name__ == "__main__":
    main()
