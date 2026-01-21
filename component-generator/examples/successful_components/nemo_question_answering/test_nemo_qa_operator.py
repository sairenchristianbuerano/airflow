"""
Test DAG for NeMo Question Answering Operator

This DAG demonstrates the usage of the NeMoQuestionAnsweringOperator
with runtime parameters for interactive execution.
"""

from datetime import datetime, timedelta
from airflow import DAG
from airflow.models.param import Param

# Import the operator directly from the module file
from custom_operators.nemo_question_answering_operator import NeMoQuestionAnsweringOperator


# Default arguments for the DAG
default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

# Define the DAG with runtime parameters
with DAG(
    dag_id='test_nemo_qa_operator',
    default_args=default_args,
    description='Test DAG for NVIDIA NeMo Question Answering Operator',
    schedule=None,  # Manual trigger only
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=['test', 'nemo', 'ml', 'question-answering'],
    params={
        # Runtime parameters - configurable via UI when triggering DAG
        'execution_mode': Param(
            default='inference',
            type='string',
            enum=['train', 'inference', 'evaluate'],
            description='Select the execution mode'
        ),
        'qa_model_type': Param(
            default='extractive',
            type='string',
            enum=['extractive', 'generative_s2s', 'generative_gpt'],
            description='Select the QA model architecture'
        ),
        'custom_output_dir': Param(
            default='/opt/airflow/logs/nemo_qa_output',
            type='string',
            description='Custom output directory for results'
        ),
    },
) as dag:

    # Task 1: Inference with BERT (extractive QA)
    inference_task = NeMoQuestionAnsweringOperator(
        task_id='nemo_qa_inference',
        mode="{{ params.execution_mode }}",  # Uses runtime parameter
        model_type="{{ params.qa_model_type }}",  # Uses runtime parameter
        pretrained_model_name='bert-base-uncased',
        output_dir="{{ params.custom_output_dir }}",
    )

    # Task 2: Example with different model (generative QA)
    generative_task = NeMoQuestionAnsweringOperator(
        task_id='nemo_qa_generative',
        mode='inference',
        model_type='generative_s2s',
        pretrained_model_name='t5-small',
        output_dir='/opt/airflow/logs/nemo_qa_generative',
    )

    # Task 3: Example with hardcoded values (no runtime params)
    static_task = NeMoQuestionAnsweringOperator(
        task_id='nemo_qa_static',
        mode='inference',
        model_type='extractive',
        pretrained_model_name='bert-base-uncased',
        dataset_file='',
        output_dir='/opt/airflow/logs/nemo_qa_static',
    )

    # Define task dependencies
    # Run inference_task first, then run the other two in parallel
    inference_task >> [generative_task, static_task]


if __name__ == "__main__":
    dag.test()
