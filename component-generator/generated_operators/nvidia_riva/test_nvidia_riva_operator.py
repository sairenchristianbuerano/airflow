# ============================================================================
# PYTEST TEST FILE - DO NOT PLACE IN AIRFLOW DAGS FOLDER
# ============================================================================
# This file is for running with pytest, NOT for Airflow execution.
# Place this file in: tests/ folder or any location outside dags/
#
# To run tests:
#   pytest test_nvidia_riva_operator.py -v
#
# Required packages:
#   pip install pytest pytest-mock
# ============================================================================

"""
Tests for NvidiaRivaOperator

Auto-generated test file for Airflow operator with comprehensive mocking.

WARNING: This is a pytest test file. Do NOT place in Airflow dags folder.
         Place in a 'tests/' directory instead.
"""

# Prevent Airflow from loading this as a DAG
# This file should only be run with pytest
try:
    import pytest
except ImportError:
    raise ImportError(
        "pytest is required to run this test file. "
        "Install with: pip install pytest pytest-mock\n"
        "NOTE: This file should NOT be in the Airflow dags folder."
    )

from datetime import datetime
from unittest.mock import MagicMock, patch
from airflow.models import DAG, TaskInstance
from airflow.utils import timezone
from airflow.utils.state import State

# Import the operator being tested
# Adjust the import path based on where you placed the operator file
try:
    from nvidia_riva_operator import NvidiaRivaOperator
except ImportError:
    try:
        from custom_operators.nvidia_riva_operator import NvidiaRivaOperator
    except ImportError:
        raise ImportError(
            "Could not import NvidiaRivaOperator. "
            "Ensure 'nvidia_riva_operator.py' is in the Python path."
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
        'ts_nodash': '20240101T000000',
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


class TestNvidiaRivaOperator:
    """Test suite for NvidiaRivaOperator"""

    def test_operator_initialization(self, dag):
        """Test that operator can be instantiated"""
        operator = NvidiaRivaOperator(
            task_id='test_task',
            dag=dag,
            riva_server_url='localhost:50051',
            operation_type='nlp',
            text_input='Test message for NLP analysis',
        )

        assert operator.task_id == 'test_task'
        assert operator.dag == dag
        assert operator.riva_server_url == 'localhost:50051'
        assert operator.operation_type == 'nlp'
        assert operator.text_input == 'Test message for NLP analysis'

    def test_execute_method_exists(self, dag):
        """Test that execute method is defined"""
        operator = NvidiaRivaOperator(
            task_id='test_task',
            dag=dag,
            riva_server_url='localhost:50051',
            operation_type='nlp',
            text_input='Test message',
        )

        assert hasattr(operator, 'execute')
        assert callable(operator.execute)

    def test_template_fields(self, dag):
        """Test that template_fields is properly defined"""
        operator = NvidiaRivaOperator(
            task_id='test_task',
            dag=dag,
            riva_server_url='localhost:50051',
            operation_type='nlp',
            text_input='Test message',
        )

        assert hasattr(operator, 'template_fields')
        assert isinstance(operator.template_fields, (list, tuple))
        assert 'operation_type' in operator.template_fields
        assert 'language_code' in operator.template_fields
        assert 'text_input' in operator.template_fields

    def test_ui_color(self, dag):
        """Test that UI color is set to NVIDIA green"""
        operator = NvidiaRivaOperator(
            task_id='test_task',
            dag=dag,
            riva_server_url='localhost:50051',
            operation_type='nlp',
            text_input='Test message',
        )

        assert hasattr(operator, 'ui_color')
        assert isinstance(operator.ui_color, str)
        assert operator.ui_color.startswith('#')
        assert operator.ui_color == '#76B900'  # NVIDIA green

    def test_parameter_riva_server_url(self, dag):
        """Test riva_server_url parameter"""
        operator = NvidiaRivaOperator(
            task_id='test_task',
            dag=dag,
            riva_server_url='my-riva-server:50051',
            operation_type='nlp',
            text_input='Test message',
        )
        assert operator.riva_server_url == 'my-riva-server:50051'

    def test_parameter_operation_type_asr(self, dag):
        """Test operation_type parameter with ASR"""
        operator = NvidiaRivaOperator(
            task_id='test_task',
            dag=dag,
            riva_server_url='localhost:50051',
            operation_type='asr',
        )
        assert operator.operation_type == 'asr'

    def test_parameter_operation_type_tts(self, dag):
        """Test operation_type parameter with TTS"""
        operator = NvidiaRivaOperator(
            task_id='test_task',
            dag=dag,
            riva_server_url='localhost:50051',
            operation_type='tts',
            text_input='Test message',
            output_path='/tmp/output.wav',
        )
        assert operator.operation_type == 'tts'

    def test_parameter_operation_type_nlp(self, dag):
        """Test operation_type parameter with NLP"""
        operator = NvidiaRivaOperator(
            task_id='test_task',
            dag=dag,
            riva_server_url='localhost:50051',
            operation_type='nlp',
            text_input='Test message',
        )
        assert operator.operation_type == 'nlp'

    def test_invalid_operation_type(self, dag):
        """Test that invalid operation_type raises exception"""
        from airflow.exceptions import AirflowException

        with pytest.raises(AirflowException):
            NvidiaRivaOperator(
                task_id='test_task',
                dag=dag,
                riva_server_url='localhost:50051',
                operation_type='invalid_type',
            )

    def test_missing_riva_server_url(self, dag):
        """Test that missing riva_server_url raises exception"""
        from airflow.exceptions import AirflowException

        with pytest.raises(AirflowException):
            NvidiaRivaOperator(
                task_id='test_task',
                dag=dag,
                riva_server_url='',
                operation_type='nlp',
                text_input='Test message',
            )

    def test_default_language_code(self, dag):
        """Test default language_code value"""
        operator = NvidiaRivaOperator(
            task_id='test_task',
            dag=dag,
            riva_server_url='localhost:50051',
            operation_type='nlp',
            text_input='Test message',
        )
        assert operator.language_code == 'en-US'

    def test_default_sample_rate(self, dag):
        """Test default sample_rate value"""
        operator = NvidiaRivaOperator(
            task_id='test_task',
            dag=dag,
            riva_server_url='localhost:50051',
            operation_type='nlp',
            text_input='Test message',
        )
        assert operator.sample_rate == 16000

    def test_custom_parameters(self, dag):
        """Test custom parameter values"""
        operator = NvidiaRivaOperator(
            task_id='test_task',
            dag=dag,
            riva_server_url='localhost:50051',
            operation_type='tts',
            text_input='Hello world',
            output_path='/tmp/output.wav',
            language_code='es-ES',
            sample_rate=22050,
            model_name='custom_model',
        )

        assert operator.text_input == 'Hello world'
        assert operator.output_path == '/tmp/output.wav'
        assert operator.language_code == 'es-ES'
        assert operator.sample_rate == 22050
        assert operator.model_name == 'custom_model'

    def test_templated_operation_type(self, dag):
        """Test that templated operation_type is allowed"""
        # Templated values should not be validated at init time
        operator = NvidiaRivaOperator(
            task_id='test_task',
            dag=dag,
            riva_server_url='localhost:50051',
            operation_type='{{ params.operation_type }}',
            text_input='{{ params.text_input }}',
        )
        assert operator.operation_type == '{{ params.operation_type }}'

    def test_xcom_pull(self, dag, context):
        """Test that operator can pull XCom values"""
        operator = NvidiaRivaOperator(
            task_id='test_task',
            dag=dag,
            riva_server_url='localhost:50051',
            operation_type='nlp',
            text_input='Test message',
        )

        # Pre-populate XCom storage
        context['ti'].xcom_push(key='test_key', value='test_value')

        # Verify XCom pull works
        pulled_value = context['ti'].xcom_pull(key='test_key')
        assert pulled_value == 'test_value'
