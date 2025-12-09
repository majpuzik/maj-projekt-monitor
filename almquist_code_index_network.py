#!/usr/bin/env python3
"""
ALMQUIST CODE RAG - Network & Docker Indexer
Index code from all network locations and Docker containers
"""

import subprocess
import os
import sys
from pathlib import Path
import tempfile
import shutil
from almquist_code_rag_system import CodeRAGSystem

# Network locations
NETWORK_LOCATIONS = {
    'nas5_apps': {
        'host': '192.168.10.35',
        'port': 4438,
        'user': 'admin',
        'password': 'Dasa_beda2208s',
        'paths': [
            '/volume1/docker/apps',
            '/volume1/apps',
        ]
    },
}

# Docker containers on NAS5 (from earlier scan)
NAS5_DOCKER_CONTAINERS = [
    'ai-cluster-dev-hub',
    'tv-program-service-ai',
    'maj-subscriptions-v2',
    'zbrane-katalog-app',
    'gitea',
    'unified-mcp-server',
    'cubee-monitor',
    'n8n',
    'mcp-v5-server',
    'mcp-external-admin',
]


def sync_from_nas5(location_config: dict, temp_dir: Path) -> Path:
    """Sync files from NAS5 using rsync"""
    print(f"\n🔄 Syncing from NAS5...")

    host = location_config['host']
    port = location_config['port']
    user = location_config['user']
    password = location_config['password']

    local_base = temp_dir / 'nas5'
    local_base.mkdir(exist_ok=True)

    for remote_path in location_config['paths']:
        print(f"   📂 Syncing: {remote_path}")

        # Create local directory
        local_path = local_base / Path(remote_path).name
        local_path.mkdir(exist_ok=True)

        # Use rsync via sshpass
        cmd = [
            'rsync', '-avz', '--progress',
            '-e', f'sshpass -p {password} ssh -p {port} -o StrictHostKeyChecking=no',
            f'{user}@{host}:{remote_path}/',
            str(local_path) + '/'
        ]

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=600  # 10 minutes
            )

            if result.returncode == 0:
                file_count = sum(1 for _ in local_path.rglob('*') if _.is_file())
                print(f"   ✅ Synced {file_count} files from {remote_path}")
            else:
                print(f"   ⚠️  Warning: {result.stderr[:200]}")
        except subprocess.TimeoutExpired:
            print(f"   ⏱️  Timeout syncing {remote_path}")
        except Exception as e:
            print(f"   ❌ Error: {e}")

    return local_base


def extract_docker_code(container_name: str, temp_dir: Path) -> Path:
    """Extract code from Docker container on NAS5"""
    print(f"\n🐳 Extracting from Docker: {container_name}")

    # Create local directory for this container
    container_dir = temp_dir / 'docker' / container_name
    container_dir.mkdir(parents=True, exist_ok=True)

    # Common code locations in Docker containers
    code_paths = [
        '/app',
        '/usr/src/app',
        '/code',
        '/opt/app',
        '/home/app',
        '/var/www',
    ]

    password = 'Dasa_beda2208s'
    host = '192.168.10.35'
    port = 4438
    user = 'admin'

    extracted = False

    for code_path in code_paths:
        # Try to copy code from container
        # First: docker exec + tar
        cmd = f"echo {password} | sudo -S /usr/local/bin/docker exec {container_name} tar -czf - {code_path} 2>/dev/null"

        full_cmd = [
            'sshpass', '-p', password,
            'ssh', '-p', str(port),
            '-o', 'StrictHostKeyChecking=no',
            f'{user}@{host}',
            cmd
        ]

        try:
            result = subprocess.run(
                full_cmd,
                capture_output=True,
                timeout=60
            )

            if result.returncode == 0 and len(result.stdout) > 100:
                # Save tar.gz
                tar_file = container_dir / f"{Path(code_path).name}.tar.gz"
                with open(tar_file, 'wb') as f:
                    f.write(result.stdout)

                # Extract
                subprocess.run(
                    ['tar', '-xzf', str(tar_file), '-C', str(container_dir)],
                    capture_output=True
                )

                print(f"   ✅ Extracted {code_path}")
                extracted = True
                break

        except Exception as e:
            continue

    if not extracted:
        print(f"   ⚠️  Could not extract code (container may not have typical code paths)")

    return container_dir


def count_code_files(directory: Path) -> dict:
    """Count code files by extension"""
    extensions = {}

    code_exts = ['.py', '.js', '.ts', '.sh', '.php', '.java', '.go', '.rs', '.rb']

    for ext in code_exts:
        count = sum(1 for _ in directory.rglob(f'*{ext}'))
        if count > 0:
            extensions[ext] = count

    return extensions


def main():
    """Main indexing workflow"""
    print("="*70)
    print("ALMQUIST CODE RAG - NETWORK & DOCKER INDEXER")
    print("="*70)

    # Initialize RAG system
    rag = CodeRAGSystem()

    # Create temporary directory
    temp_dir = Path(tempfile.mkdtemp(prefix='almquist_network_code_'))
    print(f"\n📁 Temporary directory: {temp_dir}")

    try:
        # 1. Sync from NAS5
        print("\n" + "="*70)
        print("PHASE 1: Syncing from NAS5")
        print("="*70)

        nas5_local = sync_from_nas5(NETWORK_LOCATIONS['nas5_apps'], temp_dir)

        # Count files
        file_stats = count_code_files(nas5_local)
        print(f"\n📊 NAS5 Apps Statistics:")
        for ext, count in sorted(file_stats.items(), key=lambda x: x[1], reverse=True):
            print(f"   {ext}: {count} files")

        # 2. Extract from Docker containers
        print("\n" + "="*70)
        print("PHASE 2: Extracting from Docker Containers")
        print("="*70)

        docker_extracted = 0
        for container in NAS5_DOCKER_CONTAINERS:
            container_dir = extract_docker_code(container, temp_dir)

            # Check if anything was extracted
            file_count = sum(1 for _ in container_dir.rglob('*') if _.is_file())
            if file_count > 0:
                docker_extracted += 1

        print(f"\n✅ Extracted code from {docker_extracted}/{len(NAS5_DOCKER_CONTAINERS)} containers")

        # 3. Index everything
        print("\n" + "="*70)
        print("PHASE 3: Indexing All Code")
        print("="*70)

        rag.index_location(str(temp_dir), "Network & Docker Code")

        # 4. Rebuild FAISS index
        print("\n" + "="*70)
        print("PHASE 4: Rebuilding FAISS Index")
        print("="*70)

        rag.build_faiss_index()

        print("\n" + "="*70)
        print("✅ INDEXING COMPLETE")
        print("="*70)

        # Show final statistics
        print("\n📊 Final Statistics:")
        import psycopg2
        conn = psycopg2.connect(rag.db_url)
        cursor = conn.cursor()

        cursor.execute('SELECT COUNT(*) FROM code_files WHERE is_active = true')
        total_files = cursor.fetchone()[0]

        cursor.execute('SELECT COUNT(*) FROM code_chunks')
        total_chunks = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(DISTINCT repository_name) FROM code_files WHERE repository_name IS NOT NULL AND repository_name != 'puzik'")
        total_repos = cursor.fetchone()[0]

        conn.close()

        print(f"   Total Files: {total_files:,}")
        print(f"   Total Chunks: {total_chunks:,}")
        print(f"   Total Repositories: {total_repos:,}")

    finally:
        # Cleanup
        print(f"\n🧹 Cleaning up temporary directory...")
        try:
            shutil.rmtree(temp_dir)
            print("   ✅ Cleanup complete")
        except Exception as e:
            print(f"   ⚠️  Could not cleanup {temp_dir}: {e}")
            print(f"   Please manually delete: rm -rf {temp_dir}")


if __name__ == '__main__':
    main()
