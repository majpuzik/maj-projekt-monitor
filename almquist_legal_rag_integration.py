#!/usr/bin/env python3
"""
ALMQUIST Legal RAG Integration
Integrates laws and court decisions into RAG system with intelligent chunking
"""

import sqlite3
import json
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer
from pathlib import Path
from datetime import datetime
import pickle
import re
import subprocess

class LegalRAGIntegration:
    """Integration of legal documents into RAG"""

    def __init__(self,
                 legal_db="/home/puzik/almquist_legal_sources.db",
                 rag_dir="/home/puzik/almquist_legal_rag"):
        self.legal_db = legal_db
        self.rag_dir = Path(rag_dir)

        # Load sentence transformer model
        print("📚 Loading sentence transformer model...")
        self.model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
        self.embedding_dim = 384
        print("   ✓ Model loaded")

        # Load or create RAG system
        self.load_or_create_rag()

    def load_or_create_rag(self):
        """Load existing RAG or create new"""
        print("\n📂 Loading RAG system...")

        # Ensure directory exists
        self.rag_dir.mkdir(parents=True, exist_ok=True)

        # Load FAISS index
        index_path = self.rag_dir / "faiss_index.bin"
        if index_path.exists():
            self.index = faiss.read_index(str(index_path))
            print(f"   ✓ Loaded FAISS index: {self.index.ntotal} vectors")
        else:
            self.index = faiss.IndexFlatIP(self.embedding_dim)
            print("   ✓ Created new FAISS index")

        # Load metadata
        metadata_path = self.rag_dir / "metadata.json"
        if metadata_path.exists():
            with open(metadata_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.chunks = data.get('chunks', [])
                self.metadata = data.get('metadata', [])
            print(f"   ✓ Loaded metadata: {len(self.chunks)} chunks")
        else:
            self.chunks = []
            self.metadata = []
            print("   ✓ Starting with empty metadata")

        # Load embeddings
        embeddings_path = self.rag_dir / "embeddings.npy"
        if embeddings_path.exists():
            self.embeddings = np.load(embeddings_path)
            print(f"   ✓ Loaded embeddings: {self.embeddings.shape}")
        else:
            self.embeddings = np.zeros((0, self.embedding_dim), dtype='float32')
            print("   ✓ Starting with empty embeddings")

    def chunk_law_text(self, law_text, law_number):
        """
        Chunk law text intelligently by paragraphs
        Returns list of (chunk_text, section_reference)
        """
        chunks = []

        # Split by paragraph markers (§)
        # Pattern: § followed by number
        sections = re.split(r'(§\s*\d+[a-z]?)', law_text)

        current_section = None
        current_text = ""

        for i, part in enumerate(sections):
            # Check if this is a section marker
            section_match = re.match(r'§\s*(\d+[a-z]?)', part.strip())

            if section_match:
                # Save previous chunk if exists
                if current_section and current_text.strip():
                    chunks.append({
                        'text': current_text.strip(),
                        'section': current_section
                    })

                # Start new section
                current_section = f"§ {section_match.group(1)}"
                current_text = ""

            else:
                # Add text to current section
                current_text += part

                # If chunk is getting too long (> 2000 chars), split it
                if len(current_text) > 2000:
                    # Find a good split point (sentence end)
                    split_points = [m.start() for m in re.finditer(r'\.\s+', current_text[:2000])]

                    if split_points:
                        split_at = split_points[-1] + 1
                        chunks.append({
                            'text': current_text[:split_at].strip(),
                            'section': current_section or 'Preambule'
                        })
                        current_text = current_text[split_at:]

        # Add final chunk
        if current_text.strip():
            chunks.append({
                'text': current_text.strip(),
                'section': current_section or 'Preambule'
            })

        # Filter out very short chunks (< 100 chars)
        chunks = [c for c in chunks if len(c['text']) >= 100]

        return chunks

    def chunk_decision_text(self, decision_text, case_number):
        """
        Chunk court decision text intelligently
        Returns list of chunks
        """
        chunks = []

        # Split by common sections in court decisions
        # 1. Právní věta / Summary
        # 2. Odůvodnění / Reasoning
        # 3. Výrok / Decision part

        # For now, use simple paragraph-based chunking
        # Split by double newlines or numbered paragraphs
        paragraphs = re.split(r'\n\n+|\[\d+\]', decision_text)

        current_chunk = ""
        chunk_num = 0

        for para in paragraphs:
            para = para.strip()
            if not para or len(para) < 50:
                continue

            # If adding this paragraph would make chunk too long, save current and start new
            if len(current_chunk) + len(para) > 2000 and current_chunk:
                chunks.append({
                    'text': current_chunk.strip(),
                    'section': f'Part {chunk_num + 1}'
                })
                chunk_num += 1
                current_chunk = para
            else:
                current_chunk += "\n\n" + para if current_chunk else para

        # Add final chunk
        if current_chunk.strip():
            chunks.append({
                'text': current_chunk.strip(),
                'section': f'Part {chunk_num + 1}'
            })

        # Filter out very short chunks
        chunks = [c for c in chunks if len(c['text']) >= 100]

        return chunks

    def get_unprocessed_laws(self):
        """Get laws not yet added to RAG"""
        conn = sqlite3.connect(self.legal_db)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute('''
        SELECT * FROM laws
        WHERE added_to_rag = 0
        ORDER BY id
        ''')

        laws = [dict(row) for row in cursor.fetchall()]
        conn.close()

        return laws

    def get_unprocessed_decisions(self):
        """Get court decisions not yet added to RAG"""
        conn = sqlite3.connect(self.legal_db)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute('''
        SELECT * FROM court_decisions
        WHERE added_to_rag = 0
        ORDER BY id
        ''')

        decisions = [dict(row) for row in cursor.fetchall()]
        conn.close()

        return decisions

    def add_law_to_rag(self, law):
        """Add single law to RAG with chunking"""
        print(f"\n📜 Processing: {law['law_name']} ({law['law_number']})")

        # Chunk the law
        chunks = self.chunk_law_text(law['full_text'], law['law_number'])
        print(f"   ✓ Created {len(chunks)} chunks")

        added_chunks = []
        chunk_ids = []

        for i, chunk_data in enumerate(chunks):
            try:
                # Generate embedding
                embedding = self.model.encode(
                    [chunk_data['text']],
                    convert_to_numpy=True,
                    normalize_embeddings=True
                )[0]

                # Create chunk ID
                chunk_id = f"law_{law['id']}_{chunk_data['section'].replace(' ', '_')}_{i}"

                # Create metadata
                metadata_entry = {
                    'chunk_id': chunk_id,
                    'document_type': 'law',
                    'law_number': law['law_number'],
                    'law_name': law['law_name'],
                    'section': chunk_data['section'],
                    'category': law['category'],
                    'law_type': law['law_type'],
                    'source_url': law['source_url'],
                    'effective_from': law.get('effective_from'),
                    'effective_to': law.get('effective_to'),
                    'relevance_score': 1.0,
                    'added_at': datetime.now().isoformat()
                }

                # Add to index
                self.index.add(embedding.reshape(1, -1).astype('float32'))

                # Add to lists
                self.chunks.append(chunk_data['text'])
                self.metadata.append(metadata_entry)
                self.embeddings = np.vstack([self.embeddings, embedding])

                added_chunks.append(chunk_data)
                chunk_ids.append(chunk_id)

            except Exception as e:
                print(f"   ✗ Error adding chunk {i}: {e}")
                continue

        # Mark as processed in legal DB
        if added_chunks:
            self._mark_law_as_processed(law['id'], chunk_ids)
            print(f"   ✓ Added {len(added_chunks)} chunks to RAG")

        return added_chunks

    def add_decision_to_rag(self, decision):
        """Add single court decision to RAG with chunking"""
        print(f"\n⚖️  Processing: {decision['case_number']} ({decision.get('court_name', 'Unknown')})")

        # Chunk the decision
        full_text = decision.get('full_text', '')
        if not full_text or len(full_text) < 100:
            print("   ⚠️  Text too short, skipping")
            return []

        chunks = self.chunk_decision_text(full_text, decision['case_number'])
        print(f"   ✓ Created {len(chunks)} chunks")

        added_chunks = []
        chunk_ids = []

        for i, chunk_data in enumerate(chunks):
            try:
                # Generate embedding
                embedding = self.model.encode(
                    [chunk_data['text']],
                    convert_to_numpy=True,
                    normalize_embeddings=True
                )[0]

                # Create chunk ID
                case_num_safe = decision['case_number'].replace(' ', '_').replace('/', '_')
                chunk_id = f"decision_{decision['id']}_{case_num_safe}_{i}"

                # Create metadata
                metadata_entry = {
                    'chunk_id': chunk_id,
                    'document_type': 'court_decision',
                    'case_number': decision['case_number'],
                    'court_level': decision['court_level'],
                    'court_name': decision.get('court_name', 'Unknown'),
                    'decision_type': decision.get('decision_type'),
                    'decision_date': decision.get('decision_date'),
                    'ecli': decision.get('ecli'),
                    'legal_area': decision.get('legal_area'),
                    'section': chunk_data['section'],
                    'source_url': decision.get('source_url'),
                    'relevance_score': 1.0,
                    'added_at': datetime.now().isoformat()
                }

                # Add to index
                self.index.add(embedding.reshape(1, -1).astype('float32'))

                # Add to lists
                self.chunks.append(chunk_data['text'])
                self.metadata.append(metadata_entry)
                self.embeddings = np.vstack([self.embeddings, embedding])

                added_chunks.append(chunk_data)
                chunk_ids.append(chunk_id)

            except Exception as e:
                print(f"   ✗ Error adding chunk {i}: {e}")
                continue

        # Mark as processed
        if added_chunks:
            self._mark_decision_as_processed(decision['id'], chunk_ids)
            print(f"   ✓ Added {len(added_chunks)} chunks to RAG")

        return added_chunks

    def _mark_law_as_processed(self, law_id, chunk_ids):
        """Mark law as added to RAG"""
        conn = sqlite3.connect(self.legal_db)
        cursor = conn.cursor()

        cursor.execute('''
        UPDATE laws
        SET added_to_rag = 1,
            rag_chunk_ids = ?,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
        ''', (json.dumps(chunk_ids), law_id))

        conn.commit()
        conn.close()

    def _mark_decision_as_processed(self, decision_id, chunk_ids):
        """Mark decision as added to RAG"""
        conn = sqlite3.connect(self.legal_db)
        cursor = conn.cursor()

        cursor.execute('''
        UPDATE court_decisions
        SET added_to_rag = 1,
            rag_chunk_ids = ?,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
        ''', (json.dumps(chunk_ids), decision_id))

        conn.commit()
        conn.close()

    def save_rag_system(self):
        """Save RAG system to disk"""
        print("\n💾 Saving RAG system...")

        # Save FAISS index
        index_path = self.rag_dir / "faiss_index.bin"
        faiss.write_index(self.index, str(index_path))
        print(f"   ✓ FAISS index: {self.index.ntotal} vectors")

        # Save metadata
        metadata_path = self.rag_dir / "metadata.json"
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump({
                'chunks': self.chunks,
                'metadata': self.metadata,
                'updated_at': datetime.now().isoformat(),
                'total_chunks': len(self.chunks)
            }, f, indent=2, ensure_ascii=False)
        print(f"   ✓ Metadata: {len(self.chunks)} chunks")

        # Save embeddings
        embeddings_path = self.rag_dir / "embeddings.npy"
        np.save(embeddings_path, self.embeddings)
        print(f"   ✓ Embeddings: {self.embeddings.shape}")

        # Save pickle
        pickle_path = self.rag_dir / "rag_system.pkl"
        with open(pickle_path, 'wb') as f:
            pickle.dump({
                'chunks': self.chunks,
                'metadata': self.metadata,
                'embeddings': self.embeddings
            }, f)
        print(f"   ✓ Pickle saved")

    def log_to_cdb(self, laws_processed, total_chunks_added, decisions_processed=None):
        """Log to Central Database"""
        if not laws_processed and not decisions_processed:
            return

        # Create summary
        metadata_parts = []

        if laws_processed:
            by_category = {}
            for law in laws_processed:
                cat = law.get('category', 'other')
                by_category[cat] = by_category.get(cat, 0) + 1

            categories_str = ', '.join([f"{cat}:{count}" for cat, count in by_category.items()])
            metadata_parts.append(f"{len(laws_processed)} laws | Categories: {categories_str}")

        if decisions_processed:
            by_court = {}
            for decision in decisions_processed:
                court = decision.get('court_level', 'unknown')
                by_court[court] = by_court.get(court, 0) + 1

            courts_str = ', '.join([f"{court}:{count}" for court, count in by_court.items()])
            metadata_parts.append(f"{len(decisions_processed)} decisions | Courts: {courts_str}")

        metadata = f"Legal RAG update | Added {total_chunks_added} chunks | " + " | ".join(metadata_parts)

        # Call maj-almquist-log
        try:
            subprocess.run([
                '/home/puzik/almquist-central-log/maj-almquist-log',
                'event', 'improvement', 'almquist', f'legal-rag-{datetime.now().strftime("%Y%m%d")}',
                '--status', 'completed',
                '--metadata', metadata
            ], check=True, capture_output=True, text=True)
            print(f"   ✓ Logged to CDB")
        except Exception as e:
            print(f"   ⚠️  CDB log failed: {e}")

    def run_integration(self):
        """Run full integration cycle"""
        print("\n" + "=" * 70)
        print("🏛️  ALMQUIST LEGAL RAG INTEGRATION")
        print("=" * 70)

        # Get unprocessed documents
        print("\n1️⃣ Fetching unprocessed documents...")
        laws = self.get_unprocessed_laws()
        decisions = self.get_unprocessed_decisions()
        print(f"   ✓ Found {len(laws)} unprocessed laws")
        print(f"   ✓ Found {len(decisions)} unprocessed court decisions")

        if not laws and not decisions:
            print("\n✅ No new documents to process")
            return

        total_chunks_added = 0
        laws_processed = []
        decisions_processed = []

        # Process laws
        if laws:
            print("\n2️⃣ Processing laws...")
            for law in laws:
                chunks = self.add_law_to_rag(law)
                total_chunks_added += len(chunks)
                if chunks:
                    laws_processed.append(law)

        # Process court decisions
        if decisions:
            print(f"\n{'3️⃣' if laws else '2️⃣'} Processing court decisions...")
            for decision in decisions:
                chunks = self.add_decision_to_rag(decision)
                total_chunks_added += len(chunks)
                if chunks:
                    decisions_processed.append(decision)

        # Save
        if total_chunks_added > 0:
            step = 3 if not laws or not decisions else 4
            print(f"\n{step}️⃣ Saving RAG system...")
            self.save_rag_system()

            print(f"\n{step+1}️⃣ Logging to CDB...")
            self.log_to_cdb(laws_processed, total_chunks_added, decisions_processed)

        # Summary
        print("\n" + "=" * 70)
        print("✅ INTEGRATION COMPLETED")
        print("=" * 70)
        print(f"Laws processed:        {len(laws_processed)}/{len(laws)}")
        print(f"Decisions processed:   {len(decisions_processed)}/{len(decisions)}")
        print(f"Chunks added:          {total_chunks_added}")
        print(f"Total RAG chunks:      {len(self.chunks)}")
        print(f"Total embeddings:      {self.index.ntotal}")
        print("=" * 70)

    def search(self, query, top_k=3):
        """Search RAG and return results (no printing)"""
        # Generate query embedding
        query_embedding = self.model.encode(
            [query],
            convert_to_numpy=True,
            normalize_embeddings=True
        )[0]

        # Search
        distances, indices = self.index.search(
            query_embedding.reshape(1, -1).astype('float32'),
            top_k
        )

        # Build results
        results = []
        for idx, dist in zip(indices[0], distances[0]):
            if idx >= 0 and idx < len(self.metadata):
                results.append({
                    'score': float(dist),
                    'metadata': self.metadata[idx],
                    'text': self.chunks[idx]
                })

        return results

    def test_search(self, query, top_k=3):
        """Test RAG search with printing"""
        print(f"\n🔍 Testing search: '{query}'")

        results = self.search(query, top_k=top_k)

        # Print results
        print(f"\nTop {top_k} results:")
        for i, result in enumerate(results, 1):
            meta = result['metadata']
            chunk_text = result['text'][:200]
            print(f"\n{i}. [{meta.get('law_name', 'Unknown')} {meta.get('section', '')}]")
            print(f"   Score: {result['score']:.3f}")
            print(f"   Text: {chunk_text}...")

        return results


def main():
    """Main function"""
    integrator = LegalRAGIntegration()

    # Run integration
    integrator.run_integration()

    # Test search
    print("\n" + "=" * 70)
    print("🧪 TESTING RAG SEARCH")
    print("=" * 70)

    test_queries = [
        "dědictví",
        "trestný čin krádeže",
        "pracovní smlouva"
    ]

    for query in test_queries:
        integrator.test_search(query)


if __name__ == "__main__":
    main()
