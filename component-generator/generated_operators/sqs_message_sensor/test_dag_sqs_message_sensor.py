"""
Test DAG for SqsMessageSensor

Sensor that waits for a message to arrive in an AWS SQS queue

This DAG demonstrates the custom SqsMessageSensor with runtime parameter support.
Users can input values via the Airflow UI when triggering this DAG.
"""

from airflow import DAG
from airflow.models import Param
from datetime import datetime, timedelta
import sys
import os

# Add current directory to Python path to import our custom operator
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqs_message_sensor import SqsMessageSensor

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
    dag_id='test_sqs_message_sensor',
    default_args=default_args,
    description='Sensor that waits for a message to arrive in an AWS SQS queue',
    schedule=None,  # Manual trigger only for testing
    catchup=False,
    tags=['test', 'custom-component', 'sensor'],
    params={
        'queue_url': Param(default='https://sqs.us-east-1.amazonaws.com/123456789/my-queue', type='string', description='SQS queue URL'),
    },
) as dag:

    # Create task using runtime parameters
    test_task = SqsMessageSensor(
        task_id='test_sqs_message_sensor_task',
        queue_url="{{ params.queue_url }}",
    )

# 🎯 Testing Instructions:
#
# Via UI (with custom inputs):
#   1. Access http://localhost:8080
#   2. Find DAG: test_sqs_message_sensor
#   3. Click "Trigger DAG" (play button)
#   4. Fill in the parameter form with your values
#   5. Click "Trigger" to run with those inputs
#   6. View task logs to see results
#
# Via CLI:
#   airflow dags test test_sqs_message_sensor $(date +%Y-%m-%d)
