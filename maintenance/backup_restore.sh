#!/usr/bin/env bash

################################################################################
# PRODUCTION BACKUP & RECOVERY SCRIPT
# Automated database backup, verification, and disaster recovery
################################################################################

set -euo pipefail

# ============================================================
# CONFIGURATION
# ============================================================

ENVIRONMENT="${ENVIRONMENT:-production}"
DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-5433}"
DB_NAME="${DB_NAME:-unilever_warehouse}"
DB_USER="${DB_USER:-postgres}"
BACKUP_PATH="${BACKUP_PATH:-./backups}"
RETENTION_DAYS="${RETENTION_DAYS:-30}"
LOG_FILE="${BACKUP_PATH}/backup_$(date +%Y%m%d_%H%M%S).log"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="${BACKUP_PATH}/unilever_warehouse_${TIMESTAMP}.sql"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# ============================================================
# LOGGING
# ============================================================

mkdir -p "$BACKUP_PATH"

log() {
    local message="$1"
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $message" | tee -a "$LOG_FILE"
}

error() {
    local message="$1"
    echo -e "${RED}[ERROR]${NC} $message" | tee -a "$LOG_FILE"
    exit 1
}

warning() {
    local message="$1"
    echo -e "${YELLOW}[WARNING]${NC} $message" | tee -a "$LOG_FILE"
}

# ============================================================
# BACKUP FUNCTIONS
# ============================================================

check_connectivity() {
    log "Checking database connectivity..."
    if ! PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c "SELECT 1" > /dev/null 2>&1; then
        error "Cannot connect to database at $DB_HOST:$DB_PORT"
    fi
    log "Database connectivity OK"
}

create_backup() {
    log "Creating backup of $DB_NAME..."
    
    if [ ! -w "$BACKUP_PATH" ]; then
        error "Backup directory $BACKUP_PATH is not writable"
    fi
    
    # Create backup with verbose output
    if PGPASSWORD="$DB_PASSWORD" pg_dump \
        -h "$DB_HOST" \
        -p "$DB_PORT" \
        -U "$DB_USER" \
        -d "$DB_NAME" \
        --verbose \
        --format=plain \
        --file="$BACKUP_FILE" 2>&1 | tee -a "$LOG_FILE"; then
        
        log "Backup created successfully: $BACKUP_FILE"
        log "Backup size: $(du -h "$BACKUP_FILE" | cut -f1)"
    else
        error "Backup creation failed"
    fi
}

verify_backup() {
    log "Verifying backup integrity..."
    
    if [ ! -f "$BACKUP_FILE" ]; then
        error "Backup file not found: $BACKUP_FILE"
    fi
    
    # Check file size
    local size=$(stat -f%z "$BACKUP_FILE" 2>/dev/null || stat -c%s "$BACKUP_FILE")
    if [ "$size" -lt 1000 ]; then
        error "Backup file is suspiciously small: $size bytes"
    fi
    
    # Check for backup markers
    if grep -q "PostgreSQL database dump" "$BACKUP_FILE"; then
        log "✅ Backup format verified"
    else
        error "Backup file format invalid"
    fi
    
    # Test restore to temporary database
    log "Testing backup restoration..."
    local temp_db="unilever_warehouse_restore_test_${TIMESTAMP}"
    
    PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -tc "CREATE DATABASE $temp_db" || error "Failed to create test database"
    
    if PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$temp_db" -f "$BACKUP_FILE" > /dev/null 2>&1; then
        log "✅ Backup restoration test successful"
        PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -tc "DROP DATABASE $temp_db"
    else
        PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -tc "DROP DATABASE $temp_db" || true
        error "Backup restoration test failed"
    fi
}

cleanup_old_backups() {
    log "Cleaning up backups older than $RETENTION_DAYS days..."
    
    find "$BACKUP_PATH" -name "unilever_warehouse_*.sql" -type f -mtime "+$RETENTION_DAYS" -delete
    
    local backup_count=$(find "$BACKUP_PATH" -name "unilever_warehouse_*.sql" -type f | wc -l)
    log "Active backups: $backup_count"
}

# ============================================================
# RESTORE FUNCTIONS
# ============================================================

restore_from_backup() {
    local backup_file="$1"
    
    if [ ! -f "$backup_file" ]; then
        error "Backup file not found: $backup_file"
    fi
    
    warning "RESTORE: This will overwrite the current database!"
    warning "Database: $DB_NAME at $DB_HOST:$DB_PORT"
    read -p "Type 'YES' to confirm: " confirmation
    
    if [ "$confirmation" != "YES" ]; then
        log "Restore cancelled"
        return
    fi
    
    log "Starting restore from $backup_file..."
    
    # Create backup of current database before restore
    local pre_restore_backup="${BACKUP_PATH}/unilever_warehouse_pre_restore_${TIMESTAMP}.sql"
    log "Creating pre-restore backup: $pre_restore_backup"
    PGPASSWORD="$DB_PASSWORD" pg_dump -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" > "$pre_restore_backup" || warning "Pre-restore backup failed"
    
    # Drop and recreate database
    log "Dropping existing database..."
    PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -tc "DROP DATABASE IF EXISTS $DB_NAME"
    
    log "Creating empty database..."
    PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -tc "CREATE DATABASE $DB_NAME"
    
    # Restore backup
    log "Restoring from backup..."
    if PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -f "$backup_file" 2>&1 | tee -a "$LOG_FILE"; then
        log "✅ Restore completed successfully"
    else
        error "Restore failed - pre-restore backup saved as $pre_restore_backup"
    fi
}

list_backups() {
    log "Available backups:"
    ls -lh "${BACKUP_PATH}"/unilever_warehouse_*.sql 2>/dev/null || log "No backups found"
}

# ============================================================
# VALIDATION
# ============================================================

validate_backup_integrity() {
    log "Validating all backups..."
    
    local invalid_count=0
    for backup in "${BACKUP_PATH}"/unilever_warehouse_*.sql; do
        if [ -f "$backup" ]; then
            if grep -q "PostgreSQL database dump" "$backup"; then
                log "✅ Valid: $(basename "$backup")"
            else
                warning "⚠️  Invalid: $(basename "$backup")"
                ((invalid_count++))
            fi
        fi
    done
    
    if [ $invalid_count -eq 0 ]; then
        log "All backups are valid"
    else
        warning "Found $invalid_count invalid backups"
    fi
}

# ============================================================
# MAIN
# ============================================================

main() {
    local action="${1:-backup}"
    
    log "=========================================="
    log "Database Backup & Recovery Tool"
    log "Environment: $ENVIRONMENT"
    log "Action: $action"
    log "=========================================="
    
    case "$action" in
        backup)
            check_connectivity
            create_backup
            verify_backup
            cleanup_old_backups
            log "✅ Backup completed successfully"
            ;;
        restore)
            if [ -z "${2:-}" ]; then
                error "Backup file required: $0 restore <backup_file>"
            fi
            check_connectivity
            restore_from_backup "$2"
            ;;
        list)
            list_backups
            ;;
        validate)
            validate_backup_integrity
            ;;
        *)
            echo "Usage: $0 {backup|restore|list|validate} [backup_file]"
            echo ""
            echo "Examples:"
            echo "  $0 backup                           # Create new backup"
            echo "  $0 list                             # List all backups"
            echo "  $0 validate                         # Validate all backups"
            echo "  $0 restore backups/warehouse_*.sql  # Restore from backup"
            exit 1
            ;;
    esac
}

main "$@"
