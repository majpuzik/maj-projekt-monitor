#!/usr/bin/env python3
"""
MAJ-PROJEKT-MONITOR - Comprehensive Project Lifecycle Management System

Features:
- Complete project lifecycle tracking (birth to production)
- Centralized database (CDB) integration
- Automatic logging from Claude CLI
- Hourly analysis of planning, programming, testing, fixes, goals
- Quality scoring system (0-100%)
- GUI dashboard with graphs
- Automated bot for independent operation
- GitHub integration
- Project structure visualization
- Test progress monitoring
- Security testing tracking
- Environment and customer management

Author: Claude + Maj
Date: 2025-12-03
"""

import sqlite3
import json
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import hashlib
import subprocess
from dataclasses import dataclass, asdict
from enum import Enum

# ============================================================================
# Configuration
# ============================================================================

class Config:
    """System configuration"""
    CDB_PATH = "/home/puzik/almquist-central-log/almquist.db"
    PROJECT_BASE_DIR = Path("/home/puzik")
    GITHUB_USER = "puzik"

    # Quality thresholds
    QUALITY_EXCELLENT = 90
    QUALITY_GOOD = 75
    QUALITY_ACCEPTABLE = 60
    QUALITY_POOR = 40

class ProjectPhase(Enum):
    """Project lifecycle phases"""
    PLANNING = "planning"
    DESIGN = "design"
    DEVELOPMENT = "development"
    TESTING = "testing"
    REVIEW = "review"
    DEPLOYMENT = "deployment"
    PRODUCTION = "production"
    MAINTENANCE = "maintenance"

class TaskStatus(Enum):
    """Task status"""
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    TESTING = "testing"
    DONE = "done"
    BLOCKED = "blocked"

class QualityMetric(Enum):
    """Quality metrics"""
    CODE_QUALITY = "code_quality"
    TEST_COVERAGE = "test_coverage"
    DOCUMENTATION = "documentation"
    SECURITY = "security"
    PERFORMANCE = "performance"
    MAINTAINABILITY = "maintainability"

# ============================================================================
# Data Models
# ============================================================================

@dataclass
class Project:
    """Project model"""
    id: Optional[int]
    name: str
    description: str
    phase: str
    created_at: str
    updated_at: str
    github_repo: Optional[str]
    local_path: str
    customer: Optional[str]
    environment: Optional[str]
    quality_score: float
    status: str

@dataclass
class ProjectProgram:
    """Program/script in project"""
    id: Optional[int]
    project_id: int
    name: str
    path: str
    language: str
    lines_of_code: int
    complexity_score: float
    last_modified: str
    git_hash: Optional[str]

@dataclass
class ProjectTest:
    """Test record"""
    id: Optional[int]
    project_id: int
    program_id: Optional[int]
    test_name: str
    test_type: str  # unit, integration, e2e, security
    status: str  # passed, failed, skipped
    started_at: str
    completed_at: Optional[str]
    duration_seconds: Optional[float]
    error_message: Optional[str]
    coverage_percent: Optional[float]

@dataclass
class ProjectTodo:
    """TODO item"""
    id: Optional[int]
    project_id: int
    task: str
    status: str
    priority: int
    created_at: str
    updated_at: str
    completed_at: Optional[str]
    assigned_to: str  # "claude-bot", "human", etc.

@dataclass
class QualityScore:
    """Quality score record"""
    id: Optional[int]
    project_id: int
    metric: str
    score: float
    max_score: float
    calculated_at: str
    details: str  # JSON

@dataclass
class ProjectAnalysis:
    """Hourly analysis record"""
    id: Optional[int]
    project_id: int
    analysis_time: str
    phase: str
    todos_completed: int
    todos_remaining: int
    tests_passed: int
    tests_failed: int
    quality_score: float
    issues_found: int
    recommendations: str  # JSON
    progress_percent: float

# ============================================================================
# Database Manager
# ============================================================================

class ProjectDatabase:
    """Database operations for project monitoring"""

    def __init__(self, db_path: str = Config.CDB_PATH):
        self.db_path = db_path
        self.init_database()

    def get_connection(self):
        """Get database connection"""
        return sqlite3.connect(self.db_path)

    def init_database(self):
        """Initialize database tables"""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Projects table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS projects (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL,
                    description TEXT,
                    phase TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    github_repo TEXT,
                    local_path TEXT NOT NULL,
                    customer TEXT,
                    environment TEXT,
                    quality_score REAL DEFAULT 0.0,
                    status TEXT NOT NULL
                )
            """)

            # Programs table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS project_programs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    project_id INTEGER NOT NULL,
                    name TEXT NOT NULL,
                    path TEXT NOT NULL,
                    language TEXT,
                    lines_of_code INTEGER DEFAULT 0,
                    complexity_score REAL DEFAULT 0.0,
                    last_modified TEXT NOT NULL,
                    git_hash TEXT,
                    FOREIGN KEY (project_id) REFERENCES projects(id),
                    UNIQUE(project_id, path)
                )
            """)

            # Tests table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS project_tests (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    project_id INTEGER NOT NULL,
                    program_id INTEGER,
                    test_name TEXT NOT NULL,
                    test_type TEXT NOT NULL,
                    status TEXT NOT NULL,
                    started_at TEXT NOT NULL,
                    completed_at TEXT,
                    duration_seconds REAL,
                    error_message TEXT,
                    coverage_percent REAL,
                    FOREIGN KEY (project_id) REFERENCES projects(id),
                    FOREIGN KEY (program_id) REFERENCES project_programs(id)
                )
            """)

            # TODOs table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS project_todos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    project_id INTEGER NOT NULL,
                    task TEXT NOT NULL,
                    status TEXT NOT NULL,
                    priority INTEGER DEFAULT 5,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    completed_at TEXT,
                    assigned_to TEXT NOT NULL,
                    FOREIGN KEY (project_id) REFERENCES projects(id)
                )
            """)

            # Quality scores table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS project_quality_scores (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    project_id INTEGER NOT NULL,
                    metric TEXT NOT NULL,
                    score REAL NOT NULL,
                    max_score REAL NOT NULL,
                    calculated_at TEXT NOT NULL,
                    details TEXT,
                    FOREIGN KEY (project_id) REFERENCES projects(id)
                )
            """)

            # Analysis table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS project_analysis (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    project_id INTEGER NOT NULL,
                    analysis_time TEXT NOT NULL,
                    phase TEXT NOT NULL,
                    todos_completed INTEGER DEFAULT 0,
                    todos_remaining INTEGER DEFAULT 0,
                    tests_passed INTEGER DEFAULT 0,
                    tests_failed INTEGER DEFAULT 0,
                    quality_score REAL DEFAULT 0.0,
                    issues_found INTEGER DEFAULT 0,
                    recommendations TEXT,
                    progress_percent REAL DEFAULT 0.0,
                    FOREIGN KEY (project_id) REFERENCES projects(id)
                )
            """)

            # Deployments table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS project_deployments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    project_id INTEGER NOT NULL,
                    environment TEXT NOT NULL,
                    version TEXT NOT NULL,
                    deployed_at TEXT NOT NULL,
                    deployed_by TEXT NOT NULL,
                    status TEXT NOT NULL,
                    rollback_available BOOLEAN DEFAULT 1,
                    notes TEXT,
                    FOREIGN KEY (project_id) REFERENCES projects(id)
                )
            """)

            # Security tests table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS project_security_tests (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    project_id INTEGER NOT NULL,
                    test_type TEXT NOT NULL,
                    severity TEXT NOT NULL,
                    finding TEXT,
                    status TEXT NOT NULL,
                    found_at TEXT NOT NULL,
                    fixed_at TEXT,
                    FOREIGN KEY (project_id) REFERENCES projects(id)
                )
            """)

            # Git commits table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS project_git_commits (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    project_id INTEGER NOT NULL,
                    commit_hash TEXT NOT NULL,
                    author TEXT NOT NULL,
                    message TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    files_changed INTEGER DEFAULT 0,
                    lines_added INTEGER DEFAULT 0,
                    lines_deleted INTEGER DEFAULT 0,
                    FOREIGN KEY (project_id) REFERENCES projects(id)
                )
            """)

            conn.commit()
            print(f"✓ Database initialized: {self.db_path}")

    # ========================================================================
    # Project Operations
    # ========================================================================

    def create_project(self, project: Project) -> int:
        """Create new project"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO projects (
                    name, description, phase, created_at, updated_at,
                    github_repo, local_path, customer, environment,
                    quality_score, status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                project.name, project.description, project.phase,
                project.created_at, project.updated_at, project.github_repo,
                project.local_path, project.customer, project.environment,
                project.quality_score, project.status
            ))
            project_id = cursor.lastrowid

            # Log to events
            cursor.execute("""
                INSERT INTO events (timestamp, component, event_type, metadata)
                VALUES (?, ?, ?, ?)
            """, (
                datetime.now().isoformat(),
                "maj-projekt-monitor",
                "project_created",
                json.dumps({"project_id": project_id, "name": project.name})
            ))

            conn.commit()
            return project_id

    def get_project(self, project_id: int) -> Optional[Project]:
        """Get project by ID"""
        with self.get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM projects WHERE id = ?", (project_id,))
            row = cursor.fetchone()
            if row:
                return Project(**dict(row))
            return None

    def get_project_by_name(self, name: str) -> Optional[Project]:
        """Get project by name"""
        with self.get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM projects WHERE name = ?", (name,))
            row = cursor.fetchone()
            if row:
                return Project(**dict(row))
            return None

    def update_project_phase(self, project_id: int, phase: str):
        """Update project phase"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE projects
                SET phase = ?, updated_at = ?
                WHERE id = ?
            """, (phase, datetime.now().isoformat(), project_id))

            cursor.execute("""
                INSERT INTO events (timestamp, component, event_type, metadata)
                VALUES (?, ?, ?, ?)
            """, (
                datetime.now().isoformat(),
                "maj-projekt-monitor",
                "phase_changed",
                json.dumps({"project_id": project_id, "new_phase": phase})
            ))

            conn.commit()

    def update_quality_score(self, project_id: int, score: float):
        """Update project quality score"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE projects
                SET quality_score = ?, updated_at = ?
                WHERE id = ?
            """, (score, datetime.now().isoformat(), project_id))
            conn.commit()

    # ========================================================================
    # Program Operations
    # ========================================================================

    def add_program(self, program: ProjectProgram) -> int:
        """Add program to project"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO project_programs (
                    project_id, name, path, language, lines_of_code,
                    complexity_score, last_modified, git_hash
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                program.project_id, program.name, program.path,
                program.language, program.lines_of_code,
                program.complexity_score, program.last_modified,
                program.git_hash
            ))
            conn.commit()
            return cursor.lastrowid

    def get_project_programs(self, project_id: int) -> List[ProjectProgram]:
        """Get all programs for project"""
        with self.get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM project_programs WHERE project_id = ?",
                (project_id,)
            )
            return [ProjectProgram(**dict(row)) for row in cursor.fetchall()]

    # ========================================================================
    # Test Operations
    # ========================================================================

    def add_test(self, test: ProjectTest) -> int:
        """Add test record"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO project_tests (
                    project_id, program_id, test_name, test_type, status,
                    started_at, completed_at, duration_seconds,
                    error_message, coverage_percent
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                test.project_id, test.program_id, test.test_name,
                test.test_type, test.status, test.started_at,
                test.completed_at, test.duration_seconds,
                test.error_message, test.coverage_percent
            ))
            conn.commit()
            return cursor.lastrowid

    def get_project_tests(self, project_id: int) -> List[ProjectTest]:
        """Get all tests for project"""
        with self.get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM project_tests WHERE project_id = ? ORDER BY started_at DESC",
                (project_id,)
            )
            return [ProjectTest(**dict(row)) for row in cursor.fetchall()]

    # ========================================================================
    # TODO Operations
    # ========================================================================

    def add_todo(self, todo: ProjectTodo) -> int:
        """Add TODO item"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO project_todos (
                    project_id, task, status, priority, created_at,
                    updated_at, completed_at, assigned_to
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                todo.project_id, todo.task, todo.status, todo.priority,
                todo.created_at, todo.updated_at, todo.completed_at,
                todo.assigned_to
            ))
            conn.commit()
            return cursor.lastrowid

    def update_todo_status(self, todo_id: int, status: str):
        """Update TODO status"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            completed_at = datetime.now().isoformat() if status == "done" else None
            cursor.execute("""
                UPDATE project_todos
                SET status = ?, updated_at = ?, completed_at = ?
                WHERE id = ?
            """, (status, datetime.now().isoformat(), completed_at, todo_id))
            conn.commit()

    def get_project_todos(self, project_id: int) -> List[ProjectTodo]:
        """Get all TODOs for project"""
        with self.get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM project_todos WHERE project_id = ? ORDER BY priority DESC, created_at",
                (project_id,)
            )
            return [ProjectTodo(**dict(row)) for row in cursor.fetchall()]

    # ========================================================================
    # Quality Score Operations
    # ========================================================================

    def add_quality_score(self, score: QualityScore) -> int:
        """Add quality score"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO project_quality_scores (
                    project_id, metric, score, max_score,
                    calculated_at, details
                ) VALUES (?, ?, ?, ?, ?, ?)
            """, (
                score.project_id, score.metric, score.score,
                score.max_score, score.calculated_at, score.details
            ))
            conn.commit()
            return cursor.lastrowid

    def get_quality_scores(self, project_id: int) -> List[QualityScore]:
        """Get quality scores for project"""
        with self.get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM project_quality_scores WHERE project_id = ? ORDER BY calculated_at DESC",
                (project_id,)
            )
            return [QualityScore(**dict(row)) for row in cursor.fetchall()]

    # ========================================================================
    # Analysis Operations
    # ========================================================================

    def add_analysis(self, analysis: ProjectAnalysis) -> int:
        """Add hourly analysis"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO project_analysis (
                    project_id, analysis_time, phase, todos_completed,
                    todos_remaining, tests_passed, tests_failed,
                    quality_score, issues_found, recommendations,
                    progress_percent
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                analysis.project_id, analysis.analysis_time, analysis.phase,
                analysis.todos_completed, analysis.todos_remaining,
                analysis.tests_passed, analysis.tests_failed,
                analysis.quality_score, analysis.issues_found,
                analysis.recommendations, analysis.progress_percent
            ))
            conn.commit()
            return cursor.lastrowid

    def get_recent_analyses(self, project_id: int, hours: int = 24) -> List[ProjectAnalysis]:
        """Get recent analyses"""
        cutoff = (datetime.now() - timedelta(hours=hours)).isoformat()
        with self.get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM project_analysis
                WHERE project_id = ? AND analysis_time > ?
                ORDER BY analysis_time DESC
            """, (project_id, cutoff))
            return [ProjectAnalysis(**dict(row)) for row in cursor.fetchall()]

# ============================================================================
# Project Monitor
# ============================================================================

class ProjectMonitor:
    """Main project monitoring class"""

    def __init__(self):
        self.db = ProjectDatabase()
        print("✓ MAJ-PROJEKT-MONITOR initialized")

    def create_new_project(
        self,
        name: str,
        description: str,
        local_path: str,
        github_repo: Optional[str] = None,
        customer: Optional[str] = None,
        environment: Optional[str] = None
    ) -> int:
        """Create new project"""
        now = datetime.now().isoformat()

        project = Project(
            id=None,
            name=name,
            description=description,
            phase=ProjectPhase.PLANNING.value,
            created_at=now,
            updated_at=now,
            github_repo=github_repo,
            local_path=local_path,
            customer=customer,
            environment=environment,
            quality_score=0.0,
            status="active"
        )

        project_id = self.db.create_project(project)
        print(f"✓ Created project: {name} (ID: {project_id})")

        # Create initial TODO
        self.db.add_todo(ProjectTodo(
            id=None,
            project_id=project_id,
            task="Define project requirements and scope",
            status=TaskStatus.TODO.value,
            priority=10,
            created_at=now,
            updated_at=now,
            completed_at=None,
            assigned_to="claude-bot"
        ))

        return project_id

    def scan_project_files(self, project_id: int):
        """Scan project directory and register all programs"""
        project = self.db.get_project(project_id)
        if not project:
            print(f"✗ Project {project_id} not found")
            return

        project_path = Path(project.local_path)
        if not project_path.exists():
            print(f"✗ Project path does not exist: {project_path}")
            return

        # Scan for code files
        extensions = {
            '.py': 'python',
            '.js': 'javascript',
            '.ts': 'typescript',
            '.sh': 'bash',
            '.rs': 'rust',
            '.go': 'go',
            '.java': 'java',
            '.cpp': 'cpp',
            '.c': 'c'
        }

        for ext, lang in extensions.items():
            for file_path in project_path.rglob(f'*{ext}'):
                if '.git' in file_path.parts or '__pycache__' in file_path.parts:
                    continue

                # Count lines of code
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        lines = len(f.readlines())
                except:
                    lines = 0

                # Get git hash if in repo
                git_hash = None
                try:
                    result = subprocess.run(
                        ['git', 'log', '-1', '--format=%H', str(file_path)],
                        cwd=project_path,
                        capture_output=True,
                        text=True,
                        timeout=5
                    )
                    if result.returncode == 0:
                        git_hash = result.stdout.strip()
                except:
                    pass

                program = ProjectProgram(
                    id=None,
                    project_id=project_id,
                    name=file_path.name,
                    path=str(file_path.relative_to(project_path)),
                    language=lang,
                    lines_of_code=lines,
                    complexity_score=0.0,  # TODO: Calculate
                    last_modified=datetime.fromtimestamp(
                        file_path.stat().st_mtime
                    ).isoformat(),
                    git_hash=git_hash
                )

                self.db.add_program(program)

        print(f"✓ Scanned project files for: {project.name}")

    def run_analysis(self, project_id: int) -> ProjectAnalysis:
        """Run comprehensive project analysis"""
        project = self.db.get_project(project_id)
        if not project:
            raise ValueError(f"Project {project_id} not found")

        # Get TODOs
        todos = self.db.get_project_todos(project_id)
        todos_completed = len([t for t in todos if t.status == "done"])
        todos_remaining = len([t for t in todos if t.status != "done"])

        # Get tests
        tests = self.db.get_project_tests(project_id)
        tests_passed = len([t for t in tests if t.status == "passed"])
        tests_failed = len([t for t in tests if t.status == "failed"])

        # Calculate progress
        total_todos = len(todos) if todos else 1
        progress_percent = (todos_completed / total_todos) * 100

        # Calculate quality score
        quality_scores = self.db.get_quality_scores(project_id)
        avg_quality = sum(s.score for s in quality_scores) / len(quality_scores) if quality_scores else 0.0

        # Generate recommendations
        recommendations = []
        if tests_failed > 0:
            recommendations.append(f"Fix {tests_failed} failing tests")
        if todos_remaining > 10:
            recommendations.append(f"High number of pending TODOs: {todos_remaining}")
        if avg_quality < Config.QUALITY_ACCEPTABLE:
            recommendations.append("Quality score below acceptable threshold")

        analysis = ProjectAnalysis(
            id=None,
            project_id=project_id,
            analysis_time=datetime.now().isoformat(),
            phase=project.phase,
            todos_completed=todos_completed,
            todos_remaining=todos_remaining,
            tests_passed=tests_passed,
            tests_failed=tests_failed,
            quality_score=avg_quality,
            issues_found=tests_failed + (todos_remaining // 5),
            recommendations=json.dumps(recommendations),
            progress_percent=progress_percent
        )

        self.db.add_analysis(analysis)
        return analysis

    def get_project_status(self, project_id: int) -> Dict:
        """Get complete project status"""
        project = self.db.get_project(project_id)
        if not project:
            return {}

        programs = self.db.get_project_programs(project_id)
        tests = self.db.get_project_tests(project_id)
        todos = self.db.get_project_todos(project_id)
        quality_scores = self.db.get_quality_scores(project_id)
        analyses = self.db.get_recent_analyses(project_id, hours=24)

        return {
            'project': asdict(project),
            'programs': [asdict(p) for p in programs],
            'tests': [asdict(t) for t in tests],
            'todos': [asdict(t) for t in todos],
            'quality_scores': [asdict(q) for q in quality_scores],
            'recent_analyses': [asdict(a) for a in analyses]
        }

# ============================================================================
# CLI Interface
# ============================================================================

def main():
    """Main CLI interface"""
    import argparse

    parser = argparse.ArgumentParser(description='MAJ-PROJEKT-MONITOR')
    subparsers = parser.add_subparsers(dest='command', help='Commands')

    # Create project
    create_parser = subparsers.add_parser('create', help='Create new project')
    create_parser.add_argument('name', help='Project name')
    create_parser.add_argument('path', help='Local path')
    create_parser.add_argument('--description', default='', help='Description')
    create_parser.add_argument('--github', help='GitHub repo')
    create_parser.add_argument('--customer', help='Customer name')
    create_parser.add_argument('--environment', help='Environment')

    # Scan project
    scan_parser = subparsers.add_parser('scan', help='Scan project files')
    scan_parser.add_argument('project_id', type=int, help='Project ID')

    # Analyze project
    analyze_parser = subparsers.add_parser('analyze', help='Analyze project')
    analyze_parser.add_argument('project_id', type=int, help='Project ID')

    # Get status
    status_parser = subparsers.add_parser('status', help='Get project status')
    status_parser.add_argument('project_id', type=int, help='Project ID')

    args = parser.parse_args()

    monitor = ProjectMonitor()

    if args.command == 'create':
        project_id = monitor.create_new_project(
            name=args.name,
            description=args.description,
            local_path=args.path,
            github_repo=args.github,
            customer=args.customer,
            environment=args.environment
        )
        print(f"Project created with ID: {project_id}")

    elif args.command == 'scan':
        monitor.scan_project_files(args.project_id)

    elif args.command == 'analyze':
        analysis = monitor.run_analysis(args.project_id)
        print(f"Analysis complete. Progress: {analysis.progress_percent:.1f}%")
        print(f"Quality score: {analysis.quality_score:.1f}")
        print(f"TODOs: {analysis.todos_completed}/{analysis.todos_completed + analysis.todos_remaining}")
        print(f"Tests: {analysis.tests_passed} passed, {analysis.tests_failed} failed")

    elif args.command == 'status':
        status = monitor.get_project_status(args.project_id)
        print(json.dumps(status, indent=2))

    else:
        parser.print_help()

if __name__ == '__main__':
    main()
