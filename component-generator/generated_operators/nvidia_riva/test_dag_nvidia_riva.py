"""
Test DAG for NvidiaRivaOperator

Operator for NVIDIA Riva conversational AI - supports speech-to-text (ASR), text-to-speech (TTS), and NLP inference using Riva API

This DAG demonstrates the custom NvidiaRivaOperator with runtime parameter support.
Users can input values via the Airflow UI when triggering this DAG.

IMPORTANT: Both this file AND nvidia_riva_operator.py must be in the same folder (e.g., dags/).
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
    from nvidia_riva_operator import NvidiaRivaOperator
except ImportError:
    # Option 2: Try importing from custom_operators subfolder
    try:
        from custom_operators.nvidia_riva_operator import NvidiaRivaOperator
    except ImportError:
        # Option 3: Try importing from plugins
        try:
            from plugins.nvidia_riva_operator import NvidiaRivaOperator
        except ImportError:
            raise ImportError(
                "Could not import NvidiaRivaOperator. "
                "Please ensure 'nvidia_riva_operator.py' is in one of these locations:\n"
                "  1. Same folder as this DAG file\n"
                "  2. $AIRFLOW_HOME/dags/custom_operators/\n"
                "  3. $AIRFLOW_HOME/plugins/"
            )

# Default arguments for the DAG
default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2024, 1, 1),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

# Create the DAG with runtime parameters
with DAG(
    dag_id='test_nvidia_riva_operator',
    default_args=default_args,
    description='Operator for NVIDIA Riva conversational AI - supports speech-to-text (ASR), text-to-speech (TTS), and NLP inference using Riva API',
    schedule=None,  # Manual trigger only for testing
    catchup=False,
    tags=['test', 'custom-component', 'operator', 'nvidia', 'riva', 'speech-ai'],
    params={
        # NOTE: Default to 'nlp' operation since it doesn't require audio files
        'operation_type': Param(
            default='nlp',
            type='string',
            description='Select the Riva operation type (nlp recommended for testing)',
            enum=["asr", "tts", "nlp"]
        ),
        'language_code': Param(
            default='en-US',
            type='string',
            description='Language code for processing'
        ),
        'text_input': Param(
            default='Hello, this is a test message for NVIDIA Riva NLP analysis.',
            type='string',
            description='Text input for NLP or TTS operations'
        ),
    },
) as dag:

    # Create task using runtime parameters
    # NOTE: Using NLP operation by default since ASR requires audio files
    test_task = NvidiaRivaOperator(
        task_id='test_nvidia_riva_operator_task',
        riva_server_url='localhost:50051',  # Update with your Riva server URL
        operation_type="{{ params.operation_type }}",
        language_code="{{ params.language_code }}",
        text_input="{{ params.text_input }}",  # Required for NLP and TTS
        # For ASR operation, you must provide audio_file_path:
        # audio_file_path='/path/to/audio.wav',
        # For TTS operation, you must also provide output_path:
        # output_path='/path/to/output.wav',
    )

# ============================================================================
# SETUP INSTRUCTIONS
# ============================================================================
#
# 1. Copy BOTH files to your Airflow dags folder:
#    cp nvidia_riva_operator.py $AIRFLOW_HOME/dags/
#    cp test_dag_nvidia_riva.py $AIRFLOW_HOME/dags/
#
# 2. Or create a custom_operators subfolder:
#    mkdir -p $AIRFLOW_HOME/dags/custom_operators
#    cp nvidia_riva_operator.py $AIRFLOW_HOME/dags/custom_operators/
#    touch $AIRFLOW_HOME/dags/custom_operators/__init__.py
#    cp test_dag_nvidia_riva.py $AIRFLOW_HOME/dags/
#
# TESTING:
#
# Via UI:
#   1. Access http://localhost:8080
#   2. Find DAG: test_nvidia_riva_operator
#   3. Click "Trigger DAG" (play button)
#   4. Fill in the parameter form with your values
#   5. Click "Trigger" to run with those inputs
#
# OPERATION TYPES:
#   - nlp: Natural Language Processing (default - no files required)
#   - tts: Text-to-Speech (requires text_input and output_path)
#   - asr: Speech-to-Text (requires audio_file_path)
#
# Via CLI:
#   airflow dags test test_nvidia_riva_operator 2024-01-01
