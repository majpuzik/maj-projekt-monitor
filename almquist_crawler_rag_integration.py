#!/usr/bin/env python3
"""
ALMQUIST CRAWLER → RAG Integration
Automaticky přidává high-quality chunks z crawleru do RAG systému
"""

import sqlite3
import json
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer
from pathlib import Path
from datetime import datetime
import pickle
import subprocess

class CrawlerRAGIntegration:
    """Integrace crawler chunks do RAG"""

    def __init__(self,
                 crawler_db="/home/puzik/almquist_sources.db",
                 rag_dir="/home/puzik/almquist_rag_embeddings"):
        self.crawler_db = crawler_db
        self.rag_dir = Path(rag_dir)

        # Load sentence transformer model (same as RAG)
        self.model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
        self.embedding_dim = 384

        # Load existing RAG system
        self.load_rag_system()

    def load_rag_system(self):
        """Načíst existující RAG systém"""
        print("📂 Loading existing RAG system...")

        # Load FAISS index
        index_path = self.rag_dir / "faiss_index.bin"
        if index_path.exists():
            self.index = faiss.read_index(str(index_path))
            print(f"   ✓ Loaded FAISS index: {self.index.ntotal} vectors")
        else:
            # Create new index if doesn't exist
            self.index = faiss.IndexFlatIP(self.embedding_dim)
            print("   ⚠️  No existing index, created new one")

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
            print("   ⚠️  No existing metadata, starting fresh")

        # Load embeddings
        embeddings_path = self.rag_dir / "embeddings.npy"
        if embeddings_path.exists():
            self.embeddings = np.load(embeddings_path)
            print(f"   ✓ Loaded embeddings: {self.embeddings.shape}")
        else:
            self.embeddings = np.zeros((0, self.embedding_dim), dtype='float32')
            print("   ⚠️  No existing embeddings")

    def get_unprocessed_chunks(self, min_relevance=0.7, limit=100):
        """Získat nezpracované high-quality chunks z crawleru"""
        conn = sqlite3.connect(self.crawler_db)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute('''
        SELECT ei.*, s.title as source_title, s.url as source_url
        FROM extracted_info ei
        JOIN sources s ON ei.source_id = s.id
        WHERE ei.added_to_rag = 0
        AND ei.relevance_score >= ?
        ORDER BY ei.relevance_score DESC, ei.extracted_at DESC
        LIMIT ?
        ''', (min_relevance, limit))

        chunks = [dict(row) for row in cursor.fetchall()]
        conn.close()

        return chunks

    def add_chunks_to_rag(self, chunks):
        """Přidat chunks do RAG systému"""
        if not chunks:
            print("⚠️  No chunks to add")
            return 0, []

        print(f"\n📊 Adding {len(chunks)} chunks to RAG...")

        added_count = 0
        added_chunks = []

        for chunk in chunks:
            try:
                # Generate embedding
                text = chunk['text_content']
                embedding = self.model.encode(
                    [text],
                    convert_to_numpy=True,
                    normalize_embeddings=True
                )[0]

                # Create chunk ID
                chunk_id = f"crawler_{chunk['id']}_{datetime.now().strftime('%Y%m%d')}"

                # Create metadata entry
                metadata_entry = {
                    'chunk_id': chunk_id,
                    'source': 'crawler',
                    'source_url': chunk.get('source_url', ''),
                    'source_title': chunk.get('source_title', ''),
                    'chunk_type': chunk['chunk_type'],
                    'profession': self._extract_profession(chunk.get('profession_relevance')),
                    'relevance_score': chunk['relevance_score'],
                    'extracted_at': chunk.get('extracted_at', ''),
                    'added_to_rag_at': datetime.now().isoformat()
                }

                # Add to index
                self.index.add(embedding.reshape(1, -1).astype('float32'))

                # Add to lists
                self.chunks.append(text)
                self.metadata.append(metadata_entry)
                self.embeddings = np.vstack([self.embeddings, embedding])

                # Mark as processed in crawler DB
                self._mark_as_processed(chunk['id'], chunk_id)

                added_count += 1
                added_chunks.append(chunk)

                print(f"   ✓ [{chunk['chunk_type']}] {chunk.get('source_title', 'Unknown')[:40]} (score: {chunk['relevance_score']:.2f})")

            except Exception as e:
                print(f"   ✗ Error adding chunk {chunk['id']}: {e}")
                continue

        return added_count, added_chunks

    def _extract_profession(self, profession_relevance_json):
        """Extrahovat profession z JSON"""
        if not profession_relevance_json:
            return 'zivnostnik_obecny'

        try:
            prof_dict = json.loads(profession_relevance_json)
            # Get first profession with highest score
            if prof_dict:
                return max(prof_dict.items(), key=lambda x: x[1])[0]
        except:
            pass

        return 'zivnostnik_obecny'

    def _mark_as_processed(self, chunk_id, rag_chunk_id):
        """Označit chunk jako přidaný do RAG"""
        conn = sqlite3.connect(self.crawler_db)
        cursor = conn.cursor()

        cursor.execute('''
        UPDATE extracted_info
        SET added_to_rag = 1, rag_chunk_id = ?
        WHERE id = ?
        ''', (rag_chunk_id, chunk_id))

        conn.commit()
        conn.close()

    def log_to_cdb(self, chunks_added):
        """Logovat přidané chunks do CDB"""
        if not chunks_added:
            return

        # Seskupit podle zdroje a typu
        by_source_type = {}
        for chunk in chunks_added:
            source = chunk.get('source_title', 'Unknown')
            chunk_type = chunk.get('chunk_type', 'unknown')
            profession = self._extract_profession(chunk.get('profession_relevance'))
            score = chunk.get('relevance_score', 0.0)

            key = (source, profession)
            if key not in by_source_type:
                by_source_type[key] = {'types': {}, 'scores': []}

            by_source_type[key]['types'][chunk_type] = by_source_type[key]['types'].get(chunk_type, 0) + 1
            by_source_type[key]['scores'].append(score)

        # Sestavit metadata string
        metadata_parts = []
        for (source, profession), data in by_source_type.items():
            types_str = ', '.join([f"{t}:{c}" for t, c in data['types'].items()])
            avg_score = sum(data['scores']) / len(data['scores'])
            metadata_parts.append(f"{source} → {profession} | {types_str} | avg_score:{avg_score:.2f}")

        metadata = f"RAG auto-update | Added {len(chunks_added)} chunks | " + " | ".join(metadata_parts)

        # Volat maj-almquist-log
        try:
            subprocess.run([
                '/home/puzik/almquist-central-log/maj-almquist-log',
                'event', 'improvement', 'almquist', f'rag-auto-add-{datetime.now().strftime("%Y%m%d")}',
                '--status', 'completed',
                '--metadata', metadata
            ], check=True, capture_output=True, text=True)
            print(f"   ✓ Logged to CDB")
        except Exception as e:
            print(f"   ⚠️  CDB log failed: {e}")

    def save_rag_system(self):
        """Uložit aktualizovaný RAG systém"""
        print("\n💾 Saving updated RAG system...")

        # Ensure directory exists
        self.rag_dir.mkdir(parents=True, exist_ok=True)

        # Save FAISS index
        index_path = self.rag_dir / "faiss_index.bin"
        faiss.write_index(self.index, str(index_path))
        print(f"   ✓ FAISS index saved: {self.index.ntotal} vectors")

        # Save metadata
        metadata_path = self.rag_dir / "metadata.json"
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump({
                'chunks': self.chunks,
                'metadata': self.metadata,
                'updated_at': datetime.now().isoformat(),
                'total_chunks': len(self.chunks)
            }, f, indent=2, ensure_ascii=False)
        print(f"   ✓ Metadata saved: {len(self.chunks)} chunks")

        # Save embeddings
        embeddings_path = self.rag_dir / "embeddings.npy"
        np.save(embeddings_path, self.embeddings)
        print(f"   ✓ Embeddings saved: {self.embeddings.shape}")

        # Save pickle for convenience
        pickle_path = self.rag_dir / "rag_system.pkl"
        with open(pickle_path, 'wb') as f:
            pickle.dump({
                'chunks': self.chunks,
                'metadata': self.metadata,
                'embeddings': self.embeddings
            }, f)
        print(f"   ✓ Pickle saved")

    def run_integration(self, min_relevance=0.6):
        """Spustit celý integration cycle"""
        print("\n" + "="*70)
        print("🔗 ALMQUIST CRAWLER → RAG INTEGRATION")
        print("="*70)

        # Get unprocessed chunks
        print(f"\n1️⃣ Fetching unprocessed chunks (min relevance: {min_relevance})...")
        chunks = self.get_unprocessed_chunks(min_relevance=min_relevance)
        print(f"   ✓ Found {len(chunks)} high-quality chunks")

        if not chunks:
            print("\n✅ No new chunks to add")
            return

        # Show breakdown by type
        by_type = {}
        for chunk in chunks:
            chunk_type = chunk['chunk_type']
            by_type[chunk_type] = by_type.get(chunk_type, 0) + 1

        print("\n   By type:")
        for chunk_type, count in sorted(by_type.items(), key=lambda x: x[1], reverse=True):
            print(f"     {chunk_type}: {count}")

        # Add to RAG
        print(f"\n2️⃣ Adding chunks to RAG system...")
        added_count, added_chunks = self.add_chunks_to_rag(chunks)

        # Save
        if added_count > 0:
            print(f"\n3️⃣ Saving updated RAG system...")
            self.save_rag_system()

            # Log to CDB
            print(f"\n4️⃣ Logging to CDB...")
            self.log_to_cdb(added_chunks)

        # Summary
        print("\n" + "="*70)
        print("✅ INTEGRATION COMPLETED")
        print("="*70)
        print(f"Chunks added to RAG:  {added_count}/{len(chunks)}")
        print(f"Total RAG chunks:     {len(self.chunks)}")
        print(f"Total embeddings:     {self.index.ntotal}")
        print("="*70)

    def get_stats(self):
        """Získat statistiky RAG systému"""
        conn = sqlite3.connect(self.crawler_db)
        cursor = conn.cursor()

        # Total extracted
        cursor.execute('SELECT COUNT(*) FROM extracted_info')
        total_extracted = cursor.fetchone()[0]

        # Added to RAG
        cursor.execute('SELECT COUNT(*) FROM extracted_info WHERE added_to_rag = 1')
        added_to_rag = cursor.fetchone()[0]

        # Pending (high quality)
        cursor.execute('SELECT COUNT(*) FROM extracted_info WHERE added_to_rag = 0 AND relevance_score >= 0.7')
        pending_high_quality = cursor.fetchone()[0]

        # By type
        cursor.execute('''
        SELECT chunk_type, COUNT(*), AVG(relevance_score)
        FROM extracted_info
        GROUP BY chunk_type
        ORDER BY COUNT(*) DESC
        ''')
        by_type = cursor.fetchall()

        conn.close()

        return {
            'total_extracted': total_extracted,
            'added_to_rag': added_to_rag,
            'pending_high_quality': pending_high_quality,
            'by_type': by_type,
            'rag_total_chunks': len(self.chunks)
        }


def main():
    """Main function"""
    integrator = CrawlerRAGIntegration()

    # Show stats before
    print("\n📊 Current Stats:")
    stats = integrator.get_stats()
    print(f"   Total chunks extracted:     {stats['total_extracted']}")
    print(f"   Already in RAG:             {stats['added_to_rag']}")
    print(f"   Pending (high quality):     {stats['pending_high_quality']}")
    print(f"   Current RAG total:          {stats['rag_total_chunks']}")

    # Run integration
    integrator.run_integration(min_relevance=0.6)

    # Show stats after
    print("\n📊 Updated Stats:")
    stats = integrator.get_stats()
    print(f"   Total chunks extracted:     {stats['total_extracted']}")
    print(f"   Added to RAG:               {stats['added_to_rag']}")
    print(f"   Pending (high quality):     {stats['pending_high_quality']}")
    print(f"   Current RAG total:          {stats['rag_total_chunks']}")


if __name__ == "__main__":
    main()
