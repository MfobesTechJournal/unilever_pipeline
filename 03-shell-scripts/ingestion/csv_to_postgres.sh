#!/bin/bash
#
# PHASE 3: Shell Script  
# CSV to PostgreSQL Loader
#

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_DIR="$SCRIPT_DIR/../logs"
mkdir -p "$LOG_DIR"

LOG_FILE="$LOG_DIR/csv_loader_$(date +%Y%m%d_%H%M%S).log"

# Database configuration
DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-5432}"
DB_NAME="${DB_NAME:-unilever_warehouse}"
DB_USER="${DB_USER:-postgres}"
DB_PASS="${DB_PASS:-postgres}"

log_msg() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

load_csv_to_postgres() {
    local csv_file=$1
    local table_name=$2
    
    log_msg "Loading $csv_file into $table_name"
    
    if [[ ! -f "$csv_file" ]]; then
        log_msg "ERROR: File not found: $csv_file"
        return 1
    fi
    
    # Create COPY command
    local copy_cmd="COPY $table_name FROM STDIN WITH (FORMAT csv, HEADER true, DELIMITER ',');"
    
    # Execute copy
    if PGPASSWORD="$DB_PASS" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" << EOF
$(cat "$csv_file")
$copy_cmd
EOF
    then
        log_msg "✓ Successfully loaded $(wc -l < "$csv_file") rows into $table_name"
        return 0
    else
        log_msg "ERROR: Failed to load CSV into $table_name"
        return 1
    fi
}

# Main execution
if [[ $# -lt 2 ]]; then
    log_msg "Usage: $0 <csv_file> <table_name>"
    exit 1
fi

load_csv_to_postgres "$1" "$2"
