#!/usr/bin/env python3
"""
MAJ-PROJEKT-MONITOR - Export and Print Module

Supports:
- PDF export (specifications, docs, tests, logs, handover)
- Markdown export
- Direct printer output
- Graphical diagrams export

Author: Claude + Maj
Date: 2025-12-03
"""

import sqlite3
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import subprocess
import tempfile
import shutil

# Try to import PDF libraries
try:
    from reportlab.lib.pagesizes import A4, letter
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch, cm
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle, Image
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False
    print("⚠️  ReportLab not installed. Install with: pip3 install reportlab")

# Configuration
CDB_PATH = "/home/puzik/almquist-central-log/almquist.db"

# ============================================================================
# Export Functions
# ============================================================================

class ProjectExporter:
    """Export project documentation to various formats"""

    def __init__(self, project_id: int):
        self.project_id = project_id
        self.conn = sqlite3.connect(CDB_PATH)
        self.conn.row_factory = sqlite3.Row
        self.project = self._get_project()

    def _get_project(self) -> Dict:
        """Get project details"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM projects WHERE id = ?", (self.project_id,))
        row = cursor.fetchone()
        if not row:
            raise ValueError(f"Project {self.project_id} not found")
        return dict(row)

    def _get_specifications(self) -> List[Dict]:
        """Get project specifications from analysis"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT
                'Analýza projektu #' || id as title,
                analysis_time as created_at,
                'Fáze: ' || phase || '\nKvalita: ' || quality_score || '%\nProgress: ' || progress_percent || '%\n\n' || COALESCE(recommendations, 'Žádné poznámky') as content,
                recommendations as requirements
            FROM project_analysis
            WHERE project_id = ?
            ORDER BY analysis_time DESC
            LIMIT 5
        """, (self.project_id,))
        return [dict(row) for row in cursor.fetchall()]

    def _get_documentation(self) -> List[Dict]:
        """Get project documentation from analysis"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT
                'Dokumentace z analýzy #' || id as title,
                'analysis' as doc_type,
                analysis_time as created_at,
                'Výsledky analýzy:\n' ||
                '- TODOs hotovo: ' || todos_completed || '\n' ||
                '- TODOs zbývá: ' || todos_remaining || '\n' ||
                '- Testy úspěšné: ' || tests_passed || '\n' ||
                '- Testy neúspěšné: ' || tests_failed || '\n' ||
                '- Issues nalezeno: ' || issues_found || '\n\n' ||
                COALESCE(recommendations, 'Žádná doporučení') as content
            FROM project_analysis
            WHERE project_id = ?
            ORDER BY analysis_time DESC
            LIMIT 5
        """, (self.project_id,))
        return [dict(row) for row in cursor.fetchall()]

    def _get_test_results(self) -> List[Dict]:
        """Get test results"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT
                test_name,
                test_type,
                status,
                started_at as timestamp,
                duration_seconds,
                error_message
            FROM project_tests
            WHERE project_id = ?
            ORDER BY started_at DESC
        """, (self.project_id,))
        return [dict(row) for row in cursor.fetchall()]

    def _get_logs(self, limit: int = 100) -> List[Dict]:
        """Get project logs"""
        cursor = self.conn.cursor()
        # Get all events first, then filter in Python to handle malformed JSON
        cursor.execute("""
            SELECT timestamp, component, event_type, metadata
            FROM events
            ORDER BY timestamp DESC
            LIMIT 500
        """)

        logs = []
        for row in cursor.fetchall():
            try:
                metadata = row[3]
                if metadata:
                    try:
                        meta_dict = json.loads(metadata) if isinstance(metadata, str) else metadata
                        if meta_dict and str(meta_dict.get('project_id')) == str(self.project_id):
                            logs.append(dict(row))
                    except (json.JSONDecodeError, TypeError):
                        # Skip malformed JSON
                        continue
            except:
                continue

            if len(logs) >= limit:
                break

        return logs

    def _get_programs(self) -> List[Dict]:
        """Get project programs"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT
                name,
                path,
                language,
                lines_of_code,
                complexity_score,
                last_modified,
                'active' as status,
                COALESCE(lines_of_code * 100, 0) as size_bytes,
                language || ' program' as description
            FROM project_programs
            WHERE project_id = ?
            ORDER BY last_modified DESC
        """, (self.project_id,))
        return [dict(row) for row in cursor.fetchall()]

    def _get_quality_metrics(self) -> List[Dict]:
        """Get quality metrics - aggregated by time"""
        cursor = self.conn.cursor()
        # Get unique timestamps first
        cursor.execute("""
            SELECT DISTINCT calculated_at
            FROM project_quality_scores
            WHERE project_id = ?
            ORDER BY calculated_at DESC
            LIMIT 1
        """, (self.project_id,))

        timestamps = [row[0] for row in cursor.fetchall()]
        if not timestamps:
            return []

        # For each timestamp, get all metrics and build a dictionary
        results = []
        for ts in timestamps:
            cursor.execute("""
                SELECT metric, score, max_score
                FROM project_quality_scores
                WHERE project_id = ? AND calculated_at = ?
            """, (self.project_id, ts))

            metrics_dict = {'measured_at': ts}
            for row in cursor.fetchall():
                metric_name = row[0]
                score = row[1]
                # Map metric names to expected keys
                if metric_name == 'code_quality':
                    metrics_dict['code_quality'] = score
                elif metric_name == 'test_coverage':
                    metrics_dict['test_coverage'] = score
                elif metric_name == 'documentation':
                    metrics_dict['documentation_score'] = score
                elif metric_name == 'security':
                    metrics_dict['security_score'] = score
                elif metric_name == 'performance':
                    metrics_dict['performance_score'] = score
                elif metric_name == 'maintainability':
                    metrics_dict['maintainability_score'] = score

            results.append(metrics_dict)

        return results

    # ========================================================================
    # Markdown Export
    # ========================================================================

    def export_markdown(self, output_path: Optional[str] = None) -> str:
        """Export complete project documentation as Markdown"""
        if not output_path:
            output_path = f"/home/puzik/MAJ_PROJECT_{self.project_id}_EXPORT_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"

        md = []

        # Header
        md.append(f"# {self.project['name']}")
        md.append(f"**Project ID:** {self.project_id}")
        md.append(f"**Status:** {self.project['status']}")
        md.append(f"**Phase:** {self.project['phase']}")
        md.append(f"**Quality Score:** {self.project['quality_score']:.1f}%")
        md.append(f"**Created:** {self.project['created_at']}")
        md.append(f"**Updated:** {self.project['updated_at']}")
        md.append(f"**Export Date:** {datetime.now().isoformat()}")
        md.append("")
        md.append("---")
        md.append("")

        # Description
        md.append("## 📋 Popis projektu")
        md.append("")
        md.append(self.project['description'])
        md.append("")

        if self.project['customer']:
            md.append(f"**Zákazník:** {self.project['customer']}")
        if self.project['environment']:
            md.append(f"**Prostředí:** {self.project['environment']}")
        if self.project['github_repo']:
            md.append(f"**GitHub:** {self.project['github_repo']}")
        md.append(f"**Lokální cesta:** {self.project['local_path']}")
        md.append("")
        md.append("---")
        md.append("")

        # Specifications
        specs = self._get_specifications()
        if specs:
            md.append("## 📝 Zadání a specifikace")
            md.append("")
            for spec in specs:
                md.append(f"### {spec['title']}")
                md.append(f"*Vytvořeno: {spec['created_at']}*")
                md.append("")
                md.append(spec['content'])
                md.append("")
                if spec['requirements']:
                    md.append("**Požadavky:**")
                    reqs = json.loads(spec['requirements']) if isinstance(spec['requirements'], str) else spec['requirements']
                    for req in reqs:
                        md.append(f"- {req}")
                md.append("")
            md.append("---")
            md.append("")

        # Documentation
        docs = self._get_documentation()
        if docs:
            md.append("## 📚 Dokumentace")
            md.append("")
            for doc in docs:
                md.append(f"### {doc['title']}")
                md.append(f"*Typ: {doc['doc_type']} | Vytvořeno: {doc['created_at']}*")
                md.append("")
                md.append(doc['content'])
                md.append("")
            md.append("---")
            md.append("")

        # Programs/Modules
        programs = self._get_programs()
        if programs:
            md.append("## 💻 Programové moduly")
            md.append("")
            md.append(f"**Celkem modulů:** {len(programs)}")
            md.append("")
            md.append("| Název | Popis | Velikost | Řádky | Status |")
            md.append("|-------|-------|----------|-------|--------|")
            for prog in programs:
                md.append(f"| {prog['name']} | {prog['description'][:50]}... | {prog['size_bytes']:,} B | {prog['lines_of_code']} | {prog['status']} |")
            md.append("")
            md.append("---")
            md.append("")

        # Test Results
        tests = self._get_test_results()
        if tests:
            md.append("## 🧪 Výsledky testů")
            md.append("")
            total_tests = len(tests)
            passed = len([t for t in tests if t['status'] == 'passed'])
            failed = len([t for t in tests if t['status'] == 'failed'])

            md.append(f"**Celkem testů:** {total_tests}")
            md.append(f"**Úspěšných:** {passed} ({passed/total_tests*100:.1f}%)")
            md.append(f"**Neúspěšných:** {failed} ({failed/total_tests*100:.1f}%)")
            md.append("")

            md.append("### Poslední testy")
            md.append("")
            for test in tests[:10]:  # Last 10 tests
                status_icon = "✅" if test['status'] == 'passed' else "❌"
                md.append(f"{status_icon} **{test['test_name']}** ({test['test_type']})")
                md.append(f"   - Čas: {test['timestamp']}")
                if test.get('duration_seconds'):
                    md.append(f"   - Délka: {test['duration_seconds']:.2f}s")
                if test.get('error_message'):
                    md.append(f"   - Chyba: {test['error_message']}")
                md.append("")
            md.append("---")
            md.append("")

        # Quality Metrics
        metrics = self._get_quality_metrics()
        if metrics:
            md.append("## 📊 Metriky kvality")
            md.append("")
            latest = metrics[0] if metrics else None
            if latest:
                md.append(f"**Poslední měření:** {latest['measured_at']}")
                md.append(f"- **Kvalita kódu:** {latest.get('code_quality', 0):.1f}%")
                md.append(f"- **Pokrytí testy:** {latest.get('test_coverage', 0):.1f}%")
                md.append(f"- **Dokumentace:** {latest.get('documentation_score', 0):.1f}%")
                md.append(f"- **Bezpečnost:** {latest.get('security_score', 0):.1f}%")
                md.append(f"- **Výkon:** {latest.get('performance_score', 0):.1f}%")
                md.append(f"- **Udržovatelnost:** {latest.get('maintainability_score', 0):.1f}%")
                md.append("")
            md.append("---")
            md.append("")

        # Logs
        logs = self._get_logs(limit=50)
        if logs:
            md.append("## 📋 Protokoly (poslední události)")
            md.append("")
            for log in logs:
                md.append(f"- **{log['timestamp']}** [{log['component']}] {log['event_type']}")
                if log['metadata']:
                    try:
                        meta = json.loads(log['metadata']) if isinstance(log['metadata'], str) else log['metadata']
                        if meta:
                            md.append(f"  ```json\n  {json.dumps(meta, indent=2, ensure_ascii=False)}\n  ```")
                    except:
                        pass
            md.append("")
            md.append("---")
            md.append("")

        # Handover section
        md.append("## 📦 Předání projektu")
        md.append("")
        md.append("### Kontrolní seznam")
        md.append("")
        md.append("- [ ] Všechny testy prošly")
        md.append("- [ ] Dokumentace kompletní")
        md.append("- [ ] Kód v GitHub repository")
        md.append("- [ ] Deployment dokumentace připravena")
        md.append("- [ ] Zákazník seznámen s funkcionalitou")
        md.append("- [ ] Přístupové údaje předány")
        md.append("- [ ] Monitoring nastaven")
        md.append("- [ ] Zálohovací strategie definována")
        md.append("")

        # Footer
        md.append("---")
        md.append("")
        md.append(f"*Vygenerováno MAJ-PROJEKT-MONITOR v {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*")

        # Write to file
        content = "\n".join(md)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)

        print(f"✅ Markdown export vytvořen: {output_path}")
        return output_path

    # ========================================================================
    # PDF Export
    # ========================================================================

    def export_pdf(self, output_path: Optional[str] = None) -> str:
        """Export complete project documentation as PDF"""
        if not REPORTLAB_AVAILABLE:
            print("❌ ReportLab není nainstalován. Použijte: pip3 install reportlab")
            return None

        if not output_path:
            output_path = f"/home/puzik/MAJ_PROJECT_{self.project_id}_EXPORT_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"

        # Create PDF document
        doc = SimpleDocTemplate(output_path, pagesize=A4,
                                rightMargin=2*cm, leftMargin=2*cm,
                                topMargin=2*cm, bottomMargin=2*cm)

        # Container for PDF elements
        story = []

        # Styles
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#1a73e8'),
            spaceAfter=30,
            alignment=TA_CENTER
        )
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=16,
            textColor=colors.HexColor('#1a73e8'),
            spaceAfter=12,
            spaceBefore=12
        )

        # Title Page
        story.append(Paragraph(self.project['name'], title_style))
        story.append(Spacer(1, 0.5*cm))

        # Project Info Table
        project_data = [
            ['Project ID:', str(self.project_id)],
            ['Status:', self.project['status']],
            ['Fáze:', self.project['phase']],
            ['Kvalita:', f"{self.project['quality_score']:.1f}%"],
            ['Vytvořeno:', self.project['created_at']],
            ['Aktualizováno:', self.project['updated_at']],
        ]
        if self.project['customer']:
            project_data.append(['Zákazník:', self.project['customer']])
        if self.project['github_repo']:
            project_data.append(['GitHub:', self.project['github_repo']])

        t = Table(project_data, colWidths=[4*cm, 12*cm])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#e8f0fe')),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#1a73e8')),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        story.append(t)
        story.append(Spacer(1, 1*cm))

        # Description
        story.append(Paragraph("Popis projektu", heading_style))
        story.append(Paragraph(self.project['description'], styles['Normal']))
        story.append(Spacer(1, 0.5*cm))

        story.append(PageBreak())

        # Specifications
        specs = self._get_specifications()
        if specs:
            story.append(Paragraph("Zadání a specifikace", heading_style))
            for spec in specs:
                story.append(Paragraph(f"<b>{spec['title']}</b>", styles['Heading3']))
                story.append(Paragraph(f"<i>Vytvořeno: {spec['created_at']}</i>", styles['Normal']))
                story.append(Spacer(1, 0.2*cm))
                # Split content into paragraphs
                for para in spec['content'].split('\n\n'):
                    if para.strip():
                        story.append(Paragraph(para.replace('\n', '<br/>'), styles['Normal']))
                        story.append(Spacer(1, 0.3*cm))
            story.append(PageBreak())

        # Test Results
        tests = self._get_test_results()
        if tests:
            story.append(Paragraph("Výsledky testů", heading_style))
            total_tests = len(tests)
            passed = len([t for t in tests if t['status'] == 'passed'])
            failed = len([t for t in tests if t['status'] == 'failed'])

            summary_data = [
                ['Celkem testů', 'Úspěšných', 'Neúspěšných', 'Úspěšnost'],
                [str(total_tests), str(passed), str(failed), f"{passed/total_tests*100:.1f}%"]
            ]
            t = Table(summary_data, colWidths=[4*cm, 4*cm, 4*cm, 4*cm])
            t.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a73e8')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('GRID', (0, 0), (-1, -1), 1, colors.grey),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ]))
            story.append(t)
            story.append(Spacer(1, 0.5*cm))

            # Recent tests
            story.append(Paragraph("Poslední testy:", styles['Heading3']))
            for test in tests[:10]:
                status_icon = "✓" if test['status'] == 'passed' else "✗"
                color = 'green' if test['status'] == 'passed' else 'red'
                story.append(Paragraph(
                    f"<font color='{color}'>{status_icon}</font> <b>{test['test_name']}</b> ({test['test_type']}) - {test['timestamp']}",
                    styles['Normal']
                ))
                if test.get('error_message'):
                    story.append(Paragraph(f"   Chyba: {test['error_message']}", styles['Normal']))
                story.append(Spacer(1, 0.2*cm))

            story.append(PageBreak())

        # Quality Metrics
        metrics = self._get_quality_metrics()
        if metrics:
            story.append(Paragraph("Metriky kvality", heading_style))
            latest = metrics[0]

            metrics_data = [
                ['Metrika', 'Hodnota'],
                ['Kvalita kódu', f"{latest.get('code_quality', 0):.1f}%"],
                ['Pokrytí testy', f"{latest.get('test_coverage', 0):.1f}%"],
                ['Dokumentace', f"{latest.get('documentation_score', 0):.1f}%"],
                ['Bezpečnost', f"{latest.get('security_score', 0):.1f}%"],
                ['Výkon', f"{latest.get('performance_score', 0):.1f}%"],
                ['Udržovatelnost', f"{latest.get('maintainability_score', 0):.1f}%"],
            ]
            t = Table(metrics_data, colWidths=[8*cm, 8*cm])
            t.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a73e8')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('GRID', (0, 0), (-1, -1), 1, colors.grey),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ]))
            story.append(t)
            story.append(PageBreak())

        # Handover Checklist
        story.append(Paragraph("Předání projektu - kontrolní seznam", heading_style))
        checklist = [
            "☐ Všechny testy prošly",
            "☐ Dokumentace kompletní",
            "☐ Kód v GitHub repository",
            "☐ Deployment dokumentace připravena",
            "☐ Zákazník seznámen s funkcionalitou",
            "☐ Přístupové údaje předány",
            "☐ Monitoring nastaven",
            "☐ Zálohovací strategie definována",
        ]
        for item in checklist:
            story.append(Paragraph(item, styles['Normal']))
            story.append(Spacer(1, 0.2*cm))

        # Footer
        story.append(Spacer(1, 1*cm))
        story.append(Paragraph(
            f"<i>Vygenerováno MAJ-PROJEKT-MONITOR dne {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</i>",
            styles['Normal']
        ))

        # Build PDF
        doc.build(story)

        print(f"✅ PDF export vytvořen: {output_path}")
        return output_path

    # ========================================================================
    # Printer Functions
    # ========================================================================

    def print_document(self, format: str = 'pdf', printer: Optional[str] = None) -> bool:
        """Print project documentation directly to printer"""
        # First export to file
        if format == 'pdf':
            doc_path = self.export_pdf()
        else:
            doc_path = self.export_markdown()

        if not doc_path:
            return False

        # Get available printers
        try:
            result = subprocess.run(['lpstat', '-p'], capture_output=True, text=True)
            if result.returncode != 0:
                print("❌ Nelze získat seznam tiskáren. Je CUPS nainstalován?")
                return False

            printers = []
            for line in result.stdout.split('\n'):
                if line.startswith('printer'):
                    printer_name = line.split()[1]
                    printers.append(printer_name)

            if not printers:
                print("❌ Žádné tiskárny nenalezeny")
                return False

            print(f"📋 Dostupné tiskárny: {', '.join(printers)}")

            # Use specified printer or default
            if not printer:
                printer = printers[0]
                print(f"ℹ️  Použita výchozí tiskárna: {printer}")

            # Print the document
            cmd = ['lpr', '-P', printer, doc_path]
            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.returncode == 0:
                print(f"✅ Dokument odeslán na tiskárnu: {printer}")
                print(f"📄 Soubor: {doc_path}")
                return True
            else:
                print(f"❌ Chyba při tisku: {result.stderr}")
                return False

        except Exception as e:
            print(f"❌ Chyba při tisku: {e}")
            return False

    def __del__(self):
        """Cleanup"""
        if hasattr(self, 'conn'):
            self.conn.close()


# ============================================================================
# CLI Interface
# ============================================================================

def main():
    """CLI interface"""
    if len(sys.argv) < 3:
        print("""
MAJ-PROJEKT-MONITOR - Export a tisk

Použití:
    python3 maj-projekt-monitor-export.py <project_id> <akce> [parametry]

Akce:
    markdown [cesta]    - Export do Markdown
    pdf [cesta]         - Export do PDF
    print pdf          - Tisk PDF na výchozí tiskárnu
    print pdf <name>   - Tisk PDF na konkrétní tiskárnu
    print markdown     - Tisk Markdown (konvertuje na PDF)

Příklady:
    python3 maj-projekt-monitor-export.py 1 markdown
    python3 maj-projekt-monitor-export.py 1 pdf /tmp/projekt.pdf
    python3 maj-projekt-monitor-export.py 1 print pdf
    python3 maj-projekt-monitor-export.py 1 print pdf HP_LaserJet
""")
        sys.exit(1)

    project_id = int(sys.argv[1])
    action = sys.argv[2]

    try:
        exporter = ProjectExporter(project_id)

        if action == 'markdown':
            output_path = sys.argv[3] if len(sys.argv) > 3 else None
            exporter.export_markdown(output_path)

        elif action == 'pdf':
            output_path = sys.argv[3] if len(sys.argv) > 3 else None
            exporter.export_pdf(output_path)

        elif action == 'print':
            format = sys.argv[3] if len(sys.argv) > 3 else 'pdf'
            printer = sys.argv[4] if len(sys.argv) > 4 else None
            exporter.print_document(format, printer)

        else:
            print(f"❌ Neznámá akce: {action}")
            sys.exit(1)

    except Exception as e:
        print(f"❌ Chyba: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
