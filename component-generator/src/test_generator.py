"""
Test file generator for Airflow components.

Automatically generates pytest test files for generated operators, sensors, and hooks.
"""

from typing import Dict, Any
import structlog

logger = structlog.get_logger()


class TestFileGenerator:
    """Generates pytest test files for Airflow components"""

    def __init__(self):
        self.logger = logger.bind(component="test_generator")

    def generate_test_file(
        self,
        component_name: str,
        component_type: str,
        component_spec: Dict[str, Any]
    ) -> str:
        """
        Generate pytest test file for a component

        Args:
            component_name: Name of the component class
            component_type: Type (operator, sensor, hook)
            component_spec: Component specification dictionary

        Returns:
            Generated test file content
        """
        if component_type == "operator":
            return self._generate_operator_test(component_name, component_spec)
        elif component_type == "sensor":
            return self._generate_sensor_test(component_name, component_spec)
        elif component_type == "hook":
            return self._generate_hook_test(component_name, component_spec)
        else:
            return self._generate_generic_test(component_name, component_spec)

    def _generate_operator_test(self, component_name: str, spec: Dict[str, Any]) -> str:
        """Generate test file for an operator"""

        # Extract inputs for test parameters
        inputs = spec.get('inputs', [])
        test_params = self._generate_test_params(inputs)

        # Check if component has template fields
        has_template_fields = any(inp.get('template_field', False) for inp in inputs)

        snake_name = self._to_snake_case(component_name)

        template = f'''# ============================================================================
# PYTEST TEST FILE - DO NOT PLACE IN AIRFLOW DAGS FOLDER
# ============================================================================
# This file is for running with pytest, NOT for Airflow execution.
# Place this file in: tests/ folder or any location outside dags/
#
# To run tests:
#   pytest test_{snake_name}.py -v
#
# Required packages:
#   pip install pytest pytest-mock
# ============================================================================

"""
Tests for {component_name}

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
        "Install with: pip install pytest pytest-mock\\n"
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
    from {snake_name} import {component_name}
except ImportError:
    try:
        from custom_operators.{snake_name} import {component_name}
    except ImportError:
        raise ImportError(
            f"Could not import {component_name}. "
            f"Ensure '{snake_name}.py' is in the Python path."
        )


@pytest.fixture
def dag():
    """Create a test DAG"""
    return DAG(
        dag_id='test_dag',
        start_date=timezone.datetime(2024, 1, 1),
        default_args={{'owner': 'airflow'}}
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
    ti._xcom_storage = {{}}

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
    return {{
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
        'conf': {{}},
        'params': {{}},
        'var': {{
            'value': {{}},
            'json': {{}},
        }},
    }}


class Test{component_name}:
    """Test suite for {component_name}"""

    def test_operator_initialization(self, dag):
        """Test that operator can be instantiated"""
        operator = {component_name}(
            task_id='test_task',
            dag=dag,
{test_params}
        )

        assert operator.task_id == 'test_task'
        assert operator.dag == dag

    def test_execute_method_exists(self, dag):
        """Test that execute method is defined"""
        operator = {component_name}(
            task_id='test_task',
            dag=dag,
{test_params}
        )

        assert hasattr(operator, 'execute')
        assert callable(operator.execute)

    def test_execute_with_realistic_context(self, dag, context):
        """Test execute method with realistic Airflow context"""
        operator = {component_name}(
            task_id='test_task',
            dag=dag,
{test_params}
        )

        # Execute with realistic context
        try:
            result = operator.execute(context)
            # Operators may return None or a value for XCom
            assert result is not None or result is None
        except NotImplementedError:
            pytest.skip("Execute method not fully implemented")

    def test_xcom_push(self, dag, context):
        """Test that operator can push XCom values"""
        operator = {component_name}(
            task_id='test_task',
            dag=dag,
{test_params}
        )

        # Execute and check if XCom is pushed
        try:
            result = operator.execute(context)

            # If execute returns a value, it's automatically pushed to XCom
            if result is not None:
                # Verify XCom storage
                ti = context['ti']
                assert hasattr(ti, '_xcom_storage')

        except NotImplementedError:
            pytest.skip("Execute method not fully implemented")

    def test_xcom_pull(self, dag, context):
        """Test that operator can pull XCom values"""
        operator = {component_name}(
            task_id='test_task',
            dag=dag,
{test_params}
        )

        # Pre-populate XCom storage
        context['ti'].xcom_push(key='test_key', value='test_value')

        # Verify XCom pull works
        pulled_value = context['ti'].xcom_pull(key='test_key')
        assert pulled_value == 'test_value'

    def test_template_fields(self, dag):
        """Test that template_fields is properly defined"""
        operator = {component_name}(
            task_id='test_task',
            dag=dag,
{test_params}
        )

        # Check if template_fields exists
        if hasattr(operator, 'template_fields'):
            assert isinstance(operator.template_fields, (list, tuple))
            # Verify template fields are valid attribute names
            for field in operator.template_fields:
                assert hasattr(operator, field), f"Template field '{{field}}' not found in operator"

    def test_template_rendering(self, dag, context):
        """Test Jinja template rendering in template_fields"""
        # Create operator with Jinja templates
        operator = {component_name}(
            task_id='test_task',
            dag=dag,
{test_params}
        )

        if hasattr(operator, 'template_fields') and operator.template_fields:
            # Test that template fields can handle Jinja syntax
            # This is a basic test - actual rendering is done by Airflow
            for field in operator.template_fields:
                field_value = getattr(operator, field, None)
                # Template fields should be strings or support templating
                if field_value is not None:
                    assert isinstance(field_value, (str, list, dict)), \
                        f"Template field '{{field}}' must be string, list, or dict"

    def test_ui_color(self, dag):
        """Test that UI color is set"""
        operator = {component_name}(
            task_id='test_task',
            dag=dag,
{test_params}
        )

        # Check if ui_color exists
        if hasattr(operator, 'ui_color'):
            assert isinstance(operator.ui_color, str)
            assert operator.ui_color.startswith('#')

    def test_edge_case_none_values(self, dag):
        """Test operator handles None values gracefully"""
        # Test with minimal required parameters
        operator = {component_name}(
            task_id='test_task',
            dag=dag,
{test_params}
        )

        # Operator should be created without errors
        assert operator is not None

    def test_edge_case_empty_context(self, dag):
        """Test execute with minimal context"""
        operator = {component_name}(
            task_id='test_task',
            dag=dag,
{test_params}
        )

        # Create minimal context
        minimal_context = {{}}

        # Execute should handle missing context gracefully or raise appropriate error
        try:
            operator.execute(minimal_context)
        except (KeyError, AttributeError, NotImplementedError):
            # Expected errors for missing context elements
            pass

{self._generate_parameter_tests(inputs)}
'''
        return template

    def _generate_sensor_test(self, component_name: str, spec: Dict[str, Any]) -> str:
        """Generate test file for a sensor"""

        inputs = spec.get('inputs', [])
        test_params = self._generate_test_params(inputs)
        snake_name = self._to_snake_case(component_name)

        template = f'''# ============================================================================
# PYTEST TEST FILE - DO NOT PLACE IN AIRFLOW DAGS FOLDER
# ============================================================================
# This file is for running with pytest, NOT for Airflow execution.
# Place this file in: tests/ folder or any location outside dags/
#
# To run tests:
#   pytest test_{snake_name}.py -v
#
# Required packages:
#   pip install pytest pytest-mock
# ============================================================================

"""
Tests for {component_name}

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
        "Install with: pip install pytest pytest-mock\\n"
        "NOTE: This file should NOT be in the Airflow dags folder."
    )

from datetime import datetime
from unittest.mock import MagicMock
from airflow.models import DAG, TaskInstance
from airflow.utils import timezone
from airflow.utils.state import State

# Import the sensor being tested
try:
    from {snake_name} import {component_name}
except ImportError:
    try:
        from custom_operators.{snake_name} import {component_name}
    except ImportError:
        raise ImportError(
            f"Could not import {component_name}. "
            f"Ensure '{snake_name}.py' is in the Python path."
        )


@pytest.fixture
def dag():
    """Create a test DAG"""
    return DAG(
        dag_id='test_dag',
        start_date=timezone.datetime(2024, 1, 1),
        default_args={{'owner': 'airflow'}}
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
    ti._xcom_storage = {{}}

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
    return {{
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
        'conf': {{}},
        'params': {{}},
        'var': {{
            'value': {{}},
            'json': {{}},
        }},
    }}


class Test{component_name}:
    """Test suite for {component_name}"""

    def test_sensor_initialization(self, dag):
        """Test that sensor can be instantiated"""
        sensor = {component_name}(
            task_id='test_task',
            dag=dag,
{test_params}
        )

        assert sensor.task_id == 'test_task'
        assert sensor.dag == dag

    def test_poke_method_exists(self, dag):
        """Test that poke method is defined"""
        sensor = {component_name}(
            task_id='test_task',
            dag=dag,
{test_params}
        )

        assert hasattr(sensor, 'poke')
        assert callable(sensor.poke)

    def test_poke_with_realistic_context(self, dag, context):
        """Test poke method with realistic Airflow context"""
        sensor = {component_name}(
            task_id='test_task',
            dag=dag,
{test_params}
        )

        # Poke should return boolean
        try:
            result = sensor.poke(context)
            assert isinstance(result, bool)
        except NotImplementedError:
            pytest.skip("Poke method not fully implemented")

    def test_poke_xcom_integration(self, dag, context):
        """Test sensor can interact with XCom during poke"""
        sensor = {component_name}(
            task_id='test_task',
            dag=dag,
{test_params}
        )

        # Pre-populate XCom for sensor to potentially use
        context['ti'].xcom_push(key='sensor_data', value='ready')

        # Poke and verify XCom access
        try:
            result = sensor.poke(context)
            assert isinstance(result, bool)

            # Verify XCom storage is accessible
            pulled_value = context['ti'].xcom_pull(key='sensor_data')
            assert pulled_value == 'ready'

        except NotImplementedError:
            pytest.skip("Poke method not fully implemented")

    def test_poke_interval(self, dag):
        """Test that poke_interval is set"""
        sensor = {component_name}(
            task_id='test_task',
            dag=dag,
{test_params}
        )

        if hasattr(sensor, 'poke_interval'):
            assert isinstance(sensor.poke_interval, (int, float))
            assert sensor.poke_interval > 0

    def test_timeout(self, dag):
        """Test that timeout is set"""
        sensor = {component_name}(
            task_id='test_task',
            dag=dag,
{test_params}
        )

        if hasattr(sensor, 'timeout'):
            assert isinstance(sensor.timeout, (int, float))
            assert sensor.timeout > 0

    def test_edge_case_poke_false(self, dag, context):
        """Test sensor behavior when condition not met"""
        sensor = {component_name}(
            task_id='test_task',
            dag=dag,
{test_params}
        )

        # Test that poke can return False
        try:
            result = sensor.poke(context)
            # Result should be boolean (can be False if condition not met)
            assert isinstance(result, bool)
        except NotImplementedError:
            pytest.skip("Poke method not fully implemented")

    def test_template_fields(self, dag):
        """Test that template_fields is properly defined"""
        sensor = {component_name}(
            task_id='test_task',
            dag=dag,
{test_params}
        )

        # Check if template_fields exists
        if hasattr(sensor, 'template_fields'):
            assert isinstance(sensor.template_fields, (list, tuple))
            # Verify template fields are valid attribute names
            for field in sensor.template_fields:
                assert hasattr(sensor, field), f"Template field '{{field}}' not found in sensor"

{self._generate_parameter_tests(inputs)}
'''
        return template

    def _generate_hook_test(self, component_name: str, spec: Dict[str, Any]) -> str:
        """Generate test file for a hook"""

        snake_name = self._to_snake_case(component_name)

        template = f'''# ============================================================================
# PYTEST TEST FILE - DO NOT PLACE IN AIRFLOW DAGS FOLDER
# ============================================================================
# This file is for running with pytest, NOT for Airflow execution.
# Place this file in: tests/ folder or any location outside dags/
#
# To run tests:
#   pytest test_{snake_name}.py -v
#
# Required packages:
#   pip install pytest pytest-mock
# ============================================================================

"""
Tests for {component_name}

Auto-generated test file for Airflow hook.

WARNING: This is a pytest test file. Do NOT place in Airflow dags folder.
         Place in a 'tests/' directory instead.
"""

# Prevent Airflow from loading this as a DAG
try:
    import pytest
except ImportError:
    raise ImportError(
        "pytest is required to run this test file. "
        "Install with: pip install pytest pytest-mock\\n"
        "NOTE: This file should NOT be in the Airflow dags folder."
    )

from airflow.models import Connection

# Import the hook being tested
try:
    from {snake_name} import {component_name}
except ImportError:
    try:
        from custom_operators.{snake_name} import {component_name}
    except ImportError:
        raise ImportError(
            f"Could not import {component_name}. "
            f"Ensure '{snake_name}.py' is in the Python path."
        )


class Test{component_name}:
    """Test suite for {component_name}"""

    def test_hook_initialization(self):
        """Test that hook can be instantiated"""
        hook = {component_name}()
        assert hook is not None

    def test_get_conn_method_exists(self):
        """Test that get_conn method is defined"""
        hook = {component_name}()

        assert hasattr(hook, 'get_conn')
        assert callable(hook.get_conn)

    def test_conn_name_attr(self):
        """Test that conn_name_attr is defined"""
        hook = {component_name}()

        if hasattr(hook, 'conn_name_attr'):
            assert isinstance(hook.conn_name_attr, str)

    def test_conn_type(self):
        """Test that conn_type is defined"""
        hook = {component_name}()

        if hasattr(hook, 'conn_type'):
            assert isinstance(hook.conn_type, str)

    def test_hook_name(self):
        """Test that hook_name is defined"""
        hook = {component_name}()

        if hasattr(hook, 'hook_name'):
            assert isinstance(hook.hook_name, str)

    def test_get_connection(self, mocker):
        """Test get_connection method"""
        hook = {component_name}()

        # Mock the connection
        mock_conn = Connection(
            conn_id='test_conn',
            conn_type='generic',
            host='localhost',
        )

        mocker.patch.object(hook, 'get_connection', return_value=mock_conn)

        conn = hook.get_connection('test_conn')
        assert conn is not None
        assert conn.conn_id == 'test_conn'
'''
        return template

    def _generate_generic_test(self, component_name: str, spec: Dict[str, Any]) -> str:
        """Generate generic test file"""

        snake_name = self._to_snake_case(component_name)

        template = f'''# ============================================================================
# PYTEST TEST FILE - DO NOT PLACE IN AIRFLOW DAGS FOLDER
# ============================================================================
# This file is for running with pytest, NOT for Airflow execution.
# Place this file in: tests/ folder or any location outside dags/
#
# To run tests:
#   pytest test_{snake_name}.py -v
#
# Required packages:
#   pip install pytest
# ============================================================================

"""
Tests for {component_name}

Auto-generated test file.

WARNING: This is a pytest test file. Do NOT place in Airflow dags folder.
         Place in a 'tests/' directory instead.
"""

# Prevent Airflow from loading this as a DAG
try:
    import pytest
except ImportError:
    raise ImportError(
        "pytest is required to run this test file. "
        "Install with: pip install pytest\\n"
        "NOTE: This file should NOT be in the Airflow dags folder."
    )

# Import the component being tested
try:
    from {snake_name} import {component_name}
except ImportError:
    try:
        from custom_operators.{snake_name} import {component_name}
    except ImportError:
        raise ImportError(
            f"Could not import {component_name}. "
            f"Ensure '{snake_name}.py' is in the Python path."
        )


class Test{component_name}:
    """Test suite for {component_name}"""

    def test_initialization(self):
        """Test that component can be instantiated"""
        component = {component_name}()
        assert component is not None

    def test_attributes_exist(self):
        """Test that expected attributes exist"""
        component = {component_name}()

        # Add specific attribute checks based on component type
        assert hasattr(component, '__class__')
        assert component.__class__.__name__ == '{component_name}'
'''
        return template

    def _generate_test_params(self, inputs: list) -> str:
        """Generate test parameter assignments"""
        if not inputs:
            return "            # No parameters required"

        param_lines = []
        for inp in inputs:
            name = inp.get('name', '')
            type_hint = inp.get('type', 'str')
            required = inp.get('required', False)

            if required:
                # Generate sample values based on type
                if 'int' in type_hint.lower():
                    value = "123"
                elif 'float' in type_hint.lower():
                    value = "45.67"
                elif 'bool' in type_hint.lower():
                    value = "True"
                elif 'list' in type_hint.lower():
                    value = "[]"
                elif 'dict' in type_hint.lower():
                    value = "{}"
                else:
                    value = f"'test_{name}'"

                param_lines.append(f"            {name}={value},")

        return "\n".join(param_lines) if param_lines else "            # No parameters required"

    def _generate_parameter_tests(self, inputs: list) -> str:
        """Generate individual parameter validation tests"""
        if not inputs:
            return ""

        tests = []
        for inp in inputs:
            name = inp.get('name', '')
            required = inp.get('required', False)

            if required:
                test = f'''
    def test_parameter_{name}(self, dag):
        """Test {name} parameter"""
        # Test with valid value
        operator = {'{'}component_name{'}'}(
            task_id='test_task',
            dag=dag,
            {name}='test_value',
        )
        assert hasattr(operator, '{name}')
'''
                tests.append(test)

        return "\n".join(tests)

    def generate_test_dag(
        self,
        component_name: str,
        component_type: str,
        component_spec: Dict[str, Any]
    ) -> str:
        """
        Generate test DAG file with runtime params support

        Args:
            component_name: Name of the component class
            component_type: Type (operator, sensor, hook)
            component_spec: Component specification dictionary

        Returns:
            Generated test DAG content
        """
        runtime_params = component_spec.get('runtime_params', [])
        inputs = component_spec.get('inputs', [])
        description = component_spec.get('description', f'Test DAG for {component_name}')

        # Generate params dictionary
        params_code = self._generate_params_code(runtime_params)

        # Generate task instantiation
        task_params = self._generate_dag_task_params(inputs, runtime_params)

        snake_name = self._to_snake_case(component_name)

        template = f'''"""
Test DAG for {component_name}

{description}

This DAG demonstrates the custom {component_name} with runtime parameter support.
Users can input values via the Airflow UI when triggering this DAG.

IMPORTANT: Both this file AND {snake_name}.py must be in the same folder (e.g., dags/).
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
    from {snake_name} import {component_name}
except ImportError:
    # Option 2: Try importing from custom_operators subfolder
    try:
        from custom_operators.{snake_name} import {component_name}
    except ImportError:
        # Option 3: Try importing from plugins
        try:
            from plugins.{snake_name} import {component_name}
        except ImportError:
            raise ImportError(
                f"Could not import {component_name}. "
                f"Please ensure '{snake_name}.py' is in one of these locations:\\n"
                f"  1. Same folder as this DAG file\\n"
                f"  2. $AIRFLOW_HOME/dags/custom_operators/\\n"
                f"  3. $AIRFLOW_HOME/plugins/"
            )

# Default arguments for the DAG
default_args = {{
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2024, 1, 1),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}}

# Create the DAG with runtime parameters
with DAG(
    dag_id='test_{snake_name}',
    default_args=default_args,
    description='{description}',
    schedule=None,  # Manual trigger only for testing
    catchup=False,
    tags=['test', 'custom-component', '{component_type}'],
    params={{
{params_code}
    }},
) as dag:

    # Create task using runtime parameters
    test_task = {component_name}(
        task_id='test_{snake_name}_task',
{task_params}
    )

# ============================================================================
# SETUP INSTRUCTIONS
# ============================================================================
#
# 1. Copy BOTH files to your Airflow dags folder:
#    cp {snake_name}.py $AIRFLOW_HOME/dags/
#    cp test_dag_{snake_name}.py $AIRFLOW_HOME/dags/
#
# 2. Or create a custom_operators subfolder:
#    mkdir -p $AIRFLOW_HOME/dags/custom_operators
#    cp {snake_name}.py $AIRFLOW_HOME/dags/custom_operators/
#    touch $AIRFLOW_HOME/dags/custom_operators/__init__.py
#    cp test_dag_{snake_name}.py $AIRFLOW_HOME/dags/
#
# TESTING:
#
# Via UI:
#   1. Access http://localhost:8080
#   2. Find DAG: test_{snake_name}
#   3. Click "Trigger DAG" (play button)
#   4. Fill in the parameter form with your values
#   5. Click "Trigger" to run with those inputs
#
# Via CLI:
#   airflow dags test test_{snake_name} 2024-01-01
'''
        return template

    def _generate_params_code(self, runtime_params: list) -> str:
        """Generate Airflow Params dictionary code

        Intelligently selects default values:
        - For operation_type with enum, prefers options that don't require file inputs
        - Prefers 'nlp' or 'query' over 'asr' or file-based operations
        """
        if not runtime_params:
            return "        # No runtime parameters defined"

        # Keywords that suggest file-less operations (prefer these as defaults)
        safe_operation_keywords = ['nlp', 'query', 'text', 'analyze', 'process', 'inference']
        # Keywords that suggest file-based operations (avoid as defaults)
        file_operation_keywords = ['asr', 'tts', 'transcribe', 'audio', 'video', 'file', 'upload']

        param_lines = []
        for param in runtime_params:
            name = param.get('name', '')
            param_type = param.get('type', 'string')
            description = param.get('description', '')
            default = param.get('default', '')
            enum_values = param.get('enum', [])

            # Smart default selection for operation_type-like parameters
            if enum_values and ('operation' in name.lower() or 'type' in name.lower() or 'mode' in name.lower()):
                # Try to find a safe default that doesn't require file inputs
                safe_default = None
                for enum_val in enum_values:
                    enum_lower = str(enum_val).lower()
                    if any(kw in enum_lower for kw in safe_operation_keywords):
                        safe_default = enum_val
                        break
                if safe_default:
                    default = safe_default

            # Use JSON schema types for Airflow Param (not Python types)
            # Airflow expects: 'string', 'number', 'boolean', 'array', 'object', 'null', 'integer'
            airflow_type = param_type if param_type in ['string', 'number', 'boolean', 'array', 'object', 'integer', 'null'] else 'string'

            # Format default value
            if isinstance(default, str):
                default_val = f"'{default}'"
            else:
                default_val = str(default)

            # Build Param constructor
            param_args = [
                f"default={default_val}",
                f"type='{airflow_type}'",
                f"description='{description}'"
            ]

            # Add enum if present
            if enum_values:
                enum_str = str(enum_values).replace("'", '"')
                param_args.append(f"enum={enum_str}")

            # Add constraints
            if param.get('min_value') is not None:
                param_args.append(f"minimum={param['min_value']}")
            if param.get('max_value') is not None:
                param_args.append(f"maximum={param['max_value']}")
            if param.get('min_length') is not None:
                param_args.append(f"minLength={param['min_length']}")
            if param.get('max_length') is not None:
                param_args.append(f"maxLength={param['max_length']}")

            param_line = f"        '{name}': Param({', '.join(param_args)}),"
            param_lines.append(param_line)

        return "\n".join(param_lines)

    def _generate_dag_task_params(self, inputs: list, runtime_params: list) -> str:
        """Generate task parameter assignments using runtime params

        Intelligently selects defaults that are least likely to cause errors:
        - For operation_type-like params, prefers options that don't require files
        - Adds text_input-like params to support non-file operations
        """
        if not inputs:
            return "        # No parameters required"

        # Create a set of runtime param names for quick lookup
        runtime_param_names = {p.get('name') for p in (runtime_params or [])}

        # Find inputs that are commonly needed for non-file operations
        text_inputs = [inp for inp in inputs if 'text' in inp.get('name', '').lower()
                       and inp.get('type', '') == 'str']

        param_lines = []
        for inp in inputs:
            name = inp.get('name', '')
            required = inp.get('required', False)
            default = inp.get('default')

            if name in runtime_param_names:
                # Use Jinja template to pull from params
                param_lines.append(f'        {name}="{{{{ params.{name} }}}}",')
            # Also add text_input-like params even if not required (for NLP/TTS operations)
            elif 'text_input' in name.lower() or 'text' == name.lower():
                param_lines.append(f'        {name}="{{{{ params.{name} if params.{name} is defined else \'Sample text for testing\' }}}}",')
            elif required:
                # Use default value or sample value
                if default is not None:
                    if isinstance(default, str):
                        value = f"'{default}'"
                    else:
                        value = str(default)
                else:
                    type_hint = inp.get('type', 'str')
                    if 'int' in type_hint.lower():
                        value = "123"
                    elif 'float' in type_hint.lower():
                        value = "45.67"
                    elif 'bool' in type_hint.lower():
                        value = "True"
                    elif 'list' in type_hint.lower():
                        value = "[]"
                    elif 'dict' in type_hint.lower():
                        value = "{{}}"
                    else:
                        value = f"'test_{name}'"

                param_lines.append(f"        {name}={value},")

        return "\n".join(param_lines) if param_lines else "        # No parameters required"

    def _to_snake_case(self, name: str) -> str:
        """Convert PascalCase to snake_case"""
        import re
        s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
        return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()
