# Weather Fetch Operator

**Version:** 1.0.0
**Author:** Component Generator
**Category:** data-fetching
**Component:** WeatherFetchOperator

> Fetches weather data for a specified city (with mock data for testing)


## Table of Contents

- [Overview](#overview)
- [Installation](#installation)
- [Testing & Integration](#testing--integration)
- [Quick Start](#quick-start)
- [Configuration](#configuration)
- [DAG Integration](#dag-integration)
- [API Reference](#api-reference)
- [Examples](#examples)
- [Troubleshooting](#troubleshooting)


## Overview

### Component Type
**Operator**

### Description
Fetches weather data for a specified city (with mock data for testing)

### Features
- Generate realistic mock weather data
- Return temperature, description, humidity, wind speed, etc.
- Push weather data to XCom for downstream tasks
- Support both metric and imperial units
- City-specific temperature ranges for realism

### Use Cases
This operator is suitable for:
- Workflows requiring data-fetching operations
- Data pipelines with operator-based task execution
- Integration with external systems and services


## Installation

### Prerequisites
- Apache Airflow 2.0+
- Python 3.8+

### Install Dependencies

```bash
pip install apache-airflow>=2.0.0
```

### Install Component

1. Copy the component file to your Airflow DAGs folder or plugins directory:

```bash
# Option 1: Place in DAGs folder
cp weather_fetch_operator.py $AIRFLOW_HOME/dags/

# Option 2: Place in plugins folder
cp weather_fetch_operator.py $AIRFLOW_HOME/plugins/
```

2. Restart Airflow webserver and scheduler if needed.


## Testing & Integration

This section helps you validate and integrate the generated component into your Apache Airflow environment.

### Quick Test (No Airflow Installation)

Before integrating with Airflow, you can perform a quick syntax and import validation:

```bash
# Test Python syntax
python -m py_compile weather_fetch_operator.py

# Test imports (without executing)
python -c "import ast; ast.parse(open('weather_fetch_operator.py').read())"

# Check for obvious issues
pylint weather_fetch_operator.py || flake8 weather_fetch_operator.py
```

### Integration with Local Airflow

Choose one of the following methods to integrate this component into your local Airflow setup:

#### Option 1: DAGs Folder (Recommended for Testing)

This is the **simplest and recommended approach** for testing custom components. The DAGs folder is automatically added to `PYTHONPATH` by Airflow.

```bash
# Copy component to DAGs folder
cp weather_fetch_operator.py $AIRFLOW_HOME/dags/

# Verify file is present
ls -la $AIRFLOW_HOME/dags/weather_fetch_operator.py

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
cp weather_fetch_operator.py $AIRFLOW_HOME/plugins/

# Verify file is present
ls -la $AIRFLOW_HOME/plugins/weather_fetch_operator.py

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
  # Then place weather_fetch_operator.py in ./custom_components/
```

Or copy into running container:

```bash
# Copy to running container
docker cp weather_fetch_operator.py <container_name>:/opt/airflow/dags/

# Verify inside container
docker exec <container_name> ls -la /opt/airflow/dags/weather_fetch_operator.py
```

### Testing Commands

Once integrated, test the component with these Airflow CLI commands:

#### 1. Test Component Import

```bash
# Test if Airflow can import the component
python -c "from weather_fetch_operator import WeatherFetchOperator; print('Import successful!')"
```

#### 2. Test Component in Airflow Context

Create a test DAG (`test_weather_fetch_operator.py`) in your DAGs folder:

```python
from airflow import DAG
from datetime import datetime
from weather_fetch_operator import WeatherFetchOperator

with DAG(
    dag_id='test_weather_fetch_operator',
    start_date=datetime(2024, 1, 1),
    schedule=None,  # Manual trigger only
    catchup=False
) as dag:

    test_task = WeatherFetchOperator(
        task_id='test_task',
        # Add required parameters here
    )
```

#### 3. Run Task Test (Without Scheduler)

```bash
# Test task execution without running the scheduler
airflow tasks test test_weather_fetch_operator test_task 2024-01-01
```

This command:
- ✅ Runs the task immediately without scheduling
- ✅ Shows execution output in real-time
- ✅ Doesn't record results in metadata database
- ✅ Perfect for debugging and validation

#### 4. Validate DAG

```bash
# Check if DAG is valid (no import or syntax errors)
airflow dags list | grep test_weather_fetch_operator

# Show detailed DAG info
airflow dags show test_weather_fetch_operator
```

### Common Integration Issues & Fixes

#### Issue 1: Import Error - Module Not Found

```
ModuleNotFoundError: No module named 'weather_fetch_operator'
```

**Fix:**
```bash
# Verify file location
ls $AIRFLOW_HOME/dags/weather_fetch_operator.py
ls $AIRFLOW_HOME/plugins/weather_fetch_operator.py

# Check PYTHONPATH
python -c "import sys; print('\n'.join(sys.path))"

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
airflow tasks test test_weather_fetch_operator test_task 2024-01-01 --verbose

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


## Quick Start

### Basic Usage

```python
from airflow import DAG
from datetime import datetime
from weather_fetch_operator import WeatherFetchOperator

with DAG(
    dag_id='example_dag',
    start_date=datetime(2024, 1, 1),
    schedule='@daily',
    catchup=False
) as dag:

    task = WeatherFetchOperator(
        task_id='my_task',
        city='sample_city',
    )
```


## Configuration

### Task Parameters

#### `city` (str)

**Required**

Name of the city to fetch weather for

#### `country_code` (str)

*Optional* (default: `JP`)

ISO country code (e.g., JP, US, GB)

#### `units` (str)

*Optional* (default: `metric`)

Temperature units: metric or imperial


## Runtime Parameters
This component supports runtime parameters that can be configured via the Airflow UI when triggering the DAG. This allows you to customize the component's behavior without modifying the DAG code.
### Available Parameters
#### `city` (string)
**Default:** `'Tokyo'`
City name to fetch weather for
#### `units` (string)
**Default:** `'metric'`
Temperature units
**Allowed values:** `metric`, `imperial`
### How to Use Runtime Parameters
When you trigger this DAG via the Airflow UI:

1. Click the **Play** button (▶️) next to the DAG name
2. A form will appear with input fields for each parameter
3. Fill in your desired values (or use the defaults)
4. Click **Trigger** to run the DAG with those values

The DAG will use your input values for this specific run.
### Example in DAG Code

```python
from airflow import DAG
from airflow.models.param import Param

with DAG(
    dag_id='my_dag',
    params={
        'city': Param(default='Tokyo', type='str', description='City name to fetch weather for'),
        'units': Param(default='metric', type='str', description='Temperature units'),
    },
) as dag:
    task = YourOperator(
        task_id='my_task',
        city="{{ params.city }}"
        units="{{ params.units }}"
    )
```


## DAG Integration

### Task Dependencies

```python
# Sequential execution
task_1 >> task_2 >> weatherfetchoperator_task

# Parallel execution
[task_1, task_2] >> weatherfetchoperator_task

# Fan-in pattern
weatherfetchoperator_task >> [task_3, task_4]
```

### With TaskFlow API

```python
from airflow.decorators import dag, task
from datetime import datetime

@dag(start_date=datetime(2024, 1, 1), schedule='@daily', catchup=False)
def my_pipeline():

    @task
    def prepare_data():
        return {"data": "value"}

    # Use the operator
    process_task = WeatherFetchOperator(
        task_id='process',
        # parameters here
    )

    prepare_data() >> process_task

my_pipeline()
```


## API Reference

### Class: `WeatherFetchOperator`

Inherits from: `BaseOperator`

#### Constructor

```python
WeatherFetchOperator(
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


## Examples

### Example 1: Basic Usage

See [Quick Start](#quick-start) section.

### Example 2: With Error Handling

```python
from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime
from weather_fetch_operator import WeatherFetchOperator

def handle_failure(context):
    print(f"Task {context['task_instance'].task_id} failed")

with DAG(
    dag_id='example_with_error_handling',
    start_date=datetime(2024, 1, 1),
    catchup=False,
    default_args={
        'on_failure_callback': handle_failure,
        'retries': 3,
    }
) as dag:

    task = WeatherFetchOperator(
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
        task = WeatherFetchOperator(
            task_id=f'process_{item}',
            # parameters here
        )
```


## Troubleshooting

### Common Issues

#### Import Errors

If you see import errors:

```bash
# Verify component file is in correct location
ls $AIRFLOW_HOME/dags/
# or
ls $AIRFLOW_HOME/plugins/

# Check Python path
python -c "import sys; print(sys.path)"
```

#### Connection Issues

For connection-related errors:

1. Check Airflow connections:
```bash
airflow connections list
```

2. Add connection via CLI:
```bash
airflow connections add 'my_conn' \
    --conn-type 'http' \
    --conn-host 'localhost' \
    --conn-port '8080'
```

3. Or via UI: Admin → Connections → Add

#### Task Failures

Enable debug logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

Check task logs in Airflow UI:
- Navigate to DAG → Task → Logs

### Getting Help

- Check Airflow documentation: https://airflow.apache.org/docs/
- Review task logs in Airflow UI
- Enable debug mode for detailed output


---

## Changelog

### Version 1.0.0
- Initial release

---

**Generated by:** Airflow Component Factory
**Author:** Component Generator
**License:** Apache 2.0

🤖 *This documentation was automatically generated. For issues or improvements, please contact the component author.*
