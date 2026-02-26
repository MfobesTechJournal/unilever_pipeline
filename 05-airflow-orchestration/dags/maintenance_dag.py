"""
PHASE 5: Apache Airflow  
Maintenance DAG - Weekly cleanup and optimization
"""

from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.bash import BashOperator

default_args = {
    'owner': 'database-admin',
    'retries': 1,
}

dag = DAG(
    'maintenance_dag',
    default_args=default_args,
    description='Weekly database maintenance and cleanup',
    schedule_interval='0 3 * * 0',  # Sunday 3 AM
    start_date=datetime(2026, 1, 1),
    catchup=False
)

# Cleanup old logs
cleanup_logs = BashOperator(
    task_id='cleanup_old_logs',
    bash_command="""
    find /opt/unilever_pipeline/logs -type f -mtime +30 -delete
    echo "Cleaned up logs older than 30 days"
    """
)

# Optimize database
optimize_db = BashOperator(
    task_id='optimize_database',
    bash_command="""
    psql -h localhost -d unilever_warehouse -U postgres -c "VACUUM ANALYZE;"
    echo "Database optimization completed"
    """
)

# Backup database
backup_db = BashOperator(
    task_id='backup_database',
    bash_command="""
    pg_dump -h localhost -d unilever_warehouse -U postgres | \
    gzip > /backups/warehouse_$(date +%Y%m%d_%H%M%S).sql.gz
    echo "Database backup completed"
    """
)

# Archive processed files
archive_files = BashOperator(
    task_id='archive_processed_files',
    bash_command="""
    bash /opt/unilever_pipeline/03-shell-scripts/ingestion/archive_processed.sh /staging/processed 30
    echo "File archival completed"
    """
)

# Task dependencies
cleanup_logs >> optimize_db >> backup_db
backup_db >> archive_files
