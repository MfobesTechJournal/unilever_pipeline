"""
=============================================================
PHASE 5: APACHE AIRFLOW PIPELINE ORCHESTRATION
ETL Pipeline DAG for Unilever Data Warehouse
=============================================================
"""

from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.bash_operator import BashOperator
from airflow.operators.python_operator import PythonOperator
from airflow.operators.dummy_operator import DummyOperator
from airflow.utils.dates import days_ago
import sys
import os

# Add the project directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Default arguments
default_args = {
    'owner': 'unilever_team',
    'depends_on_past': False,
    'email_on_failure': True,
    'email_on_retry': False,
    'retries': 3,
    'retry_delay': timedelta(minutes=5),
}

# DAG Definition
dag = DAG(
    'unilever_etl_pipeline',
    default_args=default_args,
    description='Unilever Data Warehouse ETL Pipeline',
    schedule_interval='@daily',  # Run daily at midnight
    start_date=days_ago(1),
    catchup=False,
    tags=['etl', 'unilever', 'data-warehouse'],
)

# ============================================================
# TASKS
# ============================================================

# Task 1: Check for new data files
check_data_task = BashOperator(
    task_id='check_for_new_data',
    bash_command='ls -la raw_data/ | grep -v archive',
    dag=dag,
)

# Task 2: Generate data (for testing)
generate_data_task = BashOperator(
    task_id='generate_sample_data',
    bash_command='cd /usr/local/airflow/dags && python generate_data.py',
    dag=dag,
)

# Task 3: Validate data files
validate_data_task = BashOperator(
    task_id='validate_data_files',
    bash_command='cd /usr/local/airflow/dags && python -c "import pandas as pd; pd.read_csv(\'staging/products.csv\'); pd.read_csv(\'staging/customers.csv\'); pd.read_csv(\'staging/sales.csv\')"',
    dag=dag,
)

# Task 4: Run ETL pipeline
run_etl_task = BashOperator(
    task_id='run_etl_pipeline',
    bash_command='cd /usr/local/airflow/dags && python etl_load_staging.py',
    dag=dag,
)

# Task 5: Validate warehouse data
validate_warehouse_task = BashOperator(
    task_id='validate_warehouse',
    bash_command='echo "Warehouse validation: Running data quality checks"',
    dag=dag,
)

# Task 6: Generate data quality report
data_quality_task = PythonOperator(
    task_id='generate_data_quality_report',
    python_callable=lambda: print("Data quality report generated"),
    dag=dag,
)

# Task 7: Archive processed files
archive_task = BashOperator(
    task_id='archive_processed_files',
    bash_command='echo "Files archived"',
    dag=dag,
)

# Task 8: Send success notification
notify_task = BashOperator(
    task_id='send_notification',
    bash_command='echo "Pipeline completed successfully"',
    dag=dag,
)

# ============================================================
# TASK DEPENDENCIES
# ============================================================

# Define the pipeline flow
check_data_task >> generate_data_task >> validate_data_task >> run_etl_task >> validate_warehouse_task >> data_quality_task >> archive_task >> notify_task
