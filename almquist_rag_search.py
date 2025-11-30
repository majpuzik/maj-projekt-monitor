#!/usr/bin/env python3
"""
ALMQUIST RAG - Search Helper
Snadné vyhledávání v RAG databázi
"""

import json
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer
from pathlib import Path

class AlmquistRAGSearch:
    """Helper třída pro vyhledávání v Almquist RAG databázi"""

    def __init__(self, rag_dir="/home/puzik/almquist_rag_embeddings"):
        self.rag_dir = Path(rag_dir)

        print("🔄 Načítám RAG systém...")

        # Načíst model (stejný jako při vytváření embeddings)
        self.model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')

        # Načíst FAISS index
        index_path = self.rag_dir / "faiss_index.bin"
        self.index = faiss.read_index(str(index_path))
        print(f"   ✓ FAISS index načten ({self.index.ntotal} vectors)")

        # Načíst metadata
        metadata_path = self.rag_dir / "metadata.json"
        with open(metadata_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            self.chunks = data['chunks']
            self.metadata = data['metadata']

        print(f"   ✓ Metadata načtena ({len(self.chunks)} chunks)")
        print("✅ RAG systém připraven\n")

    def search(self, query, top_k=5, profession_filter=None, chunk_type_filter=None):
        """
        Vyhledá nejrelevantnější chunks pro daný dotaz

        Args:
            query: Textový dotaz (česky)
            top_k: Počet výsledků (default 5)
            profession_filter: Filtrovat podle profese (např. "zivnostnik_obecny")
            chunk_type_filter: Filtrovat podle typu (např. "registration")

        Returns:
            List of tuples: (score, chunk_text, metadata)
        """
        # Embedovat query
        query_embedding = self.model.encode(
            [query],
            convert_to_numpy=True,
            normalize_embeddings=True
        )

        # Vyhledat v indexu (hledáme více než top_k, protože budeme filtrovat)
        search_k = top_k * 10 if (profession_filter or chunk_type_filter) else top_k
        distances, indices = self.index.search(query_embedding.astype('float32'), search_k)

        # Sestavit výsledky
        results = []
        for idx, score in zip(indices[0], distances[0]):
            meta = self.metadata[idx]
            chunk = self.chunks[idx]

            # Aplikovat filtry
            if profession_filter and meta['profession_id'] != profession_filter:
                continue

            if chunk_type_filter and meta['chunk_type'] != chunk_type_filter:
                continue

            results.append((score, chunk, meta))

            # Zastavit když máme dost výsledků
            if len(results) >= top_k:
                break

        return results

    def search_by_profession(self, profession_id):
        """Vrátí všechny chunks pro danou profesi"""
        results = []
        for i, meta in enumerate(self.metadata):
            if meta['profession_id'] == profession_id:
                results.append((self.chunks[i], meta))
        return results

    def print_results(self, results, show_full_text=False):
        """Pěkný výstup výsledků"""
        print("═" * 70)
        print(f"Nalezeno {len(results)} výsledků:")
        print("═" * 70)

        for i, (score, chunk, meta) in enumerate(results, 1):
            print(f"\n{i}. [{meta['profession_name']}] - {meta['chunk_type']}")
            print(f"   Score: {score:.4f}")
            print(f"   Section: {meta['section']}")

            if show_full_text:
                print(f"\n{chunk}")
            else:
                # Zobrazit jen preview
                preview = chunk[:300].replace('\n', ' ')
                print(f"\n   {preview}...")

            print("-" * 70)

    def get_profession_overview(self, profession_id):
        """Získá overview chunk pro profesi"""
        for i, meta in enumerate(self.metadata):
            if meta['profession_id'] == profession_id and meta['chunk_type'] == 'overview':
                return self.chunks[i], meta
        return None, None

    def interactive_search(self):
        """Interaktivní vyhledávání"""
        print("\n╔═══════════════════════════════════════════════════════════╗")
        print("║     ALMQUIST RAG - Interaktivní vyhledávání              ║")
        print("╚═══════════════════════════════════════════════════════════╝\n")

        print("Dostupné profese:")
        professions = {}
        for meta in self.metadata:
            prof_id = meta['profession_id']
            prof_name = meta['profession_name']
            professions[prof_id] = prof_name

        for prof_id, prof_name in set(professions.items()):
            print(f"  - {prof_id}: {prof_name}")

        print("\nDostupné typy chunks:")
        chunk_types = set(meta['chunk_type'] for meta in self.metadata)
        for ct in sorted(chunk_types):
            print(f"  - {ct}")

        print("\n" + "=" * 70)
        print("Pro ukončení napište 'quit' nebo 'exit'")
        print("=" * 70)

        while True:
            print()
            query = input("🔎 Váš dotaz: ").strip()

            if query.lower() in ['quit', 'exit', 'q']:
                print("Nashledanou!")
                break

            if not query:
                continue

            # Vyhledat
            results = self.search(query, top_k=3)
            self.print_results(results, show_full_text=False)


def main():
    """Demo použití"""
    rag = AlmquistRAGSearch()

    # Demo queries
    demo_queries = [
        "Jak dlouho trvá založení živnosti?",
        "Jaké náklady má registrace lékaře?",
        "Co musí advokát platit každý měsíc?",
        "Jak Almquist pomůže účetním?",
        "Jaké problémy mají IT freelanceři?",
    ]

    print("DEMO VYHLEDÁVÁNÍ")
    print("=" * 70)

    for query in demo_queries:
        print(f"\n🔎 '{query}'")
        results = rag.search(query, top_k=2)

        for i, (score, chunk, meta) in enumerate(results, 1):
            preview = chunk[:150].replace('\n', ' ')
            print(f"  {i}. [{meta['profession_name']}] {meta['chunk_type']} (score: {score:.3f})")
            print(f"     {preview}...")

    print("\n" + "=" * 70)

    # Spustit interaktivní režim
    choice = input("\nChcete spustit interaktivní vyhledávání? [a/N]: ").strip().lower()
    if choice == 'a':
        rag.interactive_search()


if __name__ == "__main__":
    main()
