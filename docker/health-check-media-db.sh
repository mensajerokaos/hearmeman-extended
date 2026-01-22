#!/bin/bash
# =============================================================================
# Media Analysis Database Health Check
# =============================================================================
# Comprehensive health check for the media analysis PostgreSQL database.
#
# Usage:
#   ./docker/health-check-media-db.sh           # Standard health check
#   ./docker/health-check-media-db.sh --verbose # Detailed output
#   ./docker/health-check-media-db.sh --json    # JSON output
#   ./docker/health-check-media-db.sh --quick   # Quick check only
#
# Exit codes:
#   0 - Healthy
#   1 - Unhealthy
#   2 - Degraded (warnings but functional)
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

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Arguments
VERBOSE=false
JSON_OUTPUT=false
QUICK_CHECK=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --verbose) VERBOSE=true; shift ;;
        --json) JSON_OUTPUT=true; shift ;;
        --quick) QUICK_CHECK=true; shift ;;
        --help)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --verbose   Show detailed output"
            echo "  --json      Output results as JSON"
            echo "  --quick     Quick check (service running only)"
            echo "  --help      Show this help"
            exit 0
            ;;
        *) echo "Unknown: $1"; exit 1 ;;
    esac
done

# Results storage
declare -A CHECKS
WARNINGS=0
FAILURES=0

check() {
    local name="$1"
    local status="$2"
    local value="$3"

    CHECKS["${name}_status"]="$status"
    CHECKS["${name}_value"]="$value"

    if [ "$status" = "fail" ]; then
        ((FAILURES++))
    elif [ "$status" = "warn" ]; then
        ((WARNINGS++))
    fi

    if $JSON_OUTPUT; then
        return
    fi

    case $status in
        pass) echo -e "${GREEN}[OK]${NC} $name: $value" ;;
        warn) echo -e "${YELLOW}[WARN]${NC} $name: $value" ;;
        fail) echo -e "${RED}[FAIL]${NC} $name: $value" ;;
    esac
}

# Execute SQL and return result
run_sql() {
    local query="$1"
    cd "$PROJECT_ROOT"
    docker compose -f "$COMPOSE_FILE" exec -T "$SERVICE_NAME" \
        psql -U "$DB_USER" -d "$DB_NAME" -tAc "$query" 2>/dev/null
}

# Check 1: Service is running
check_service_running() {
    cd "$PROJECT_ROOT"
    if docker compose -f "$COMPOSE_FILE" ps --status running 2>/dev/null | grep -q "$SERVICE_NAME"; then
        check "service_running" "pass" "$SERVICE_NAME is running"
    else
        check "service_running" "fail" "$SERVICE_NAME is not running"
        return 1
    fi
}

# Check 2: Database is accessible
check_db_accessible() {
    cd "$PROJECT_ROOT"
    if docker compose -f "$COMPOSE_FILE" exec -T "$SERVICE_NAME" \
        pg_isready -U "$DB_USER" -d "$DB_NAME" > /dev/null 2>&1; then
        check "db_accessible" "pass" "Database accepting connections"
    else
        check "db_accessible" "fail" "Database not accepting connections"
        return 1
    fi
}

# Check 3: All expected tables exist
check_tables_exist() {
    local expected=5  # analysis_job, media_file, analysis_result, transcription, processing_log
    local actual
    actual=$(run_sql "SELECT COUNT(*) FROM pg_tables WHERE schemaname='public' AND tablename IN ('analysis_job','media_file','analysis_result','transcription','processing_log')")

    if [ "$actual" = "$expected" ]; then
        check "tables_exist" "pass" "$actual/$expected tables present"
    elif [ "$actual" -gt 0 ]; then
        check "tables_exist" "warn" "$actual/$expected tables present"
    else
        check "tables_exist" "fail" "No tables found"
    fi
}

# Check 4: Table row counts
check_row_counts() {
    local total=0
    local counts=""

    for table in analysis_job media_file analysis_result transcription processing_log; do
        local count
        count=$(run_sql "SELECT COUNT(*) FROM $table" 2>/dev/null || echo "0")
        counts="$counts $table:$count"
        total=$((total + count))
    done

    if [ "$total" -ge 0 ]; then
        check "row_counts" "pass" "Total rows: $total ($counts)"
    else
        check "row_counts" "fail" "Could not count rows"
    fi
}

# Check 5: Connection pool status
check_connections() {
    local active
    local max
    active=$(run_sql "SELECT count(*) FROM pg_stat_activity WHERE datname='$DB_NAME'")
    max=$(run_sql "SHOW max_connections")

    if [ -n "$active" ] && [ -n "$max" ]; then
        local usage=$((active * 100 / max))
        if [ "$usage" -lt 80 ]; then
            check "connections" "pass" "$active/$max connections ($usage%)"
        elif [ "$usage" -lt 95 ]; then
            check "connections" "warn" "$active/$max connections ($usage%) - high usage"
        else
            check "connections" "fail" "$active/$max connections ($usage%) - critical"
        fi
    else
        check "connections" "warn" "Could not check connection status"
    fi
}

# Check 6: Disk usage
check_disk_usage() {
    local db_size
    db_size=$(run_sql "SELECT pg_size_pretty(pg_database_size('$DB_NAME'))")

    if [ -n "$db_size" ]; then
        check "disk_usage" "pass" "Database size: $db_size"
    else
        check "disk_usage" "warn" "Could not determine disk usage"
    fi

    # Check container disk space
    cd "$PROJECT_ROOT"
    local disk_usage
    disk_usage=$(docker compose -f "$COMPOSE_FILE" exec -T "$SERVICE_NAME" \
        df -h /var/lib/postgresql/data 2>/dev/null | tail -1 | awk '{print $5}' || echo "unknown")

    if [ "$disk_usage" != "unknown" ]; then
        local pct="${disk_usage%\%}"
        if [ "$pct" -lt 80 ]; then
            check "container_disk" "pass" "Container disk: $disk_usage used"
        elif [ "$pct" -lt 95 ]; then
            check "container_disk" "warn" "Container disk: $disk_usage used"
        else
            check "container_disk" "fail" "Container disk: $disk_usage used - critical"
        fi
    fi
}

# Check 7: Long-running queries
check_long_queries() {
    local long_queries
    long_queries=$(run_sql "SELECT COUNT(*) FROM pg_stat_activity WHERE state='active' AND query_start < NOW() - INTERVAL '5 minutes'")

    if [ "$long_queries" = "0" ]; then
        check "long_queries" "pass" "No queries running > 5 minutes"
    elif [ "$long_queries" -lt 3 ]; then
        check "long_queries" "warn" "$long_queries queries running > 5 minutes"
    else
        check "long_queries" "fail" "$long_queries queries running > 5 minutes"
    fi
}

# Check 8: Index usage
check_index_usage() {
    local unused
    unused=$(run_sql "SELECT COUNT(*) FROM pg_stat_user_indexes WHERE idx_scan = 0")

    if [ "$unused" = "0" ]; then
        check "index_usage" "pass" "All indexes have been used"
    elif [ "$unused" -lt 5 ]; then
        check "index_usage" "warn" "$unused unused indexes"
    else
        check "index_usage" "warn" "$unused unused indexes - consider review"
    fi
}

# Output JSON
output_json() {
    echo "{"
    echo "  \"timestamp\": \"$(date -Iseconds)\","
    echo "  \"service\": \"$SERVICE_NAME\","
    echo "  \"database\": \"$DB_NAME\","
    echo "  \"status\": \"$(get_overall_status)\","
    echo "  \"checks\": {"

    local first=true
    for key in "${!CHECKS[@]}"; do
        if [[ "$key" == *_status ]]; then
            local base="${key%_status}"
            local status="${CHECKS[${base}_status]}"
            local value="${CHECKS[${base}_value]}"

            if $first; then first=false; else echo ","; fi
            echo -n "    \"$base\": {\"status\": \"$status\", \"value\": \"$value\"}"
        fi
    done

    echo ""
    echo "  },"
    echo "  \"warnings\": $WARNINGS,"
    echo "  \"failures\": $FAILURES"
    echo "}"
}

get_overall_status() {
    if [ "$FAILURES" -gt 0 ]; then
        echo "unhealthy"
    elif [ "$WARNINGS" -gt 0 ]; then
        echo "degraded"
    else
        echo "healthy"
    fi
}

get_exit_code() {
    if [ "$FAILURES" -gt 0 ]; then
        return 1
    elif [ "$WARNINGS" -gt 0 ]; then
        return 2
    else
        return 0
    fi
}

# Main
main() {
    if ! $JSON_OUTPUT; then
        echo ""
        echo "======================================"
        echo " Media Analysis DB Health Check"
        echo " $(date)"
        echo "======================================"
        echo ""
    fi

    # Quick check exits early
    if $QUICK_CHECK; then
        check_service_running || exit 1
        check_db_accessible || exit 1

        if $JSON_OUTPUT; then
            output_json
        else
            echo ""
            echo "Quick check: PASSED"
        fi
        exit 0
    fi

    # Full health check
    check_service_running
    if [ "$FAILURES" -eq 0 ]; then
        check_db_accessible

        if [ "$FAILURES" -eq 0 ]; then
            check_tables_exist
            check_row_counts
            check_connections
            check_disk_usage
            check_long_queries
            check_index_usage
        fi
    fi

    if $JSON_OUTPUT; then
        output_json
    else
        echo ""
        echo "======================================"
        local status
        status=$(get_overall_status)
        case $status in
            healthy)
                echo -e "${GREEN}STATUS: HEALTHY${NC}"
                ;;
            degraded)
                echo -e "${YELLOW}STATUS: DEGRADED ($WARNINGS warnings)${NC}"
                ;;
            unhealthy)
                echo -e "${RED}STATUS: UNHEALTHY ($FAILURES failures)${NC}"
                ;;
        esac
        echo "======================================"
    fi

    get_exit_code
}

main
