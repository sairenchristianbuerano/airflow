"""
Test DAG for S3FileOperator

Operator for AWS S3 file operations including upload, download, copy, and delete

This DAG demonstrates the custom S3FileOperator with runtime parameter support.
Users can input values via the Airflow UI when triggering this DAG.
"""

from airflow import DAG
from airflow.models import Param
from datetime import datetime, timedelta
import sys
import os

# Add current directory to Python path to import our custom operator
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from s3_file_operator import S3FileOperator

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
    dag_id='test_s3_file_operator',
    default_args=default_args,
    description='Operator for AWS S3 file operations including upload, download, copy, and delete',
    schedule=None,  # Manual trigger only for testing
    catchup=False,
    tags=['test', 'custom-component', 'operator'],
    params={
        'bucket_name': Param(default='my-bucket', type='string', description='S3 bucket name'),
        'operation': Param(default='download', type='string', description='S3 operation type'),
    },
) as dag:

    # Create task using runtime parameters
    test_task = S3FileOperator(
        task_id='test_s3_file_operator_task',
        bucket_name="{{ params.bucket_name }}",
        key='test_key',
        operation="{{ params.operation }}",
    )

# 🎯 Testing Instructions:
#
# Via UI (with custom inputs):
#   1. Access http://localhost:8080
#   2. Find DAG: test_s3_file_operator
#   3. Click "Trigger DAG" (play button)
#   4. Fill in the parameter form with your values
#   5. Click "Trigger" to run with those inputs
#   6. View task logs to see results
#
# Via CLI:
#   airflow dags test test_s3_file_operator $(date +%Y-%m-%d)
