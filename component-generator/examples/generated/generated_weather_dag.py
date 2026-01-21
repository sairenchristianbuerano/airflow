"""
Test DAG for WeatherFetchOperator

Fetches weather data for a specified city (with mock data for testing)

This DAG demonstrates the custom WeatherFetchOperator with runtime parameter support.
Users can input values via the Airflow UI when triggering this DAG.
"""

from airflow import DAG
from airflow.models import Param
from datetime import datetime, timedelta
import sys
import os

# Add current directory to Python path to import our custom operator
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from weather_fetch_operator import WeatherFetchOperator

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
    dag_id='test_weather_fetch_operator',
    default_args=default_args,
    description='Fetches weather data for a specified city (with mock data for testing)',
    schedule=None,  # Manual trigger only for testing
    catchup=False,
    tags=['test', 'custom-component', 'operator'],
    params={
        'city': Param(default='Tokyo', type='string', description='City name to fetch weather for'),
        'units': Param(default='metric', type='string', description='Temperature units', enum=["metric", "imperial"]),
    },
) as dag:

    # Create task using runtime parameters
    test_task = WeatherFetchOperator(
        task_id='test_weather_fetch_operator_task',
        city="{{ params.city }}",
        units="{{ params.units }}",
    )

# 🎯 Testing Instructions:
#
# Via UI (with custom inputs):
#   1. Access http://localhost:8080
#   2. Find DAG: test_weather_fetch_operator
#   3. Click "Trigger DAG" (play button)
#   4. Fill in the parameter form with your values
#   5. Click "Trigger" to run with those inputs
#   6. View task logs to see results
#
# Via CLI:
#   airflow dags test test_weather_fetch_operator $(date +%Y-%m-%d)
