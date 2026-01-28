"""
Test DAG for DatabaseRecordSensor

Sensor that waits for a record to exist in a database table based on SQL condition

This DAG demonstrates the custom DatabaseRecordSensor with runtime parameter support.
Users can input values via the Airflow UI when triggering this DAG.
"""

from airflow import DAG
from airflow.models import Param
from datetime import datetime, timedelta
import sys
import os

# Add current directory to Python path to import our custom operator
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database_record_sensor import DatabaseRecordSensor

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
    dag_id='test_database_record_sensor',
    default_args=default_args,
    description='Sensor that waits for a record to exist in a database table based on SQL condition',
    schedule=None,  # Manual trigger only for testing
    catchup=False,
    tags=['test', 'custom-component', 'sensor'],
    params={
        'table': Param(default='my_table', type='string', description='Table name to query'),
        'sql_condition': Param(default='status = done', type='string', description='SQL WHERE condition'),
    },
) as dag:

    # Create task using runtime parameters
    test_task = DatabaseRecordSensor(
        task_id='test_database_record_sensor_task',
        table="{{ params.table }}",
        sql_condition="{{ params.sql_condition }}",
    )

# 🎯 Testing Instructions:
#
# Via UI (with custom inputs):
#   1. Access http://localhost:8080
#   2. Find DAG: test_database_record_sensor
#   3. Click "Trigger DAG" (play button)
#   4. Fill in the parameter form with your values
#   5. Click "Trigger" to run with those inputs
#   6. View task logs to see results
#
# Via CLI:
#   airflow dags test test_database_record_sensor $(date +%Y-%m-%d)
