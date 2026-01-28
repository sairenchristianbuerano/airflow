"""
Test DAG for JsonTransformOperator

Operator for transforming JSON data using JMESPath expressions

This DAG demonstrates the custom JsonTransformOperator with runtime parameter support.
Users can input values via the Airflow UI when triggering this DAG.
"""

from airflow import DAG
from airflow.models import Param
from datetime import datetime, timedelta
import sys
import os

# Add current directory to Python path to import our custom operator
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from json_transform_operator import JsonTransformOperator

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
    dag_id='test_json_transform_operator',
    default_args=default_args,
    description='Operator for transforming JSON data using JMESPath expressions',
    schedule=None,  # Manual trigger only for testing
    catchup=False,
    tags=['test', 'custom-component', 'operator'],
    params={
        'expression': Param(default='@', type='string', description='JMESPath expression'),
    },
) as dag:

    # Create task using runtime parameters
    test_task = JsonTransformOperator(
        task_id='test_json_transform_operator_task',
        input_json='test_input_json',
        expression="{{ params.expression }}",
    )

# 🎯 Testing Instructions:
#
# Via UI (with custom inputs):
#   1. Access http://localhost:8080
#   2. Find DAG: test_json_transform_operator
#   3. Click "Trigger DAG" (play button)
#   4. Fill in the parameter form with your values
#   5. Click "Trigger" to run with those inputs
#   6. View task logs to see results
#
# Via CLI:
#   airflow dags test test_json_transform_operator $(date +%Y-%m-%d)
