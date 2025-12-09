#!/bin/bash
################################################################################
# ALMQUIST CODE SEARCH - Control Script
# Easy management of code search and indexing system
################################################################################

PYTHON="/home/puzik/miniconda3/bin/python3"
RAG_SCRIPT="/home/puzik/almquist_code_rag_system.py"
WEB_SCRIPT="/home/puzik/almquist_code_search_web.py"
PID_FILE="/home/puzik/almquist_code_search_web.pid"

case "$1" in
    init)
        echo "🚀 Initializing Code RAG database..."
        $PYTHON $RAG_SCRIPT init
        ;;

    index)
        echo "📚 Starting full code indexing..."
        echo "⏳ This will take several minutes..."
        echo ""
        $PYTHON $RAG_SCRIPT index
        ;;

    index-bg)
        echo "📚 Starting code indexing in background..."
        nohup $PYTHON $RAG_SCRIPT index > /home/puzik/almquist_code_indexing.log 2>&1 &
        echo $! > /home/puzik/almquist_code_indexing.pid
        echo "✅ Indexing started in background"
        echo "📋 Log: tail -f /home/puzik/almquist_code_indexing.log"
        ;;

    rebuild)
        echo "🔨 Rebuilding FAISS index from database..."
        $PYTHON $RAG_SCRIPT rebuild
        ;;

    search)
        if [ -z "$2" ]; then
            echo "❌ Usage: $0 search 'your query'"
            exit 1
        fi
        echo "🔍 Searching for: '$2'"
        echo ""
        $PYTHON $RAG_SCRIPT search --query "$2" --limit 5
        ;;

    start)
        if [ -f "$PID_FILE" ] && kill -0 $(cat $PID_FILE) 2>/dev/null; then
            echo "⚠️  Web interface already running (PID: $(cat $PID_FILE))"
            exit 1
        fi

        echo "🚀 Starting Code Search Web Interface..."
        nohup $PYTHON $WEB_SCRIPT > /home/puzik/almquist_code_search_web.log 2>&1 &
        echo $! > $PID_FILE
        sleep 2

        if kill -0 $(cat $PID_FILE) 2>/dev/null; then
            echo "✅ Web interface started successfully"
            echo "📍 Access at: http://localhost:5555"
            echo "📋 Log: tail -f /home/puzik/almquist_code_search_web.log"
        else
            echo "❌ Failed to start web interface"
            rm -f $PID_FILE
            exit 1
        fi
        ;;

    stop)
        if [ ! -f "$PID_FILE" ]; then
            echo "⚠️  Web interface not running"
            exit 1
        fi

        PID=$(cat $PID_FILE)
        echo "🛑 Stopping web interface (PID: $PID)..."
        kill $PID 2>/dev/null
        rm -f $PID_FILE
        echo "✅ Web interface stopped"
        ;;

    restart)
        $0 stop
        sleep 2
        $0 start
        ;;

    status)
        echo "╔════════════════════════════════════════════════════════════════╗"
        echo "║         ALMQUIST CODE SEARCH - System Status                  ║"
        echo "╚════════════════════════════════════════════════════════════════╝"
        echo ""

        # Web interface status
        if [ -f "$PID_FILE" ] && kill -0 $(cat $PID_FILE) 2>/dev/null; then
            echo "🟢 Web Interface: RUNNING (PID: $(cat $PID_FILE))"
            echo "   URL: http://localhost:5555"
        else
            echo "🔴 Web Interface: STOPPED"
        fi
        echo ""

        # Indexing status
        if [ -f "/home/puzik/almquist_code_indexing.pid" ] && kill -0 $(cat /home/puzik/almquist_code_indexing.pid) 2>/dev/null; then
            echo "🟡 Indexing: IN PROGRESS (PID: $(cat /home/puzik/almquist_code_indexing.pid))"
        else
            echo "⚪ Indexing: IDLE"
        fi
        echo ""

        # Database statistics
        echo "📊 Database Statistics:"
        psql postgresql://almquist_user:almquist_secure_password_2025@localhost:5432/almquist_db -t -c "
            SELECT
                '   Files: ' || COUNT(*) as files
            FROM code_files WHERE is_active = true;
        " 2>/dev/null | grep -v "^$"

        psql postgresql://almquist_user:almquist_secure_password_2025@localhost:5432/almquist_db -t -c "
            SELECT
                '   Chunks: ' || COUNT(*) as chunks
            FROM code_chunks;
        " 2>/dev/null | grep -v "^$"

        psql postgresql://almquist_user:almquist_secure_password_2025@localhost:5432/almquist_db -t -c "
            SELECT
                '   Repositories: ' || COUNT(DISTINCT repository_name) as repos
            FROM code_files WHERE repository_name IS NOT NULL;
        " 2>/dev/null | grep -v "^$"

        psql postgresql://almquist_user:almquist_secure_password_2025@localhost:5432/almquist_db -t -c "
            SELECT
                '   Total searches: ' || COUNT(*) as searches
            FROM code_search_history;
        " 2>/dev/null | grep -v "^$"

        echo ""

        # FAISS index status
        if [ -f "/home/puzik/almquist_code_rag/code_faiss_index.bin" ]; then
            SIZE=$(du -h /home/puzik/almquist_code_rag/code_faiss_index.bin | cut -f1)
            echo "💾 FAISS Index: $SIZE"
        else
            echo "💾 FAISS Index: NOT BUILT (run 'rebuild')"
        fi
        echo ""
        ;;

    logs)
        if [ "$2" == "web" ]; then
            tail -f /home/puzik/almquist_code_search_web.log
        elif [ "$2" == "index" ]; then
            tail -f /home/puzik/almquist_code_indexing.log
        else
            echo "Usage: $0 logs [web|index]"
            exit 1
        fi
        ;;

    stats)
        echo "📊 Detailed Statistics:"
        echo ""
        psql postgresql://almquist_user:almquist_secure_password_2025@localhost:5432/almquist_db -c "
            SELECT
                language,
                COUNT(*) as files,
                SUM(line_count) as total_lines,
                ROUND(AVG(line_count)::numeric, 0) as avg_lines,
                pg_size_pretty(SUM(file_size_bytes)::bigint) as total_size
            FROM code_files
            WHERE is_active = true
            GROUP BY language
            ORDER BY COUNT(*) DESC;
        " 2>/dev/null
        ;;

    *)
        echo "╔════════════════════════════════════════════════════════════════╗"
        echo "║         ALMQUIST CODE SEARCH - Control Script                 ║"
        echo "╚════════════════════════════════════════════════════════════════╝"
        echo ""
        echo "Usage: $0 {command}"
        echo ""
        echo "Commands:"
        echo "  init          - Initialize database schema"
        echo "  index         - Index all code (foreground)"
        echo "  index-bg      - Index all code (background)"
        echo "  rebuild       - Rebuild FAISS index from database"
        echo "  search 'query'- Search code from CLI"
        echo ""
        echo "  start         - Start web interface"
        echo "  stop          - Stop web interface"
        echo "  restart       - Restart web interface"
        echo "  status        - Show system status"
        echo ""
        echo "  logs web      - Show web interface logs"
        echo "  logs index    - Show indexing logs"
        echo "  stats         - Show detailed statistics"
        echo ""
        echo "Examples:"
        echo "  $0 init"
        echo "  $0 index-bg"
        echo "  $0 start"
        echo "  $0 search 'PDF processing function'"
        echo "  $0 status"
        echo ""
        exit 1
        ;;
esac
