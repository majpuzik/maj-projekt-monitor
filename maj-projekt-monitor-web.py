#!/usr/bin/env python3
"""
MAJ-PROJEKT-MONITOR WEB GUI - Interactive Project Dashboard

Real-time dashboard for monitoring all projects:
- Project overview with phase visualization
- Quality score graphs
- Test progress tracking
- TODO list management
- Timeline visualization
- Automated bot status
- Problem alerts
- Performance metrics

Features:
- Real-time updates via WebSocket
- Interactive charts (Chart.js)
- Responsive design
- Color-coded status indicators (green/yellow/red)
- Historical data visualization

Author: Claude + Maj
Date: 2025-12-03
"""

from flask import Flask, render_template, jsonify, request, send_from_directory
from flask_socketio import SocketIO, emit
import sqlite3
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List
import threading
import time

# Import main monitor
sys.path.insert(0, str(Path(__file__).parent))
import importlib.util
spec = importlib.util.spec_from_file_location("maj_projekt_monitor", str(Path(__file__).parent / "maj-projekt-monitor.py"))
maj_projekt_monitor = importlib.util.module_from_spec(spec)
spec.loader.exec_module(maj_projekt_monitor)

ProjectMonitor = maj_projekt_monitor.ProjectMonitor
ProjectDatabase = maj_projekt_monitor.ProjectDatabase
Config = maj_projekt_monitor.Config
ProjectPhase = maj_projekt_monitor.ProjectPhase

# ============================================================================
# Flask App Setup
# ============================================================================

app = Flask(__name__)
app.config['SECRET_KEY'] = 'maj-projekt-monitor-2025'
socketio = SocketIO(app, cors_allowed_origins="*")

monitor = ProjectMonitor()
db = monitor.db

# ============================================================================
# Background Update Thread
# ============================================================================

def background_updater():
    """Send real-time updates to all connected clients"""
    while True:
        try:
            # Get all project statuses
            projects = []
            with db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT id FROM projects WHERE status = 'active'")
                project_ids = [row[0] for row in cursor.fetchall()]

            for project_id in project_ids:
                status = monitor.get_project_status(project_id)
                if status:
                    projects.append(status)

            # Emit update
            socketio.emit('project_update', {
                'projects': projects,
                'timestamp': datetime.now().isoformat()
            })

            time.sleep(5)  # Update every 5 seconds

        except Exception as e:
            print(f"Background updater error: {e}")
            time.sleep(10)

# Start background thread
update_thread = threading.Thread(target=background_updater, daemon=True)
update_thread.start()

# ============================================================================
# API Endpoints
# ============================================================================

@app.route('/')
def index():
    """Main dashboard"""
    return render_template('dashboard.html')

@app.route('/api/projects')
def get_projects():
    """Get all projects"""
    with db.get_connection() as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM projects WHERE status = 'active' ORDER BY updated_at DESC")
        projects = [dict(row) for row in cursor.fetchall()]

    return jsonify({'projects': projects})

@app.route('/api/project/<int:project_id>')
def get_project(project_id):
    """Get project details"""
    status = monitor.get_project_status(project_id)
    return jsonify(status)

@app.route('/api/project/<int:project_id>/analysis')
def get_project_analysis(project_id):
    """Get project analysis history"""
    hours = request.args.get('hours', 24, type=int)
    analyses = db.get_recent_analyses(project_id, hours=hours)

    return jsonify({
        'analyses': [
            {
                'time': a.analysis_time,
                'quality': a.quality_score,
                'progress': a.progress_percent,
                'tests_passed': a.tests_passed,
                'tests_failed': a.tests_failed,
                'todos_completed': a.todos_completed,
                'todos_remaining': a.todos_remaining
            }
            for a in analyses
        ]
    })

@app.route('/api/project/<int:project_id>/quality')
def get_project_quality(project_id):
    """Get quality metrics"""
    scores = db.get_quality_scores(project_id)

    # Group by metric
    metrics = {}
    for score in scores:
        if score.metric not in metrics:
            metrics[score.metric] = []
        metrics[score.metric].append({
            'time': score.calculated_at,
            'score': score.score,
            'max_score': score.max_score
        })

    return jsonify({'metrics': metrics})

@app.route('/api/project/<int:project_id>/tests')
def get_project_tests(project_id):
    """Get test results"""
    tests = db.get_project_tests(project_id)

    return jsonify({
        'tests': [
            {
                'name': t.test_name,
                'type': t.test_type,
                'status': t.status,
                'started_at': t.started_at,
                'duration': t.duration_seconds,
                'error': t.error_message
            }
            for t in tests[:50]  # Last 50 tests
        ]
    })

@app.route('/api/project/<int:project_id>/todos')
def get_project_todos(project_id):
    """Get project TODOs"""
    todos = db.get_project_todos(project_id)

    return jsonify({
        'todos': [
            {
                'id': t.id,
                'task': t.task,
                'status': t.status,
                'priority': t.priority,
                'created_at': t.created_at,
                'assigned_to': t.assigned_to
            }
            for t in todos
        ]
    })

@app.route('/api/project/<int:project_id>/structure')
def get_project_structure(project_id):
    """Get project structure (files/programs)"""
    programs = db.get_project_programs(project_id)

    # Group by language
    by_language = {}
    total_loc = 0

    for prog in programs:
        if prog.language not in by_language:
            by_language[prog.language] = []
        by_language[prog.language].append({
            'name': prog.name,
            'path': prog.path,
            'lines': prog.lines_of_code
        })
        total_loc += prog.lines_of_code

    return jsonify({
        'programs': by_language,
        'total_programs': len(programs),
        'total_lines': total_loc
    })

@app.route('/api/project/<int:project_id>/export/markdown')
def export_markdown(project_id):
    """Export project documentation as Markdown"""
    try:
        # Import export module
        import importlib.util
        spec = importlib.util.spec_from_file_location("maj_projekt_monitor_export",
                                                      str(Path(__file__).parent / "maj-projekt-monitor-export.py"))
        export_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(export_module)

        exporter = export_module.ProjectExporter(project_id)
        output_path = exporter.export_markdown()

        return send_from_directory(
            str(Path(output_path).parent),
            Path(output_path).name,
            as_attachment=True
        )
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/project/<int:project_id>/export/pdf')
def export_pdf(project_id):
    """Export project documentation as PDF"""
    try:
        # Import export module
        import importlib.util
        spec = importlib.util.spec_from_file_location("maj_projekt_monitor_export",
                                                      str(Path(__file__).parent / "maj-projekt-monitor-export.py"))
        export_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(export_module)

        exporter = export_module.ProjectExporter(project_id)
        output_path = exporter.export_pdf()

        if not output_path:
            return jsonify({'error': 'PDF export failed - ReportLab not installed'}), 500

        return send_from_directory(
            str(Path(output_path).parent),
            Path(output_path).name,
            as_attachment=True
        )
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/project/<int:project_id>/print/<format>')
def print_document(project_id, format):
    """Print project documentation"""
    try:
        # Import export module
        import importlib.util
        spec = importlib.util.spec_from_file_location("maj_projekt_monitor_export",
                                                      str(Path(__file__).parent / "maj-projekt-monitor-export.py"))
        export_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(export_module)

        exporter = export_module.ProjectExporter(project_id)
        success = exporter.print_document(format)

        if success:
            return jsonify({'message': f'Document sent to printer in {format} format'})
        else:
            return jsonify({'error': 'Print failed'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/overview')
def get_overview():
    """Get system overview"""
    with db.get_connection() as conn:
        cursor = conn.cursor()

        # Count projects by phase
        cursor.execute("""
            SELECT phase, COUNT(*) as count
            FROM projects
            WHERE status = 'active'
            GROUP BY phase
        """)
        by_phase = dict(cursor.fetchall())

        # Overall statistics
        cursor.execute("""
            SELECT
                COUNT(*) as total_projects,
                AVG(quality_score) as avg_quality,
                SUM(CASE WHEN quality_score >= 90 THEN 1 ELSE 0 END) as excellent_projects,
                SUM(CASE WHEN quality_score >= 75 THEN 1 ELSE 0 END) as good_projects
            FROM projects
            WHERE status = 'active'
        """)
        stats = dict(zip(['total_projects', 'avg_quality', 'excellent_projects', 'good_projects'],
                        cursor.fetchone()))

        # Recent activity
        cursor.execute("""
            SELECT component, event_type, timestamp, details
            FROM events
            WHERE component = 'maj-projekt-monitor'
            ORDER BY timestamp DESC
            LIMIT 20
        """)
        recent_activity = [
            {
                'component': row[0],
                'event': row[1],
                'time': row[2],
                'details': json.loads(row[3]) if row[3] else {}
            }
            for row in cursor.fetchall()
        ]

    return jsonify({
        'by_phase': by_phase,
        'statistics': stats,
        'recent_activity': recent_activity
    })

@app.route('/api/bot/status')
def get_bot_status():
    """Get bot status"""
    # Check if bot is running
    import psutil
    bot_running = False
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            if 'maj-projekt-monitor-bot' in ' '.join(proc.info['cmdline'] or []):
                bot_running = True
                break
        except:
            pass

    return jsonify({
        'running': bot_running,
        'last_check': datetime.now().isoformat()
    })

# ============================================================================
# WebSocket Events
# ============================================================================

@socketio.on('connect')
def handle_connect():
    """Client connected"""
    print(f"Client connected: {request.sid}")
    emit('connected', {'message': 'Connected to MAJ-PROJEKT-MONITOR'})

@socketio.on('disconnect')
def handle_disconnect():
    """Client disconnected"""
    print(f"Client disconnected: {request.sid}")

@socketio.on('analyze_project')
def handle_analyze_project(data):
    """Trigger project analysis"""
    project_id = data.get('project_id')
    if project_id:
        try:
            analysis = monitor.run_analysis(project_id)
            emit('analysis_complete', {
                'project_id': project_id,
                'analysis': {
                    'quality': analysis.quality_score,
                    'progress': analysis.progress_percent,
                    'tests_passed': analysis.tests_passed,
                    'tests_failed': analysis.tests_failed
                }
            })
        except Exception as e:
            emit('error', {'message': str(e)})

# ============================================================================
# HTML Templates
# ============================================================================

@app.route('/static/<path:filename>')
def static_files(filename):
    """Serve static files"""
    return send_from_directory('static', filename)

# ============================================================================
# Run Server
# ============================================================================

def create_template():
    """Create HTML template"""
    template_dir = Path(__file__).parent / "templates"
    template_dir.mkdir(exist_ok=True)

    html_content = '''<!DOCTYPE html>
<html lang="cs">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>MAJ-PROJEKT-MONITOR - Dashboard</title>
    <script src="https://cdn.socket.io/4.5.4/socket.io.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
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
            background: white;
            padding: 30px;
            border-radius: 15px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.1);
            margin-bottom: 30px;
        }

        .header h1 {
            color: #667eea;
            font-size: 2.5em;
            margin-bottom: 10px;
        }

        .header .subtitle {
            color: #666;
            font-size: 1.1em;
        }

        .status-indicator {
            display: inline-block;
            width: 12px;
            height: 12px;
            border-radius: 50%;
            margin-left: 10px;
            animation: pulse 2s infinite;
        }

        .status-indicator.green {
            background: #10b981;
        }

        .status-indicator.yellow {
            background: #f59e0b;
        }

        .status-indicator.red {
            background: #ef4444;
        }

        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }

        .grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
            gap: 20px;
            margin-bottom: 20px;
        }

        .card {
            background: white;
            padding: 25px;
            border-radius: 15px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.1);
            transition: transform 0.2s, box-shadow 0.2s;
        }

        .card:hover {
            transform: translateY(-5px);
            box-shadow: 0 15px 50px rgba(0,0,0,0.15);
        }

        .card h2 {
            color: #333;
            margin-bottom: 15px;
            font-size: 1.5em;
        }

        .project-card {
            border-left: 5px solid #667eea;
        }

        .quality-score {
            font-size: 3em;
            font-weight: bold;
            text-align: center;
            margin: 20px 0;
        }

        .quality-score.excellent { color: #10b981; }
        .quality-score.good { color: #3b82f6; }
        .quality-score.acceptable { color: #f59e0b; }
        .quality-score.poor { color: #ef4444; }

        .progress-bar {
            width: 100%;
            height: 30px;
            background: #e5e7eb;
            border-radius: 15px;
            overflow: hidden;
            margin: 10px 0;
        }

        .progress-fill {
            height: 100%;
            background: linear-gradient(90deg, #667eea, #764ba2);
            transition: width 0.5s ease;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-weight: bold;
        }

        .stat {
            display: flex;
            justify-content: space-between;
            padding: 10px 0;
            border-bottom: 1px solid #e5e7eb;
        }

        .stat:last-child {
            border-bottom: none;
        }

        .stat-label {
            color: #666;
        }

        .stat-value {
            font-weight: bold;
            color: #333;
        }

        .phase-badge {
            display: inline-block;
            padding: 5px 15px;
            border-radius: 20px;
            font-size: 0.9em;
            font-weight: bold;
            text-transform: uppercase;
        }

        .phase-planning { background: #fef3c7; color: #92400e; }
        .phase-design { background: #dbeafe; color: #1e40af; }
        .phase-development { background: #e0e7ff; color: #3730a3; }
        .phase-testing { background: #fce7f3; color: #831843; }
        .phase-review { background: #f3e8ff; color: #6b21a8; }
        .phase-deployment { background: #ffedd5; color: #9a3412; }
        .phase-production { background: #d1fae5; color: #065f46; }

        canvas {
            max-height: 300px;
        }

        .todo-list {
            max-height: 400px;
            overflow-y: auto;
        }

        .todo-item {
            padding: 10px;
            margin: 5px 0;
            background: #f9fafb;
            border-radius: 8px;
            border-left: 3px solid #667eea;
        }

        .todo-item.done {
            opacity: 0.6;
            text-decoration: line-through;
        }

        .activity-log {
            max-height: 400px;
            overflow-y: auto;
            font-size: 0.9em;
        }

        .activity-item {
            padding: 8px;
            border-bottom: 1px solid #e5e7eb;
        }

        .activity-time {
            color: #999;
            font-size: 0.85em;
        }

        @media (max-width: 768px) {
            .grid {
                grid-template-columns: 1fr;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🤖 MAJ-PROJEKT-MONITOR</h1>
            <p class="subtitle">
                Comprehensive Project Lifecycle Management System
                <span class="status-indicator green" id="connection-status"></span>
            </p>
        </div>

        <div id="overview-section" class="grid">
            <!-- Overview cards will be injected here -->
        </div>

        <div id="projects-section" class="grid">
            <!-- Project cards will be injected here -->
        </div>
    </div>

    <script>
        // Socket.IO connection
        const socket = io();

        socket.on('connect', () => {
            console.log('Connected to server');
            document.getElementById('connection-status').className = 'status-indicator green';
        });

        socket.on('disconnect', () => {
            console.log('Disconnected from server');
            document.getElementById('connection-status').className = 'status-indicator red';
        });

        socket.on('project_update', (data) => {
            updateDashboard(data);
        });

        // Initial load
        loadOverview();
        loadProjects();

        // Reload every 30 seconds
        setInterval(loadProjects, 30000);

        async function loadOverview() {
            try {
                const response = await fetch('/api/overview');
                const data = await response.json();
                displayOverview(data);
            } catch (error) {
                console.error('Error loading overview:', error);
            }
        }

        async function loadProjects() {
            try {
                const response = await fetch('/api/projects');
                const data = await response.json();
                displayProjects(data.projects);
            } catch (error) {
                console.error('Error loading projects:', error);
            }
        }

        function displayOverview(data) {
            const section = document.getElementById('overview-section');
            const stats = data.statistics;

            section.innerHTML = `
                <div class="card">
                    <h2>📊 System Overview</h2>
                    <div class="stat">
                        <span class="stat-label">Total Projects</span>
                        <span class="stat-value">${stats.total_projects || 0}</span>
                    </div>
                    <div class="stat">
                        <span class="stat-label">Average Quality</span>
                        <span class="stat-value">${(stats.avg_quality || 0).toFixed(1)}/100</span>
                    </div>
                    <div class="stat">
                        <span class="stat-label">Excellent Projects</span>
                        <span class="stat-value">${stats.excellent_projects || 0}</span>
                    </div>
                </div>

                <div class="card">
                    <h2>📈 Projects by Phase</h2>
                    ${Object.entries(data.by_phase || {}).map(([phase, count]) => `
                        <div class="stat">
                            <span class="stat-label phase-badge phase-${phase}">${phase}</span>
                            <span class="stat-value">${count}</span>
                        </div>
                    `).join('')}
                </div>

                <div class="card">
                    <h2>🔔 Recent Activity</h2>
                    <div class="activity-log">
                        ${(data.recent_activity || []).map(activity => `
                            <div class="activity-item">
                                <strong>${activity.event}</strong>
                                <div class="activity-time">${new Date(activity.time).toLocaleString()}</div>
                            </div>
                        `).join('')}
                    </div>
                </div>
            `;
        }

        function displayProjects(projects) {
            const section = document.getElementById('projects-section');

            if (!projects || projects.length === 0) {
                section.innerHTML = '<div class="card"><h2>No active projects</h2></div>';
                return;
            }

            section.innerHTML = projects.map(project => {
                const qualityClass = project.quality_score >= 90 ? 'excellent' :
                                    project.quality_score >= 75 ? 'good' :
                                    project.quality_score >= 60 ? 'acceptable' : 'poor';

                return `
                    <div class="card project-card">
                        <h2>${project.name}</h2>
                        <span class="phase-badge phase-${project.phase}">${project.phase}</span>

                        <div class="quality-score ${qualityClass}">
                            ${project.quality_score.toFixed(0)}
                        </div>

                        <div class="stat">
                            <span class="stat-label">Customer</span>
                            <span class="stat-value">${project.customer || 'N/A'}</span>
                        </div>

                        <div class="stat">
                            <span class="stat-label">Environment</span>
                            <span class="stat-value">${project.environment || 'N/A'}</span>
                        </div>

                        <div class="stat">
                            <span class="stat-label">Last Updated</span>
                            <span class="stat-value">${new Date(project.updated_at).toLocaleDateString()}</span>
                        </div>

                        <button onclick="analyzeProject(${project.id})"
                                style="width: 100%; padding: 12px; margin-top: 15px; background: #667eea; color: white; border: none; border-radius: 8px; cursor: pointer; font-weight: bold;">
                            🔍 Analyze Now
                        </button>

                        <div style="display: flex; gap: 10px; margin-top: 10px;">
                            <button onclick="exportMarkdown(${project.id})"
                                    style="flex: 1; padding: 10px; background: #10b981; color: white; border: none; border-radius: 8px; cursor: pointer; font-size: 12px;">
                                📄 MD
                            </button>
                            <button onclick="exportPDF(${project.id})"
                                    style="flex: 1; padding: 10px; background: #ef4444; color: white; border: none; border-radius: 8px; cursor: pointer; font-size: 12px;">
                                📑 PDF
                            </button>
                            <button onclick="printDocument(${project.id})"
                                    style="flex: 1; padding: 10px; background: #8b5cf6; color: white; border: none; border-radius: 8px; cursor: pointer; font-size: 12px;">
                                🖨️ Print
                            </button>
                        </div>
                    </div>
                `;
            }).join('');
        }

        function analyzeProject(projectId) {
            socket.emit('analyze_project', { project_id: projectId });
            alert(`Analysis started for project ${projectId}`);
        }

        function exportMarkdown(projectId) {
            window.location.href = `/api/project/${projectId}/export/markdown`;
        }

        function exportPDF(projectId) {
            window.location.href = `/api/project/${projectId}/export/pdf`;
        }

        function printDocument(projectId) {
            fetch(`/api/project/${projectId}/print/pdf`)
                .then(response => response.json())
                .then(data => {
                    if (data.error) {
                        alert('Print error: ' + data.error);
                    } else {
                        alert(data.message);
                    }
                })
                .catch(error => {
                    alert('Print failed: ' + error);
                });
        }

        function updateDashboard(data) {
            // Real-time updates from WebSocket
            console.log('Dashboard update:', data);
        }
    </script>
</body>
</html>'''

    with open(template_dir / "dashboard.html", "w", encoding="utf-8") as f:
        f.write(html_content)

    print("✓ Template created")

def main():
    """Start web server"""
    create_template()

    print("=" * 70)
    print("🚀 MAJ-PROJEKT-MONITOR Web Dashboard")
    print("=" * 70)
    print("Starting server on http://0.0.0.0:5050")
    print("Press Ctrl+C to stop")
    print("=" * 70)

    socketio.run(app, host='0.0.0.0', port=5050, debug=False, allow_unsafe_werkzeug=True)

if __name__ == '__main__':
    main()
