"""
Test DAG for RestApiHook

Hook for connecting to REST APIs with authentication, retry logic, and response handling

This DAG demonstrates the custom RestApiHook usage with a PythonOperator.
Users can input values via the Airflow UI when triggering this DAG.

IMPORTANT: Both this file AND rest_api_hook.py must be in the same folder (e.g., dags/).
"""

from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta

# Import Param with Airflow 3.x compatibility
try:
    from airflow.sdk import Param  # Airflow 3.x
except ImportError:
    from airflow.models.param import Param  # Airflow 2.x fallback

# ============================================================================
# HOOK IMPORT - The hook file must be in the same folder as this DAG
# ============================================================================
try:
    from rest_api_hook import RestApiHook
except ImportError:
    try:
        from custom_operators.rest_api_hook import RestApiHook
    except ImportError:
        try:
            from plugins.rest_api_hook import RestApiHook
        except ImportError:
            raise ImportError(
                f"Could not import RestApiHook. "
                f"Please ensure 'rest_api_hook.py' is in one of these locations:\n"
                f"  1. Same folder as this DAG file\n"
                f"  2. $AIRFLOW_HOME/dags/custom_operators/\n"
                f"  3. $AIRFLOW_HOME/plugins/"
            )


def test_rest_api_hook(**context):
    """
    Test function that demonstrates RestApiHook usage.

    This function:
    1. Creates a RestApiHook instance
    2. Tests basic connectivity (mocked for demo)
    3. Returns status information
    """
    params = context.get('params', {})
    endpoint = params.get('endpoint', '/health')
    method = params.get('method', 'GET')
    base_url = params.get('base_url', 'https://httpbin.org')

    print(f"Testing RestApiHook with:")
    print(f"  Base URL: {base_url}")
    print(f"  Endpoint: {endpoint}")
    print(f"  Method: {method}")

    # Create hook instance (without connection for demo)
    hook = RestApiHook(
        conn_id='rest_api_demo',
        base_url=base_url,
        auth_type='none',
        retry_count=3,
        timeout=30
    )

    print(f"Hook initialized successfully!")
    print(f"  Hook name: {hook.hook_name}")
    print(f"  Conn type: {hook.conn_type}")
    print(f"  Retry count: {hook.retry_count}")

    # Note: Actual API calls would require a valid Airflow connection
    # For demo purposes, we just verify the hook is properly configured

    return {
        'status': 'success',
        'hook_name': hook.hook_name,
        'base_url': base_url,
        'endpoint': endpoint,
        'method': method
    }


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
    dag_id='test_rest_api_hook',
    default_args=default_args,
    description='Hook for connecting to REST APIs with authentication, retry logic, and response handling',
    schedule=None,  # Manual trigger only for testing
    catchup=False,
    tags=['test', 'custom-component', 'hook', 'rest-api', 'integration'],
    params={
        'base_url': Param(
            default='https://httpbin.org',
            type='string',
            description='Base URL for the REST API'
        ),
        'endpoint': Param(
            default='/get',
            type='string',
            description='API endpoint path'
        ),
        'method': Param(
            default='GET',
            type='string',
            description='HTTP method'
        ),
    },
) as dag:

    # Create task using PythonOperator to demonstrate hook usage
    test_task = PythonOperator(
        task_id='test_rest_api_hook_task',
        python_callable=test_rest_api_hook,
        provide_context=True,
    )

# ============================================================================
# SETUP INSTRUCTIONS
# ============================================================================
#
# 1. Copy BOTH files to your Airflow dags folder:
#    cp rest_api_hook.py $AIRFLOW_HOME/dags/
#    cp test_dag_rest_api_hook.py $AIRFLOW_HOME/dags/
#
# 2. Or create a custom_operators subfolder:
#    mkdir -p $AIRFLOW_HOME/dags/custom_operators
#    cp rest_api_hook.py $AIRFLOW_HOME/dags/custom_operators/
#    touch $AIRFLOW_HOME/dags/custom_operators/__init__.py
#    cp test_dag_rest_api_hook.py $AIRFLOW_HOME/dags/
#
# 3. (Optional) Create an Airflow connection for actual API calls:
#    airflow connections add 'rest_api_demo' \
#      --conn-type 'http' \
#      --conn-host 'httpbin.org' \
#      --conn-schema 'https'
#
# TESTING:
#
# Via UI:
#   1. Access http://localhost:8080
#   2. Find DAG: test_rest_api_hook
#   3. Click "Trigger DAG" (play button)
#   4. Fill in the parameter form with your values
#   5. Click "Trigger" to run with those inputs
#
# Via CLI:
#   airflow dags test test_rest_api_hook 2024-01-01
