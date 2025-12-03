#!/usr/bin/env python3
"""
ALMQUIST UNIFIED RAG LAUNCHER
Univerzální launcher pro všechny RAG domény s LLM podporou

Podporuje:
- Legal RAG (zákony, soudní rozhodnutí) - 2159 vektorů
- Profese RAG (živnosti, profese) - 41 vektorů
- Corporate RAG (firemní dokumenty z Paperless-NGX) - auto-sync
- Dotace RAG (připraveno)
"""

import sys
from pathlib import Path
from almquist_universal_rag_with_llm import AlmquistUniversalRAG


class UnifiedRAGLauncher:
    """Unified launcher for all RAG domains"""

    def __init__(self):
        self.available_domains = {
            'legal': {
                'rag_dir': '/home/puzik/almquist_legal_rag',
                'description': 'Právní RAG (zákony, soudní rozhodnutí)',
                'vectors': 2159,
                'status': '✅ Aktivní (24/7 crawlery)'
            },
            'professions': {
                'rag_dir': '/home/puzik/almquist_rag_embeddings',
                'description': 'Profese RAG (živnosti, IT freelancers)',
                'vectors': 41,
                'status': '✅ Statický'
            },
            'corporate': {
                'rag_dir': '/home/puzik/almquist_corporate_rag',
                'description': 'Firemní dokumenty (Paperless-NGX)',
                'vectors': 0,
                'status': '🔄 Auto-sync z Paperless-NGX'
            },
            'grants': {
                'rag_dir': '/home/puzik/almquist_grants_rag',
                'description': 'Dotace RAG (evropské i národní dotace)',
                'vectors': 0,
                'status': '📋 Připraveno (není vytvořeno)'
            }
        }

    def list_domains(self):
        """List all available domains"""
        print("\n" + "="*70)
        print("📚 DOSTUPNÉ RAG DOMÉNY")
        print("="*70)

        for domain_id, info in self.available_domains.items():
            status_emoji = info['status'].split()[0]
            print(f"\n{status_emoji} {domain_id.upper()}")
            print(f"   {info['description']}")
            print(f"   Vektory: {info['vectors']}")
            print(f"   Status: {info['status']}")
            print(f"   Path: {info['rag_dir']}")

        print("\n" + "="*70)

    def launch(
        self,
        domain: str,
        use_llm: bool = True,
        llm_model: str = "llama3.2:3b",
        llm_endpoint: str = "http://localhost:11434",
        interactive: bool = False
    ):
        """Launch RAG system for specific domain"""

        if domain not in self.available_domains:
            print(f"❌ Unknown domain: {domain}")
            print(f"Available: {', '.join(self.available_domains.keys())}")
            return None

        domain_info = self.available_domains[domain]
        rag_dir = domain_info['rag_dir']

        # Check if RAG exists
        if not Path(rag_dir).exists():
            print(f"❌ RAG directory does not exist: {rag_dir}")
            print(f"   Status: {domain_info['status']}")
            return None

        # Initialize RAG
        print(f"\n{'='*70}")
        print(f"🚀 LAUNCHING: {domain.upper()} RAG")
        print(f"{'='*70}\n")

        rag = AlmquistUniversalRAG(
            rag_dir=rag_dir,
            domain=domain,
            llm_endpoint=llm_endpoint,
            llm_model=llm_model,
            use_llm=use_llm
        )

        if interactive:
            self.interactive_mode(rag, domain)
        else:
            return rag

    def interactive_mode(self, rag, domain):
        """Interactive Q&A mode"""
        print(f"\n{'='*70}")
        print(f"💬 INTERACTIVE MODE - {domain.upper()} RAG")
        print(f"{'='*70}")
        print("Type 'quit' or 'exit' to end session")
        print("Type 'help' for commands")
        print(f"{'='*70}\n")

        while True:
            try:
                query = input("\n❓ Your question: ").strip()

                if not query:
                    continue

                if query.lower() in ['quit', 'exit', 'q']:
                    print("\n👋 Goodbye!")
                    break

                if query.lower() == 'help':
                    print("\n📖 COMMANDS:")
                    print("  - Type your question in Czech")
                    print("  - 'quit'/'exit' - End session")
                    print("  - 'help' - Show this help")
                    continue

                # Query RAG
                result = rag.query(
                    query,
                    top_k=3,
                    generate_answer=rag.use_llm
                )

                # Display result
                rag.print_result(result, verbose=False)

            except KeyboardInterrupt:
                print("\n\n👋 Session interrupted. Goodbye!")
                break
            except Exception as e:
                print(f"\n❌ Error: {e}")

    def demo(self, domain: str):
        """Run demo queries for specific domain"""
        demo_queries = {
            'legal': [
                "Jaké jsou podmínky pro uzavření kupní smlouvy?",
                "Jaký trest hrozí za krádež?",
                "Kolik dní dovolené mi náleží?"
            ],
            'professions': [
                "Jaké jsou povinnosti živnostníka?",
                "Jak založit IT živnost?",
                "Jaké daně platí OSVČ?"
            ],
            'grants': [
                "Jaké dotace jsou k dispozici pro malé podniky?",
                "Evropské dotace pro inovace",
                "Dotace na digitalizaci"
            ]
        }

        queries = demo_queries.get(domain, [])

        if not queries:
            print(f"No demo queries for domain: {domain}")
            return

        rag = self.launch(domain, use_llm=True, interactive=False)

        if not rag:
            return

        print(f"\n{'='*70}")
        print(f"🎬 DEMO - {domain.upper()} RAG")
        print(f"{'='*70}\n")

        for i, query in enumerate(queries, 1):
            print(f"\n{'─'*70}")
            print(f"Demo {i}/{len(queries)}")
            print(f"{'─'*70}")

            result = rag.query(query, top_k=3, generate_answer=True)
            rag.print_result(result, verbose=False)

            if i < len(queries):
                input("\nPress Enter for next demo...")


def main():
    """Main function"""
    import argparse

    parser = argparse.ArgumentParser(
        description='Almquist Unified RAG Launcher',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # List all domains
  python3 almquist_unified_rag_launcher.py --list

  # Launch legal RAG (interactive)
  python3 almquist_unified_rag_launcher.py --domain legal --interactive

  # Launch professions RAG (no LLM, search only)
  python3 almquist_unified_rag_launcher.py --domain professions --no-llm

  # Run demo for legal RAG
  python3 almquist_unified_rag_launcher.py --domain legal --demo

  # Use DGX Ollama for faster inference
  python3 almquist_unified_rag_launcher.py --domain legal --endpoint http://100.90.154.98:11434 --interactive
        """
    )

    parser.add_argument('--list', action='store_true',
                        help='List all available domains')
    parser.add_argument('--domain', type=str,
                        choices=['legal', 'professions', 'grants'],
                        help='Domain to launch')
    parser.add_argument('--interactive', '-i', action='store_true',
                        help='Interactive Q&A mode')
    parser.add_argument('--demo', action='store_true',
                        help='Run demo queries')
    parser.add_argument('--no-llm', action='store_true',
                        help='Disable LLM (search only)')
    parser.add_argument('--model', type=str, default='llama3.2:3b',
                        help='LLM model (default: llama3.2:3b)')
    parser.add_argument('--endpoint', type=str, default='http://localhost:11434',
                        help='Ollama endpoint (default: localhost:11434)')

    args = parser.parse_args()

    launcher = UnifiedRAGLauncher()

    if args.list:
        launcher.list_domains()
        return

    if not args.domain:
        print("❌ Please specify --domain or use --list to see available domains")
        parser.print_help()
        return

    if args.demo:
        launcher.demo(args.domain)
    else:
        launcher.launch(
            domain=args.domain,
            use_llm=not args.no_llm,
            llm_model=args.model,
            llm_endpoint=args.endpoint,
            interactive=args.interactive
        )


if __name__ == "__main__":
    main()
