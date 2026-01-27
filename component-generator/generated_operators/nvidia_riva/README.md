# NVIDIA Riva Speech AI Operator

**Version:** 1.0.0
**Author:** Airflow Component Factory
**Category:** ml
**Component:** NvidiaRivaOperator

> Operator for NVIDIA Riva conversational AI - supports speech-to-text (ASR), text-to-speech (TTS), and NLP inference using Riva API


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
Operator for NVIDIA Riva conversational AI - supports speech-to-text (ASR), text-to-speech (TTS), and NLP inference using Riva API

### Features
- Speech-to-Text (ASR) transcription
- Text-to-Speech (TTS) synthesis
- NLP inference and analysis
- Secure gRPC connections with SSL support
- Multiple language support
- Runtime parameters for UI-configurable DAGs (Airflow 3.x compatible)

### Use Cases
This operator is suitable for:
- Workflows requiring ML/AI speech operations
- Data pipelines with voice transcription needs
- Integration with NVIDIA Riva services
- Building conversational AI applications


## Installation

### Prerequisites
- Apache Airflow 2.0+ (recommended: 3.x)
- Python 3.8+
- NVIDIA Riva server running and accessible

### Install Dependencies

```bash
pip install grpcio>=1.50.0
pip install protobuf>=4.0.0
```

### Install Component

1. Copy the component file to your Airflow DAGs folder or plugins directory:

```bash
# Option 1: Place in DAGs folder
cp nvidia_riva_operator.py $AIRFLOW_HOME/dags/

# Option 2: Place in plugins folder
cp nvidia_riva_operator.py $AIRFLOW_HOME/plugins/
```

2. Restart Airflow webserver and scheduler if needed.


## Testing & Integration

This section helps you validate and integrate the generated component into your Apache Airflow environment.

### Quick Test (No Airflow Installation)

Before integrating with Airflow, you can perform a quick syntax and import validation:

```bash
# Test Python syntax
python -m py_compile nvidia_riva_operator.py

# Test imports (without executing)
python -c "import ast; ast.parse(open('nvidia_riva_operator.py').read())"

# Check for obvious issues
pylint nvidia_riva_operator.py || flake8 nvidia_riva_operator.py
```

### Integration with Local Airflow

Choose one of the following methods to integrate this component into your local Airflow setup:

#### Option 1: DAGs Folder (Recommended for Testing)

This is the **simplest and recommended approach** for testing custom components. The DAGs folder is automatically added to `PYTHONPATH` by Airflow.

```bash
# Copy component to DAGs folder
cp nvidia_riva_operator.py $AIRFLOW_HOME/dags/

# Verify file is present
ls -la $AIRFLOW_HOME/dags/nvidia_riva_operator.py

# No restart needed - Airflow auto-detects files in DAGs folder
```

**Pros:**
- No Airflow restart required
- Automatically on PYTHONPATH
- Perfect for rapid iteration and testing
- Can create test DAG in same folder

**Cons:**
- Less organized for reusable components
- Mixed with DAG definitions

#### Option 2: Plugins Folder (For Reusable Components)

Use this approach when you want to make components available across multiple DAGs.

```bash
# Copy component to plugins folder
cp nvidia_riva_operator.py $AIRFLOW_HOME/plugins/

# Verify file is present
ls -la $AIRFLOW_HOME/plugins/nvidia_riva_operator.py

# Restart Airflow services (required for plugins)
airflow webserver --daemon
airflow scheduler --daemon
```

#### Option 3: Docker Volume Mounting (For Containerized Airflow)

If you're running Airflow in Docker, mount the component directory:

```yaml
# Add to docker-compose.yml or docker run command
volumes:
  - ./custom_components:/opt/airflow/dags/custom_components
  # Then place nvidia_riva_operator.py in ./custom_components/
```

Or copy into running container:

```bash
# Copy to running container
docker cp nvidia_riva_operator.py <container_name>:/opt/airflow/dags/

# Verify inside container
docker exec <container_name> ls -la /opt/airflow/dags/nvidia_riva_operator.py
```

### Testing Commands

Once integrated, test the component with these Airflow CLI commands:

#### 1. Test Component Import

```bash
# Test if Airflow can import the component
python -c "from nvidia_riva_operator import NvidiaRivaOperator; print('Import successful!')"
```

#### 2. Run Task Test (Without Scheduler)

```bash
# Test task execution without running the scheduler
airflow tasks test test_nvidia_riva_operator test_nvidia_riva_operator_task 2024-01-01
```


## Quick Start

### Basic Usage

```python
from airflow import DAG
from datetime import datetime
from nvidia_riva_operator import NvidiaRivaOperator

with DAG(
    dag_id='example_dag',
    start_date=datetime(2024, 1, 1),
    schedule='@daily',
    catchup=False
) as dag:

    # NLP operation (default - no files required)
    task = NvidiaRivaOperator(
        task_id='my_task',
        riva_server_url='localhost:50051',
        operation_type='nlp',
        text_input='Analyze this text for sentiment and entities.',
        language_code='en-US',
    )
```


## Configuration

### Task Parameters

#### `riva_server_url` (str)

**Required**

NVIDIA Riva server gRPC endpoint (e.g., localhost:50051)

#### `operation_type` (str)

**Required**

Type of Riva operation: asr (speech-to-text), tts (text-to-speech), or nlp

#### `audio_file_path` (str)

*Optional* (default: `None`)

Path to audio file for ASR transcription (WAV format recommended)

#### `text_input` (str)

*Optional* (default: `None`)

Text input for TTS or NLP operations

#### `language_code` (str)

*Optional* (default: `en-US`)

Language code for processing (e.g., en-US)

#### `sample_rate` (int)

*Optional* (default: `16000`)

Audio sample rate in Hz

#### `output_path` (str)

*Optional* (default: `None`)

Output path for TTS audio file

#### `model_name` (str)

*Optional* (default: `None`)

Specific Riva model to use (optional)

#### `ssl_cert_path` (str)

*Optional* (default: `None`)

Path to SSL certificate for secure connections


## Runtime Parameters

This component supports runtime parameters that can be configured via the Airflow UI when triggering the DAG.

### Available Parameters

#### `operation_type` (string)
**Default:** `'nlp'`
Select the Riva operation type (nlp recommended for testing - doesn't require files)
**Allowed values:** `asr`, `tts`, `nlp`

#### `language_code` (string)
**Default:** `'en-US'`
Language code for processing

#### `text_input` (string)
**Default:** `'Hello, this is a test message for NVIDIA Riva NLP analysis.'`
Text input for NLP or TTS operations

### How to Use Runtime Parameters

When you trigger this DAG via the Airflow UI:

1. Click the **Play** button next to the DAG name
2. A form will appear with input fields for each parameter
3. Fill in your desired values (or use the defaults)
4. Click **Trigger** to run the DAG with those values


## DAG Integration

### Task Dependencies

```python
# Sequential execution
task_1 >> task_2 >> nvidiarivaoperator_task

# Parallel execution
[task_1, task_2] >> nvidiarivaoperator_task

# Fan-in pattern
nvidiarivaoperator_task >> [task_3, task_4]
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
    process_task = NvidiaRivaOperator(
        task_id='process',
        riva_server_url='localhost:50051',
        operation_type='nlp',
        text_input='Process this text',
    )

    prepare_data() >> process_task

my_pipeline()
```


## API Reference

### Class: `NvidiaRivaOperator`

Inherits from: `BaseOperator`

#### Constructor

```python
NvidiaRivaOperator(
    task_id: str,
    riva_server_url: str,
    operation_type: str,
    audio_file_path: Optional[str] = None,
    text_input: Optional[str] = None,
    language_code: Optional[str] = "en-US",
    sample_rate: Optional[int] = 16000,
    output_path: Optional[str] = None,
    model_name: Optional[str] = None,
    ssl_cert_path: Optional[str] = None,
    **kwargs
)
```

#### Methods

##### `execute(context: Dict) -> Any`

Executes the operator logic.

**Parameters:**
- `context` (Dict): Airflow context dictionary containing task instance, execution date, etc.

**Returns:**
- For ASR: Transcribed text (str)
- For TTS: Output file path (str)
- For NLP: Analysis results (dict)

#### Attributes

- `template_fields`: `['operation_type', 'language_code', 'text_input', 'audio_file_path', 'output_path', 'model_name']`
- `ui_color`: `#76B900` (NVIDIA green)


## Examples

### Example 1: Speech-to-Text (ASR)

```python
from airflow import DAG
from datetime import datetime
from nvidia_riva_operator import NvidiaRivaOperator

with DAG(
    dag_id='riva_asr_example',
    start_date=datetime(2024, 1, 1),
    schedule='@daily',
    catchup=False
) as dag:

    transcribe_audio = NvidiaRivaOperator(
        task_id='transcribe_audio',
        riva_server_url='localhost:50051',
        operation_type='asr',
        audio_file_path='/data/audio/recording.wav',
        language_code='en-US',
    )
```

### Example 2: Text-to-Speech (TTS)

```python
from airflow import DAG
from datetime import datetime
from nvidia_riva_operator import NvidiaRivaOperator

with DAG(
    dag_id='riva_tts_example',
    start_date=datetime(2024, 1, 1),
    schedule='@daily',
    catchup=False
) as dag:

    synthesize_speech = NvidiaRivaOperator(
        task_id='synthesize_speech',
        riva_server_url='localhost:50051',
        operation_type='tts',
        text_input='Hello, welcome to NVIDIA Riva text-to-speech.',
        output_path='/data/audio/output.wav',
        language_code='en-US',
        sample_rate=22050,
    )
```

### Example 3: NLP Analysis

```python
from airflow import DAG
from datetime import datetime
from nvidia_riva_operator import NvidiaRivaOperator

with DAG(
    dag_id='riva_nlp_example',
    start_date=datetime(2024, 1, 1),
    schedule='@daily',
    catchup=False
) as dag:

    analyze_text = NvidiaRivaOperator(
        task_id='analyze_text',
        riva_server_url='localhost:50051',
        operation_type='nlp',
        text_input='I need to book a flight to New York next Monday.',
        language_code='en-US',
    )
```


## Troubleshooting

### Common Issues

#### Connection Error to Riva Server

```
AirflowException: Failed to connect to Riva server: localhost:50051
```

**Fix:**
- Verify Riva server is running: `docker ps | grep riva`
- Check network connectivity: `telnet localhost 50051`
- Ensure correct server URL and port

#### Missing Audio File

```
AirflowException: Audio file not found: /path/to/audio.wav
```

**Fix:**
- Verify file exists and path is correct
- Check file permissions
- For Docker, ensure volume is mounted correctly

#### Import Errors

```
ModuleNotFoundError: No module named 'grpc'
```

**Fix:**
```bash
pip install grpcio>=1.50.0
pip install protobuf>=4.0.0
```

#### Airflow 3.x Param Deprecation Warning

If you see:
```
DeprecationWarning: airflow.models.param.Param is deprecated
```

The test DAG included with this operator already uses Airflow 3.x compatible imports:
```python
try:
    from airflow.sdk import Param  # Airflow 3.x
except ImportError:
    from airflow.models.param import Param  # Airflow 2.x fallback
```

### Getting Help

- NVIDIA Riva Documentation: https://docs.nvidia.com/deeplearning/riva/
- Apache Airflow Documentation: https://airflow.apache.org/docs/


---

## Changelog

### Version 1.0.0
- Initial release
- Support for ASR, TTS, and NLP operations
- SSL/TLS connection support
- Runtime parameter support
- Airflow 3.x Task SDK compatibility

---

**Generated by:** Airflow Component Factory
**License:** Apache 2.0

*This documentation was automatically generated. For issues or improvements, please contact the component author.*
