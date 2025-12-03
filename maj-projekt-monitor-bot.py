#!/usr/bin/env python3
"""
MAJ-PROJEKT-MONITOR BOT - Automated Project Lifecycle Manager

This bot autonomously manages project lifecycle from birth to production:
- Hourly analysis of all active projects
- Automatic TODO management
- Test execution and monitoring
- Quality scoring
- Problem detection and reporting
- Phase transitions
- Continuous improvement recommendations

The bot operates independently and reports progress, problems, and results
through the GUI and logs.

Author: Claude + Maj
Date: 2025-12-03
"""

import time
import sqlite3
import subprocess
import sys
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import json
import schedule
import logging

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
TaskStatus = maj_projekt_monitor.TaskStatus
QualityMetric = maj_projekt_monitor.QualityMetric
ProjectTest = maj_projekt_monitor.ProjectTest
ProjectTodo = maj_projekt_monitor.ProjectTodo
QualityScore = maj_projekt_monitor.QualityScore

# ============================================================================
# Bot Configuration
# ============================================================================

class BotConfig:
    """Bot configuration"""
    ANALYSIS_INTERVAL_MINUTES = 60  # Hourly analysis
    TEST_INTERVAL_MINUTES = 30  # Run tests every 30 min
    QUALITY_CHECK_INTERVAL_MINUTES = 120  # Quality check every 2 hours

    LOG_FILE = "/home/puzik/logs/maj-projekt-monitor-bot.log"

    # Quality thresholds for phase transitions
    PHASE_QUALITY_REQUIREMENTS = {
        ProjectPhase.PLANNING: 50,
        ProjectPhase.DESIGN: 60,
        ProjectPhase.DEVELOPMENT: 70,
        ProjectPhase.TESTING: 80,
        ProjectPhase.REVIEW: 90,
        ProjectPhase.DEPLOYMENT: 95,
        ProjectPhase.PRODUCTION: 100
    }

# ============================================================================
# Logging Setup
# ============================================================================

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(BotConfig.LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('maj-projekt-bot')

# ============================================================================
# Bot Intelligence
# ============================================================================

class ProjectBot:
    """Intelligent bot for autonomous project management"""

    def __init__(self):
        self.monitor = ProjectMonitor()
        self.db = self.monitor.db
        logger.info("🤖 MAJ-PROJEKT-MONITOR BOT initialized")

    def get_active_projects(self) -> List[int]:
        """Get list of active project IDs"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id FROM projects WHERE status = 'active' ORDER BY id"
            )
            return [row[0] for row in cursor.fetchall()]

    # ========================================================================
    # Autonomous Analysis
    # ========================================================================

    def hourly_analysis(self):
        """Perform hourly analysis of all projects"""
        logger.info("=" * 70)
        logger.info("🔍 Starting hourly analysis of all projects")
        logger.info("=" * 70)

        projects = self.get_active_projects()

        if not projects:
            logger.info("No active projects found")
            return

        for project_id in projects:
            try:
                self.analyze_project(project_id)
            except Exception as e:
                logger.error(f"Error analyzing project {project_id}: {e}")

        logger.info("✓ Hourly analysis completed")

    def analyze_project(self, project_id: int):
        """Comprehensive project analysis"""
        project = self.db.get_project(project_id)
        if not project:
            return

        logger.info(f"\n📊 Analyzing: {project.name} (Phase: {project.phase})")

        # Run analysis
        analysis = self.monitor.run_analysis(project_id)

        # Report
        logger.info(f"  Progress: {analysis.progress_percent:.1f}%")
        logger.info(f"  Quality: {analysis.quality_score:.1f}/100")
        logger.info(f"  TODOs: {analysis.todos_completed} done, {analysis.todos_remaining} remaining")
        logger.info(f"  Tests: {analysis.tests_passed} passed, {analysis.tests_failed} failed")
        logger.info(f"  Issues: {analysis.issues_found}")

        # Recommendations
        recommendations = json.loads(analysis.recommendations)
        if recommendations:
            logger.info("  Recommendations:")
            for rec in recommendations:
                logger.info(f"    • {rec}")

        # Check if we should transition phase
        self.check_phase_transition(project_id, analysis)

        # Auto-fix issues if possible
        self.attempt_auto_fixes(project_id, analysis)

    # ========================================================================
    # Phase Management
    # ========================================================================

    def check_phase_transition(self, project_id: int, analysis):
        """Check if project should transition to next phase"""
        project = self.db.get_project(project_id)
        current_phase = ProjectPhase(project.phase)

        # Check requirements for current phase
        required_quality = BotConfig.PHASE_QUALITY_REQUIREMENTS.get(current_phase, 0)

        can_transition = (
            analysis.quality_score >= required_quality and
            analysis.tests_failed == 0 and
            analysis.todos_remaining == 0 and
            analysis.progress_percent >= 100
        )

        if can_transition:
            next_phase = self.get_next_phase(current_phase)
            if next_phase:
                logger.info(f"✓ {project.name} ready for phase transition: {current_phase.value} → {next_phase.value}")
                self.db.update_project_phase(project_id, next_phase.value)

                # Create TODOs for new phase
                self.create_phase_todos(project_id, next_phase)
        else:
            blockers = []
            if analysis.quality_score < required_quality:
                blockers.append(f"Quality: {analysis.quality_score:.1f} < {required_quality}")
            if analysis.tests_failed > 0:
                blockers.append(f"{analysis.tests_failed} failing tests")
            if analysis.todos_remaining > 0:
                blockers.append(f"{analysis.todos_remaining} pending TODOs")

            logger.info(f"  ⚠️  Phase transition blocked: {', '.join(blockers)}")

    def get_next_phase(self, current: ProjectPhase) -> Optional[ProjectPhase]:
        """Get next phase in lifecycle"""
        phases = list(ProjectPhase)
        try:
            idx = phases.index(current)
            if idx + 1 < len(phases):
                return phases[idx + 1]
        except:
            pass
        return None

    def create_phase_todos(self, project_id: int, phase: ProjectPhase):
        """Create TODOs for new phase"""
        now = datetime.now().isoformat()

        todos_by_phase = {
            ProjectPhase.PLANNING: [
                "Define project scope and objectives",
                "Identify stakeholders and requirements",
                "Create project timeline",
                "Define success criteria"
            ],
            ProjectPhase.DESIGN: [
                "Create system architecture",
                "Design database schema",
                "Define API interfaces",
                "Create wireframes/mockups"
            ],
            ProjectPhase.DEVELOPMENT: [
                "Implement core functionality",
                "Write unit tests",
                "Code review",
                "Documentation"
            ],
            ProjectPhase.TESTING: [
                "Run integration tests",
                "Performance testing",
                "Security testing",
                "User acceptance testing"
            ],
            ProjectPhase.REVIEW: [
                "Code quality review",
                "Documentation review",
                "Security audit",
                "Performance optimization"
            ],
            ProjectPhase.DEPLOYMENT: [
                "Prepare deployment environment",
                "Create deployment scripts",
                "Backup strategy",
                "Deploy to production"
            ],
            ProjectPhase.PRODUCTION: [
                "Monitor system health",
                "Handle user feedback",
                "Bug fixes",
                "Performance monitoring"
            ]
        }

        tasks = todos_by_phase.get(phase, [])
        for task in tasks:
            todo = ProjectTodo(
                id=None,
                project_id=project_id,
                task=task,
                status=TaskStatus.TODO.value,
                priority=5,
                created_at=now,
                updated_at=now,
                completed_at=None,
                assigned_to="claude-bot"
            )
            self.db.add_todo(todo)

        logger.info(f"  ✓ Created {len(tasks)} TODOs for {phase.value} phase")

    # ========================================================================
    # Test Management
    # ========================================================================

    def run_project_tests(self):
        """Run tests for all projects"""
        logger.info("🧪 Running tests for all projects")

        projects = self.get_active_projects()

        for project_id in projects:
            try:
                self.run_tests(project_id)
            except Exception as e:
                logger.error(f"Error running tests for project {project_id}: {e}")

    def run_tests(self, project_id: int):
        """Run tests for a project"""
        project = self.db.get_project(project_id)
        if not project:
            return

        project_path = Path(project.local_path)
        if not project_path.exists():
            return

        logger.info(f"  Testing: {project.name}")

        # Check for pytest
        if (project_path / "pytest.ini").exists() or any(project_path.rglob("test_*.py")):
            self.run_pytest(project_id, project_path)

        # Check for npm test
        if (project_path / "package.json").exists():
            self.run_npm_test(project_id, project_path)

    def run_pytest(self, project_id: int, project_path: Path):
        """Run pytest tests"""
        try:
            result = subprocess.run(
                ['python3', '-m', 'pytest', '--tb=short', '-v'],
                cwd=project_path,
                capture_output=True,
                text=True,
                timeout=300
            )

            # Parse results
            passed = result.stdout.count(' PASSED')
            failed = result.stdout.count(' FAILED')

            # Record test
            test = ProjectTest(
                id=None,
                project_id=project_id,
                program_id=None,
                test_name="pytest_suite",
                test_type="unit",
                status="passed" if result.returncode == 0 else "failed",
                started_at=datetime.now().isoformat(),
                completed_at=datetime.now().isoformat(),
                duration_seconds=None,
                error_message=result.stderr if result.returncode != 0 else None,
                coverage_percent=None
            )

            self.db.add_test(test)
            logger.info(f"    pytest: {passed} passed, {failed} failed")

        except Exception as e:
            logger.error(f"    pytest failed: {e}")

    def run_npm_test(self, project_id: int, project_path: Path):
        """Run npm tests"""
        try:
            result = subprocess.run(
                ['npm', 'test'],
                cwd=project_path,
                capture_output=True,
                text=True,
                timeout=300
            )

            test = ProjectTest(
                id=None,
                project_id=project_id,
                program_id=None,
                test_name="npm_test",
                test_type="unit",
                status="passed" if result.returncode == 0 else "failed",
                started_at=datetime.now().isoformat(),
                completed_at=datetime.now().isoformat(),
                duration_seconds=None,
                error_message=result.stderr if result.returncode != 0 else None,
                coverage_percent=None
            )

            self.db.add_test(test)
            logger.info(f"    npm test: {'passed' if result.returncode == 0 else 'failed'}")

        except Exception as e:
            logger.error(f"    npm test failed: {e}")

    # ========================================================================
    # Quality Assessment
    # ========================================================================

    def assess_quality(self):
        """Assess code quality for all projects"""
        logger.info("📏 Assessing code quality")

        projects = self.get_active_projects()

        for project_id in projects:
            try:
                self.assess_project_quality(project_id)
            except Exception as e:
                logger.error(f"Error assessing quality for project {project_id}: {e}")

    def assess_project_quality(self, project_id: int):
        """Assess quality for a project"""
        project = self.db.get_project(project_id)
        if not project:
            return

        logger.info(f"  Assessing: {project.name}")

        scores = {}

        # Code quality (pylint, flake8, etc.)
        scores['code_quality'] = self.check_code_quality(project_id)

        # Test coverage
        scores['test_coverage'] = self.check_test_coverage(project_id)

        # Documentation
        scores['documentation'] = self.check_documentation(project_id)

        # Security
        scores['security'] = self.check_security(project_id)

        # Calculate overall score
        overall = sum(scores.values()) / len(scores)

        # Update project quality score
        self.db.update_quality_score(project_id, overall)

        # Record individual scores
        now = datetime.now().isoformat()
        for metric, score in scores.items():
            quality_score = QualityScore(
                id=None,
                project_id=project_id,
                metric=metric,
                score=score,
                max_score=100.0,
                calculated_at=now,
                details=json.dumps({})
            )
            self.db.add_quality_score(quality_score)

        logger.info(f"    Overall quality: {overall:.1f}/100")
        for metric, score in scores.items():
            logger.info(f"    {metric}: {score:.1f}/100")

    def check_code_quality(self, project_id: int) -> float:
        """Check code quality using static analysis"""
        project = self.db.get_project(project_id)
        project_path = Path(project.local_path)

        # Count Python files
        py_files = list(project_path.rglob("*.py"))
        if not py_files:
            return 100.0  # No Python files, assume OK

        # Simple heuristic: check for common issues
        issues = 0
        total_lines = 0

        for py_file in py_files:
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    total_lines += len(lines)

                    for line in lines:
                        # Check for bad practices
                        if 'TODO' in line or 'FIXME' in line:
                            issues += 1
                        if 'print(' in line and 'debug' in line.lower():
                            issues += 1
            except:
                pass

        if total_lines == 0:
            return 100.0

        # Calculate score
        issue_ratio = issues / total_lines
        score = max(0, 100 - (issue_ratio * 1000))

        return score

    def check_test_coverage(self, project_id: int) -> float:
        """Check test coverage"""
        tests = self.db.get_project_tests(project_id)
        if not tests:
            return 0.0

        # Calculate from recent tests
        recent_tests = [t for t in tests if t.coverage_percent is not None]
        if recent_tests:
            return sum(t.coverage_percent for t in recent_tests) / len(recent_tests)

        # Estimate based on test/code ratio
        programs = self.db.get_project_programs(project_id)
        test_files = [p for p in programs if 'test' in p.name.lower()]

        if not programs:
            return 0.0

        ratio = len(test_files) / len(programs)
        return min(100, ratio * 100)

    def check_documentation(self, project_id: int) -> float:
        """Check documentation quality"""
        project = self.db.get_project(project_id)
        project_path = Path(project.local_path)

        score = 0.0

        # Check for README
        if (project_path / "README.md").exists():
            score += 30

        # Check for docs directory
        if (project_path / "docs").exists():
            score += 20

        # Check for docstrings in Python files
        py_files = list(project_path.rglob("*.py"))
        if py_files:
            documented = 0
            for py_file in py_files:
                try:
                    with open(py_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                        if '"""' in content or "'''" in content:
                            documented += 1
                except:
                    pass

            if py_files:
                doc_ratio = documented / len(py_files)
                score += doc_ratio * 50

        return min(100, score)

    def check_security(self, project_id: int) -> float:
        """Basic security check"""
        project = self.db.get_project(project_id)
        project_path = Path(project.local_path)

        issues = 0

        # Check for hardcoded secrets
        for py_file in project_path.rglob("*.py"):
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read().lower()
                    if 'password' in content and '=' in content:
                        issues += 1
                    if 'api_key' in content and '=' in content:
                        issues += 1
                    if 'secret' in content and '=' in content:
                        issues += 1
            except:
                pass

        # Basic score
        score = max(0, 100 - (issues * 10))
        return score

    # ========================================================================
    # Auto-Fix Attempts
    # ========================================================================

    def attempt_auto_fixes(self, project_id: int, analysis):
        """Attempt to automatically fix common issues"""
        if analysis.tests_failed > 0:
            logger.info("  🔧 Attempting auto-fixes for failing tests...")
            # TODO: Implement smart fixes

        if analysis.quality_score < Config.QUALITY_ACCEPTABLE:
            logger.info("  🔧 Attempting quality improvements...")
            # TODO: Auto-format code, add docstrings, etc.

    # ========================================================================
    # Status Reporting
    # ========================================================================

    def generate_status_report(self):
        """Generate comprehensive status report"""
        logger.info("\n" + "=" * 70)
        logger.info("📈 PROJECT STATUS REPORT")
        logger.info("=" * 70)

        projects = self.get_active_projects()

        for project_id in projects:
            project = self.db.get_project(project_id)
            if not project:
                continue

            status = self.monitor.get_project_status(project_id)

            logger.info(f"\n{project.name}")
            logger.info(f"  Phase: {project.phase}")
            logger.info(f"  Quality: {project.quality_score:.1f}/100")
            logger.info(f"  Programs: {len(status['programs'])}")
            logger.info(f"  Tests: {len(status['tests'])}")
            logger.info(f"  TODOs: {len([t for t in status['todos'] if t['status'] != 'done'])}")

        logger.info("\n" + "=" * 70)

# ============================================================================
# Scheduler
# ============================================================================

def run_bot():
    """Run bot with scheduler"""
    bot = ProjectBot()

    # Schedule tasks
    schedule.every(BotConfig.ANALYSIS_INTERVAL_MINUTES).minutes.do(bot.hourly_analysis)
    schedule.every(BotConfig.TEST_INTERVAL_MINUTES).minutes.do(bot.run_project_tests)
    schedule.every(BotConfig.QUALITY_CHECK_INTERVAL_MINUTES).minutes.do(bot.assess_quality)
    schedule.every().hour.do(bot.generate_status_report)

    logger.info("🤖 Bot started. Running scheduled tasks...")

    # Run initial analysis
    bot.hourly_analysis()

    # Main loop
    while True:
        try:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
        except KeyboardInterrupt:
            logger.info("Bot stopped by user")
            break
        except Exception as e:
            logger.error(f"Bot error: {e}")
            time.sleep(60)

# ============================================================================
# Main
# ============================================================================

if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='MAJ-PROJEKT-MONITOR BOT')
    parser.add_argument('--once', action='store_true', help='Run once and exit')
    parser.add_argument('--analyze', type=int, help='Analyze specific project')
    parser.add_argument('--test', type=int, help='Test specific project')
    parser.add_argument('--quality', type=int, help='Check quality of specific project')

    args = parser.parse_args()

    bot = ProjectBot()

    if args.analyze:
        bot.analyze_project(args.analyze)
    elif args.test:
        bot.run_tests(args.test)
    elif args.quality:
        bot.assess_project_quality(args.quality)
    elif args.once:
        bot.hourly_analysis()
        bot.run_project_tests()
        bot.assess_quality()
        bot.generate_status_report()
    else:
        run_bot()
