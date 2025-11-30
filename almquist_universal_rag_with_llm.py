#!/usr/bin/env python3
"""
ALMQUIST UNIVERSAL RAG WITH LLM GENERATION
Univerzální RAG systém s podporou LLM generování odpovědí
Podporuje všechny domény: legal, profese, dotace, etc.
"""

import json
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import requests
from datetime import datetime
import time

class AlmquistUniversalRAG:
    """
    Univerzální RAG systém s LLM generováním

    Features:
    - Multi-domain support (legal, professions, grants, etc.)
    - Vector search using FAISS
    - LLM-powered answer generation
    - Context-aware responses
    - Source attribution
    """

    def __init__(
        self,
        rag_dir: str,
        domain: str = "legal",
        llm_endpoint: str = "http://localhost:11434",  # Ollama default
        llm_model: str = "llama3.2:3b",
        use_llm: bool = True
    ):
        """
        Initialize Universal RAG

        Args:
            rag_dir: Path to RAG embeddings directory
            domain: Domain name (legal, professions, grants, etc.)
            llm_endpoint: LLM API endpoint (Ollama or vLLM)
            llm_model: LLM model name
            use_llm: Whether to use LLM for generation (False = search only)
        """
        self.rag_dir = Path(rag_dir)
        self.domain = domain
        self.llm_endpoint = llm_endpoint
        self.llm_model = llm_model
        self.use_llm = use_llm

        print(f"🔄 Initializing Almquist Universal RAG ({domain})...")
        print(f"   RAG directory: {rag_dir}")
        print(f"   LLM endpoint: {llm_endpoint}")
        print(f"   LLM model: {llm_model}")
        print(f"   LLM generation: {'enabled' if use_llm else 'disabled'}")

        # Load embedding model
        print("   Loading sentence transformer...")
        self.model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
        print("   ✓ Model loaded")

        # Load FAISS index
        index_path = self.rag_dir / "faiss_index.bin"
        if not index_path.exists():
            raise FileNotFoundError(f"FAISS index not found: {index_path}")

        self.index = faiss.read_index(str(index_path))
        print(f"   ✓ FAISS index loaded ({self.index.ntotal} vectors)")

        # Load metadata
        metadata_path = self.rag_dir / "metadata.json"
        if not metadata_path.exists():
            raise FileNotFoundError(f"Metadata not found: {metadata_path}")

        with open(metadata_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            self.chunks = data['chunks']
            self.metadata = data['metadata']

        print(f"   ✓ Metadata loaded ({len(self.chunks)} chunks)")

        # Test LLM connection if enabled
        if self.use_llm:
            if self.test_llm_connection():
                print("   ✓ LLM connection successful")
            else:
                print("   ⚠️  LLM connection failed, falling back to search-only mode")
                self.use_llm = False

        print("✅ RAG system ready\n")

    def test_llm_connection(self) -> bool:
        """Test if LLM endpoint is accessible"""
        try:
            # Try Ollama API
            response = requests.post(
                f"{self.llm_endpoint}/api/generate",
                json={
                    "model": self.llm_model,
                    "prompt": "Test",
                    "stream": False
                },
                timeout=5
            )
            return response.status_code == 200
        except Exception as e:
            print(f"   LLM connection test failed: {e}")
            return False

    def search(
        self,
        query: str,
        top_k: int = 5,
        filter_metadata: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Vector search for relevant chunks

        Args:
            query: Search query
            top_k: Number of results to return
            filter_metadata: Optional metadata filters

        Returns:
            List of results with scores, chunks, and metadata
        """
        # Embed query
        query_embedding = self.model.encode(
            [query],
            convert_to_numpy=True,
            normalize_embeddings=True
        )

        # Search in FAISS
        search_k = top_k * 10 if filter_metadata else top_k
        distances, indices = self.index.search(
            query_embedding.astype('float32'),
            search_k
        )

        # Build results
        results = []
        for idx, score in zip(indices[0], distances[0]):
            if idx < 0 or idx >= len(self.metadata):
                continue

            meta = self.metadata[idx]
            chunk = self.chunks[idx]

            # Apply filters if specified
            if filter_metadata:
                if not all(meta.get(k) == v for k, v in filter_metadata.items()):
                    continue

            results.append({
                'score': float(score),
                'text': chunk,
                'metadata': meta
            })

            if len(results) >= top_k:
                break

        return results

    def generate_answer(
        self,
        query: str,
        context_chunks: List[Dict[str, Any]],
        max_tokens: int = 500,
        temperature: float = 0.7
    ) -> Dict[str, Any]:
        """
        Generate answer using LLM with RAG context

        Args:
            query: User question
            context_chunks: Retrieved context chunks
            max_tokens: Maximum tokens in response
            temperature: LLM temperature

        Returns:
            Dict with answer, sources, and metadata
        """
        if not self.use_llm:
            return {
                'answer': "LLM generation is disabled. Search results only.",
                'sources': context_chunks,
                'mode': 'search_only'
            }

        # Build context from chunks
        context = self._build_context(context_chunks)

        # Build prompt
        prompt = self._build_prompt(query, context)

        # Generate with LLM
        start_time = time.time()

        try:
            response = requests.post(
                f"{self.llm_endpoint}/api/generate",
                json={
                    "model": self.llm_model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": temperature,
                        "num_predict": max_tokens
                    }
                },
                timeout=60
            )

            if response.status_code == 200:
                result = response.json()
                answer = result.get('response', '').strip()

                generation_time = time.time() - start_time

                return {
                    'answer': answer,
                    'sources': context_chunks,
                    'mode': 'llm_generated',
                    'generation_time': generation_time,
                    'model': self.llm_model,
                    'timestamp': datetime.now().isoformat()
                }
            else:
                return {
                    'answer': f"LLM generation failed (status {response.status_code})",
                    'sources': context_chunks,
                    'mode': 'error'
                }

        except Exception as e:
            return {
                'answer': f"LLM generation error: {str(e)}",
                'sources': context_chunks,
                'mode': 'error'
            }

    def _build_context(self, chunks: List[Dict[str, Any]]) -> str:
        """Build context string from chunks"""
        context_parts = []

        for i, chunk in enumerate(chunks[:5], 1):  # Use top 5 chunks
            meta = chunk['metadata']
            text = chunk['text']

            # Format based on document type
            doc_type = meta.get('document_type', 'unknown')

            if doc_type == 'law':
                law_name = meta.get('law_name', 'Unknown')
                section = meta.get('section', '')
                source = f"[{law_name} {section}]"
            elif doc_type == 'court_decision':
                case = meta.get('case_number', 'Unknown')
                court = meta.get('court_name', 'Unknown')
                source = f"[{court}, sp. zn. {case}]"
            else:
                source = f"[{meta.get('source', 'Unknown')}]"

            context_parts.append(f"{source}\n{text}\n")

        return "\n---\n\n".join(context_parts)

    def _build_prompt(self, query: str, context: str) -> str:
        """Build LLM prompt with query and context"""

        # Domain-specific system prompts
        system_prompts = {
            'legal': """Jsi právní asistent s expertními znalostmi českého práva.
Odpovídej profesionálně, přesně a srozumitelně.
Vždy uveď zdroje informací (zákony, rozhodnutí soudů).
Pokud si nejsi jistý, řekni to.""",

            'professions': """Jsi asistent pro podnikatele a živnostníky v České republice.
Poskytuj přesné a aktuální informace o povinnostech, daních a požadavcích.
Vysvětluj jednoduše a srozumitelně.""",

            'grants': """Jsi expert na dotace a granty v České republice.
Pomáhej uživatelům najít vhodné dotační příležitosti.
Poskytuj konkrétní a aktuální informace."""
        }

        system_prompt = system_prompts.get(
            self.domain,
            "Jsi asistent poskytující informace na základě dostupných dokumentů."
        )

        prompt = f"""{system_prompt}

KONTEXT (relevantní dokumenty):
{context}

OTÁZKA UŽIVATELE:
{query}

INSTRUKCE:
1. Odpověz na otázku přesně a srozumitelně
2. Vždy se odkazuj na konkrétní zdroje z kontextu
3. Pokud kontext neobsahuje odpověď, řekni to
4. Odpověz v češtině
5. Buď struč ný, ale kompletní

ODPOVĚĎ:"""

        return prompt

    def query(
        self,
        question: str,
        top_k: int = 5,
        generate_answer: bool = True
    ) -> Dict[str, Any]:
        """
        Complete RAG query: search + generate answer

        Args:
            question: User question
            top_k: Number of context chunks to retrieve
            generate_answer: Whether to generate LLM answer

        Returns:
            Dict with search results and optional LLM answer
        """
        # 1. Vector search
        search_results = self.search(question, top_k=top_k)

        # 2. Generate answer if requested
        if generate_answer and self.use_llm:
            answer_result = self.generate_answer(question, search_results)

            return {
                'query': question,
                'search_results': search_results,
                'generated_answer': answer_result['answer'],
                'sources': answer_result['sources'],
                'generation_time': answer_result.get('generation_time'),
                'mode': answer_result['mode'],
                'timestamp': datetime.now().isoformat()
            }
        else:
            return {
                'query': question,
                'search_results': search_results,
                'mode': 'search_only',
                'timestamp': datetime.now().isoformat()
            }

    def print_result(self, result: Dict[str, Any], verbose: bool = True):
        """Pretty print RAG result"""
        print(f"\n{'='*70}")
        print(f"❓ QUERY: {result['query']}")
        print(f"{'='*70}")

        if 'generated_answer' in result:
            print(f"\n💡 GENERATED ANSWER:")
            print(f"{result['generated_answer']}")

            if result.get('generation_time'):
                print(f"\n⏱️  Generation time: {result['generation_time']:.2f}s")

        print(f"\n📚 SOURCES ({len(result['search_results'])} results):")

        for i, res in enumerate(result['search_results'], 1):
            meta = res['metadata']
            doc_type = meta.get('document_type', 'unknown')

            if doc_type == 'law':
                doc_id = f"{meta.get('law_name', 'Unknown')} {meta.get('section', '')}"
            elif doc_type == 'court_decision':
                doc_id = f"{meta.get('court_name', 'Unknown')}, {meta.get('case_number', 'Unknown')}"
            else:
                doc_id = meta.get('source', 'Unknown')

            print(f"\n{i}. [{doc_id}] (score: {res['score']:.3f})")

            if verbose:
                text_preview = res['text'][:200] + "..." if len(res['text']) > 200 else res['text']
                print(f"   {text_preview}")

        print(f"\n{'='*70}\n")


def main():
    """Example usage"""

    # Example 1: Legal RAG with LLM
    print("=" * 70)
    print("EXAMPLE 1: Legal RAG with LLM Generation")
    print("=" * 70)

    legal_rag = AlmquistUniversalRAG(
        rag_dir="/home/puzik/almquist_legal_rag",
        domain="legal",
        use_llm=True
    )

    query = "Jaké jsou podmínky pro výpověď z pracovního poměru?"
    result = legal_rag.query(query, top_k=3, generate_answer=True)
    legal_rag.print_result(result)

    # Example 2: Search-only mode (no LLM)
    print("\n" + "=" * 70)
    print("EXAMPLE 2: Search-Only Mode (no LLM)")
    print("=" * 70)

    legal_rag_search = AlmquistUniversalRAG(
        rag_dir="/home/puzik/almquist_legal_rag",
        domain="legal",
        use_llm=False
    )

    result = legal_rag_search.query(query, top_k=3, generate_answer=False)
    legal_rag_search.print_result(result)


if __name__ == "__main__":
    main()
