#!/bin/bash
#
# PHASE 3: Shell Script
# Archive Processed Files
#

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_DIR="$SCRIPT_DIR/../logs"
ARCHIVE_DIR="$SCRIPT_DIR/../archive"
mkdir -p "$LOG_DIR" "$ARCHIVE_DIR"

LOG_FILE="$LOG_DIR/archiver_$(date +%Y%m%d_%H%M%S).log"

log_msg() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

archive_processed_files() {
    local source_dir=$1
    local days_old=${2:-30}
    
    log_msg "Archiving files from $source_dir older than $days_old days"
    
    if [[ ! -d "$source_dir" ]]; then
        log_msg "ERROR: Directory not found: $source_dir"
        return 1
    fi
    
    local archive_date=$(date +%Y%m%d)
    local tar_file="$ARCHIVE_DIR/processed_${archive_date}.tar.gz"
    
    # Find files older than specified days
    local file_count=0
    while IFS= read -r file; do
        ((file_count++))
        log_msg "Archiving: $file"
    done < <(find "$source_dir" -type f -mtime +$days_old)
    
    if [[ $file_count -gt 0 ]]; then
        # Create tar archive
        tar -czf "$tar_file" -C "$source_dir" . 2>/dev/null || true
        log_msg "✓ Created archive: $tar_file ($file_count files)"
        
        # Remove original files
        find "$source_dir" -type f -mtime +$days_old -delete
        log_msg "✓ Deleted original files"
    else
        log_msg "No files found to archive"
    fi
    
    return 0
}

# Main execution
if [[ $# -eq 0 ]]; then
    log_msg "Usage: $0 <directory> [days_old]"
    exit 1
fi

archive_processed_files "$1" "${2:-30}"
