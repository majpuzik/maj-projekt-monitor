#!/bin/bash
#
# MAJ-PROJEKT-MONITOR CONTROL SCRIPT
# Complete lifecycle management system control
#
# Usage:
#   ./maj-projekt-monitor-control.sh [command]
#
# Commands:
#   start       - Start all services (bot + web dashboard)
#   stop        - Stop all services
#   restart     - Restart all services
#   status      - Check status of all services
#   bot         - Start only the bot
#   web         - Start only the web dashboard
#   analyze     - Run analysis on all projects
#   create      - Create new project
#   logs        - Show logs
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BOT_SCRIPT="$SCRIPT_DIR/maj-projekt-monitor-bot.py"
WEB_SCRIPT="$SCRIPT_DIR/maj-projekt-monitor-web.py"
MONITOR_SCRIPT="$SCRIPT_DIR/maj-projekt-monitor.py"

BOT_PID_FILE="/tmp/maj-projekt-monitor-bot.pid"
WEB_PID_FILE="/tmp/maj-projekt-monitor-web.pid"
LOG_DIR="$HOME/logs"
BOT_LOG="$LOG_DIR/maj-projekt-monitor-bot.log"
WEB_LOG="$LOG_DIR/maj-projekt-monitor-web.log"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Create logs directory
mkdir -p "$LOG_DIR"

# ============================================================================
# Helper Functions
# ============================================================================

print_header() {
    echo -e "${BLUE}==========================================================================${NC}"
    echo -e "${BLUE}  🤖 MAJ-PROJEKT-MONITOR - Comprehensive Project Lifecycle Manager${NC}"
    echo -e "${BLUE}==========================================================================${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_info() {
    echo -e "${YELLOW}ℹ $1${NC}"
}

PYTHON="/home/puzik/miniconda3/bin/python3"
PIP="/home/puzik/miniconda3/bin/pip3"

check_python() {
    if ! command -v $PYTHON &> /dev/null; then
        print_error "Python 3 is not installed at $PYTHON"
        exit 1
    fi
}

check_dependencies() {
    print_info "Checking dependencies..."

    # Check Python packages
    $PYTHON -c "import flask" 2>/dev/null || {
        print_error "Flask not installed. Installing..."
        $PIP install flask flask-socketio schedule psutil
    }

    print_success "Dependencies OK"
}

is_bot_running() {
    if [ -f "$BOT_PID_FILE" ]; then
        PID=$(cat "$BOT_PID_FILE")
        if ps -p "$PID" > /dev/null 2>&1; then
            return 0
        fi
    fi
    return 1
}

is_web_running() {
    if [ -f "$WEB_PID_FILE" ]; then
        PID=$(cat "$WEB_PID_FILE")
        if ps -p "$PID" > /dev/null 2>&1; then
            return 0
        fi
    fi
    return 1
}

# ============================================================================
# Commands
# ============================================================================

start_bot() {
    if is_bot_running; then
        print_info "Bot is already running (PID: $(cat $BOT_PID_FILE))"
        return
    fi

    print_info "Starting MAJ-PROJEKT-MONITOR Bot..."

    nohup $PYTHON "$BOT_SCRIPT" > "$BOT_LOG" 2>&1 &
    BOT_PID=$!
    echo $BOT_PID > "$BOT_PID_FILE"

    sleep 2

    if is_bot_running; then
        print_success "Bot started (PID: $BOT_PID)"
        print_info "Logs: $BOT_LOG"
    else
        print_error "Failed to start bot"
        rm -f "$BOT_PID_FILE"
        exit 1
    fi
}

start_web() {
    if is_web_running; then
        print_info "Web dashboard is already running (PID: $(cat $WEB_PID_FILE))"
        return
    fi

    print_info "Starting MAJ-PROJEKT-MONITOR Web Dashboard..."

    nohup $PYTHON "$WEB_SCRIPT" > "$WEB_LOG" 2>&1 &
    WEB_PID=$!
    echo $WEB_PID > "$WEB_PID_FILE"

    sleep 3

    if is_web_running; then
        print_success "Web dashboard started (PID: $WEB_PID)"
        print_success "Dashboard URL: http://$(hostname -I | awk '{print $1}'):5050"
        print_info "Logs: $WEB_LOG"
    else
        print_error "Failed to start web dashboard"
        rm -f "$WEB_PID_FILE"
        exit 1
    fi
}

stop_bot() {
    if ! is_bot_running; then
        print_info "Bot is not running"
        return
    fi

    PID=$(cat "$BOT_PID_FILE")
    print_info "Stopping bot (PID: $PID)..."

    kill $PID 2>/dev/null || true
    sleep 2

    if ps -p "$PID" > /dev/null 2>&1; then
        print_info "Force killing bot..."
        kill -9 $PID 2>/dev/null || true
    fi

    rm -f "$BOT_PID_FILE"
    print_success "Bot stopped"
}

stop_web() {
    if ! is_web_running; then
        print_info "Web dashboard is not running"
        return
    fi

    PID=$(cat "$WEB_PID_FILE")
    print_info "Stopping web dashboard (PID: $PID)..."

    kill $PID 2>/dev/null || true
    sleep 2

    if ps -p "$PID" > /dev/null 2>&1; then
        print_info "Force killing web dashboard..."
        kill -9 $PID 2>/dev/null || true
    fi

    rm -f "$WEB_PID_FILE"
    print_success "Web dashboard stopped"
}

show_status() {
    print_header

    echo ""
    echo "Bot Status:"
    if is_bot_running; then
        PID=$(cat "$BOT_PID_FILE")
        print_success "Running (PID: $PID)"
    else
        print_error "Not running"
    fi

    echo ""
    echo "Web Dashboard Status:"
    if is_web_running; then
        PID=$(cat "$WEB_PID_FILE")
        print_success "Running (PID: $PID)"
        print_info "URL: http://$(hostname -I | awk '{print $1}'):5050"
    else
        print_error "Not running"
    fi

    echo ""
    echo "Database:"
    if [ -f "/home/puzik/almquist-central-log/almquist.db" ]; then
        DB_SIZE=$(du -h "/home/puzik/almquist-central-log/almquist.db" | cut -f1)
        print_success "Connected (Size: $DB_SIZE)"
    else
        print_error "Not found"
    fi

    echo ""
    echo "Recent Logs:"
    echo "---"
    if [ -f "$BOT_LOG" ]; then
        tail -n 5 "$BOT_LOG"
    fi
}

run_analysis() {
    print_info "Running analysis on all projects..."
    $PYTHON "$BOT_SCRIPT" --once
    print_success "Analysis complete"
}

create_project() {
    echo ""
    read -p "Project name: " PROJECT_NAME
    read -p "Project path: " PROJECT_PATH
    read -p "Description: " DESCRIPTION
    read -p "GitHub repo (optional): " GITHUB
    read -p "Customer (optional): " CUSTOMER
    read -p "Environment (optional): " ENVIRONMENT

    print_info "Creating project: $PROJECT_NAME"

    $PYTHON "$MONITOR_SCRIPT" create "$PROJECT_NAME" "$PROJECT_PATH" \
        --description "$DESCRIPTION" \
        ${GITHUB:+--github "$GITHUB"} \
        ${CUSTOMER:+--customer "$CUSTOMER"} \
        ${ENVIRONMENT:+--environment "$ENVIRONMENT"}

    print_success "Project created"

    # Scan files
    PROJECT_ID=$($PYTHON -c "
import sys
sys.path.insert(0, '$SCRIPT_DIR')
from maj_projekt_monitor import ProjectDatabase
db = ProjectDatabase()
project = db.get_project_by_name('$PROJECT_NAME')
print(project.id if project else 0)
")

    if [ "$PROJECT_ID" != "0" ]; then
        print_info "Scanning project files..."
        $PYTHON "$MONITOR_SCRIPT" scan "$PROJECT_ID"
        print_success "Project setup complete (ID: $PROJECT_ID)"
    fi
}

show_logs() {
    echo ""
    echo "=== Bot Logs ==="
    tail -f "$BOT_LOG"
}

# ============================================================================
# Main
# ============================================================================

print_header
check_python

COMMAND=${1:-help}

case $COMMAND in
    start)
        check_dependencies
        start_bot
        start_web
        echo ""
        show_status
        ;;

    stop)
        stop_bot
        stop_web
        ;;

    restart)
        stop_bot
        stop_web
        sleep 2
        start_bot
        start_web
        ;;

    status)
        show_status
        ;;

    bot)
        check_dependencies
        start_bot
        ;;

    web)
        check_dependencies
        start_web
        ;;

    stop-bot)
        stop_bot
        ;;

    stop-web)
        stop_web
        ;;

    analyze)
        run_analysis
        ;;

    create)
        create_project
        ;;

    logs)
        show_logs
        ;;

    help|*)
        echo "Usage: $0 [command]"
        echo ""
        echo "Commands:"
        echo "  start       - Start all services (bot + web)"
        echo "  stop        - Stop all services"
        echo "  restart     - Restart all services"
        echo "  status      - Show status"
        echo "  bot         - Start only bot"
        echo "  web         - Start only web dashboard"
        echo "  stop-bot    - Stop bot"
        echo "  stop-web    - Stop web dashboard"
        echo "  analyze     - Run analysis now"
        echo "  create      - Create new project"
        echo "  logs        - Show logs (follow mode)"
        echo "  help        - Show this help"
        ;;
esac
