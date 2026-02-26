#!/bin/bash
#
# PHASE 3: Shell Script
# CSV File Validator & Format Checker
#

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_DIR="$SCRIPT_DIR/../logs"
mkdir -p "$LOG_DIR"

LOG_FILE="$LOG_DIR/csv_validator_$(date +%Y%m%d_%H%M%S).log"

log_msg() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

validate_csv_file() {
    local file=$1
    local delimiter=$2
    
    log_msg "Validating: $file"
    
    # Check if file exists
    if [[ ! -f "$file" ]]; then
        log_msg "ERROR: File not found: $file"
        return 1
    fi
    
    # Check file size (max 1GB)
    local size=$(stat -f%z "$file" 2>/dev/null || stat -c%s "$file" 2>/dev/null)
    if [[ $size -gt 1073741824 ]]; then
        log_msg "ERROR: File exceeds 1GB limit: $size bytes"
        return 1
    fi
    
    # Check delimiter consistency
    local header_cols=$(head -1 "$file" | tr -cd "$delimiter" | wc -c)
    local error_rows=0
    
    while IFS= read -r line; do
        local cols=$(echo "$line" | tr -cd "$delimiter" | wc -c)
        if [[ $cols -ne $header_cols ]]; then
            ((error_rows++))
        fi
    done < "$file"
    
    if [[ $error_rows -gt 0 ]]; then
        log_msg "WARNING: Found $error_rows rows with mismatched columns"
    fi
    
    # Check for required columns
    local header=$(head -1 "$file")
    local required_cols=("id" "date" "amount")
    
    for col in "${required_cols[@]}"; do
        if [[ ! "$header" =~ $col ]]; then
            log_msg "WARNING: Missing expected column: $col"
        fi
    done
    
    log_msg "Validation completed for $file"
    return 0
}

# Main execution
if [[ $# -eq 0 ]]; then
    log_msg "Usage: $0 <file_path> [delimiter]"
    exit 1
fi

delimiter="${2:-, }"
validate_csv_file "$1" "$delimiter"
