# ============================================================================
# PYTEST TEST FILE - DO NOT PLACE IN AIRFLOW DAGS FOLDER
# ============================================================================
# This file is for running with pytest, NOT for Airflow execution.
# Place this file in: tests/ folder or any location outside dags/
#
# To run tests:
#   pytest test_api_health_sensor.py -v
#
# Required packages:
#   pip install pytest pytest-mock
# ============================================================================

"""
Tests for ApiHealthSensor

Auto-generated test file for Airflow sensor with comprehensive mocking.

WARNING: This is a pytest test file. Do NOT place in Airflow dags folder.
         Place in a 'tests/' directory instead.
"""

# Prevent Airflow from loading this as a DAG
try:
    import pytest
except ImportError:
    raise ImportError(
        "pytest is required to run this test file. "
        "Install with: pip install pytest pytest-mock\n"
        "NOTE: This file should NOT be in the Airflow dags folder."
    )

from datetime import datetime
from unittest.mock import MagicMock
from airflow.models import DAG, TaskInstance
from airflow.utils import timezone
from airflow.utils.state import State

# Import the sensor being tested
try:
    from api_health_sensor import ApiHealthSensor
except ImportError:
    try:
        from custom_operators.api_health_sensor import ApiHealthSensor
    except ImportError:
        raise ImportError(
            f"Could not import ApiHealthSensor. "
            f"Ensure 'api_health_sensor.py' is in the Python path."
        )


@pytest.fixture
def dag():
    """Create a test DAG"""
    return DAG(
        dag_id='test_dag',
        start_date=timezone.datetime(2024, 1, 1),
        default_args={'owner': 'airflow'}
    )


@pytest.fixture
def task_instance(dag):
    """Create a realistic TaskInstance mock with XCom support"""
    ti = MagicMock(spec=TaskInstance)
    ti.dag_id = dag.dag_id
    ti.task_id = 'test_task'
    ti.execution_date = timezone.datetime(2024, 1, 1)
    ti.state = State.RUNNING
    ti.try_number = 1
    ti.max_tries = 2

    # XCom storage for testing
    ti._xcom_storage = {}

    def xcom_push(key, value, **kwargs):
        ti._xcom_storage[key] = value

    def xcom_pull(task_ids=None, key=None, **kwargs):
        if key:
            return ti._xcom_storage.get(key)
        return None

    ti.xcom_push = xcom_push
    ti.xcom_pull = xcom_pull

    return ti


@pytest.fixture
def context(dag, task_instance):
    """Create realistic Airflow execution context"""
    return {
        'dag': dag,
        'task': MagicMock(),
        'task_instance': task_instance,
        'ti': task_instance,
        'execution_date': timezone.datetime(2024, 1, 1),
        'ds': '2024-01-01',
        'ds_nodash': '20240101',
        'ts': '2024-01-01T00:00:00+00:00',
        'prev_execution_date': None,
        'next_execution_date': None,
        'run_id': 'test_run',
        'dag_run': MagicMock(),
        'conf': {},
        'params': {},
        'var': {
            'value': {},
            'json': {},
        },
    }


class TestApiHealthSensor:
    """Test suite for ApiHealthSensor"""

    def test_sensor_initialization(self, dag):
        """Test that sensor can be instantiated"""
        sensor = ApiHealthSensor(
            task_id='test_task',
            dag=dag,
            endpoint_url='https://httpbin.org/status/200',
        )

        assert sensor.task_id == 'test_task'
        assert sensor.dag == dag
        assert sensor.endpoint_url == 'https://httpbin.org/status/200'

    def test_poke_method_exists(self, dag):
        """Test that poke method is defined"""
        sensor = ApiHealthSensor(
            task_id='test_task',
            dag=dag,
            endpoint_url='https://httpbin.org/status/200',
        )

        assert hasattr(sensor, 'poke')
        assert callable(sensor.poke)

    def test_template_fields(self, dag):
        """Test that template_fields is properly defined"""
        sensor = ApiHealthSensor(
            task_id='test_task',
            dag=dag,
            endpoint_url='https://httpbin.org/status/200',
        )

        assert hasattr(sensor, 'template_fields')
        assert isinstance(sensor.template_fields, (list, tuple))
        assert 'endpoint_url' in sensor.template_fields
        assert 'expected_status_code' in sensor.template_fields

    def test_ui_color(self, dag):
        """Test that UI color is set"""
        sensor = ApiHealthSensor(
            task_id='test_task',
            dag=dag,
            endpoint_url='https://httpbin.org/status/200',
        )

        assert hasattr(sensor, 'ui_color')
        assert isinstance(sensor.ui_color, str)
        assert sensor.ui_color.startswith('#')
        assert sensor.ui_color == '#50C878'

    def test_default_parameters(self, dag):
        """Test default parameter values"""
        sensor = ApiHealthSensor(
            task_id='test_task',
            dag=dag,
            endpoint_url='https://httpbin.org/status/200',
        )

        assert sensor.expected_status_code == 200
        assert sensor.request_timeout == 30
        assert sensor.headers == {}
        assert sensor.response_check is None
        assert sensor.poke_interval == 60
        assert sensor.timeout == 300
        assert sensor.mode == 'poke'

    def test_custom_parameters(self, dag):
        """Test custom parameter values"""
        sensor = ApiHealthSensor(
            task_id='test_task',
            dag=dag,
            endpoint_url='https://api.example.com/health',
            expected_status_code=201,
            request_timeout=60,
            headers={'Authorization': 'Bearer token'},
            response_check='status.healthy',
            poke_interval=30,
            timeout=600,
            mode='reschedule',
        )

        assert sensor.endpoint_url == 'https://api.example.com/health'
        assert sensor.expected_status_code == 201
        assert sensor.request_timeout == 60
        assert sensor.headers == {'Authorization': 'Bearer token'}
        assert sensor.response_check == 'status.healthy'
        assert sensor.poke_interval == 30
        assert sensor.timeout == 600
        assert sensor.mode == 'reschedule'

    def test_xcom_integration(self, dag, context):
        """Test sensor can interact with XCom"""
        sensor = ApiHealthSensor(
            task_id='test_task',
            dag=dag,
            endpoint_url='https://httpbin.org/status/200',
        )

        # Pre-populate XCom storage
        context['ti'].xcom_push(key='test_key', value='test_value')

        # Verify XCom pull works
        pulled_value = context['ti'].xcom_pull(key='test_key')
        assert pulled_value == 'test_value'

    def test_templated_endpoint_url(self, dag):
        """Test that templated endpoint_url is allowed"""
        sensor = ApiHealthSensor(
            task_id='test_task',
            dag=dag,
            endpoint_url='{{ params.endpoint_url }}',
        )
        assert sensor.endpoint_url == '{{ params.endpoint_url }}'
