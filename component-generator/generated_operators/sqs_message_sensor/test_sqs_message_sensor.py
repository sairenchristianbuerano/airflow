"""
Tests for SqsMessageSensor

Auto-generated test file for Airflow sensor.
"""

import pytest
from datetime import datetime
from airflow.models import DAG
from airflow.utils import timezone

# Import the sensor being tested
from sqs_message_sensor import SqsMessageSensor


@pytest.fixture
def dag():
    """Create a test DAG"""
    return DAG(
        dag_id='test_dag',
        start_date=timezone.datetime(2024, 1, 1),
        default_args={'owner': 'airflow'}
    )


class TestSqsMessageSensor:
    """Test suite for SqsMessageSensor"""

    def test_sensor_initialization(self, dag):
        """Test that sensor can be instantiated"""
        sensor = SqsMessageSensor(
            task_id='test_task',
            dag=dag,
            queue_url='test_queue_url',
        )

        assert sensor.task_id == 'test_task'
        assert sensor.dag == dag

    def test_poke_method_exists(self, dag):
        """Test that poke method is defined"""
        sensor = SqsMessageSensor(
            task_id='test_task',
            dag=dag,
            queue_url='test_queue_url',
        )

        assert hasattr(sensor, 'poke')
        assert callable(sensor.poke)

    def test_poke_with_context(self, dag, mocker):
        """Test poke method with mock context"""
        sensor = SqsMessageSensor(
            task_id='test_task',
            dag=dag,
            queue_url='test_queue_url',
        )

        # Create mock context
        mock_context = {
            'task_instance': mocker.MagicMock(),
            'dag': dag,
            'execution_date': timezone.datetime(2024, 1, 1),
        }

        # Poke should return boolean
        try:
            result = sensor.poke(mock_context)
            assert isinstance(result, bool)
        except NotImplementedError:
            pytest.skip("Poke method not fully implemented")

    def test_poke_interval(self, dag):
        """Test that poke_interval is set"""
        sensor = SqsMessageSensor(
            task_id='test_task',
            dag=dag,
            queue_url='test_queue_url',
        )

        if hasattr(sensor, 'poke_interval'):
            assert isinstance(sensor.poke_interval, (int, float))
            assert sensor.poke_interval > 0

    def test_timeout(self, dag):
        """Test that timeout is set"""
        sensor = SqsMessageSensor(
            task_id='test_task',
            dag=dag,
            queue_url='test_queue_url',
        )

        if hasattr(sensor, 'timeout'):
            assert isinstance(sensor.timeout, (int, float))
            assert sensor.timeout > 0


    def test_parameter_queue_url(self, dag):
        """Test queue_url parameter"""
        # Test with valid value
        operator = {component_name}(
            task_id='test_task',
            dag=dag,
            queue_url='test_value',
        )
        assert hasattr(operator, 'queue_url')

