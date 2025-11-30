#!/usr/bin/env python3
"""
ALMQUIST RAG MERGER
Merge new data from crawlers into Legal RAG
Runs periodically to keep RAG up-to-date with 24/7 crawlers
"""

import sqlite3
import json
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer
from pathlib import Path
from datetime import datetime
import shutil
import hashlib


class RAGMerger:
    """Merge new legal documents into RAG"""

    def __init__(
        self,
        legal_db: str = "/home/puzik/almquist_legal_sources.db",
        rag_dir: str = "/home/puzik/almquist_legal_rag",
        backup_dir: str = "/home/puzik/almquist_rag_backups"
    ):
        self.legal_db = legal_db
        self.rag_dir = Path(rag_dir)
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(exist_ok=True)

        # Load sentence transformer
        print("📚 Loading sentence transformer...")
        self.model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
        self.embedding_dim = 384

    def compute_content_hash(self, text: str) -> str:
        """Compute SHA256 hash of document text"""
        return hashlib.sha256(text.encode('utf-8')).hexdigest()

    def backup_current_rag(self):
        """Backup current RAG before merging"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = self.backup_dir / f"legal_rag_backup_{timestamp}"
        backup_path.mkdir(exist_ok=True)

        print(f"📦 Creating backup: {backup_path}")

        for file in ['embeddings.npy', 'faiss_index.bin', 'metadata.json']:
            src = self.rag_dir / file
            if src.exists():
                shutil.copy2(src, backup_path / file)

        print(f"   ✓ Backup created")
        return backup_path

    def load_current_rag(self):
        """Load current RAG data"""
        print(f"\n📥 Loading current RAG from {self.rag_dir}...")

        # Load metadata
        metadata_path = self.rag_dir / "metadata.json"
        with open(metadata_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            chunks = data['chunks']
            metadata = data['metadata']

        # Load embeddings
        embeddings_path = self.rag_dir / "embeddings.npy"
        embeddings = np.load(embeddings_path)

        # Load FAISS index
        index_path = self.rag_dir / "faiss_index.bin"
        index = faiss.read_index(str(index_path))

        print(f"   ✓ Loaded {len(chunks)} existing chunks")

        return chunks, metadata, embeddings, index

    def get_new_documents(self, existing_metadata):
        """Get new documents from DB that aren't in RAG yet"""
        print(f"\n🔍 Checking for new documents in {self.legal_db}...")

        # Get existing document IDs and content hashes
        existing_ids = set()
        existing_hashes = set()

        for meta in existing_metadata:
            if meta['document_type'] == 'law':
                existing_ids.add(f"law_{meta['law_number']}")
            elif meta['document_type'] == 'court_decision':
                existing_ids.add(f"case_{meta.get('case_number', 'unknown')}")

            # Also store content hash if available
            if 'content_hash' in meta:
                existing_hashes.add(meta['content_hash'])

        conn = sqlite3.connect(self.legal_db)
        cursor = conn.cursor()

        new_docs = []

        # Check laws
        cursor.execute("""
            SELECT law_number, law_name, full_text, category, source_url,
                   effective_from, effective_to
            FROM laws
            WHERE full_text IS NOT NULL AND full_text != ''
        """)

        for row in cursor.fetchall():
            law_number, law_name, full_text, category, source_url, eff_from, eff_to = row
            doc_id = f"law_{law_number}"
            content_hash = self.compute_content_hash(full_text)

            # Check both ID and content hash to avoid duplicates
            if doc_id not in existing_ids and content_hash not in existing_hashes:
                new_docs.append({
                    'type': 'law',
                    'law_number': law_number,
                    'law_name': law_name,
                    'text': full_text,
                    'category': category,
                    'source_url': source_url,
                    'effective_from': eff_from,
                    'effective_to': eff_to,
                    'content_hash': content_hash
                })
                existing_hashes.add(content_hash)  # Prevent duplicates within this batch

        # Check court decisions
        cursor.execute("""
            SELECT case_number, court_name, full_text, legal_area,
                   decision_date, ecli, source_url
            FROM court_decisions
            WHERE full_text IS NOT NULL AND full_text != ''
        """)

        for row in cursor.fetchall():
            case_num, court, text, category, date, ecli, url = row
            doc_id = f"case_{case_num}"
            content_hash = self.compute_content_hash(text)

            # Check both ID and content hash to avoid duplicates
            if doc_id not in existing_ids and content_hash not in existing_hashes:
                new_docs.append({
                    'type': 'court_decision',
                    'case_number': case_num,
                    'court_name': court,
                    'text': text,
                    'category': category,
                    'decision_date': date,
                    'ecli': ecli,
                    'url': url,
                    'content_hash': content_hash
                })
                existing_hashes.add(content_hash)  # Prevent duplicates within this batch

        conn.close()

        print(f"   ✓ Found {len(new_docs)} new documents")
        print(f"      Laws: {sum(1 for d in new_docs if d['type'] == 'law')}")
        print(f"      Court decisions: {sum(1 for d in new_docs if d['type'] == 'court_decision')}")

        return new_docs

    def chunk_text(self, text, max_length=500):
        """Chunk text into smaller pieces"""
        # Simple sentence-based chunking
        sentences = text.split('. ')
        chunks = []
        current_chunk = ""

        for sentence in sentences:
            if len(current_chunk) + len(sentence) < max_length:
                current_chunk += sentence + ". "
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = sentence + ". "

        if current_chunk:
            chunks.append(current_chunk.strip())

        return chunks

    def process_new_documents(self, new_docs):
        """Process and chunk new documents"""
        print(f"\n⚙️  Processing {len(new_docs)} new documents...")

        all_chunks = []
        all_metadata = []

        for doc in new_docs:
            if doc['type'] == 'law':
                text_chunks = self.chunk_text(doc['text'])

                for i, chunk in enumerate(text_chunks):
                    all_chunks.append(chunk)
                    all_metadata.append({
                        'chunk_id': f"law_{doc['law_number']}_chunk_{i}",
                        'document_type': 'law',
                        'law_number': doc['law_number'],
                        'law_name': doc['law_name'],
                        'section': f"chunk {i+1}/{len(text_chunks)}",
                        'category': doc['category'],
                        'law_type': 'zákon',
                        'source_url': doc['source_url'],
                        'effective_from': doc['effective_from'],
                        'effective_to': doc['effective_to'],
                        'content_hash': doc['content_hash'],
                        'relevance_score': 1.0,
                        'added_at': datetime.now().isoformat()
                    })

            elif doc['type'] == 'court_decision':
                text_chunks = self.chunk_text(doc['text'])

                for i, chunk in enumerate(text_chunks):
                    all_chunks.append(chunk)
                    all_metadata.append({
                        'chunk_id': f"case_{doc['case_number']}_chunk_{i}",
                        'document_type': 'court_decision',
                        'case_number': doc['case_number'],
                        'court_name': doc['court_name'],
                        'section': f"chunk {i+1}/{len(text_chunks)}",
                        'category': doc['category'],
                        'decision_date': doc['decision_date'],
                        'ecli': doc['ecli'],
                        'source_url': doc['url'],
                        'content_hash': doc['content_hash'],
                        'relevance_score': 1.0,
                        'added_at': datetime.now().isoformat()
                    })

        print(f"   ✓ Created {len(all_chunks)} new chunks")

        return all_chunks, all_metadata

    def merge(self, dry_run=False):
        """Main merge function"""
        print("\n" + "="*70)
        print("🔄 ALMQUIST RAG MERGER")
        print("="*70)
        print(f"Mode: {'DRY RUN (no changes)' if dry_run else 'LIVE (will update RAG)'}")
        print("="*70)

        # 1. Backup current RAG
        if not dry_run:
            backup_path = self.backup_current_rag()

        # 2. Load current RAG
        chunks, metadata, embeddings, index = self.load_current_rag()

        # 3. Get new documents
        new_docs = self.get_new_documents(metadata)

        if not new_docs:
            print("\n✅ No new documents to merge. RAG is up-to-date!")
            return

        # 4. Process new documents
        new_chunks, new_metadata = self.process_new_documents(new_docs)

        # 5. Generate embeddings for new chunks
        print(f"\n🧠 Generating embeddings for {len(new_chunks)} new chunks...")
        new_embeddings = self.model.encode(
            new_chunks,
            convert_to_numpy=True,
            normalize_embeddings=True,
            show_progress_bar=True
        )
        print(f"   ✓ Embeddings generated")

        # 6. Merge
        print(f"\n🔗 Merging...")
        merged_chunks = chunks + new_chunks
        merged_metadata = metadata + new_metadata
        merged_embeddings = np.vstack([embeddings, new_embeddings])

        print(f"   ✓ Total chunks: {len(merged_chunks)} (was {len(chunks)}, +{len(new_chunks)})")

        # 7. Create new FAISS index
        print(f"\n📊 Creating new FAISS index...")
        new_index = faiss.IndexFlatIP(self.embedding_dim)
        new_index.add(merged_embeddings.astype('float32'))
        print(f"   ✓ Index created with {new_index.ntotal} vectors")

        # 8. Save (if not dry run)
        if dry_run:
            print(f"\n🔍 DRY RUN - No changes made")
            print(f"   Would add {len(new_chunks)} chunks")
            print(f"   New total: {len(merged_chunks)} chunks")
        else:
            print(f"\n💾 Saving updated RAG...")

            # Save embeddings
            np.save(self.rag_dir / "embeddings.npy", merged_embeddings)

            # Save FAISS index
            faiss.write_index(new_index, str(self.rag_dir / "faiss_index.bin"))

            # Save metadata
            with open(self.rag_dir / "metadata.json", 'w', encoding='utf-8') as f:
                json.dump({
                    'chunks': merged_chunks,
                    'metadata': merged_metadata,
                    'last_updated': datetime.now().isoformat(),
                    'total_vectors': len(merged_chunks)
                }, f, ensure_ascii=False, indent=2)

            print(f"   ✓ RAG updated successfully!")
            print(f"   Backup saved to: {backup_path}")

        print("\n" + "="*70)
        print("✅ MERGE COMPLETE")
        print("="*70)

        # Statistics
        print(f"\nStatistics:")
        print(f"  Old size: {len(chunks)} chunks")
        print(f"  New size: {len(merged_chunks)} chunks")
        print(f"  Added: {len(new_chunks)} chunks")
        print(f"  Growth: +{len(new_chunks)/len(chunks)*100:.1f}%")


def main():
    """Main function"""
    import argparse

    parser = argparse.ArgumentParser(description='Almquist RAG Merger')
    parser.add_argument('--dry-run', action='store_true',
                        help='Dry run - show what would be merged without changing anything')

    args = parser.parse_args()

    merger = RAGMerger()
    merger.merge(dry_run=args.dry_run)


if __name__ == "__main__":
    main()
