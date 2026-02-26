#!/bin/bash
# Phase 3: Monitor Raw Data Directory for New Files
# Description: Watches specified directory for new CSV/JSON/Excel files
# Logs: 03-shell-scripts/logs/monitor_YYYY-MM-DD.log

set -e

# Configuration
RAW_DATA_DIR="${RAW_DATA_DIR:-raw_data}"
STAGING_DIR="${STAGING_DIR:-staging}"
ARCHIVE_DIR="${ARCHIVE_DIR:-raw_data/archive}"
LOG_DIR="03-shell-scripts/logs"
LOG_FILE="${LOG_DIR}/monitor_$(date +%Y-%m-%d).log"

# Create directories if they don't exist
mkdir -p "$RAW_DATA_DIR" "$STAGING_DIR" "$ARCHIVE_DIR" "$LOG_DIR"

# Logging function
log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# Main monitoring function
monitor_files() {
    log "Starting file monitoring for $RAW_DATA_DIR"
    
    # Get today's date folder
    today=$(date +%Y-%m-%d)
    today_dir="$RAW_DATA_DIR/$today"
    
    if [ ! -d "$today_dir" ]; then
        log "Creating directory: $today_dir"
        mkdir -p "$today_dir"
    fi
    
    # Find all new files (CSV, JSON, XLSX)
    log "Scanning for new files..."
    
    find "$today_dir" -type f \( -name "*.csv" -o -name "*.json" -o -name "*.xlsx" \) 2>/dev/null | while read -r file; do
        if [ -f "$file" ]; then
            log "Found file: $file"
            
            # Validate file
            if validate_file "$file"; then
                log "✓ Validation passed: $file"
                
                # Move to staging
                if move_to_staging "$file"; then
                    log "✓ Moved to staging: $file"
                fi
            else
                log "✗ Validation failed: $file"
            fi
        fi
    done
    
    log "File monitoring completed"
}

# Validate file format and size
validate_file() {
    local file=$1
    local max_size=$((1073741824))  # 1GB in bytes
    
    # Check if file exists
    if [ ! -f "$file" ]; then
        log "ERROR: File not found: $file"
        return 1
    fi
    
    # Check file size
    local size=$(stat -f%z "$file" 2>/dev/null || stat -c%s "$file" 2>/dev/null || echo 0)
    if [ "$size" -eq 0 ]; then
        log "ERROR: File is empty: $file"
        return 1
    fi
    
    if [ "$size" -gt "$max_size" ]; then
        log "ERROR: File exceeds max size (1GB): $file"
        return 1
    fi
    
    # Check file extension
    local ext="${file##*.}"
    case "$ext" in
        csv|json|xlsx)
            return 0
            ;;
        *)
            log "ERROR: Unsupported file type: $ext"
            return 1
            ;;
    esac
}

# Move validated file to staging
move_to_staging() {
    local file=$1
    local filename=$(basename "$file")
    local staging_file="$STAGING_DIR/$filename"
    
    if cp "$file" "$staging_file"; then
        # Archive the original
        local timestamp=$(date +%Y%m%d_%H%M%S)
        mkdir -p "$ARCHIVE_DIR/$timestamp"
        mv "$file" "$ARCHIVE_DIR/$timestamp/$filename"
        return 0
    else
        log "ERROR: Failed to copy file to staging: $file"
        return 1
    fi
}

# Main execution
main() {
    log "========================================="
    log "File Monitoring Service Started"
    log "========================================="
    log "Raw Data Directory: $RAW_DATA_DIR"
    log "Staging Directory: $STAGING_DIR"
    log "Archive Directory: $ARCHIVE_DIR"
    
    monitor_files
    
    log "========================================="
    log "File Monitoring Service Completed"
    log "========================================="
}

# Run main function
main "$@"
