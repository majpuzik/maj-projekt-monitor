# MAJ Project Management System

Complete project lifecycle management system with autonomous monitoring, quality tracking, and professional documentation export.

## 🚀 Key Components

### 1. MAJ-PROJEKT-MONITOR
**Complete project lifecycle management system**

- **maj-projekt-monitor.py** - Core monitoring system with 9 CDB tables
- **maj-projekt-monitor-bot.py** - Autonomous hourly analysis bot
- **maj-projekt-monitor-web.py** - Real-time Flask dashboard (port 5050)
- **maj-projekt-monitor-export.py** - PDF/Markdown/Print export system
- **maj-projekt-monitor-control.sh** - Service control script

**Features:**
- Complete lifecycle tracking (planning → production)
- Quality scoring (6 metrics)
- Automated analysis and recommendations
- Real-time WebSocket dashboard
- GitHub integration
- Professional document export

### 2. MAJ-ALMQUIST-LOCAL
**Legal RAG system for Czech law**

- Legal decisions crawler
- Laws and regulations database
- 151 Python modules
- Vector embeddings with Qdrant
- Self-learning capabilities

## 📊 Export System

Export complete project documentation in multiple formats:

- **📄 Markdown** - Complete docs, perfect for GitHub (~15MB)
- **📑 PDF** - Professional documents, print-ready (~5KB)
- **🖨️ Print** - Direct CUPS printer integration

**Exported content:**
- Project specifications
- Technical documentation
- Test results and statistics
- Quality metrics (6 categories)
- Event logs
- Handover checklist

## 🎯 Quick Start

### Install Dependencies

```bash
# For PDF export
pip3 install reportlab

# For web dashboard
pip3 install flask flask-socketio
```

### Start Dashboard

```bash
# Start web server
./maj-projekt-monitor-control.sh web

# Open in browser
firefox http://localhost:5050
```

### Export Documentation

```bash
# Export to Markdown
python3 maj-projekt-monitor-export.py 1 markdown

# Export to PDF
python3 maj-projekt-monitor-export.py 1 pdf

# Print directly
python3 maj-projekt-monitor-export.py 1 print pdf
```

## 📁 Project Structure

```
/home/puzik/
├── maj-projekt-monitor.py              # Main monitor (2,874 lines)
├── maj-projekt-monitor-bot.py          # Autonomous bot (1,156 lines)
├── maj-projekt-monitor-web.py          # Web dashboard (851 lines)
├── maj-projekt-monitor-export.py       # Export system (691 lines)
├── maj-projekt-monitor-control.sh      # Control script
├── MAJ_PROJEKT_MONITOR_README.md       # Main documentation
├── MAJ_PROJEKT_MONITOR_EXPORT_README.md # Export guide
├── MAJ_PROJEKT_MONITOR_DOKUMENTACE.html # Interactive docs
└── almquist-central-log/
    └── almquist.db                     # Central database (CDB)
```

## 🗄️ Database Schema

**9 CDB Tables:**
- `projects` - Project registry
- `project_programs` - Source code modules
- `project_tests` - Test results
- `project_todos` - Task tracking
- `project_quality_scores` - Quality metrics
- `project_analysis` - Hourly analysis results
- `project_deployments` - Deployment history
- `project_security_tests` - Security testing
- `project_git_commits` - Git integration

## 📈 Features

### Monitoring
- ✅ Real-time project status
- ✅ Quality scoring (0-100%)
- ✅ Automated hourly analysis
- ✅ Test result tracking
- ✅ GitHub commit integration

### Quality Metrics
- Code quality
- Test coverage
- Documentation completeness
- Security assessment
- Performance analysis
- Maintainability score

### Export & Reporting
- Professional PDF documents
- Markdown documentation
- Direct printer support
- Handover checklists
- Project summaries

### Web Dashboard
- Real-time updates (WebSocket)
- Interactive charts
- Color-coded status (🟢🟡🔴)
- One-click export buttons
- Project overview

## 🔧 Configuration

Edit `maj-projekt-monitor.py`:

```python
class Config:
    CDB_PATH = "/home/puzik/almquist-central-log/almquist.db"
    PROJECT_BASE_DIR = Path("/home/puzik")
    GITHUB_USER = "puzik"
```

## 📖 Documentation

- [Main Documentation](MAJ_PROJEKT_MONITOR_README.md)
- [Export Guide](MAJ_PROJEKT_MONITOR_EXPORT_README.md)
- [Interactive HTML Docs](MAJ_PROJEKT_MONITOR_DOKUMENTACE.html)

## 🧪 Testing

Tested on 2 projects:
- MAJ-PROJEKT-MONITOR (this system)
- MAJ-ALMQUIST-LOCAL (Legal RAG)

All export formats verified:
- ✅ Markdown export (~15MB with logs)
- ✅ PDF export (~5KB compressed)
- ✅ Web dashboard working
- ✅ Print integration tested

## 📊 Statistics

- **Total Lines of Code:** ~5,600
- **Components:** 4 Python scripts + 1 shell script
- **Documentation:** 4 files, 118KB
- **Database Tables:** 9 tables in CDB
- **Export Formats:** 3 (MD, PDF, Print)

## 🤝 Contributing

This is a personal project management system. Feel free to fork and adapt for your needs.

## 📝 License

Personal use - M.A.J. Puzik © 2025

## 🎯 Roadmap

Future enhancements:
- [ ] Export to HTML (interactive)
- [ ] Export to Word (.docx)
- [ ] Export graphs as PNG/SVG
- [ ] Batch export all projects
- [ ] Email automation
- [ ] Cron job for daily exports

## 🔗 Links

- Web Dashboard: http://192.168.10.200:5050
- Central DB: `/home/puzik/almquist-central-log/almquist.db`

---

**Generated with [Claude Code](https://claude.com/claude-code)**

Co-Authored-By: Claude <noreply@anthropic.com>
