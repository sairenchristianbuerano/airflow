# Airflow Local Setup - NeMo Question Answering Operator

This guide helps you set up and test the generated NeMo Question Answering Operator in your local Airflow environment.

## Generated Files

### 1. Operator Files
- **[custom_operators/nemo_question_answering_operator.py](custom_operators/nemo_question_answering_operator.py)** (11.5 KB)
  - Complete operator implementation
  - Supports train, inference, and evaluate modes
  - Runtime parameter support for UI configuration
  - Airflow 2.x/3.x dual compatibility

- **[custom_operators/test_nemo_question_answering_operator.py](custom_operators/test_nemo_question_answering_operator.py)** (7.5 KB)
  - Comprehensive pytest test suite
  - XCom testing with fixtures
  - Edge case coverage

### 2. Test DAG
- **[dags/test_nemo_qa_operator.py](dags/test_nemo_qa_operator.py)**
  - Demonstrates operator usage
  - 3 example tasks (inference, generative, static)
  - Runtime parameters configured
  - Manual trigger only (schedule=None)

### 3. Documentation
- **[sample_test.json](sample_test.json)** - Full generation output (46.9 KB)
  - Complete code
  - 26 KB of comprehensive documentation
  - Test suite

## Prerequisites

### Required
- Python 3.8+
- Apache Airflow 2.0+ (recommended: 2.8+)

### Optional
- NVIDIA NeMo Toolkit (for actual execution)
- PyTorch 2.0+
- Transformers 4.30+

## Installation Options

Choose one of the following installation methods based on your setup:

### Option 1: Standalone Testing (No Airflow Installation Required)

Test the operator without installing Airflow:

```bash
# 1. Navigate to repo directory
cd ~/Desktop/sairen-files/github/repo/airflow

# 2. Test Python syntax
python -m py_compile custom_operators/nemo_question_answering_operator.py

# 3. Test imports
python -c "from custom_operators import NeMoQuestionAnsweringOperator; print('✅ Import successful!')"

# 4. Run pytest tests (if pytest installed)
pytest custom_operators/test_nemo_question_answering_operator.py -v
```

### Option 2: Local Airflow Installation

If you have Airflow installed locally:

#### Step 1: Set AIRFLOW_HOME

```bash
# Set AIRFLOW_HOME (if not already set)
export AIRFLOW_HOME=~/airflow

# Verify
echo $AIRFLOW_HOME
```

#### Step 2: Copy Files to Airflow DAGs Folder (Recommended)

```bash
# Create custom_operators directory in DAGs folder
mkdir -p $AIRFLOW_HOME/dags/custom_operators

# Copy operator files
cp -r custom_operators/* $AIRFLOW_HOME/dags/custom_operators/

# Copy test DAG
cp dags/test_nemo_qa_operator.py $AIRFLOW_HOME/dags/

# Verify files are in place
ls -la $AIRFLOW_HOME/dags/custom_operators/
ls -la $AIRFLOW_HOME/dags/test_nemo_qa_operator.py
```

#### Step 3: Verify DAG is Detected

```bash
# List all DAGs (should include test_nemo_qa_operator)
airflow dags list | grep test_nemo_qa_operator

# Show DAG structure
airflow dags show test_nemo_qa_operator

# Check for import errors
airflow dags list-import-errors
```

#### Step 4: Test Task Execution

```bash
# Test a single task without running the scheduler
airflow tasks test test_nemo_qa_operator nemo_qa_inference 2024-01-01

# Run with verbose output for debugging
airflow tasks test test_nemo_qa_operator nemo_qa_inference 2024-01-01 --verbose
```

### Option 3: Airflow Plugins Folder (For Reusable Components)

For making the operator available across multiple DAGs:

```bash
# Create plugins directory structure
mkdir -p $AIRFLOW_HOME/plugins/custom_operators

# Copy operator
cp custom_operators/nemo_question_answering_operator.py $AIRFLOW_HOME/plugins/custom_operators/
cp custom_operators/__init__.py $AIRFLOW_HOME/plugins/custom_operators/

# Copy test DAG
cp dags/test_nemo_qa_operator.py $AIRFLOW_HOME/dags/

# Restart Airflow (required for plugins)
airflow webserver --daemon
airflow scheduler --daemon
```

### Option 4: Docker Airflow Setup

If running Airflow in Docker:

```bash
# Find your Airflow container
docker ps | grep airflow

# Copy files to container
docker cp custom_operators <container_name>:/opt/airflow/dags/
docker cp dags/test_nemo_qa_operator.py <container_name>:/opt/airflow/dags/

# Verify files inside container
docker exec <container_name> ls -la /opt/airflow/dags/custom_operators/
docker exec <container_name> ls -la /opt/airflow/dags/test_nemo_qa_operator.py

# Test DAG inside container
docker exec <container_name> airflow dags list | grep test_nemo_qa_operator
```

## Usage

### 1. Trigger DAG via Airflow UI

1. Open Airflow UI: http://localhost:8080
2. Find DAG: `test_nemo_qa_operator`
3. Click **Play** button (▶️)
4. **Configure Runtime Parameters:**
   - `execution_mode`: Choose from train, inference, evaluate
   - `qa_model_type`: Choose from extractive, generative_s2s, generative_gpt
   - `custom_output_dir`: Specify output directory
5. Click **Trigger**

### 2. Trigger DAG via CLI

```bash
# Trigger with default parameters
airflow dags trigger test_nemo_qa_operator

# Trigger with custom parameters
airflow dags trigger test_nemo_qa_operator \
  --conf '{"execution_mode": "inference", "qa_model_type": "extractive", "custom_output_dir": "/tmp/my_output"}'

# Check DAG run status
airflow dags list-runs -d test_nemo_qa_operator
```

### 3. Use in Your Own DAG

Create a new DAG file in `$AIRFLOW_HOME/dags/my_custom_dag.py`:

```python
from datetime import datetime
from airflow import DAG
import sys
import os

# Add custom_operators to path (if in DAGs folder)
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from custom_operators import NeMoQuestionAnsweringOperator

with DAG(
    dag_id='my_nemo_pipeline',
    start_date=datetime(2024, 1, 1),
    schedule='@daily',
    catchup=False
) as dag:

    qa_task = NeMoQuestionAnsweringOperator(
        task_id='question_answering',
        mode='inference',
        model_type='extractive',
        pretrained_model_name='bert-base-uncased',
        output_dir='/tmp/nemo_output',
    )
```

## Testing

### Run Unit Tests

```bash
# Install pytest if not already installed
pip install pytest pytest-mock

# Run all tests
cd ~/Desktop/sairen-files/github/repo/airflow
pytest custom_operators/test_nemo_question_answering_operator.py -v

# Run specific test
pytest custom_operators/test_nemo_question_answering_operator.py::TestNeMoQuestionAnsweringOperator::test_operator_initialization -v

# Run with coverage
pytest custom_operators/test_nemo_question_answering_operator.py --cov=custom_operators --cov-report=html
```

### Test Task Execution

```bash
# Test single task (doesn't require scheduler)
airflow tasks test test_nemo_qa_operator nemo_qa_inference 2024-01-01

# Test with specific execution date
airflow tasks test test_nemo_qa_operator nemo_qa_static 2024-01-15

# Run DAG backfill for a date range
airflow dags backfill test_nemo_qa_operator --start-date 2024-01-01 --end-date 2024-01-01
```

## Troubleshooting

### Issue 1: Module Not Found

**Error:**
```
ModuleNotFoundError: No module named 'custom_operators'
```

**Fix:**
```bash
# Option A: Ensure files are in DAGs folder
ls $AIRFLOW_HOME/dags/custom_operators/

# Option B: Check Python path in DAG file
# The DAG should have: sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Option C: Verify __init__.py exists
ls $AIRFLOW_HOME/dags/custom_operators/__init__.py
```

### Issue 2: Import Errors

**Check for import errors:**
```bash
# List import errors
airflow dags list-import-errors

# Test Python import directly
python -c "from custom_operators import NeMoQuestionAnsweringOperator; print('Success!')"
```

### Issue 3: Task Execution Fails

**View detailed logs:**
```bash
# Run task with verbose output
airflow tasks test test_nemo_qa_operator nemo_qa_inference 2024-01-01 --verbose

# Check logs in UI
# Navigate to: DAG → Task → Logs tab
```

### Issue 4: Runtime Parameters Not Working

**Verify params in DAG:**
```python
# In your DAG file, ensure params are defined:
with DAG(
    ...,
    params={
        'execution_mode': Param(default='inference', type='string', ...),
    }
) as dag:
    task = NeMoQuestionAnsweringOperator(
        mode="{{ params.execution_mode }}",  # Use Jinja template
        ...
    )
```

## Directory Structure

```
~/Desktop/sairen-files/github/repo/airflow/
├── custom_operators/
│   ├── __init__.py
│   ├── nemo_question_answering_operator.py  (11.5 KB)
│   └── test_nemo_question_answering_operator.py  (7.5 KB)
├── dags/
│   └── test_nemo_qa_operator.py
├── sample_test.json  (46.9 KB - full generation output)
├── AIRFLOW_SETUP.md  (this file)
└── PARAMETER_ORDERING_FIX.md
```

## Next Steps

1. **Install Dependencies** (for actual NeMo execution):
   ```bash
   pip install nemo-toolkit[nlp]>=1.20.0
   pip install torch>=2.0.0
   pip install transformers>=4.30.0
   ```

2. **Start Airflow** (if not running):
   ```bash
   # Initialize database (first time only)
   airflow db init

   # Create admin user (first time only)
   airflow users create \
     --username admin \
     --password admin \
     --firstname Admin \
     --lastname User \
     --role Admin \
     --email admin@example.com

   # Start webserver and scheduler
   airflow webserver --port 8080
   airflow scheduler
   ```

3. **Access Airflow UI**:
   - URL: http://localhost:8080
   - Username: admin
   - Password: admin

4. **Trigger Test DAG**: Find `test_nemo_qa_operator` and trigger it

5. **Customize**: Modify the operator or create your own DAGs using this operator

## Additional Resources

- **Generated Documentation**: See `sample_test.json` (documentation field) for comprehensive usage guide
- **Component Spec**: See `component_spec_simple.yaml` for the YAML specification used to generate this operator
- **Parameter Ordering Fix**: See `PARAMETER_ORDERING_FIX.md` for details on the recent fix

## Getting Help

If you encounter issues:

1. Check the troubleshooting section above
2. Review Airflow logs: `$AIRFLOW_HOME/logs/`
3. Test operator import: `python -c "from custom_operators import NeMoQuestionAnsweringOperator"`
4. Verify DAG syntax: `python dags/test_nemo_qa_operator.py`
5. Check Airflow version compatibility: `airflow version`

---

**Generated by:** Airflow Component Generator
**Date:** 2026-01-20
**Component:** NeMoQuestionAnsweringOperator
**Status:** ✅ Ready for testing
