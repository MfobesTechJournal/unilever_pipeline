#!/bin/bash
#
# PHASE 7: Database Admin
# Automated Backup & Recovery Procedures
#

set -euo pipefail

BACKUP_DIR="/backups"
DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-5432}"
DB_NAME="${DB_NAME:-unilever_warehouse}"
DB_USER="${DB_USER:-postgres}"
LOG_DIR="$BACKUP_DIR/logs"
mkdir -p "$BACKUP_DIR" "$LOG_DIR"

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
LOG_FILE="$LOG_DIR/backup_${TIMESTAMP}.log"

log_msg() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

backup_database() {
    log_msg "Starting full database backup..."
    
    local backup_file="$BACKUP_DIR/full_backup_${TIMESTAMP}.sql.gz"
    
    if PGPASSWORD="$DB_PASS" pg_dump -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" | gzip > "$backup_file"; then
        local size=$(du -h "$backup_file" | cut -f1)
        log_msg "✓ Full backup completed: $backup_file ($size)"
        
        # Copy to S3 for offsite backup
        if command -v aws &> /dev/null; then
            aws s3 cp "$backup_file" "s3://unilever-backups/$(basename "$backup_file")"
            log_msg "✓ Backup copied to S3"
        fi
        return 0
    else
        log_msg "ERROR: Backup failed"
        return 1
    fi
}

backup_schema_only() {
    log_msg "Starting schema-only backup..."
    
    local backup_file="$BACKUP_DIR/schema_${TIMESTAMP}.sql.gz"
    
    if PGPASSWORD="$DB_PASS" pg_dump -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -s | gzip > "$backup_file"; then
        log_msg "✓ Schema backup completed: $backup_file"
        return 0
    else
        log_msg "ERROR: Schema backup failed"
        return 1
    fi
}

restore_database() {
    local backup_file=$1
    
    log_msg "Restoring database from $backup_file..."
    
    if [[ ! -f "$backup_file" ]]; then
        log_msg "ERROR: Backup file not found: $backup_file"
        return 1
    fi
    
    # Create restore target database
    PGPASSWORD="$DB_PASS" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -c "CREATE DATABASE ${DB_NAME}_restore;"
    
    # Restore from backup
    if gunzip -c "$backup_file" | PGPASSWORD="$DB_PASS" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "${DB_NAME}_restore"; then
        log_msg "✓ Restore completed to ${DB_NAME}_restore database"
        log_msg "Run: ALTER DATABASE ${DB_NAME}_restore RENAME TO $DB_NAME;" to activate
        return 0
    else
        log_msg "ERROR: Restore failed"
        return 1
    fi
}

point_in_time_recovery() {
    local target_time=$1
    
    log_msg "Setting up Point-in-Time Recovery to: $target_time"
    
    # Requires WAL archiving to be enabled
    PGPASSWORD="$DB_PASS" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" << EOF
CREATE RESTORE POINT before_incident_${TIMESTAMP};
SELECT * FROM pg_get_wal_resource_manager();
EOF
    
    log_msg "✓ PITR checkpoint created"
}

cleanup_old_backups() {
    local days_old=${1:-7}
    
    log_msg "Cleaning backups older than $days_old days..."
    
    find "$BACKUP_DIR" -name "*.gz" -mtime +$days_old -delete
    log_msg "✓ Old backups cleaned"
}

# Main menu
case "${1:-}" in
    full)
        backup_database
        ;;
    schema)
        backup_schema_only
        ;;
    restore)
        if [[ $# -lt 2 ]]; then
            log_msg "Usage: $0 restore <backup_file>"
            exit 1
        fi
        restore_database "$2"
        ;;
    pitr)
        if [[ $# -lt 2 ]]; then
            log_msg "Usage: $0 pitr <target_time>"
            exit 1
        fi
        point_in_time_recovery "$2"
        ;;
    cleanup)
        cleanup_old_backups "${2:-7}"
        ;;
    *)
        log_msg "Usage: $0 {full|schema|restore|pitr|cleanup}"
        exit 1
        ;;
esac
