#!/bin/bash
# =============================================================================
# Media Analysis Database Monitoring Script
# =============================================================================
# Collects and reports database metrics for monitoring.
#
# Usage:
#   ./docker/monitor-media-db.sh              # Standard metrics output
#   ./docker/monitor-media-db.sh --json       # JSON format
#   ./docker/monitor-media-db.sh --prometheus # Prometheus exposition format
#   ./docker/monitor-media-db.sh --watch      # Continuous monitoring (5s interval)
#
# Metrics collected:
#   - Table sizes and row counts
#   - Index usage statistics
#   - Active connections
#   - Long-running queries
#   - Database statistics
#   - Cache hit ratio
# =============================================================================

set -e

# Configuration
COMPOSE_FILE="${COMPOSE_FILE:-docker/docker-compose.yml}"
SERVICE_NAME="media-pg-1"
DB_NAME="media_analysis"
DB_USER="media_analysis_user"

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Arguments
OUTPUT_FORMAT="text"
WATCH_MODE=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --json) OUTPUT_FORMAT="json"; shift ;;
        --prometheus) OUTPUT_FORMAT="prometheus"; shift ;;
        --watch) WATCH_MODE=true; shift ;;
        --help)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --json        Output as JSON"
            echo "  --prometheus  Output in Prometheus format"
            echo "  --watch       Continuous monitoring (5s interval)"
            echo "  --help        Show this help"
            exit 0
            ;;
        *) echo "Unknown: $1"; exit 1 ;;
    esac
done

# Execute SQL
run_sql() {
    local query="$1"
    cd "$PROJECT_ROOT"
    docker compose -f "$COMPOSE_FILE" exec -T "$SERVICE_NAME" \
        psql -U "$DB_USER" -d "$DB_NAME" -tAc "$query" 2>/dev/null
}

# Collect metrics
collect_metrics() {
    local timestamp
    timestamp=$(date -Iseconds)

    # Database size
    local db_size_bytes
    db_size_bytes=$(run_sql "SELECT pg_database_size('$DB_NAME')")

    # Table statistics
    local table_stats
    table_stats=$(run_sql "
        SELECT json_agg(row_to_json(t))
        FROM (
            SELECT
                schemaname,
                relname as table_name,
                n_live_tup as live_rows,
                n_dead_tup as dead_rows,
                n_tup_ins as inserts,
                n_tup_upd as updates,
                n_tup_del as deletes,
                last_vacuum,
                last_autovacuum,
                pg_total_relation_size(relid) as total_size_bytes
            FROM pg_stat_user_tables
            WHERE schemaname = 'public'
            ORDER BY n_live_tup DESC
        ) t
    ")

    # Index statistics
    local index_stats
    index_stats=$(run_sql "
        SELECT json_agg(row_to_json(t))
        FROM (
            SELECT
                schemaname,
                relname as table_name,
                indexrelname as index_name,
                idx_scan as scans,
                idx_tup_read as tuples_read,
                idx_tup_fetch as tuples_fetched,
                pg_relation_size(indexrelid) as size_bytes
            FROM pg_stat_user_indexes
            WHERE schemaname = 'public'
            ORDER BY idx_scan DESC
        ) t
    ")

    # Connection statistics
    local connections_active
    connections_active=$(run_sql "SELECT count(*) FROM pg_stat_activity WHERE datname='$DB_NAME' AND state='active'")

    local connections_idle
    connections_idle=$(run_sql "SELECT count(*) FROM pg_stat_activity WHERE datname='$DB_NAME' AND state='idle'")

    local connections_total
    connections_total=$(run_sql "SELECT count(*) FROM pg_stat_activity WHERE datname='$DB_NAME'")

    local max_connections
    max_connections=$(run_sql "SHOW max_connections")

    # Cache hit ratio
    local cache_hit_ratio
    cache_hit_ratio=$(run_sql "
        SELECT ROUND(
            100.0 * sum(heap_blks_hit) / nullif(sum(heap_blks_hit) + sum(heap_blks_read), 0),
            2
        ) FROM pg_statio_user_tables
    ")

    # Long running queries
    local long_queries
    long_queries=$(run_sql "
        SELECT count(*)
        FROM pg_stat_activity
        WHERE state = 'active'
        AND query_start < NOW() - INTERVAL '1 minute'
        AND datname = '$DB_NAME'
    ")

    # Transaction statistics
    local commits
    commits=$(run_sql "SELECT xact_commit FROM pg_stat_database WHERE datname='$DB_NAME'")

    local rollbacks
    rollbacks=$(run_sql "SELECT xact_rollback FROM pg_stat_database WHERE datname='$DB_NAME'")

    # Output based on format
    case $OUTPUT_FORMAT in
        json)
            cat <<EOF
{
  "timestamp": "$timestamp",
  "database": "$DB_NAME",
  "metrics": {
    "database_size_bytes": ${db_size_bytes:-0},
    "connections": {
      "active": ${connections_active:-0},
      "idle": ${connections_idle:-0},
      "total": ${connections_total:-0},
      "max": ${max_connections:-100}
    },
    "cache_hit_ratio": ${cache_hit_ratio:-0},
    "long_running_queries": ${long_queries:-0},
    "transactions": {
      "commits": ${commits:-0},
      "rollbacks": ${rollbacks:-0}
    },
    "tables": ${table_stats:-[]},
    "indexes": ${index_stats:-[]}
  }
}
EOF
            ;;

        prometheus)
            cat <<EOF
# HELP media_db_size_bytes Database size in bytes
# TYPE media_db_size_bytes gauge
media_db_size_bytes{database="$DB_NAME"} ${db_size_bytes:-0}

# HELP media_db_connections Number of database connections
# TYPE media_db_connections gauge
media_db_connections{database="$DB_NAME",state="active"} ${connections_active:-0}
media_db_connections{database="$DB_NAME",state="idle"} ${connections_idle:-0}
media_db_connections{database="$DB_NAME",state="total"} ${connections_total:-0}

# HELP media_db_connections_max Maximum allowed connections
# TYPE media_db_connections_max gauge
media_db_connections_max{database="$DB_NAME"} ${max_connections:-100}

# HELP media_db_cache_hit_ratio Cache hit ratio percentage
# TYPE media_db_cache_hit_ratio gauge
media_db_cache_hit_ratio{database="$DB_NAME"} ${cache_hit_ratio:-0}

# HELP media_db_long_queries Number of queries running > 1 minute
# TYPE media_db_long_queries gauge
media_db_long_queries{database="$DB_NAME"} ${long_queries:-0}

# HELP media_db_transactions_total Total transaction counts
# TYPE media_db_transactions_total counter
media_db_transactions_total{database="$DB_NAME",type="commit"} ${commits:-0}
media_db_transactions_total{database="$DB_NAME",type="rollback"} ${rollbacks:-0}
EOF
            ;;

        text)
            echo "======================================"
            echo " Media Analysis DB Metrics"
            echo " $timestamp"
            echo "======================================"
            echo ""
            echo "DATABASE SIZE"
            echo "  Total: $(numfmt --to=iec-i --suffix=B ${db_size_bytes:-0} 2>/dev/null || echo "${db_size_bytes:-0} bytes")"
            echo ""
            echo "CONNECTIONS"
            echo "  Active: ${connections_active:-0}"
            echo "  Idle: ${connections_idle:-0}"
            echo "  Total: ${connections_total:-0}/${max_connections:-100}"
            echo ""
            echo "PERFORMANCE"
            echo "  Cache Hit Ratio: ${cache_hit_ratio:-0}%"
            echo "  Long Queries: ${long_queries:-0}"
            echo ""
            echo "TRANSACTIONS"
            echo "  Commits: ${commits:-0}"
            echo "  Rollbacks: ${rollbacks:-0}"
            echo ""
            echo "TABLE SIZES"
            run_sql "
                SELECT
                    relname || ': ' ||
                    n_live_tup || ' rows, ' ||
                    pg_size_pretty(pg_total_relation_size(relid))
                FROM pg_stat_user_tables
                WHERE schemaname = 'public'
                ORDER BY pg_total_relation_size(relid) DESC
            " | while read line; do
                echo "  $line"
            done
            echo ""
            echo "TOP 5 INDEXES BY USAGE"
            run_sql "
                SELECT
                    indexrelname || ' (' || relname || '): ' ||
                    idx_scan || ' scans'
                FROM pg_stat_user_indexes
                WHERE schemaname = 'public'
                ORDER BY idx_scan DESC
                LIMIT 5
            " | while read line; do
                echo "  $line"
            done
            echo ""
            ;;
    esac
}

# Main
main() {
    if $WATCH_MODE; then
        echo "Monitoring $DB_NAME (press Ctrl+C to stop)"
        echo ""
        while true; do
            clear
            collect_metrics
            sleep 5
        done
    else
        collect_metrics
    fi
}

main
