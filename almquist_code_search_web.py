#!/usr/bin/env python3
"""
ALMQUIST CODE SEARCH - Web Interface
Beautiful web UI for searching your code
"""

from flask import Flask, render_template_string, request, jsonify
from almquist_code_rag_system import CodeRAGSystem
import psycopg2
import psycopg2.extras
from datetime import datetime
import sys

app = Flask(__name__)

# Initialize RAG system
rag = CodeRAGSystem()

# HTML Template
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="cs">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Almquist Code Search</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }

        .container {
            max-width: 1400px;
            margin: 0 auto;
        }

        .header {
            text-align: center;
            color: white;
            margin-bottom: 40px;
        }

        .header h1 {
            font-size: 3em;
            margin-bottom: 10px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.2);
        }

        .header p {
            font-size: 1.2em;
            opacity: 0.9;
        }

        .stats {
            display: flex;
            gap: 20px;
            justify-content: center;
            margin-bottom: 30px;
            flex-wrap: wrap;
        }

        .stat-card {
            background: white;
            padding: 20px 30px;
            border-radius: 12px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            text-align: center;
        }

        .stat-number {
            font-size: 2em;
            font-weight: bold;
            color: #667eea;
        }

        .stat-label {
            color: #666;
            margin-top: 5px;
        }

        .search-box {
            background: white;
            padding: 40px;
            border-radius: 16px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            margin-bottom: 30px;
        }

        .search-input-container {
            display: flex;
            gap: 10px;
            margin-bottom: 20px;
        }

        #searchInput {
            flex: 1;
            padding: 15px 20px;
            font-size: 16px;
            border: 2px solid #e0e0e0;
            border-radius: 8px;
            outline: none;
            transition: border-color 0.3s;
        }

        #searchInput:focus {
            border-color: #667eea;
        }

        .search-button {
            padding: 15px 40px;
            font-size: 16px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            font-weight: bold;
            transition: transform 0.2s;
        }

        .search-button:hover {
            transform: translateY(-2px);
        }

        .filters {
            display: flex;
            gap: 15px;
            flex-wrap: wrap;
        }

        .filter-group {
            display: flex;
            align-items: center;
            gap: 8px;
        }

        .filter-group label {
            color: #666;
            font-weight: 500;
        }

        .filter-group select {
            padding: 8px 12px;
            border: 2px solid #e0e0e0;
            border-radius: 6px;
            outline: none;
            cursor: pointer;
        }

        .results {
            display: grid;
            gap: 20px;
        }

        .result-card {
            background: white;
            padding: 25px;
            border-radius: 12px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            transition: transform 0.2s, box-shadow 0.2s;
        }

        .result-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 12px rgba(0,0,0,0.15);
        }

        .result-header {
            display: flex;
            justify-content: space-between;
            align-items: start;
            margin-bottom: 15px;
            flex-wrap: wrap;
            gap: 10px;
        }

        .result-title {
            flex: 1;
        }

        .result-filename {
            font-size: 1.2em;
            font-weight: bold;
            color: #333;
            margin-bottom: 5px;
        }

        .result-path {
            font-size: 0.9em;
            color: #666;
            word-break: break-all;
        }

        .result-score {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 8px 16px;
            border-radius: 20px;
            font-weight: bold;
        }

        .result-meta {
            display: flex;
            gap: 15px;
            margin-bottom: 15px;
            flex-wrap: wrap;
        }

        .meta-tag {
            display: inline-flex;
            align-items: center;
            gap: 5px;
            padding: 6px 12px;
            background: #f0f0f0;
            border-radius: 6px;
            font-size: 0.9em;
            color: #666;
        }

        .code-preview {
            background: #1e1e1e;
            color: #d4d4d4;
            padding: 20px;
            border-radius: 8px;
            overflow-x: auto;
            font-family: 'Courier New', monospace;
            font-size: 14px;
            line-height: 1.6;
            position: relative;
        }

        .code-preview pre {
            margin: 0;
        }

        .copy-button {
            position: absolute;
            top: 10px;
            right: 10px;
            background: #667eea;
            color: white;
            border: none;
            padding: 8px 15px;
            border-radius: 6px;
            cursor: pointer;
            font-size: 12px;
            opacity: 0.8;
            transition: opacity 0.2s;
        }

        .copy-button:hover {
            opacity: 1;
        }

        .loading {
            text-align: center;
            padding: 40px;
            color: white;
            font-size: 1.2em;
        }

        .no-results {
            text-align: center;
            padding: 60px 40px;
            background: white;
            border-radius: 12px;
            color: #666;
        }

        .no-results h2 {
            margin-bottom: 10px;
            color: #333;
        }

        .language-badge {
            display: inline-block;
            padding: 4px 10px;
            border-radius: 4px;
            font-size: 0.85em;
            font-weight: bold;
        }

        .lang-python { background: #3776ab; color: white; }
        .lang-javascript { background: #f7df1e; color: black; }
        .lang-typescript { background: #3178c6; color: white; }
        .lang-bash { background: #4eaa25; color: white; }
        .lang-php { background: #777bb4; color: white; }
        .lang-default { background: #999; color: white; }

        @media (max-width: 768px) {
            .header h1 {
                font-size: 2em;
            }

            .search-input-container {
                flex-direction: column;
            }

            .result-header {
                flex-direction: column;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔍 Almquist Code Search</h1>
            <p>Semantic search across all your scripts and repositories</p>
        </div>

        <div class="stats" id="stats">
            <div class="stat-card">
                <div class="stat-number" id="totalFiles">-</div>
                <div class="stat-label">Code Files</div>
            </div>
            <div class="stat-card">
                <div class="stat-number" id="totalChunks">-</div>
                <div class="stat-label">Code Chunks</div>
            </div>
            <div class="stat-card">
                <div class="stat-number" id="totalRepos">-</div>
                <div class="stat-label">Repositories</div>
            </div>
        </div>

        <div class="search-box">
            <div class="search-input-container">
                <input type="text" id="searchInput" placeholder="e.g., 'function to process PDF files', 'database migration script', 'API endpoint for user authentication'">
                <button class="search-button" onclick="search()">Search</button>
            </div>

            <div class="filters">
                <div class="filter-group">
                    <label>Language:</label>
                    <select id="languageFilter">
                        <option value="">All</option>
                        <option value="python">Python</option>
                        <option value="javascript">JavaScript</option>
                        <option value="typescript">TypeScript</option>
                        <option value="bash">Bash</option>
                        <option value="php">PHP</option>
                    </select>
                </div>
                <div class="filter-group">
                    <label>Results:</label>
                    <select id="limitFilter">
                        <option value="10">10</option>
                        <option value="20">20</option>
                        <option value="50">50</option>
                    </select>
                </div>
            </div>
        </div>

        <div id="results"></div>
    </div>

    <script>
        // Load stats on page load
        loadStats();

        // Enable Enter key to search
        document.getElementById('searchInput').addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                search();
            }
        });

        async function loadStats() {
            try {
                const response = await fetch('/api/stats');
                const stats = await response.json();

                document.getElementById('totalFiles').textContent = stats.total_files.toLocaleString();
                document.getElementById('totalChunks').textContent = stats.total_chunks.toLocaleString();
                document.getElementById('totalRepos').textContent = stats.total_repos.toLocaleString();
            } catch (error) {
                console.error('Error loading stats:', error);
            }
        }

        async function search() {
            const query = document.getElementById('searchInput').value.trim();
            if (!query) {
                alert('Please enter a search query');
                return;
            }

            const language = document.getElementById('languageFilter').value;
            const limit = document.getElementById('limitFilter').value;

            const resultsDiv = document.getElementById('results');
            resultsDiv.innerHTML = '<div class="loading">🔄 Searching...</div>';

            try {
                const response = await fetch('/api/search', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ query, language, limit: parseInt(limit) })
                });

                const data = await response.json();

                if (data.results.length === 0) {
                    resultsDiv.innerHTML = `
                        <div class="no-results">
                            <h2>No results found</h2>
                            <p>Try different keywords or check if indexing is complete</p>
                        </div>
                    `;
                    return;
                }

                let html = '';
                data.results.forEach((result, index) => {
                    const langClass = `lang-${result.language}`;
                    html += `
                        <div class="result-card">
                            <div class="result-header">
                                <div class="result-title">
                                    <div class="result-filename">📄 ${result.file_name}</div>
                                    <div class="result-path">${result.file_path}</div>
                                </div>
                                <div class="result-score">Score: ${result.score.toFixed(3)}</div>
                            </div>

                            <div class="result-meta">
                                <span class="meta-tag">
                                    <span class="language-badge ${langClass}">${result.language}</span>
                                </span>
                                <span class="meta-tag">📍 Lines ${result.start_line}-${result.end_line}</span>
                                <span class="meta-tag">🏷️ ${result.chunk_type}</span>
                                ${result.repository ? `<span class="meta-tag">📦 ${result.repository}</span>` : ''}
                            </div>

                            <div class="code-preview">
                                <button class="copy-button" onclick="copyCode(${index})">Copy</button>
                                <pre id="code-${index}">${escapeHtml(result.code)}</pre>
                            </div>
                        </div>
                    `;
                });

                resultsDiv.innerHTML = html;

            } catch (error) {
                resultsDiv.innerHTML = `
                    <div class="no-results">
                        <h2>Error</h2>
                        <p>${error.message}</p>
                    </div>
                `;
            }
        }

        function copyCode(index) {
            const codeElement = document.getElementById(`code-${index}`);
            const text = codeElement.textContent;

            navigator.clipboard.writeText(text).then(() => {
                const button = codeElement.previousElementSibling;
                const originalText = button.textContent;
                button.textContent = '✓ Copied!';
                setTimeout(() => {
                    button.textContent = originalText;
                }, 2000);
            });
        }

        function escapeHtml(text) {
            const div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        }
    </script>
</body>
</html>
'''


@app.route('/')
def index():
    """Main page"""
    return render_template_string(HTML_TEMPLATE)


@app.route('/api/stats')
def get_stats():
    """Get system statistics"""
    try:
        conn = psycopg2.connect(rag.db_url)
        cursor = conn.cursor()

        # Total files
        cursor.execute('SELECT COUNT(*) FROM code_files WHERE is_active = true')
        total_files = cursor.fetchone()[0]

        # Total chunks
        cursor.execute('SELECT COUNT(*) FROM code_chunks')
        total_chunks = cursor.fetchone()[0]

        # Total repositories
        cursor.execute('SELECT COUNT(DISTINCT repository_name) FROM code_files WHERE repository_name IS NOT NULL')
        total_repos = cursor.fetchone()[0]

        conn.close()

        return jsonify({
            'total_files': total_files,
            'total_chunks': total_chunks,
            'total_repos': total_repos,
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/search', methods=['POST'])
def api_search():
    """Search API endpoint"""
    try:
        data = request.json
        query = data.get('query', '').strip()
        language = data.get('language') or None
        limit = data.get('limit', 10)

        if not query:
            return jsonify({'error': 'Query is required'}), 400

        # Search
        results = rag.search(query, k=limit, language_filter=language)

        return jsonify({
            'query': query,
            'results': results,
            'count': len(results),
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    print("🚀 Starting Almquist Code Search Web Interface...")
    print("📍 Access at: http://localhost:5555")
    print()

    app.run(host='0.0.0.0', port=5555, debug=True)
