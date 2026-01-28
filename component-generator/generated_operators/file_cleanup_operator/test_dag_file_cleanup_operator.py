"""
Test DAG for FileCleanupOperator

Operator for cleaning up temporary files and directories with age-based and pattern-based filtering

This DAG demonstrates the custom FileCleanupOperator with runtime parameter support.
Users can input values via the Airflow UI when triggering this DAG.
"""

from airflow import DAG
from airflow.models import Param
from datetime import datetime, timedelta
import sys
import os

# Add current directory to Python path to import our custom operator
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from file_cleanup_operator import FileCleanupOperator

# Default arguments for the DAG
default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2024, 1, 1),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

# Create the DAG with runtime parameters
with DAG(
    dag_id='test_file_cleanup_operator',
    default_args=default_args,
    description='Operator for cleaning up temporary files and directories with age-based and pattern-based filtering',
    schedule=None,  # Manual trigger only for testing
    catchup=False,
    tags=['test', 'custom-component', 'operator'],
    params={
        'max_age_days': Param(default=7, type='integer', description='Maximum file age in days'),
        'dry_run': Param(default=True, type='boolean', description='Dry run mode'),
    },
) as dag:

    # Create task using runtime parameters
    test_task = FileCleanupOperator(
        task_id='test_file_cleanup_operator_task',
        directory='test_directory',
        max_age_days="{{ params.max_age_days }}",
        dry_run="{{ params.dry_run }}",
    )

# 🎯 Testing Instructions:
#
# Via UI (with custom inputs):
#   1. Access http://localhost:8080
#   2. Find DAG: test_file_cleanup_operator
#   3. Click "Trigger DAG" (play button)
#   4. Fill in the parameter form with your values
#   5. Click "Trigger" to run with those inputs
#   6. View task logs to see results
#
# Via CLI:
#   airflow dags test test_file_cleanup_operator $(date +%Y-%m-%d)
