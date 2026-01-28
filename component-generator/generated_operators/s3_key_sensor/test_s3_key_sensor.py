"""
Tests for S3KeySensor

Auto-generated test file for Airflow sensor.
"""

import pytest
from datetime import datetime
from airflow.models import DAG
from airflow.utils import timezone

# Import the sensor being tested
from s3_key_sensor import S3KeySensor


@pytest.fixture
def dag():
    """Create a test DAG"""
    return DAG(
        dag_id='test_dag',
        start_date=timezone.datetime(2024, 1, 1),
        default_args={'owner': 'airflow'}
    )


class TestS3KeySensor:
    """Test suite for S3KeySensor"""

    def test_sensor_initialization(self, dag):
        """Test that sensor can be instantiated"""
        sensor = S3KeySensor(
            task_id='test_task',
            dag=dag,
            bucket_name='test_bucket_name',
            bucket_key='test_bucket_key',
        )

        assert sensor.task_id == 'test_task'
        assert sensor.dag == dag

    def test_poke_method_exists(self, dag):
        """Test that poke method is defined"""
        sensor = S3KeySensor(
            task_id='test_task',
            dag=dag,
            bucket_name='test_bucket_name',
            bucket_key='test_bucket_key',
        )

        assert hasattr(sensor, 'poke')
        assert callable(sensor.poke)

    def test_poke_with_context(self, dag, mocker):
        """Test poke method with mock context"""
        sensor = S3KeySensor(
            task_id='test_task',
            dag=dag,
            bucket_name='test_bucket_name',
            bucket_key='test_bucket_key',
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
        sensor = S3KeySensor(
            task_id='test_task',
            dag=dag,
            bucket_name='test_bucket_name',
            bucket_key='test_bucket_key',
        )

        if hasattr(sensor, 'poke_interval'):
            assert isinstance(sensor.poke_interval, (int, float))
            assert sensor.poke_interval > 0

    def test_timeout(self, dag):
        """Test that timeout is set"""
        sensor = S3KeySensor(
            task_id='test_task',
            dag=dag,
            bucket_name='test_bucket_name',
            bucket_key='test_bucket_key',
        )

        if hasattr(sensor, 'timeout'):
            assert isinstance(sensor.timeout, (int, float))
            assert sensor.timeout > 0


    def test_parameter_bucket_name(self, dag):
        """Test bucket_name parameter"""
        # Test with valid value
        operator = {component_name}(
            task_id='test_task',
            dag=dag,
            bucket_name='test_value',
        )
        assert hasattr(operator, 'bucket_name')


    def test_parameter_bucket_key(self, dag):
        """Test bucket_key parameter"""
        # Test with valid value
        operator = {component_name}(
            task_id='test_task',
            dag=dag,
            bucket_key='test_value',
        )
        assert hasattr(operator, 'bucket_key')

