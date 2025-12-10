#!/bin/bash
################################################################################
# ALMQUIST CODE RAG - Browse CLI
# Browse indexed files from command line
################################################################################

DB_URL="postgresql://almquist_user:almquist_secure_password_2025@localhost:5432/almquist_db"

case "$1" in
    list)
        LANGUAGE="${2}"
        if [ -n "$LANGUAGE" ]; then
            echo "📁 Files with language: $LANGUAGE"
            psql "$DB_URL" -c "
                SELECT file_name,
                       SUBSTRING(file_path, 1, 60) as path,
                       line_count as lines,
                       indexed_at::date as indexed
                FROM code_files
                WHERE language = '$LANGUAGE' AND is_active = true
                ORDER BY indexed_at DESC
                LIMIT 50;
            "
        else
            echo "📁 All indexed files (last 50)"
            psql "$DB_URL" -c "
                SELECT file_name,
                       language,
                       line_count as lines,
                       indexed_at::date as indexed
                FROM code_files
                WHERE is_active = true
                ORDER BY indexed_at DESC
                LIMIT 50;
            "
        fi
        ;;

    docker)
        echo "🐳 Files from Docker containers"
        psql "$DB_URL" -c "
            SELECT file_name,
                   language,
                   SUBSTRING(file_path, 1, 70) as path
            FROM code_files
            WHERE file_path LIKE '%/docker/%' AND is_active = true
            ORDER BY file_path
            LIMIT 100;
        "
        ;;

    stats)
        echo "📊 Statistics by Language"
        psql "$DB_URL" -c "
            SELECT language,
                   COUNT(*) as files,
                   SUM(line_count) as total_lines,
                   ROUND(AVG(line_count)) as avg_lines
            FROM code_files
            WHERE is_active = true
            GROUP BY language
            ORDER BY COUNT(*) DESC;
        "
        ;;

    file)
        FILE_ID="$2"
        if [ -z "$FILE_ID" ]; then
            echo "Usage: $0 file <id>"
            exit 1
        fi
        echo "📄 File Detail (ID: $FILE_ID)"
        psql "$DB_URL" -c "
            SELECT file_name,
                   file_path,
                   language,
                   line_count,
                   file_size_bytes / 1024 as size_kb,
                   repository_name,
                   git_remote_url,
                   git_branch,
                   indexed_at,
                   last_modified,
                   array_length(functions, 1) as func_count,
                   array_length(classes, 1) as class_count
            FROM code_files
            WHERE id = $FILE_ID;
        "

        echo ""
        echo "Functions & Classes:"
        psql "$DB_URL" -t -c "
            SELECT 'Functions: ' || COALESCE(array_to_string(functions, ', '), 'none') as functions,
                   'Classes: ' || COALESCE(array_to_string(classes, ', '), 'none') as classes
            FROM code_files
            WHERE id = $FILE_ID;
        "
        ;;

    search-name)
        NAME="$2"
        if [ -z "$NAME" ]; then
            echo "Usage: $0 search-name <filename>"
            exit 1
        fi
        echo "🔍 Searching for files matching: $NAME"
        psql "$DB_URL" -c "
            SELECT id,
                   file_name,
                   language,
                   SUBSTRING(file_path, 1, 60) as path
            FROM code_files
            WHERE file_name ILIKE '%$NAME%' AND is_active = true
            ORDER BY file_name
            LIMIT 50;
        "
        ;;

    repos)
        echo "📦 Repositories"
        psql "$DB_URL" -c "
            SELECT repository_name,
                   COUNT(*) as files,
                   SUM(line_count) as total_lines
            FROM code_files
            WHERE is_active = true AND repository_name IS NOT NULL
            GROUP BY repository_name
            ORDER BY COUNT(*) DESC;
        "
        ;;

    history)
        echo "📜 Indexing History"
        psql "$DB_URL" -c "
            SELECT indexed_at::timestamp(0) as when,
                   location,
                   files_indexed as files,
                   chunks_created as chunks,
                   indexing_duration_seconds || 's' as duration,
                   notes
            FROM code_indexing_history
            ORDER BY indexed_at DESC
            LIMIT 20;
        "
        ;;

    *)
        echo "╔════════════════════════════════════════════════════════════════╗"
        echo "║      ALMQUIST CODE RAG - Browse CLI                           ║"
        echo "╚════════════════════════════════════════════════════════════════╝"
        echo ""
        echo "Usage: $0 {command} [options]"
        echo ""
        echo "Commands:"
        echo "  list [language]     - List files (optionally filter by language)"
        echo "  docker              - List files from Docker containers"
        echo "  stats               - Show statistics by language"
        echo "  file <id>           - Show file details"
        echo "  search-name <name>  - Search files by name"
        echo "  repos               - List repositories"
        echo "  history             - Show indexing history"
        echo ""
        echo "Examples:"
        echo "  $0 list python"
        echo "  $0 docker"
        echo "  $0 search-name server.js"
        echo "  $0 file 5000"
        echo "  $0 stats"
        echo ""
        exit 1
        ;;
esac
