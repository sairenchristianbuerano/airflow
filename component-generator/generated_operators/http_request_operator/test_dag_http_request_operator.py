"""
Test DAG for HttpRequestOperator

Operator for making HTTP requests with support for all methods, headers, authentication, and response handling

This DAG demonstrates the custom HttpRequestOperator with runtime parameter support.
Users can input values via the Airflow UI when triggering this DAG.
"""

from airflow import DAG
from airflow.models import Param
from datetime import datetime, timedelta
import sys
import os

# Add current directory to Python path to import our custom operator
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from http_request_operator import HttpRequestOperator

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
    dag_id='test_http_request_operator',
    default_args=default_args,
    description='Operator for making HTTP requests with support for all methods, headers, authentication, and response handling',
    schedule=None,  # Manual trigger only for testing
    catchup=False,
    tags=['test', 'custom-component', 'operator'],
    params={
        'url': Param(default='https://httpbin.org/get', type='string', description='Request URL'),
        'method': Param(default='GET', type='string', description='HTTP method'),
    },
) as dag:

    # Create task using runtime parameters
    test_task = HttpRequestOperator(
        task_id='test_http_request_operator_task',
        url="{{ params.url }}",
        method="{{ params.method }}",
    )

# 🎯 Testing Instructions:
#
# Via UI (with custom inputs):
#   1. Access http://localhost:8080
#   2. Find DAG: test_http_request_operator
#   3. Click "Trigger DAG" (play button)
#   4. Fill in the parameter form with your values
#   5. Click "Trigger" to run with those inputs
#   6. View task logs to see results
#
# Via CLI:
#   airflow dags test test_http_request_operator $(date +%Y-%m-%d)
