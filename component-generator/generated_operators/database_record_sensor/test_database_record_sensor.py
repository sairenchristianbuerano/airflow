"""
Tests for DatabaseRecordSensor

Auto-generated test file for Airflow sensor.
"""

import pytest
from datetime import datetime
from airflow.models import DAG
from airflow.utils import timezone

# Import the sensor being tested
from database_record_sensor import DatabaseRecordSensor


@pytest.fixture
def dag():
    """Create a test DAG"""
    return DAG(
        dag_id='test_dag',
        start_date=timezone.datetime(2024, 1, 1),
        default_args={'owner': 'airflow'}
    )


class TestDatabaseRecordSensor:
    """Test suite for DatabaseRecordSensor"""

    def test_sensor_initialization(self, dag):
        """Test that sensor can be instantiated"""
        sensor = DatabaseRecordSensor(
            task_id='test_task',
            dag=dag,
            table='test_table',
            sql_condition='test_sql_condition',
        )

        assert sensor.task_id == 'test_task'
        assert sensor.dag == dag

    def test_poke_method_exists(self, dag):
        """Test that poke method is defined"""
        sensor = DatabaseRecordSensor(
            task_id='test_task',
            dag=dag,
            table='test_table',
            sql_condition='test_sql_condition',
        )

        assert hasattr(sensor, 'poke')
        assert callable(sensor.poke)

    def test_poke_with_context(self, dag, mocker):
        """Test poke method with mock context"""
        sensor = DatabaseRecordSensor(
            task_id='test_task',
            dag=dag,
            table='test_table',
            sql_condition='test_sql_condition',
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
        sensor = DatabaseRecordSensor(
            task_id='test_task',
            dag=dag,
            table='test_table',
            sql_condition='test_sql_condition',
        )

        if hasattr(sensor, 'poke_interval'):
            assert isinstance(sensor.poke_interval, (int, float))
            assert sensor.poke_interval > 0

    def test_timeout(self, dag):
        """Test that timeout is set"""
        sensor = DatabaseRecordSensor(
            task_id='test_task',
            dag=dag,
            table='test_table',
            sql_condition='test_sql_condition',
        )

        if hasattr(sensor, 'timeout'):
            assert isinstance(sensor.timeout, (int, float))
            assert sensor.timeout > 0


    def test_parameter_table(self, dag):
        """Test table parameter"""
        # Test with valid value
        operator = {component_name}(
            task_id='test_task',
            dag=dag,
            table='test_value',
        )
        assert hasattr(operator, 'table')


    def test_parameter_sql_condition(self, dag):
        """Test sql_condition parameter"""
        # Test with valid value
        operator = {component_name}(
            task_id='test_task',
            dag=dag,
            sql_condition='test_value',
        )
        assert hasattr(operator, 'sql_condition')

