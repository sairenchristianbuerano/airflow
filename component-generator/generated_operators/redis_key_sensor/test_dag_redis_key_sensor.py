"""
Test DAG for RedisKeySensor

Sensor that waits for a key to exist in Redis with optional value checking

This DAG demonstrates the custom RedisKeySensor with runtime parameter support.
Users can input values via the Airflow UI when triggering this DAG.
"""

from airflow import DAG
from airflow.models import Param
from datetime import datetime, timedelta
import sys
import os

# Add current directory to Python path to import our custom operator
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from redis_key_sensor import RedisKeySensor

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
    dag_id='test_redis_key_sensor',
    default_args=default_args,
    description='Sensor that waits for a key to exist in Redis with optional value checking',
    schedule=None,  # Manual trigger only for testing
    catchup=False,
    tags=['test', 'custom-component', 'sensor'],
    params={
        'key': Param(default='my_key', type='string', description='Redis key to wait for'),
    },
) as dag:

    # Create task using runtime parameters
    test_task = RedisKeySensor(
        task_id='test_redis_key_sensor_task',
        key="{{ params.key }}",
    )

# 🎯 Testing Instructions:
#
# Via UI (with custom inputs):
#   1. Access http://localhost:8080
#   2. Find DAG: test_redis_key_sensor
#   3. Click "Trigger DAG" (play button)
#   4. Fill in the parameter form with your values
#   5. Click "Trigger" to run with those inputs
#   6. View task logs to see results
#
# Via CLI:
#   airflow dags test test_redis_key_sensor $(date +%Y-%m-%d)
