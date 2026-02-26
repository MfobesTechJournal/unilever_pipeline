"""
PHASE 5: Apache Airflow
Incremental ETL DAG - Only load new/changed data
"""

from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from airflow.utils.task_group import TaskGroup

default_args = {
    'owner': 'data-engineering',
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
    'email_on_failure': True,
    'email': ['data-team@unilever.com']
}

dag = DAG(
    'incremental_etl_dag',
    default_args=default_args,
    description='Incremental ETL - Load only new/changed records',
    schedule_interval='0 */6 * * *',  # Every 6 hours
    start_date=datetime(2026, 1, 1),
    catchup=False
)

def check_incremental_data(**context):
    """Check for new data since last run"""
    execution_date = context['execution_date']
    prev_execution_date = context['prev_execution_date']
    print(f"Checking for data changes between {prev_execution_date} and {execution_date}")
    return {'has_changes': True}

def extract_incremental(**context):
    """Extract only changed records"""
    print("Extracting incremental data...")
    return {'records_extracted': 5000}

def transform_incremental(**context):
    """Transform incremental data"""
    ti = context['task_instance']
    extracted = ti.xcom_pull(task_ids='extract_incremental')
    print(f"Transforming {extracted['records_extracted']} records")
    return {'records_transformed': extracted['records_extracted']}

def load_incremental(**context):
    """Load incremental changes"""
    ti = context['task_instance']
    transformed = ti.xcom_pull(task_ids='transform_incremental')
    print(f"Loading {transformed['records_transformed']} records")
    return {'records_loaded': transformed['records_transformed']}

# Tasks
with TaskGroup('check_phase', dag=dag):
    check_data = PythonOperator(
        task_id='check_incremental_data',
        python_callable=check_incremental_data,
        provide_context=True
    )

with TaskGroup('etl_phase', dag=dag):
    extract = PythonOperator(
        task_id='extract_incremental',
        python_callable=extract_incremental,
        provide_context=True
    )
    
    transform = PythonOperator(
        task_id='transform_incremental',
        python_callable=transform_incremental,
        provide_context=True
    )
    
    load = PythonOperator(
        task_id='load_incremental',
        python_callable=load_incremental,
        provide_context=True
    )
    
    extract >> transform >> load

notify = BashOperator(
    task_id='notify_completion',
    bash_command='echo "Incremental ETL completed"'
)

check_data >> extract >> notify
