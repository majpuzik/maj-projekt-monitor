#!/usr/bin/env python3
"""
ALMQUIST CODE RAG SYSTEM
Universal code search and retrieval system for all your scripts

Indexes:
- All local git repositories
- /home/puzik/apps/** (all apps)
- /home/puzik/*.{py,sh,js,ts} (standalone scripts)
- /home/puzik/github-repos/** (GitHub clones)

Features:
- Semantic code search with embeddings
- Syntax-aware chunking
- Multi-language support (Python, JS, TS, Bash, PHP, etc.)
- Git metadata integration
- Function/class extraction
"""

import psycopg2
import psycopg2.extras
import os
import sys
import git
from pathlib import Path
from typing import List, Dict, Any, Optional
import hashlib
from datetime import datetime
import json
import re
from sentence_transformers import SentenceTransformer
import faiss
import numpy as np
import pickle


class CodeRAGSystem:
    """Main code RAG system"""

    # Supported file extensions
    CODE_EXTENSIONS = {
        '.py': 'python',
        '.js': 'javascript',
        '.ts': 'typescript',
        '.tsx': 'typescript',
        '.jsx': 'javascript',
        '.sh': 'bash',
        '.bash': 'bash',
        '.zsh': 'bash',
        '.php': 'php',
        '.java': 'java',
        '.cpp': 'cpp',
        '.c': 'c',
        '.go': 'go',
        '.rs': 'rust',
        '.rb': 'ruby',
        '.sql': 'sql',
        '.html': 'html',
        '.css': 'css',
        '.json': 'json',
        '.yaml': 'yaml',
        '.yml': 'yaml',
        '.md': 'markdown',
        '.txt': 'text',
    }

    def __init__(self,
                 db_url="postgresql://almquist_user:almquist_secure_password_2025@localhost:5432/almquist_db",
                 rag_dir="/home/puzik/almquist_code_rag"):
        self.db_url = db_url
        self.rag_dir = Path(rag_dir)
        self.rag_dir.mkdir(exist_ok=True)

        # Initialize embedding model (code-optimized)
        print("🔧 Loading embedding model...")
        self.model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')

        # Initialize FAISS index
        self.index = None
        self.code_chunks = []
        self.chunk_metadata = []

        # Load existing index if available
        self._load_index()

        print("✅ Code RAG system initialized")

    def init_database(self):
        """Initialize PostgreSQL database schema"""
        conn = psycopg2.connect(self.db_url)
        cursor = conn.cursor()

        # Code files table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS code_files (
            id SERIAL PRIMARY KEY,
            file_path TEXT NOT NULL,
            file_name TEXT NOT NULL,
            file_extension TEXT,
            language TEXT,

            repository_path TEXT,
            repository_name TEXT,
            git_remote_url TEXT,
            git_branch TEXT,

            file_size_bytes INTEGER,
            line_count INTEGER,

            content_hash TEXT UNIQUE,
            content TEXT,

            functions TEXT[],
            classes TEXT[],
            imports TEXT[],

            indexed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_modified TIMESTAMP,

            is_active BOOLEAN DEFAULT true
        )
        ''')

        # Code chunks table (for embeddings)
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS code_chunks (
            id SERIAL PRIMARY KEY,
            file_id INTEGER REFERENCES code_files(id),
            chunk_index INTEGER,

            chunk_text TEXT NOT NULL,
            chunk_type TEXT,
            chunk_context TEXT,

            start_line INTEGER,
            end_line INTEGER,

            embedding_vector BYTEA,

            indexed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')

        # Search history
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS code_search_history (
            id SERIAL PRIMARY KEY,
            query TEXT NOT NULL,
            results_count INTEGER,
            searched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            execution_time_ms INTEGER
        )
        ''')

        # Create indexes
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_code_files_path ON code_files(file_path)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_code_files_language ON code_files(language)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_code_files_repo ON code_files(repository_name)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_code_chunks_file ON code_chunks(file_id)')

        conn.commit()
        conn.close()

        print("✅ Database schema initialized")

    def scan_location(self, root_path: str, location_type: str = "local") -> List[Path]:
        """Scan a location for code files"""
        root = Path(root_path)
        if not root.exists():
            print(f"⚠️  Path does not exist: {root_path}")
            return []

        code_files = []

        # Directories to skip
        skip_dirs = {
            'node_modules', '__pycache__', '.git', 'venv', 'env',
            '.pytest_cache', 'dist', 'build', '.next', '.nuxt',
            'coverage', '.cache', '.vscode', '.idea', 'mariadb-data',
            'mysql', 'postgres', 'mongodb', 'redis'
        }

        print(f"🔍 Scanning: {root_path}")

        for file_path in root.rglob('*'):
            # Skip directories
            if file_path.is_dir():
                continue

            # Skip if in ignored directory
            if any(skip in file_path.parts for skip in skip_dirs):
                continue

            # Check if it's a code file
            if file_path.suffix in self.CODE_EXTENSIONS:
                code_files.append(file_path)

        print(f"  📁 Found {len(code_files)} code files")
        return code_files

    def extract_code_metadata(self, file_path: Path, content: str) -> Dict[str, Any]:
        """Extract metadata from code file"""
        language = self.CODE_EXTENSIONS.get(file_path.suffix, 'unknown')

        metadata = {
            'functions': [],
            'classes': [],
            'imports': [],
        }

        # Python-specific extraction
        if language == 'python':
            # Functions
            functions = re.findall(r'def\s+(\w+)\s*\(', content)
            metadata['functions'] = list(set(functions))

            # Classes
            classes = re.findall(r'class\s+(\w+)\s*[:\(]', content)
            metadata['classes'] = list(set(classes))

            # Imports
            imports = re.findall(r'(?:from\s+[\w.]+\s+)?import\s+([\w,\s]+)', content)
            metadata['imports'] = [imp.strip() for imp_list in imports for imp in imp_list.split(',')]

        # JavaScript/TypeScript
        elif language in ['javascript', 'typescript']:
            # Functions
            functions = re.findall(r'(?:function\s+(\w+)|(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s*)?\()', content)
            metadata['functions'] = list(set([f for group in functions for f in group if f]))

            # Classes
            classes = re.findall(r'class\s+(\w+)', content)
            metadata['classes'] = list(set(classes))

            # Imports
            imports = re.findall(r'import\s+.*?from\s+[\'"](.+?)[\'"]', content)
            metadata['imports'] = list(set(imports))

        # Bash
        elif language == 'bash':
            # Functions
            functions = re.findall(r'(?:function\s+)?(\w+)\s*\(\)\s*\{', content)
            metadata['functions'] = list(set(functions))

        return metadata

    def get_git_info(self, file_path: Path) -> Optional[Dict[str, str]]:
        """Get git repository information for a file"""
        try:
            # Find git repository
            current = file_path.parent
            while current != current.parent:
                git_dir = current / '.git'
                if git_dir.exists():
                    repo = git.Repo(current)

                    # Get remote URL
                    remote_url = None
                    if repo.remotes:
                        remote_url = repo.remotes.origin.url

                    return {
                        'repository_path': str(current),
                        'repository_name': current.name,
                        'git_remote_url': remote_url,
                        'git_branch': repo.active_branch.name if not repo.head.is_detached else 'detached',
                    }

                current = current.parent
        except Exception as e:
            pass

        return None

    def chunk_code(self, content: str, file_path: Path, chunk_size: int = 1000) -> List[Dict[str, Any]]:
        """Chunk code intelligently (by function/class or fixed size)"""
        language = self.CODE_EXTENSIONS.get(file_path.suffix, 'unknown')
        chunks = []

        lines = content.split('\n')

        # Try to chunk by function/class for Python
        if language == 'python':
            current_chunk = []
            current_type = None
            start_line = 0

            for i, line in enumerate(lines):
                # Check for function/class definition
                if re.match(r'^(?:def|class)\s+\w+', line):
                    # Save previous chunk
                    if current_chunk:
                        chunks.append({
                            'text': '\n'.join(current_chunk),
                            'type': current_type or 'code',
                            'start_line': start_line,
                            'end_line': i - 1,
                        })

                    # Start new chunk
                    current_chunk = [line]
                    current_type = 'class' if line.startswith('class') else 'function'
                    start_line = i
                else:
                    current_chunk.append(line)

                    # Split if chunk too large
                    if len('\n'.join(current_chunk)) > chunk_size:
                        chunks.append({
                            'text': '\n'.join(current_chunk),
                            'type': current_type or 'code',
                            'start_line': start_line,
                            'end_line': i,
                        })
                        current_chunk = []
                        start_line = i + 1

            # Add last chunk
            if current_chunk:
                chunks.append({
                    'text': '\n'.join(current_chunk),
                    'type': current_type or 'code',
                    'start_line': start_line,
                    'end_line': len(lines) - 1,
                })

        # Fixed-size chunking for other languages
        else:
            current_chunk = []
            start_line = 0

            for i, line in enumerate(lines):
                current_chunk.append(line)

                if len('\n'.join(current_chunk)) >= chunk_size:
                    chunks.append({
                        'text': '\n'.join(current_chunk),
                        'type': 'code',
                        'start_line': start_line,
                        'end_line': i,
                    })
                    current_chunk = []
                    start_line = i + 1

            # Add last chunk
            if current_chunk:
                chunks.append({
                    'text': '\n'.join(current_chunk),
                    'type': 'code',
                    'start_line': start_line,
                    'end_line': len(lines) - 1,
                })

        return chunks

    def index_file(self, file_path: Path) -> int:
        """Index a single code file"""
        try:
            # Read file
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()

            # Skip empty files
            if not content.strip():
                return 0

            # Calculate hash
            content_hash = hashlib.sha256(content.encode('utf-8')).hexdigest()

            # Check if already indexed
            conn = psycopg2.connect(self.db_url)
            cursor = conn.cursor()
            cursor.execute('SELECT id FROM code_files WHERE content_hash = %s', (content_hash,))
            existing = cursor.fetchone()

            if existing:
                conn.close()
                return 0  # Already indexed

            # Extract metadata
            language = self.CODE_EXTENSIONS.get(file_path.suffix, 'unknown')
            metadata = self.extract_code_metadata(file_path, content)
            git_info = self.get_git_info(file_path)

            # Get file stats
            stats = file_path.stat()
            line_count = len(content.split('\n'))

            # Insert file record
            cursor.execute('''
                INSERT INTO code_files (
                    file_path, file_name, file_extension, language,
                    repository_path, repository_name, git_remote_url, git_branch,
                    file_size_bytes, line_count,
                    content_hash, content,
                    functions, classes, imports,
                    last_modified
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            ''', (
                str(file_path), file_path.name, file_path.suffix, language,
                git_info['repository_path'] if git_info else None,
                git_info['repository_name'] if git_info else None,
                git_info['git_remote_url'] if git_info else None,
                git_info['git_branch'] if git_info else None,
                stats.st_size, line_count,
                content_hash, content,
                metadata['functions'], metadata['classes'], metadata['imports'],
                datetime.fromtimestamp(stats.st_mtime)
            ))

            file_id = cursor.fetchone()[0]

            # Chunk and embed
            chunks = self.chunk_code(content, file_path)

            for i, chunk in enumerate(chunks):
                # Generate embedding
                embedding = self.model.encode([chunk['text']], convert_to_numpy=True)[0]
                embedding_bytes = embedding.tobytes()

                # Insert chunk
                cursor.execute('''
                    INSERT INTO code_chunks (
                        file_id, chunk_index, chunk_text, chunk_type,
                        start_line, end_line, embedding_vector
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                ''', (
                    file_id, i, chunk['text'], chunk['type'],
                    chunk['start_line'], chunk['end_line'], embedding_bytes
                ))

                # Add to in-memory index
                self.code_chunks.append(chunk['text'])
                self.chunk_metadata.append({
                    'file_path': str(file_path),
                    'file_name': file_path.name,
                    'language': language,
                    'chunk_type': chunk['type'],
                    'start_line': chunk['start_line'],
                    'end_line': chunk['end_line'],
                    'repository': git_info['repository_name'] if git_info else None,
                })

            conn.commit()
            conn.close()

            return len(chunks)

        except Exception as e:
            print(f"  ❌ Error indexing {file_path}: {e}")
            return 0

    def index_location(self, root_path: str, location_name: str = None):
        """Index all code files in a location"""
        print(f"\n{'='*70}")
        print(f"📂 Indexing: {location_name or root_path}")
        print(f"{'='*70}\n")

        files = self.scan_location(root_path)

        total_chunks = 0
        indexed_files = 0

        for i, file_path in enumerate(files):
            if (i + 1) % 10 == 0:
                print(f"  Progress: {i+1}/{len(files)} files...")

            chunks = self.index_file(file_path)
            if chunks > 0:
                indexed_files += 1
                total_chunks += chunks

        print(f"\n✅ Indexed {indexed_files} new files ({total_chunks} chunks)")

    def build_faiss_index(self):
        """Build FAISS index from database"""
        print("\n🔨 Building FAISS index...")

        conn = psycopg2.connect(self.db_url)
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

        cursor.execute('''
            SELECT c.embedding_vector, f.file_path, f.file_name, f.language,
                   c.chunk_text, c.chunk_type, c.start_line, c.end_line,
                   f.repository_name
            FROM code_chunks c
            JOIN code_files f ON c.file_id = f.id
            WHERE f.is_active = true
            ORDER BY c.id
        ''')

        embeddings = []
        self.code_chunks = []
        self.chunk_metadata = []

        for row in cursor:
            # Convert bytes back to numpy array
            embedding = np.frombuffer(row['embedding_vector'], dtype=np.float32)
            embeddings.append(embedding)

            self.code_chunks.append(row['chunk_text'])
            self.chunk_metadata.append({
                'file_path': row['file_path'],
                'file_name': row['file_name'],
                'language': row['language'],
                'chunk_type': row['chunk_type'],
                'start_line': row['start_line'],
                'end_line': row['end_line'],
                'repository': row['repository_name'],
            })

        conn.close()

        if not embeddings:
            print("⚠️  No embeddings found in database")
            return

        # Create FAISS index
        embeddings_matrix = np.vstack(embeddings).astype('float32')
        dimension = embeddings_matrix.shape[1]

        self.index = faiss.IndexFlatIP(dimension)  # Inner product (cosine similarity)
        faiss.normalize_L2(embeddings_matrix)  # Normalize for cosine similarity
        self.index.add(embeddings_matrix)

        print(f"✅ FAISS index built: {self.index.ntotal} vectors")

        # Save index
        self._save_index()

    def _save_index(self):
        """Save FAISS index to disk"""
        if self.index is None:
            return

        index_path = self.rag_dir / "code_faiss_index.bin"
        faiss.write_index(self.index, str(index_path))

        metadata_path = self.rag_dir / "code_metadata.pkl"
        with open(metadata_path, 'wb') as f:
            pickle.dump({
                'chunks': self.code_chunks,
                'metadata': self.chunk_metadata,
            }, f)

        print(f"💾 Index saved to: {self.rag_dir}")

    def _load_index(self):
        """Load FAISS index from disk"""
        index_path = self.rag_dir / "code_faiss_index.bin"
        metadata_path = self.rag_dir / "code_metadata.pkl"

        if not index_path.exists() or not metadata_path.exists():
            return

        try:
            self.index = faiss.read_index(str(index_path))

            with open(metadata_path, 'rb') as f:
                data = pickle.load(f)
                self.code_chunks = data['chunks']
                self.chunk_metadata = data['metadata']

            print(f"📂 Loaded existing index: {self.index.ntotal} vectors")
        except Exception as e:
            print(f"⚠️  Could not load index: {e}")

    def search(self, query: str, k: int = 10, language_filter: str = None) -> List[Dict[str, Any]]:
        """Search code by semantic similarity"""
        if self.index is None or self.index.ntotal == 0:
            print("⚠️  Index is empty. Run indexing first.")
            return []

        start_time = datetime.now()

        # Embed query
        query_embedding = self.model.encode([query], convert_to_numpy=True)[0]
        query_embedding = query_embedding.reshape(1, -1).astype('float32')
        faiss.normalize_L2(query_embedding)

        # Search
        distances, indices = self.index.search(query_embedding, k * 2)  # Get more for filtering

        results = []
        for dist, idx in zip(distances[0], indices[0]):
            if idx >= len(self.chunk_metadata):
                continue

            metadata = self.chunk_metadata[idx]

            # Apply language filter
            if language_filter and metadata['language'] != language_filter:
                continue

            results.append({
                'score': float(dist),
                'code': self.code_chunks[idx],
                **metadata
            })

            if len(results) >= k:
                break

        # Log search
        exec_time = int((datetime.now() - start_time).total_seconds() * 1000)
        try:
            conn = psycopg2.connect(self.db_url)
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO code_search_history (query, results_count, execution_time_ms)
                VALUES (%s, %s, %s)
            ''', (query, len(results), exec_time))
            conn.commit()
            conn.close()
        except:
            pass

        return results


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description='Almquist Code RAG System')
    parser.add_argument('action', choices=['init', 'index', 'search', 'rebuild'],
                       help='Action to perform')
    parser.add_argument('--query', '-q', help='Search query')
    parser.add_argument('--language', '-l', help='Filter by language')
    parser.add_argument('--limit', '-k', type=int, default=10, help='Number of results')

    args = parser.parse_args()

    # Initialize system
    rag = CodeRAGSystem()

    if args.action == 'init':
        print("🚀 Initializing Code RAG System...")
        rag.init_database()

    elif args.action == 'index':
        print("📚 Starting full code indexing...")

        # Index locations
        locations = [
            ('/home/puzik/apps', 'Apps Directory'),
            ('/home/puzik/github-repos', 'GitHub Repositories'),
            ('/home/puzik/almquist-pro', 'Almquist Pro'),
            ('/home/puzik/maj-monitor', 'MAJ Monitor'),
            ('/home/puzik/maj-guardian', 'MAJ Guardian'),
            ('/home/puzik', 'Home Scripts (top-level only)'),
        ]

        for location, name in locations:
            if os.path.exists(location):
                if location == '/home/puzik':
                    # For home directory, only index top-level scripts
                    files = [Path(location) / f for f in os.listdir(location)
                            if Path(location / f).suffix in rag.CODE_EXTENSIONS]
                    print(f"\n📂 Indexing: {name}")
                    for file in files:
                        rag.index_file(file)
                else:
                    rag.index_location(location, name)

        # Build FAISS index
        rag.build_faiss_index()

        print("\n" + "="*70)
        print("✅ INDEXING COMPLETE")
        print("="*70)

    elif args.action == 'rebuild':
        print("🔨 Rebuilding FAISS index from database...")
        rag.build_faiss_index()

    elif args.action == 'search':
        if not args.query:
            print("❌ Please provide a search query with --query")
            sys.exit(1)

        print(f"\n🔍 Searching for: '{args.query}'")
        if args.language:
            print(f"   Language filter: {args.language}")
        print()

        results = rag.search(args.query, k=args.limit, language_filter=args.language)

        if not results:
            print("❌ No results found")
            return

        print(f"Found {len(results)} results:\n")

        for i, result in enumerate(results, 1):
            print(f"{'='*70}")
            print(f"Result #{i} (score: {result['score']:.4f})")
            print(f"{'='*70}")
            print(f"📁 File: {result['file_name']}")
            print(f"📂 Path: {result['file_path']}")
            print(f"💻 Language: {result['language']}")
            if result['repository']:
                print(f"📦 Repository: {result['repository']}")
            print(f"📍 Lines: {result['start_line']}-{result['end_line']}")
            print(f"🏷️  Type: {result['chunk_type']}")
            print(f"\n{result['code'][:500]}")
            if len(result['code']) > 500:
                print("... (truncated)")
            print()


if __name__ == '__main__':
    main()
