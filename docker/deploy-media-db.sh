#!/bin/bash
# =============================================================================
# Deploy Media Analysis Database
# =============================================================================
# This script deploys the media analysis PostgreSQL database to Docker.
#
# Usage:
#   ./docker/deploy-media-db.sh              # Deploy/update database
#   ./docker/deploy-media-db.sh --fresh      # Fresh install (destroys data!)
#   ./docker/deploy-media-db.sh --dry-run    # Preview changes only
#   ./docker/deploy-media-db.sh --help       # Show this help
#
# Environment:
#   MEDIA_DB_PASSWORD: Database password (default: mediapass123)
#   COMPOSE_FILE: Docker compose file (default: docker/docker-compose.yml)
# =============================================================================

set -e

# Configuration
COMPOSE_FILE="${COMPOSE_FILE:-docker/docker-compose.yml}"
SERVICE_NAME="media-pg-1"
DB_NAME="media_analysis"
DB_USER="media_analysis_user"
DB_PASSWORD="${MEDIA_DB_PASSWORD:-mediapass123}"
HEALTHCHECK_TIMEOUT=60

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Parse arguments
DRY_RUN=false
FRESH_INSTALL=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        --fresh)
            FRESH_INSTALL=true
            shift
            ;;
        --help)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --fresh     Fresh install (destroys existing data)"
            echo "  --dry-run   Preview changes without executing"
            echo "  --help      Show this help message"
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            exit 1
            ;;
    esac
done

log() {
    echo -e "${GREEN}[$(date '+%H:%M:%S')]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[$(date '+%H:%M:%S')] WARNING:${NC} $1"
}

error() {
    echo -e "${RED}[$(date '+%H:%M:%S')] ERROR:${NC} $1"
}

# Check prerequisites
check_prerequisites() {
    log "Checking prerequisites..."

    if ! command -v docker &> /dev/null; then
        error "docker not found. Please install Docker."
        exit 1
    fi

    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        error "docker-compose not found. Please install Docker Compose."
        exit 1
    fi

    if [ ! -f "$PROJECT_ROOT/$COMPOSE_FILE" ]; then
        error "Docker compose file not found: $PROJECT_ROOT/$COMPOSE_FILE"
        exit 1
    fi

    log "Prerequisites OK"
}

# Validate docker-compose file
validate_compose() {
    log "Validating docker-compose.yml..."

    cd "$PROJECT_ROOT"

    if docker compose -f "$COMPOSE_FILE" config > /dev/null 2>&1; then
        log "Docker compose file is valid"
    else
        error "Docker compose file validation failed"
        docker compose -f "$COMPOSE_FILE" config
        exit 1
    fi
}

# Check if service is running
is_service_running() {
    docker compose -f "$PROJECT_ROOT/$COMPOSE_FILE" ps --status running 2>/dev/null | grep -q "$SERVICE_NAME"
}

# Stop existing service
stop_service() {
    log "Stopping existing $SERVICE_NAME service..."

    cd "$PROJECT_ROOT"

    if is_service_running; then
        if $DRY_RUN; then
            log "[DRY RUN] Would stop $SERVICE_NAME"
        else
            docker compose -f "$COMPOSE_FILE" stop "$SERVICE_NAME" || true
            log "Service stopped"
        fi
    else
        log "Service is not running"
    fi
}

# Remove volumes (fresh install only)
remove_volumes() {
    if $FRESH_INSTALL; then
        warn "FRESH INSTALL: This will destroy all existing data!"
        echo -n "Are you sure? (yes/no): "

        if $DRY_RUN; then
            echo "[DRY RUN] Would prompt for confirmation"
            log "[DRY RUN] Would remove volumes"
            return
        fi

        read -r confirmation
        if [ "$confirmation" != "yes" ]; then
            error "Aborted by user"
            exit 1
        fi

        cd "$PROJECT_ROOT"
        docker compose -f "$COMPOSE_FILE" down -v --remove-orphans 2>/dev/null || true
        log "Volumes removed"
    fi
}

# Start service
start_service() {
    log "Starting $SERVICE_NAME service..."

    cd "$PROJECT_ROOT"

    if $DRY_RUN; then
        log "[DRY RUN] Would start $SERVICE_NAME"
        return
    fi

    docker compose -f "$COMPOSE_FILE" up -d "$SERVICE_NAME"
    log "Service started"
}

# Wait for healthcheck
wait_for_health() {
    log "Waiting for healthcheck (max ${HEALTHCHECK_TIMEOUT}s)..."

    if $DRY_RUN; then
        log "[DRY RUN] Would wait for healthcheck"
        return
    fi

    cd "$PROJECT_ROOT"

    for i in $(seq 1 $HEALTHCHECK_TIMEOUT); do
        if docker compose -f "$COMPOSE_FILE" exec -T "$SERVICE_NAME" pg_isready -U "$DB_USER" -d "$DB_NAME" > /dev/null 2>&1; then
            log "Database is ready (took ${i}s)"
            return 0
        fi
        echo -n "."
        sleep 1
    done

    echo ""
    error "Database failed to become healthy within ${HEALTHCHECK_TIMEOUT}s"
    exit 1
}

# Run initialization SQL
run_init_sql() {
    log "Running database initialization..."

    if $DRY_RUN; then
        log "[DRY RUN] Would run init-media-db.sql"
        return
    fi

    INIT_SQL="$PROJECT_ROOT/docker/init-media-db.sql"

    if [ -f "$INIT_SQL" ]; then
        cd "$PROJECT_ROOT"
        docker compose -f "$COMPOSE_FILE" exec -T "$SERVICE_NAME" \
            psql -U postgres -d "$DB_NAME" -f /docker-entrypoint-initdb.d/init-media-db.sql 2>/dev/null || {
                # If init script doesn't exist in container, copy and run
                docker cp "$INIT_SQL" "${SERVICE_NAME}:/tmp/init.sql"
                docker compose -f "$COMPOSE_FILE" exec -T "$SERVICE_NAME" \
                    psql -U postgres -d "$DB_NAME" -f /tmp/init.sql
            }
        log "Initialization complete"
    else
        warn "No init-media-db.sql found, skipping initialization"
    fi
}

# Verify database
verify_database() {
    log "Verifying database..."

    if $DRY_RUN; then
        log "[DRY RUN] Would verify database"
        return
    fi

    cd "$PROJECT_ROOT"

    # Check database exists
    DB_EXISTS=$(docker compose -f "$COMPOSE_FILE" exec -T "$SERVICE_NAME" \
        psql -U postgres -tAc "SELECT 1 FROM pg_database WHERE datname='$DB_NAME'" 2>/dev/null)

    if [ "$DB_EXISTS" = "1" ]; then
        log "Database '$DB_NAME' exists"
    else
        error "Database '$DB_NAME' not found"
        exit 1
    fi

    # Check user can connect
    if docker compose -f "$COMPOSE_FILE" exec -T "$SERVICE_NAME" \
        psql -U "$DB_USER" -d "$DB_NAME" -c "SELECT 1" > /dev/null 2>&1; then
        log "User '$DB_USER' can connect"
    else
        error "User '$DB_USER' cannot connect to database"
        exit 1
    fi

    # Check extensions
    EXTENSIONS=$(docker compose -f "$COMPOSE_FILE" exec -T "$SERVICE_NAME" \
        psql -U "$DB_USER" -d "$DB_NAME" -tAc "SELECT extname FROM pg_extension WHERE extname IN ('uuid-ossp', 'pg_trgm')" 2>/dev/null)

    if echo "$EXTENSIONS" | grep -q "uuid-ossp"; then
        log "Extension uuid-ossp is installed"
    else
        warn "Extension uuid-ossp may not be installed"
    fi

    if echo "$EXTENSIONS" | grep -q "pg_trgm"; then
        log "Extension pg_trgm is installed"
    else
        warn "Extension pg_trgm may not be installed"
    fi

    log "Database verification complete"
}

# Main deployment flow
main() {
    echo ""
    echo "======================================"
    echo " Media Analysis Database Deployment"
    echo "======================================"
    echo ""

    if $DRY_RUN; then
        warn "DRY RUN MODE - No changes will be made"
        echo ""
    fi

    if $FRESH_INSTALL; then
        warn "FRESH INSTALL MODE - Existing data will be destroyed"
        echo ""
    fi

    check_prerequisites
    validate_compose
    stop_service
    remove_volumes
    start_service
    wait_for_health
    run_init_sql
    verify_database

    echo ""
    echo "======================================"
    if $DRY_RUN; then
        log "DRY RUN COMPLETE - No changes were made"
    else
        log "DEPLOYMENT COMPLETE"
        echo ""
        log "Database connection:"
        echo "  Host: localhost"
        echo "  Port: 5433"
        echo "  Database: $DB_NAME"
        echo "  User: $DB_USER"
        echo ""
        echo "Connection string:"
        echo "  postgresql://$DB_USER:****@localhost:5433/$DB_NAME"
    fi
    echo "======================================"
}

# Run main
main
