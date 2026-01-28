"""
Test DAG for PostgresQueryOperator

Operator for executing SQL queries on PostgreSQL databases with parameterized queries and result handling

This DAG demonstrates the custom PostgresQueryOperator with runtime parameter support.
Users can input values via the Airflow UI when triggering this DAG.
"""

from airflow import DAG
from airflow.models import Param
from datetime import datetime, timedelta
import sys
import os

# Add current directory to Python path to import our custom operator
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from postgres_query_operator import PostgresQueryOperator

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
    dag_id='test_postgres_query_operator',
    default_args=default_args,
    description='Operator for executing SQL queries on PostgreSQL databases with parameterized queries and result handling',
    schedule=None,  # Manual trigger only for testing
    catchup=False,
    tags=['test', 'custom-component', 'operator'],
    params={
        'sql': Param(default='SELECT 1', type='string', description='SQL query to execute'),
    },
) as dag:

    # Create task using runtime parameters
    test_task = PostgresQueryOperator(
        task_id='test_postgres_query_operator_task',
        sql="{{ params.sql }}",
    )

# 🎯 Testing Instructions:
#
# Via UI (with custom inputs):
#   1. Access http://localhost:8080
#   2. Find DAG: test_postgres_query_operator
#   3. Click "Trigger DAG" (play button)
#   4. Fill in the parameter form with your values
#   5. Click "Trigger" to run with those inputs
#   6. View task logs to see results
#
# Via CLI:
#   airflow dags test test_postgres_query_operator $(date +%Y-%m-%d)
