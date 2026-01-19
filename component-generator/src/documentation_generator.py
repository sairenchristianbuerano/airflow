"""
Documentation generator for Airflow components.

Generates comprehensive markdown documentation including:
- Component overview
- Installation instructions
- Usage examples
- API reference
- Airflow DAG integration guide
"""

from typing import Dict, Any, List
import structlog

logger = structlog.get_logger()


class DocumentationGenerator:
    """Generates markdown documentation for Airflow components"""

    def __init__(self):
        self.logger = logger.bind(component="documentation_generator")

    def generate_documentation(
        self,
        component_name: str,
        component_type: str,
        spec: Dict[str, Any],
        code: str
    ) -> str:
        """
        Generate comprehensive documentation for a component

        Args:
            component_name: Name of the component class
            component_type: Type (operator, sensor, hook)
            spec: Component specification dictionary
            code: Generated component code

        Returns:
            Markdown documentation string
        """
        sections = []

        # Header
        sections.append(self._generate_header(component_name, spec))

        # Table of Contents
        sections.append(self._generate_toc())

        # Overview
        sections.append(self._generate_overview(component_name, component_type, spec))

        # Installation
        sections.append(self._generate_installation(spec))

        # Testing & Integration
        sections.append(self._generate_testing_integration(component_name, spec))

        # Quick Start
        sections.append(self._generate_quick_start(component_name, component_type, spec))

        # Configuration
        sections.append(self._generate_configuration(spec))

        # Runtime Parameters (if defined)
        runtime_params_section = self._generate_runtime_parameters(spec)
        if runtime_params_section:
            sections.append(runtime_params_section)

        # DAG Integration
        sections.append(self._generate_dag_integration(component_name, component_type, spec))

        # API Reference
        sections.append(self._generate_api_reference(component_name, component_type, spec))

        # Examples
        sections.append(self._generate_examples(component_name, component_type, spec))

        # Troubleshooting
        sections.append(self._generate_troubleshooting(component_name, component_type))

        # Footer
        sections.append(self._generate_footer(spec))

        return "\n\n".join(sections)

    def _generate_header(self, component_name: str, spec: Dict[str, Any]) -> str:
        """Generate documentation header"""
        display_name = spec.get('display_name', component_name)
        version = spec.get('version', '1.0.0')
        author = spec.get('author', 'Airflow Component Factory')
        category = spec.get('category', 'custom')

        return f'''# {display_name}

**Version:** {version}
**Author:** {author}
**Category:** {category}
**Component:** {component_name}

> {spec.get('description', 'Custom Airflow component')}
'''

    def _generate_toc(self) -> str:
        """Generate table of contents"""
        return '''## Table of Contents

- [Overview](#overview)
- [Installation](#installation)
- [Testing & Integration](#testing--integration)
- [Quick Start](#quick-start)
- [Configuration](#configuration)
- [DAG Integration](#dag-integration)
- [API Reference](#api-reference)
- [Examples](#examples)
- [Troubleshooting](#troubleshooting)
'''

    def _generate_overview(self, component_name: str, component_type: str, spec: Dict[str, Any]) -> str:
        """Generate overview section"""
        requirements = spec.get('requirements', [])
        req_list = "\n".join([f"- {req}" for req in requirements]) if requirements else "- No specific requirements listed"

        return f'''## Overview

### Component Type
**{component_type.capitalize()}**

### Description
{spec.get('description', 'Custom Airflow component')}

### Features
{req_list}

### Use Cases
This {component_type} is suitable for:
- Workflows requiring {spec.get('category', 'custom')} operations
- Data pipelines with {component_type}-based task execution
- Integration with external systems and services
'''

    def _generate_installation(self, spec: Dict[str, Any]) -> str:
        """Generate installation section"""
        dependencies = spec.get('dependencies', [])

        dep_installs = []
        if dependencies:
            for dep in dependencies:
                if 'apache-airflow-providers' in dep:
                    dep_installs.append(f"pip install {dep}")
                else:
                    dep_installs.append(f"pip install {dep}")

        install_commands = "\n".join(dep_installs) if dep_installs else "# No additional dependencies required"

        return f'''## Installation

### Prerequisites
- Apache Airflow 2.0+
- Python 3.8+

### Install Dependencies

```bash
{install_commands}
```

### Install Component

1. Copy the component file to your Airflow DAGs folder or plugins directory:

```bash
# Option 1: Place in DAGs folder
cp {self._to_snake_case(spec.get('name', 'component'))}.py $AIRFLOW_HOME/dags/

# Option 2: Place in plugins folder
cp {self._to_snake_case(spec.get('name', 'component'))}.py $AIRFLOW_HOME/plugins/
```

2. Restart Airflow webserver and scheduler if needed.
'''

    def _generate_testing_integration(self, component_name: str, spec: Dict[str, Any]) -> str:
        """Generate testing and integration guide section"""
        component_file = f"{self._to_snake_case(spec.get('name', 'component'))}.py"

        return f'''## Testing & Integration

This section helps you validate and integrate the generated component into your Apache Airflow environment.

### Quick Test (No Airflow Installation)

Before integrating with Airflow, you can perform a quick syntax and import validation:

```bash
# Test Python syntax
python -m py_compile {component_file}

# Test imports (without executing)
python -c "import ast; ast.parse(open('{component_file}').read())"

# Check for obvious issues
pylint {component_file} || flake8 {component_file}
```

### Integration with Local Airflow

Choose one of the following methods to integrate this component into your local Airflow setup:

#### Option 1: DAGs Folder (Recommended for Testing)

This is the **simplest and recommended approach** for testing custom components. The DAGs folder is automatically added to `PYTHONPATH` by Airflow.

```bash
# Copy component to DAGs folder
cp {component_file} $AIRFLOW_HOME/dags/

# Verify file is present
ls -la $AIRFLOW_HOME/dags/{component_file}

# No restart needed - Airflow auto-detects files in DAGs folder
```

**Pros:**
- ✅ No Airflow restart required
- ✅ Automatically on PYTHONPATH
- ✅ Perfect for rapid iteration and testing
- ✅ Can create test DAG in same folder

**Cons:**
- ❌ Less organized for reusable components
- ❌ Mixed with DAG definitions

#### Option 2: Plugins Folder (For Reusable Components)

Use this approach when you want to make components available across multiple DAGs.

```bash
# Copy component to plugins folder
cp {component_file} $AIRFLOW_HOME/plugins/

# Verify file is present
ls -la $AIRFLOW_HOME/plugins/{component_file}

# Restart Airflow services (required for plugins)
airflow webserver --daemon
airflow scheduler --daemon
```

**Pros:**
- ✅ Better organization for reusable components
- ✅ Automatically on PYTHONPATH
- ✅ Supports advanced plugin features (custom views, hooks, etc.)

**Cons:**
- ❌ Requires Airflow restart to detect changes
- ❌ Lazy loading may delay component availability

#### Option 3: Docker Volume Mounting (For Containerized Airflow)

If you're running Airflow in Docker, mount the component directory:

```yaml
# Add to docker-compose.yml or docker run command
volumes:
  - ./custom_components:/opt/airflow/dags/custom_components
  # Then place {component_file} in ./custom_components/
```

Or copy into running container:

```bash
# Copy to running container
docker cp {component_file} <container_name>:/opt/airflow/dags/

# Verify inside container
docker exec <container_name> ls -la /opt/airflow/dags/{component_file}
```

### Testing Commands

Once integrated, test the component with these Airflow CLI commands:

#### 1. Test Component Import

```bash
# Test if Airflow can import the component
python -c "from {self._to_snake_case(component_name)} import {component_name}; print('Import successful!')"
```

#### 2. Test Component in Airflow Context

Create a test DAG (`test_{self._to_snake_case(component_name)}.py`) in your DAGs folder:

```python
from airflow import DAG
from datetime import datetime
from {self._to_snake_case(component_name)} import {component_name}

with DAG(
    dag_id='test_{self._to_snake_case(component_name)}',
    start_date=datetime(2024, 1, 1),
    schedule=None,  # Manual trigger only
    catchup=False
) as dag:

    test_task = {component_name}(
        task_id='test_task',
        # Add required parameters here
    )
```

#### 3. Run Task Test (Without Scheduler)

```bash
# Test task execution without running the scheduler
airflow tasks test test_{self._to_snake_case(component_name)} test_task 2024-01-01
```

This command:
- ✅ Runs the task immediately without scheduling
- ✅ Shows execution output in real-time
- ✅ Doesn't record results in metadata database
- ✅ Perfect for debugging and validation

#### 4. Validate DAG

```bash
# Check if DAG is valid (no import or syntax errors)
airflow dags list | grep test_{self._to_snake_case(component_name)}

# Show detailed DAG info
airflow dags show test_{self._to_snake_case(component_name)}
```

### Common Integration Issues & Fixes

#### Issue 1: Import Error - Module Not Found

```
ModuleNotFoundError: No module named '{self._to_snake_case(component_name)}'
```

**Fix:**
```bash
# Verify file location
ls $AIRFLOW_HOME/dags/{component_file}
ls $AIRFLOW_HOME/plugins/{component_file}

# Check PYTHONPATH
python -c "import sys; print('\\n'.join(sys.path))"

# Ensure Airflow can see the file
airflow config get-value core dags_folder
airflow config get-value core plugins_folder
```

#### Issue 2: Import Error - Missing Dependencies

```
ModuleNotFoundError: No module named 'requests'
```

**Fix:**
```bash
# Install missing dependencies in Airflow environment
pip install <missing_package>

# For Docker, exec into container
docker exec -it <container_name> pip install <missing_package>
```

#### Issue 3: Validation Errors

```
ERROR - Validation failed: Invalid parameter type
```

**Fix:**
- Check parameter types match specification
- Ensure all required parameters are provided
- Review Airflow logs: `airflow tasks test` shows detailed errors

#### Issue 4: Runtime Execution Errors

```
ERROR - Task execution failed
```

**Fix:**
```bash
# Enable debug logging in test DAG
import logging
logging.basicConfig(level=logging.DEBUG)

# Run with verbose output
airflow tasks test test_{self._to_snake_case(component_name)} test_task 2024-01-01 --verbose

# Check task logs in Airflow UI
# Navigate to: DAG → Task → Logs tab
```

### Next Steps

After successful testing:

1. **Remove test DAG** (if created for testing only)
2. **Use component in production DAGs** from DAGs folder or plugins
3. **Monitor first few executions** in Airflow UI
4. **Report issues** to component author for improvements

### Best Practices

- ✅ Always test with `airflow tasks test` before scheduling
- ✅ Use meaningful task_id values for debugging
- ✅ Enable logging in your component for troubleshooting
- ✅ Test with sample data before running on production data
- ✅ Review generated documentation for component-specific requirements
'''

    def _generate_quick_start(self, component_name: str, component_type: str, spec: Dict[str, Any]) -> str:
        """Generate quick start section"""
        inputs = spec.get('inputs', [])
        required_params = [inp for inp in inputs if inp.get('required', False)]

        param_example = self._generate_param_example(required_params)

        if component_type == "operator":
            example = f'''```python
from airflow import DAG
from datetime import datetime
from {self._to_snake_case(component_name)} import {component_name}

with DAG(
    dag_id='example_dag',
    start_date=datetime(2024, 1, 1),
    schedule='@daily',
    catchup=False
) as dag:

    task = {component_name}(
        task_id='my_task',
{param_example}
    )
```'''
        elif component_type == "sensor":
            example = f'''```python
from airflow import DAG
from datetime import datetime
from {self._to_snake_case(component_name)} import {component_name}

with DAG(
    dag_id='example_dag',
    start_date=datetime(2024, 1, 1),
    schedule='@daily',
    catchup=False
) as dag:

    sensor = {component_name}(
        task_id='wait_for_condition',
{param_example}
        poke_interval=60,  # Check every 60 seconds
        timeout=3600,  # Timeout after 1 hour
    )
```'''
        else:  # hook
            example = f'''```python
from {self._to_snake_case(component_name)} import {component_name}

# Initialize hook
hook = {component_name}()

# Get connection
conn = hook.get_conn()

# Use connection for operations
# ... your code here ...
```'''

        return f'''## Quick Start

### Basic Usage

{example}
'''

    def _generate_configuration(self, spec: Dict[str, Any]) -> str:
        """Generate configuration section"""
        inputs = spec.get('inputs', [])
        config_params = spec.get('config_params', [])

        if not inputs and not config_params:
            return "## Configuration\n\nNo configuration parameters required."

        param_docs = []

        if inputs:
            param_docs.append("### Task Parameters\n")
            for inp in inputs:
                name = inp.get('name', '')
                type_hint = inp.get('type', 'str')
                description = inp.get('description', 'No description')
                required = inp.get('required', False)
                default = inp.get('default', 'None')

                req_badge = "**Required**" if required else f"*Optional* (default: `{default}`)"

                param_docs.append(f"#### `{name}` ({type_hint})\n")
                param_docs.append(f"{req_badge}\n")
                param_docs.append(f"{description}\n")

        if config_params:
            param_docs.append("### Configuration Parameters\n")
            for param in config_params:
                name = param.get('name', '')
                type_hint = param.get('type', 'str')
                description = param.get('description', 'No description')
                default = param.get('default', 'None')

                param_docs.append(f"#### `{name}` ({type_hint})\n")
                param_docs.append(f"*Optional* (default: `{default}`)\n")
                param_docs.append(f"{description}\n")

        return f"## Configuration\n\n" + "\n".join(param_docs)

    def _generate_runtime_parameters(self, spec: Dict[str, Any]) -> str:
        """Generate runtime parameters section for UI-driven execution"""
        runtime_params = spec.get('runtime_params', [])

        if not runtime_params:
            return ""  # Return empty string if no runtime params

        param_docs = []
        param_docs.append("## Runtime Parameters\n")
        param_docs.append(
            "This component supports runtime parameters that can be configured via the Airflow UI when triggering the DAG. "
            "This allows you to customize the component's behavior without modifying the DAG code.\n"
        )

        param_docs.append("### Available Parameters\n")

        for param in runtime_params:
            name = param.get('name', '')
            param_type = param.get('type', 'string')
            description = param.get('description', 'No description')
            default = param.get('default', '')
            enum_values = param.get('enum', [])

            # Parameter header
            param_docs.append(f"#### `{name}` ({param_type})\n")

            # Default value
            if isinstance(default, str):
                param_docs.append(f"**Default:** `'{default}'`\n")
            else:
                param_docs.append(f"**Default:** `{default}`\n")

            # Description
            param_docs.append(f"{description}\n")

            # Enum values if present
            if enum_values:
                enum_str = ", ".join([f"`{v}`" for v in enum_values])
                param_docs.append(f"**Allowed values:** {enum_str}\n")

            # Constraints
            constraints = []
            if param.get('min_value') is not None:
                constraints.append(f"minimum: {param['min_value']}")
            if param.get('max_value') is not None:
                constraints.append(f"maximum: {param['max_value']}")
            if param.get('min_length') is not None:
                constraints.append(f"min length: {param['min_length']}")
            if param.get('max_length') is not None:
                constraints.append(f"max length: {param['max_length']}")

            if constraints:
                param_docs.append(f"**Constraints:** {', '.join(constraints)}\n")

        # Usage instructions
        param_docs.append("### How to Use Runtime Parameters\n")
        param_docs.append(
            "When you trigger this DAG via the Airflow UI:\n\n"
            "1. Click the **Play** button (▶️) next to the DAG name\n"
            "2. A form will appear with input fields for each parameter\n"
            "3. Fill in your desired values (or use the defaults)\n"
            "4. Click **Trigger** to run the DAG with those values\n\n"
            "The DAG will use your input values for this specific run.\n"
        )

        # Code example
        param_example_lines = []
        for param in runtime_params:
            name = param.get('name')
            param_example_lines.append(f'        {name}="{{{{ params.{name} }}}}"')

        param_docs.append(
            "### Example in DAG Code\n\n"
            "```python\n"
            "from airflow import DAG\n"
            "from airflow.models.param import Param\n\n"
            "with DAG(\n"
            "    dag_id='my_dag',\n"
            "    params={\n"
        )

        for param in runtime_params:
            name = param.get('name')
            param_type = param.get('type', 'string')
            default = param.get('default', '')
            description = param.get('description', '')

            if isinstance(default, str):
                default_val = f"'{default}'"
            else:
                default_val = str(default)

            type_map = {'string': 'str', 'number': 'number', 'boolean': 'boolean'}
            airflow_type = type_map.get(param_type, 'str')

            param_docs.append(f"        '{name}': Param(default={default_val}, type='{airflow_type}', description='{description}'),\n")

        param_docs.append(
            "    },\n"
            ") as dag:\n"
            "    task = YourOperator(\n"
            "        task_id='my_task',\n"
        )
        param_docs.append("\n".join(param_example_lines))
        param_docs.append(
            "\n    )\n"
            "```\n"
        )

        return "".join(param_docs)

    def _generate_dag_integration(self, component_name: str, component_type: str, spec: Dict[str, Any]) -> str:
        """Generate DAG integration guide"""

        if component_type == "hook":
            return f'''## DAG Integration

### Using in Custom Operators

Hooks are typically used within operators:

```python
from airflow.models import BaseOperator
from {self._to_snake_case(component_name)} import {component_name}

class MyCustomOperator(BaseOperator):
    def execute(self, context):
        hook = {component_name}()
        conn = hook.get_conn()
        # Use connection
        return result
```
'''

        return f'''## DAG Integration

### Task Dependencies

```python
# Sequential execution
task_1 >> task_2 >> {component_name.lower()}_task

# Parallel execution
[task_1, task_2] >> {component_name.lower()}_task

# Fan-in pattern
{component_name.lower()}_task >> [task_3, task_4]
```

### With TaskFlow API

```python
from airflow.decorators import dag, task
from datetime import datetime

@dag(start_date=datetime(2024, 1, 1), schedule='@daily', catchup=False)
def my_pipeline():

    @task
    def prepare_data():
        return {{"data": "value"}}

    # Use the {component_type}
    process_task = {component_name}(
        task_id='process',
        # parameters here
    )

    prepare_data() >> process_task

my_pipeline()
```
'''

    def _generate_api_reference(self, component_name: str, component_type: str, spec: Dict[str, Any]) -> str:
        """Generate API reference"""
        inputs = spec.get('inputs', [])

        if component_type == "operator":
            return f'''## API Reference

### Class: `{component_name}`

Inherits from: `BaseOperator`

#### Constructor

```python
{component_name}(
    task_id: str,
    *args,
    **kwargs
)
```

#### Methods

##### `execute(context: Dict) -> Any`

Executes the operator logic.

**Parameters:**
- `context` (Dict): Airflow context dictionary containing task instance, execution date, etc.

**Returns:**
- Result of the operation (type varies)

#### Attributes

- `template_fields`: List of fields that support Jinja templating
- `ui_color`: Hex color code for UI representation
'''
        elif component_type == "sensor":
            return f'''## API Reference

### Class: `{component_name}`

Inherits from: `BaseSensor`

#### Constructor

```python
{component_name}(
    task_id: str,
    poke_interval: int = 60,
    timeout: int = 604800,
    mode: str = 'poke',
    *args,
    **kwargs
)
```

#### Methods

##### `poke(context: Dict) -> bool`

Checks the condition and returns True if met.

**Parameters:**
- `context` (Dict): Airflow context dictionary

**Returns:**
- `bool`: True if condition is met, False otherwise
'''
        else:  # hook
            return f'''## API Reference

### Class: `{component_name}`

Inherits from: `BaseHook`

#### Constructor

```python
{component_name}(*args, **kwargs)
```

#### Methods

##### `get_conn() -> Any`

Gets or creates connection to external system.

**Returns:**
- Connection object
'''

    def _generate_examples(self, component_name: str, component_type: str, spec: Dict[str, Any]) -> str:
        """Generate examples section"""

        return f'''## Examples

### Example 1: Basic Usage

See [Quick Start](#quick-start) section.

### Example 2: With Error Handling

```python
from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime
from {self._to_snake_case(component_name)} import {component_name}

def handle_failure(context):
    print(f"Task {{context['task_instance'].task_id}} failed")

with DAG(
    dag_id='example_with_error_handling',
    start_date=datetime(2024, 1, 1),
    catchup=False,
    default_args={{
        'on_failure_callback': handle_failure,
        'retries': 3,
    }}
) as dag:

    task = {component_name}(
        task_id='my_task',
        # parameters here
    )
```

### Example 3: Dynamic Task Generation

```python
from airflow import DAG
from datetime import datetime

with DAG(
    dag_id='dynamic_tasks',
    start_date=datetime(2024, 1, 1),
    catchup=False
) as dag:

    items = ['item1', 'item2', 'item3']

    for item in items:
        task = {component_name}(
            task_id=f'process_{{item}}',
            # parameters here
        )
```
'''

    def _generate_troubleshooting(self, component_name: str, component_type: str) -> str:
        """Generate comprehensive troubleshooting and best practices section"""

        return f'''## Troubleshooting

### Common Import and Setup Issues

#### Issue 1: Import Errors - Module Not Found

**Symptoms:**
```
ModuleNotFoundError: No module named '{self._to_snake_case(component_name)}'
```

**Solutions:**

1. **Verify file location:**
```bash
# Check DAGs folder (recommended)
ls -la $AIRFLOW_HOME/dags/{self._to_snake_case(component_name)}.py

# Check plugins folder
ls -la $AIRFLOW_HOME/plugins/{self._to_snake_case(component_name)}.py
```

2. **Check PYTHONPATH:**
```bash
# Verify Airflow's Python path includes your component location
python -c "import sys; print('\\n'.join(sys.path))"

# Check Airflow config
airflow config get-value core dags_folder
airflow config get-value core plugins_folder
```

3. **Docker-specific:**
```bash
# If running in Docker, verify file is inside container
docker exec <container_name> ls /opt/airflow/dags/{self._to_snake_case(component_name)}.py

# Copy file to container if missing
docker cp {self._to_snake_case(component_name)}.py <container_name>:/opt/airflow/dags/
```

4. **Restart Airflow (if using plugins folder):**
```bash
# Plugins folder requires restart
airflow webserver --daemon
airflow scheduler --daemon
```

#### Issue 2: Missing Dependency Errors

**Symptoms:**
```
ModuleNotFoundError: No module named 'requests'
ImportError: cannot import name 'AirflowException'
```

**Solutions:**

1. **Install missing Python packages:**
```bash
# Local installation
pip install <missing_package>

# Docker installation
docker exec <container_name> pip install <missing_package>

# For Airflow providers
pip install apache-airflow-providers-<provider_name>
```

2. **Check Airflow version compatibility:**
```bash
# Check installed Airflow version
airflow version

# Some components require Airflow 2.0+
# Upgrade if needed: pip install --upgrade apache-airflow
```

3. **Virtual environment issues:**
```bash
# Ensure you're using the same Python environment as Airflow
which python
which airflow

# Activate correct environment
source /path/to/airflow/venv/bin/activate
```

#### Issue 3: Validation Errors During Generation

**Symptoms:**
```
ValidationError: Invalid parameter type
TypeError: expected str, got int
AttributeError: 'NoneType' object has no attribute 'execute'
```

**Solutions:**

1. **Check parameter types match specification:**
- Ensure all required parameters are provided
- Verify types: `int`, `str`, `bool`, `list`, `dict`
- Check for None values where not allowed

2. **Review generated code:**
```bash
# Validate Python syntax
python -m py_compile {self._to_snake_case(component_name)}.py

# Run linter for issues
ruff check {self._to_snake_case(component_name)}.py

# Type check (if mypy installed)
mypy --strict {self._to_snake_case(component_name)}.py
```

3. **Inspect validation warnings:**
- Check component generator logs for warnings
- Review validation results in generation response
- Address security issues flagged during generation

### Runtime and Execution Issues

#### Issue 4: Task Execution Failures

**Symptoms:**
```
ERROR - Task failed with exception
AirflowException: Task execution failed
```

**Solutions:**

1. **Enable debug logging in DAG:**
```python
import logging
logging.basicConfig(level=logging.DEBUG)

with DAG(..., default_args={{'owner': 'airflow'}}) as dag:
    # Your tasks here
```

2. **Run task test for detailed output:**
```bash
# Test task execution without scheduler
airflow tasks test <dag_id> <task_id> 2024-01-01 --verbose

# Example for this component
airflow tasks test test_{self._to_snake_case(component_name)} test_task 2024-01-01
```

3. **Check task logs in Airflow UI:**
- Navigate to: **DAG → Task → Logs tab**
- Look for stack traces and error messages
- Check both task log and scheduler log

4. **Verify context variables:**
```python
def execute(self, context):
    # Print available context for debugging
    self.log.info(f"Context keys: {{list(context.keys())}}")
    self.log.info(f"Execution date: {{context['execution_date']}}")
    self.log.info(f"Task instance: {{context['task_instance']}}")
```

#### Issue 5: Template Rendering Failures

**Symptoms:**
```
jinja2.exceptions.UndefinedError: 'params' is undefined
```

**Solutions:**

1. **Verify template_fields are defined:**
```python
# Check if template_fields is properly set
operator = {component_name}(task_id='test')
print(operator.template_fields)  # Should list templated attributes
```

2. **Ensure Jinja syntax is correct:**
```python
# Correct Jinja template
task = {component_name}(
    task_id='my_task',
    some_field="{{{{ params.my_param }}}}"  # Double braces in Python f-string
)
```

3. **Verify params are defined in DAG:**
```python
with DAG(
    dag_id='my_dag',
    params={{
        'my_param': Param(default='value', type='string')
    }}
) as dag:
    task = {component_name}(...)
```

#### Issue 6: XCom Push/Pull Issues

**Symptoms:**
```
ERROR - XCom value not found
KeyError: 'some_key'
```

**Solutions:**

1. **Verify XCom is pushed before pulling:**
```python
# Task 1: Push XCom
def task1_execute(context):
    result = "my_value"
    context['ti'].xcom_push(key='my_key', value=result)
    return result  # Also automatically pushes to 'return_value' key

# Task 2: Pull XCom
def task2_execute(context):
    value = context['ti'].xcom_pull(task_ids='task1', key='my_key')
    if value is None:
        self.log.warning("XCom value not found!")
```

2. **Check XCom in Airflow UI:**
- Navigate to: **Admin → XComs**
- Verify key, task_id, and execution_date match

3. **Handle missing XCom gracefully:**
```python
value = context['ti'].xcom_pull(task_ids='upstream', key='data')
if value is None:
    value = "default_value"  # Use fallback
```

### Performance Considerations

#### Optimize Component Execution Time

1. **Use connection pooling for hooks:**
```python
# Reuse connections instead of creating new ones
hook = {component_name}()
conn = hook.get_conn()  # Connection is cached
```

2. **Batch operations when possible:**
- Process multiple items in single task
- Avoid creating thousands of dynamic tasks
- Use SubDAGs or TaskGroups for organization

3. **Set appropriate timeouts:**
```python
task = {component_name}(
    task_id='my_task',
    execution_timeout=timedelta(minutes=30)  # Prevent hanging
)
```

4. **Monitor resource usage:**
- Check Airflow UI: **Browse → Task Instances → Duration**
- Identify slow tasks and optimize

#### Reduce Airflow Metadata DB Load

1. **Limit DAG file processing:**
```python
# Only parse DAG file when needed (Airflow 2.0+)
if not os.environ.get('AIRFLOW_CTX_DAG_ID'):
    import sys
    sys.exit(0)
```

2. **Use appropriate schedule intervals:**
- Avoid `@continuous` for heavy DAGs
- Use `@hourly` or `@daily` unless real-time needed

3. **Clean up old task instances:**
```bash
# Remove old task instances to reduce DB size
airflow db clean --clean-before-timestamp <timestamp> --yes
```

### Security Best Practices

#### Avoid Hardcoded Credentials

**❌ Don't do this:**
```python
# BAD: Hardcoded credentials
api_key = "sk-1234567890abcdef"  # Security risk!
password = "mypassword123"  # Never hardcode
```

**✅ Do this instead:**
```python
# GOOD: Use Airflow Variables
from airflow.models import Variable

api_key = Variable.get("my_api_key")  # Stored securely in Airflow

# Or use Connections for external services
from airflow.hooks.base import BaseHook

conn = BaseHook.get_connection("my_service_conn")
api_key = conn.password
```

#### Use Airflow Connections for External Services

```bash
# Add connection via CLI
airflow connections add 'my_api' \\
    --conn-type 'http' \\
    --conn-host 'api.example.com' \\
    --conn-password 'your_api_key'

# Or via UI: Admin → Connections → Add
```

#### Enable Secrets Backend (Production)

```python
# airflow.cfg
[secrets]
backend = airflow.providers.hashicorp.secrets.vault.VaultBackend
backend_kwargs = {{"connections_path": "airflow/connections", "url": "http://vault:8200"}}
```

#### Validate Input Parameters

```python
def execute(self, context):
    # Validate inputs to prevent injection attacks
    if not self.some_param:
        raise AirflowException("some_param is required")

    # Sanitize string inputs
    safe_param = str(self.some_param).strip()

    # Validate against whitelist if possible
    allowed_values = ['value1', 'value2']
    if safe_param not in allowed_values:
        raise AirflowException(f"Invalid value: {{safe_param}}")
```

### Component-Specific Debugging

#### For Operators

1. **Test execute() method independently:**
```python
# Create minimal context for testing
from airflow.models import TaskInstance
from unittest.mock import MagicMock

context = {{
    'ti': MagicMock(spec=TaskInstance),
    'execution_date': datetime(2024, 1, 1)
}}

operator = {component_name}(task_id='test')
result = operator.execute(context)
print(f"Result: {{result}}")
```

2. **Check template field rendering:**
```python
# Verify template fields are resolved
operator = {component_name}(task_id='test', some_field="{{{{ ds }}}}")
print(f"Template fields: {{operator.template_fields}}")
```

#### For Sensors

1. **Test poke() method:**
```python
sensor = {component_name}(task_id='test', poke_interval=5, timeout=60)

# Test poke returns boolean
result = sensor.poke(context)
assert isinstance(result, bool), "poke() must return boolean"
```

2. **Adjust timeouts for long-running conditions:**
```python
sensor = {component_name}(
    task_id='wait_for_file',
    timeout=3600,  # 1 hour max wait
    poke_interval=60,  # Check every minute
    mode='reschedule'  # Free up worker slot between pokes
)
```

#### For Hooks

1. **Test connection retrieval:**
```python
hook = {component_name}()

# Verify connection is established
conn = hook.get_conn()
assert conn is not None, "Connection failed"
```

2. **Check connection configuration:**
```bash
# Verify connection exists and is properly configured
airflow connections get my_conn_id
```

### Advanced Debugging Techniques

#### Enable Airflow Debug Mode

```bash
# Set environment variable
export AIRFLOW__LOGGING__LOGGING_LEVEL=DEBUG

# Or in airflow.cfg
[logging]
logging_level = DEBUG
```

#### Use Python Debugger

```python
import pdb

def execute(self, context):
    # Set breakpoint
    pdb.set_trace()

    # Your code here
    result = self.do_something()
    return result
```

#### Profile Component Performance

```python
import cProfile
import pstats

def execute(self, context):
    profiler = cProfile.Profile()
    profiler.enable()

    # Your code here
    result = self.do_something()

    profiler.disable()
    stats = pstats.Stats(profiler)
    stats.sort_stats('cumtime')
    stats.print_stats(10)  # Print top 10 slowest functions

    return result
```

### Getting Additional Help

#### Airflow Resources

- **Official Documentation:** https://airflow.apache.org/docs/
- **Airflow GitHub Issues:** https://github.com/apache/airflow/issues
- **Airflow Slack Community:** https://apache-airflow.slack.com

#### Component Generator Resources

- **Check validation warnings** in generation response
- **Review generated test file** for usage examples
- **Enable verbose logging** in component generator service

#### Reporting Component Issues

If you encounter issues with generated components:

1. **Collect debug information:**
   - Component specification (YAML)
   - Generated code
   - Error messages and stack traces
   - Airflow version: `airflow version`
   - Python version: `python --version`

2. **Check validation results:**
   - Review any warnings from component generator
   - Run static analysis: `mypy`, `ruff`, `pylint`

3. **Contact component author** with:
   - Detailed error description
   - Steps to reproduce
   - Expected vs actual behavior
   - Debug information collected above

### Quick Reference: Debugging Checklist

**Before raising an issue, verify:**

- ✅ Component file is in correct location (`$AIRFLOW_HOME/dags/` or `$AIRFLOW_HOME/plugins/`)
- ✅ All dependencies are installed (`pip list | grep <package>`)
- ✅ Airflow can import the component (`python -c "from {self._to_snake_case(component_name)} import {component_name}"`)
- ✅ DAG file has no syntax errors (`python -m py_compile my_dag.py`)
- ✅ Task can be tested (`airflow tasks test <dag_id> <task_id> 2024-01-01`)
- ✅ Logs have been reviewed (Airflow UI → Logs)
- ✅ Required connections/variables are configured (Admin → Connections/Variables)
- ✅ Parameters match expected types (check spec vs usage)

'''

    def _generate_footer(self, spec: Dict[str, Any]) -> str:
        """Generate documentation footer"""
        version = spec.get('version', '1.0.0')
        author = spec.get('author', 'Airflow Component Factory')

        return f'''---

## Changelog

### Version {version}
- Initial release

---

**Generated by:** Airflow Component Factory
**Author:** {author}
**License:** Apache 2.0

🤖 *This documentation was automatically generated. For issues or improvements, please contact the component author.*
'''

    def _generate_param_example(self, params: List[Dict]) -> str:
        """Generate parameter example code"""
        if not params:
            return "        # No required parameters"

        lines = []
        for param in params:
            name = param.get('name', '')
            type_hint = param.get('type', 'str')

            # Generate sample values
            if 'int' in type_hint.lower():
                value = "123"
            elif 'float' in type_hint.lower():
                value = "45.67"
            elif 'bool' in type_hint.lower():
                value = "True"
            elif 'list' in type_hint.lower():
                value = "['item1', 'item2']"
            elif 'dict' in type_hint.lower():
                value = "{'key': 'value'}"
            else:
                value = f"'sample_{name}'"

            lines.append(f"        {name}={value},")

        return "\n".join(lines)

    def _to_snake_case(self, name: str) -> str:
        """Convert PascalCase to snake_case"""
        import re
        s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
        return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()
