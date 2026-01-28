"""
Test DAG for ApiHealthSensor

Sensor that monitors API endpoint health and waits for successful response before proceeding

This DAG demonstrates the custom ApiHealthSensor with runtime parameter support.
Users can input values via the Airflow UI when triggering this DAG.

IMPORTANT: Both this file AND api_health_sensor.py must be in the same folder (e.g., dags/).
"""

from airflow import DAG
from datetime import datetime, timedelta

# Import Param with Airflow 3.x compatibility
try:
    from airflow.sdk import Param  # Airflow 3.x
except ImportError:
    from airflow.models.param import Param  # Airflow 2.x fallback

# ============================================================================
# OPERATOR IMPORT - The operator file must be in the same folder as this DAG
# ============================================================================
# Option 1: If operator is in the same folder as this DAG file
try:
    from api_health_sensor import ApiHealthSensor
except ImportError:
    # Option 2: Try importing from custom_operators subfolder
    try:
        from custom_operators.api_health_sensor import ApiHealthSensor
    except ImportError:
        # Option 3: Try importing from plugins
        try:
            from plugins.api_health_sensor import ApiHealthSensor
        except ImportError:
            raise ImportError(
                f"Could not import ApiHealthSensor. "
                f"Please ensure 'api_health_sensor.py' is in one of these locations:\n"
                f"  1. Same folder as this DAG file\n"
                f"  2. $AIRFLOW_HOME/dags/custom_operators/\n"
                f"  3. $AIRFLOW_HOME/plugins/"
            )

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
    dag_id='test_api_health_sensor',
    default_args=default_args,
    description='Sensor that monitors API endpoint health and waits for successful response before proceeding',
    schedule=None,  # Manual trigger only for testing
    catchup=False,
    tags=['test', 'custom-component', 'sensor', 'monitoring', 'api-health'],
    params={
        'endpoint_url': Param(
            default='https://httpbin.org/status/200',
            type='string',
            description='API endpoint URL to check'
        ),
        'expected_status_code': Param(
            default=200,
            type='integer',
            description='Expected HTTP status code'
        ),
    },
) as dag:

    # Create task using runtime parameters
    test_task = ApiHealthSensor(
        task_id='test_api_health_sensor_task',
        endpoint_url="{{ params.endpoint_url }}",
        expected_status_code="{{ params.expected_status_code }}",
        poke_interval=30,  # Check every 30 seconds
        timeout=300,  # 5 minute timeout
        mode='poke',
    )

# ============================================================================
# SETUP INSTRUCTIONS
# ============================================================================
#
# 1. Copy BOTH files to your Airflow dags folder:
#    cp api_health_sensor.py $AIRFLOW_HOME/dags/
#    cp test_dag_api_health_sensor.py $AIRFLOW_HOME/dags/
#
# 2. Or create a custom_operators subfolder:
#    mkdir -p $AIRFLOW_HOME/dags/custom_operators
#    cp api_health_sensor.py $AIRFLOW_HOME/dags/custom_operators/
#    touch $AIRFLOW_HOME/dags/custom_operators/__init__.py
#    cp test_dag_api_health_sensor.py $AIRFLOW_HOME/dags/
#
# TESTING:
#
# Via UI:
#   1. Access http://localhost:8080
#   2. Find DAG: test_api_health_sensor
#   3. Click "Trigger DAG" (play button)
#   4. Fill in the parameter form with your values
#   5. Click "Trigger" to run with those inputs
#
# Via CLI:
#   airflow dags test test_api_health_sensor 2024-01-01
