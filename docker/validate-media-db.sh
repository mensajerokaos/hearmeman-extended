#!/bin/bash
# =============================================================================
# Validate Media Analysis Database Configuration
# =============================================================================
# Validates database configuration without starting or modifying anything.
#
# Usage:
#   ./docker/validate-media-db.sh
#   ./docker/validate-media-db.sh --verbose
#   ./docker/validate-media-db.sh --json
#
# Exit codes:
#   0 - All validations passed
#   1 - One or more validations failed
# =============================================================================

set -e

# Configuration
COMPOSE_FILE="${COMPOSE_FILE:-docker/docker-compose.yml}"
SERVICE_NAME="media-pg-1"
DB_NAME="media_analysis"
DB_USER="media_analysis_user"
DB_PORT="${MEDIA_DB_PORT:-5433}"

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Parse arguments
VERBOSE=false
JSON_OUTPUT=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --verbose)
            VERBOSE=true
            shift
            ;;
        --json)
            JSON_OUTPUT=true
            shift
            ;;
        --help)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --verbose   Show detailed output"
            echo "  --json      Output results as JSON"
            echo "  --help      Show this help"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Results array for JSON output
declare -A RESULTS

check() {
    local name="$1"
    local status="$2"
    local message="$3"

    RESULTS["$name"]="$status"

    if $JSON_OUTPUT; then
        return
    fi

    if [ "$status" = "pass" ]; then
        echo -e "${GREEN}[PASS]${NC} $name"
    elif [ "$status" = "warn" ]; then
        echo -e "${YELLOW}[WARN]${NC} $name: $message"
    else
        echo -e "${RED}[FAIL]${NC} $name: $message"
    fi

    if $VERBOSE && [ -n "$message" ]; then
        echo "       $message"
    fi
}

# Validate docker-compose.yml exists
validate_compose_exists() {
    if [ -f "$PROJECT_ROOT/$COMPOSE_FILE" ]; then
        check "compose_file_exists" "pass" ""
    else
        check "compose_file_exists" "fail" "File not found: $COMPOSE_FILE"
    fi
}

# Validate docker-compose.yml syntax
validate_compose_syntax() {
    cd "$PROJECT_ROOT"
    if docker compose -f "$COMPOSE_FILE" config > /dev/null 2>&1; then
        check "compose_syntax" "pass" ""
    else
        check "compose_syntax" "fail" "Invalid YAML syntax"
    fi
}

# Validate media-pg-1 service is defined
validate_service_defined() {
    cd "$PROJECT_ROOT"
    if docker compose -f "$COMPOSE_FILE" config --services 2>/dev/null | grep -q "$SERVICE_NAME"; then
        check "service_defined" "pass" ""
    else
        check "service_defined" "fail" "Service '$SERVICE_NAME' not defined in compose file"
    fi
}

# Validate environment variables
validate_environment() {
    # Check MEDIA_DATABASE_URL
    if [ -n "$MEDIA_DATABASE_URL" ]; then
        check "env_database_url" "pass" ""
    else
        check "env_database_url" "warn" "MEDIA_DATABASE_URL not set (will use default)"
    fi

    # Check required Docker environment
    if command -v docker &> /dev/null; then
        check "docker_installed" "pass" ""
    else
        check "docker_installed" "fail" "Docker not installed"
    fi

    # Check Docker is running
    if docker info > /dev/null 2>&1; then
        check "docker_running" "pass" ""
    else
        check "docker_running" "fail" "Docker daemon not running"
    fi
}

# Validate init SQL exists
validate_init_sql() {
    INIT_SQL="$PROJECT_ROOT/docker/init-media-db.sql"
    if [ -f "$INIT_SQL" ]; then
        check "init_sql_exists" "pass" ""

        # Validate SQL syntax (basic check)
        if grep -qE "CREATE (DATABASE|USER|EXTENSION)" "$INIT_SQL"; then
            check "init_sql_valid" "pass" ""
        else
            check "init_sql_valid" "warn" "Init SQL may be incomplete"
        fi
    else
        check "init_sql_exists" "warn" "init-media-db.sql not found"
    fi
}

# Validate alembic configuration
validate_alembic() {
    ALEMBIC_INI="$PROJECT_ROOT/alembic.ini"
    if [ -f "$ALEMBIC_INI" ]; then
        check "alembic_config" "pass" ""
    else
        check "alembic_config" "warn" "alembic.ini not found"
    fi

    # Check migrations directory
    MIGRATIONS_DIR="$PROJECT_ROOT/migrations/versions"
    if [ -d "$MIGRATIONS_DIR" ]; then
        MIGRATION_COUNT=$(find "$MIGRATIONS_DIR" -name "*.py" -type f | wc -l)
        if [ "$MIGRATION_COUNT" -gt 0 ]; then
            check "migrations_exist" "pass" "$MIGRATION_COUNT migration(s) found"
        else
            check "migrations_exist" "warn" "No migrations found"
        fi
    else
        check "migrations_exist" "fail" "Migrations directory not found"
    fi
}

# Validate port availability
validate_port() {
    if command -v lsof &> /dev/null; then
        if lsof -i ":$DB_PORT" > /dev/null 2>&1; then
            # Port is in use - check if it's our service
            if docker compose -f "$PROJECT_ROOT/$COMPOSE_FILE" ps 2>/dev/null | grep -q "$SERVICE_NAME.*running"; then
                check "port_available" "pass" "Port $DB_PORT in use by $SERVICE_NAME"
            else
                check "port_available" "warn" "Port $DB_PORT in use by another process"
            fi
        else
            check "port_available" "pass" "Port $DB_PORT is available"
        fi
    elif command -v ss &> /dev/null; then
        if ss -tuln | grep -q ":$DB_PORT "; then
            check "port_available" "warn" "Port $DB_PORT may be in use"
        else
            check "port_available" "pass" "Port $DB_PORT is available"
        fi
    else
        check "port_available" "warn" "Cannot check port availability"
    fi
}

# Test database connection (if running)
validate_connection() {
    cd "$PROJECT_ROOT"
    if docker compose -f "$COMPOSE_FILE" ps --status running 2>/dev/null | grep -q "$SERVICE_NAME"; then
        if docker compose -f "$COMPOSE_FILE" exec -T "$SERVICE_NAME" \
            pg_isready -U "$DB_USER" -d "$DB_NAME" > /dev/null 2>&1; then
            check "db_connection" "pass" "Database is accessible"
        else
            check "db_connection" "fail" "Database is running but not accessible"
        fi
    else
        check "db_connection" "warn" "Database service is not running"
    fi
}

# Output JSON results
output_json() {
    echo "{"
    local first=true
    for key in "${!RESULTS[@]}"; do
        if $first; then
            first=false
        else
            echo ","
        fi
        echo -n "  \"$key\": \"${RESULTS[$key]}\""
    done
    echo ""
    echo "}"
}

# Calculate overall result
get_overall_result() {
    for key in "${!RESULTS[@]}"; do
        if [ "${RESULTS[$key]}" = "fail" ]; then
            return 1
        fi
    done
    return 0
}

# Main
main() {
    if ! $JSON_OUTPUT; then
        echo ""
        echo "======================================"
        echo " Media Analysis DB Configuration Check"
        echo "======================================"
        echo ""
    fi

    validate_compose_exists
    validate_compose_syntax
    validate_service_defined
    validate_environment
    validate_init_sql
    validate_alembic
    validate_port
    validate_connection

    if $JSON_OUTPUT; then
        output_json
    else
        echo ""
        echo "======================================"

        if get_overall_result; then
            echo -e "${GREEN}VALIDATION PASSED${NC}"
            echo "======================================"
            exit 0
        else
            echo -e "${RED}VALIDATION FAILED${NC}"
            echo "======================================"
            exit 1
        fi
    fi
}

main
