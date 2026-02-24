#!/bin/bash

# ============================================================
# PHASE 3: SHELL SCRIPTING FOR DATA INGESTION
# Advanced Data Ingestion Script with Monitoring & Notifications
# ============================================================

# ======================
# CONFIGURATION
# ======================

RAW_DATA_DIR="raw_data"
STAGING_DIR="staging"
ARCHIVE_DIR="raw_data/archive"
LOG_DIR="logs"
ERROR_DIR="logs/errors"
BACKUP_DIR="backups"

# Email configuration
EMAIL_FROM="noreply@unilever.com"
EMAIL_TO="admin@unilever.com"
SMTP_SERVER="smtp.gmail.com"
SMTP_PORT="587"

# Database configuration
DB_HOST="localhost"
DB_PORT="5433"
DB_NAME="unilever_warehouse"
DB_USER="postgres"

# Timestamps
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
DATE_STR=$(date +%Y-%m-%d)
LOG_FILE="$LOG_DIR/ingestion_$TIMESTAMP.log"
ERROR_FILE="$ERROR_DIR/ingestion_$TIMESTAMP.error"

# Create directories
mkdir -p $RAW_DATA_DIR
mkdir -p $STAGING_DIR
mkdir -p $ARCHIVE_DIR
mkdir -p $LOG_DIR
mkdir -p $ERROR_DIR
mkdir -p $BACKUP_DIR

# ======================
# FUNCTIONS
# ======================

log_message() {
    local level=$1
    local message=$2
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] [$level] $message" | tee -a $LOG_FILE
}

log_error() {
    local message=$1
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] [ERROR] $message" | tee -a $LOG_FILE
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] [ERROR] $message" >> $ERROR_FILE
}

send_email() {
    local subject=$1
    local body=$2
    
    # Using sendmail or mail command
    if command -v sendmail &> /dev/null; then
        echo -e "Subject: $subject\nFrom: $EMAIL_FROM\nTo: $EMAIL_TO\n\n$body" | sendmail -t
    elif command -v mail &> /dev/null; then
        echo "$body" | mail -s "$subject" $EMAIL_TO
    else
        log_message "WARN" "Email utility not found. Install sendmail or mail."
    fi
}

send_slack() {
    local message=$1
    local webhook_url=${SLACK_WEBHOOK_URL:-""}
    
    if [ -n "$webhook_url" ]; then
        curl -s -X POST -H 'Content-type: application/json' \
            --data "{\"text\":\"$message\"}" \
            $webhook_url
    fi
}

validate_csv() {
    local file=$1
    local filename=$(basename $file)
    
    # Check file exists
    if [ ! -f "$file" ]; then
        log_error "File does not exist: $filename"
        return 1
    fi
    
    # Check file is not empty
    if [ ! -s "$file" ]; then
        log_error "File is empty: $filename"
        return 1
    fi
    
    # Check minimum file size (1KB)
    local size=$(stat -c%s "$file" 2>/dev/null || stat -f%z "$file" 2>/dev/null)
    if [ $size -lt 1024 ]; then
        log_error "File too small ($size bytes): $filename"
        return 1
    fi
    
    # Check CSV format (has headers)
    local header=$(head -n 1 "$file")
    if [ -z "$header" ]; then
        log_error "CSV has no header: $filename"
        return 1
    fi
    
    log_message "INFO" "Validated: $filename ($size bytes)"
    return 0
}

check_database_connection() {
    if command -v psql &> /dev/null; then
        if PGPASSWORD=123456 psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -c "SELECT 1" &> /dev/null; then
            return 0
        else
            log_error "Database connection failed"
            return 1
        fi
    else
        log_error "psql command not found"
        return 1
    fi
}

backup_staging() {
    local backup_file="$BACKUP_DIR/staging_$TIMESTAMP.tar.gz"
    tar -czf $backup_file $STAGING_DIR/* 2>/dev/null
    log_message "INFO" "Staging backed up to: $backup_file"
    
    # Keep only last 7 backups
    ls -t $BACKUP_DIR/staging_*.tar.gz | tail -n +8 | xargs -r rm
}

detect_new_folders() {
    local folders=()
    for dir in $RAW_DATA_DIR/*/; do
        if [ -d "$dir" ] && [ "$(basename $dir)" != "archive" ]; then
            folder_name=$(basename $dir)
            # Check if folder was already processed
            if [ ! -d "$ARCHIVE_DIR/${folder_name}_"* ] 2>/dev/null; then
                folders+=("$dir")
            fi
        fi
    done
    echo "${folders[@]}"
}

move_to_staging() {
    local source_dir=$1
    local success=true
    
    for file in $source_dir/*.csv; do
        if [ -f "$file" ]; then
            filename=$(basename $file)
            
            if validate_csv "$file"; then
                cp "$file" "$STAGING_DIR/$filename"
                log_message "INFO" "Copied: $filename to staging"
            else
                success=false
            fi
        fi
    done
    
    $success
}

archive_folder() {
    local source_dir=$1
    local folder_name=$(basename $source_dir)
    local archive_path="$ARCHIVE_DIR/${folder_name}_$TIMESTAMP"
    
    mkdir -p $archive_path
    
    mv $source_dir/* $archive_path/ 2>/dev/null
    rmdir $source_dir 2>/dev/null
    
    log_message "INFO" "Archived to: $archive_path"
}

run_etl() {
    log_message "INFO" "Starting ETL pipeline..."
    
    if command -v python &> /dev/null; then
        python etl_load_staging.py >> $LOG_FILE 2>&1
        return $?
    else
        log_error "Python not found"
        return 1
    fi
}

# ======================
# MAIN EXECUTION
# ======================

main() {
    local start_time=$(date +%s)
    
    log_message "INFO" "========================================="
    log_message "INFO" "Starting Data Ingestion Process"
    log_message "INFO" "========================================="
    
    # Check database connection
    if ! check_database_connection; then
        log_error "Database connection check failed"
        send_email "ETL Pipeline Failed - DB Connection" "Database connection check failed at $TIMESTAMP"
        send_slack "🚨 ETL Failed: Database connection failed"
        exit 1
    fi
    
    # Backup staging area
    if [ -n "$(ls -A $STAGING_DIR 2>/dev/null)" ]; then
        backup_staging
    fi
    
    # Detect new folders
    new_folders=$(detect_new_folders)
    
    if [ -z "$new_folders" ]; then
        log_message "INFO" "No new data folders found"
        exit 0
    fi
    
    # Process each folder
    for folder in $new_folders; do
        log_message "INFO" "Processing folder: $folder"
        
        if move_to_staging "$folder"; then
            if run_etl; then
                archive_folder "$folder"
                log_message "INFO" "Successfully processed: $folder"
                send_slack "✅ ETL Success: Processed $folder"
            else
                log_error "ETL failed for: $folder"
                send_email "ETL Pipeline Failed" "ETL failed for folder: $folder at $TIMESTAMP"
                send_slack "🚨 ETL Failed: $folder"
            fi
        else
            log_error "File validation failed for: $folder"
            send_email "ETL Pipeline Failed - Validation" "File validation failed for: $folder"
        fi
    done
    
    local end_time=$(date +%s)
    local duration=$((end_time - start_time))
    
    log_message "INFO" "========================================="
    log_message "INFO" "Completed in $duration seconds"
    log_message "INFO" "========================================="
    
    # Cleanup old logs (keep last 30 days)
    find $LOG_DIR -name "ingestion_*.log" -mtime +30 -delete
    find $ERROR_DIR -name "ingestion_*.error" -mtime +30 -delete
}

# ======================
# CRON SETUP
# ======================

setup_cron() {
    local cron_job="0 2 * * * cd $(pwd) && ./ingest_data.sh >> /dev/null 2>&1"
    
    # Add to crontab
    (crontab -l 2>/dev/null; echo "$cron_job") | crontab -
    
    log_message "INFO" "Cron job scheduled: Daily at 2 AM"
    echo "Cron job added:"
    echo "$cron_job"
}

# ======================
# USAGE
# ======================

usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  --run          Run the ingestion process"
    echo "  --setup-cron   Setup daily cron job (runs at 2 AM)"
    echo "  --help         Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 --run"
    echo "  $0 --setup-cron"
}

# ======================
# ENTRY POINT
# ======================

case "${1:-}" in
    --run)
        main
        ;;
    --setup-cron)
        setup_cron
        ;;
    --help|*)
        usage
        ;;
esac
