#!/bin/bash
#
# PHASE 3: Cron Job Runner
# Execute daily ETL pipeline
#

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$SCRIPT_DIR/../../.."
LOG_DIR="$PROJECT_ROOT/03-shell-scripts/logs"
mkdir -p "$LOG_DIR"

LOG_FILE="$LOG_DIR/daily_etl_$(date +%Y%m%d_%H%M%S).log"

log_msg() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

log_msg "=========================================="
log_msg "Starting Daily ETL Pipeline"
log_msg "=========================================="

# Change to project directory
cd "$PROJECT_ROOT" || exit 1

# Run data generators
log_msg "Generating sample data..."
python 02-data-sources/raw-data-simulator/generate_sales_data.py >> "$LOG_FILE" 2>&1 || log_msg "Warning: Sales data generation failed"

# Monitor new files
log_msg "Monitoring for new files..."
bash 03-shell-scripts/ingestion/monitor_new_files.sh >> "$LOG_FILE" 2>&1 || log_msg "Warning: File monitoring failed"

# Run ETL pipeline
log_msg "Running ETL pipeline..."
python 04-etl-pipeline/run_pipeline.py >> "$LOG_FILE" 2>&1 || log_msg "Warning: ETL pipeline failed"

log_msg "=========================================="
log_msg "Daily ETL Pipeline Completed"
log_msg "=========================================="
