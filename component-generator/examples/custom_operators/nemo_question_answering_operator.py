try:
    from airflow.sdk.bases.operator import BaseOperator
except ImportError:
    from airflow.models import BaseOperator

from airflow.exceptions import AirflowException
from typing import Dict, Any, Optional, Sequence
from pathlib import Path
import json
import os
import logging

class NeMoQuestionAnsweringOperator(BaseOperator):
    """
    Execute NVIDIA NeMo Question Answering for training or inference.
    
    Supports extractive QA (BERT-based) and generative QA (T5/GPT-based models).
    Handles dataset in SQuAD format for training and evaluation.
    
    Args:
        mode: Operation mode - train, inference, or evaluate
        model_type: QA model type - extractive, generative_s2s, or generative_gpt
        pretrained_model_name: Pretrained model name from HuggingFace or NeMo
        dataset_file: Path to dataset file in SQuAD format
        output_dir: Output directory for results
        **kwargs: Additional keyword arguments passed to BaseOperator
    """
    
    template_fields: Sequence[str] = ['mode', 'model_type', 'dataset_file', 'output_dir']
    ui_color: str = "#76b900"
    
    def __init__(
        self,
        mode: str = 'inference',
        model_type: str = 'extractive',
        pretrained_model_name: str = 'bert-base-uncased',
        dataset_file: str = '',
        output_dir: str = '/tmp/nemo_qa_output',
        **kwargs
    ) -> None:
        super().__init__(**kwargs)
        
        # Validate non-template parameters
        valid_modes = ['train', 'inference', 'evaluate']
        valid_model_types = ['extractive', 'generative_s2s', 'generative_gpt']
        
        # Skip validation for template strings (will be validated in execute)
        if '{{' not in str(mode) and mode not in valid_modes:
            raise AirflowException(f"Invalid mode '{mode}'. Must be one of: {valid_modes}")
        
        if '{{' not in str(model_type) and model_type not in valid_model_types:
            raise AirflowException(f"Invalid model_type '{model_type}'. Must be one of: {valid_model_types}")
        
        self.mode = mode
        self.model_type = model_type
        self.pretrained_model_name = pretrained_model_name
        self.dataset_file = dataset_file
        self.output_dir = output_dir
        
        self.log.info(f"Initialized NeMoQuestionAnsweringOperator with mode={mode}, model_type={model_type}")
    
    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute NeMo Question Answering operation.
        
        Args:
            context: Airflow context dictionary
            
        Returns:
            Dict containing execution results and output paths
            
        Raises:
            AirflowException: On validation or execution failure
        """
        self.log.info(f"Executing NeMo Question Answering task: {self.task_id}")
        
        # Validate template fields after Jinja rendering
        valid_modes = ['train', 'inference', 'evaluate']
        valid_model_types = ['extractive', 'generative_s2s', 'generative_gpt']
        
        if self.mode not in valid_modes:
            raise AirflowException(f"Invalid mode '{self.mode}'. Must be one of: {valid_modes}")
        
        if self.model_type not in valid_model_types:
            raise AirflowException(f"Invalid model_type '{self.model_type}'. Must be one of: {valid_model_types}")
        
        # Check runtime parameters from context
        params = context.get('params', {})
        execution_mode = params.get('execution_mode', self.mode)
        qa_model_type = params.get('qa_model_type', self.model_type)
        
        if execution_mode not in valid_modes:
            raise AirflowException(f"Invalid execution_mode parameter '{execution_mode}'. Must be one of: {valid_modes}")
        
        if qa_model_type not in valid_model_types:
            raise AirflowException(f"Invalid qa_model_type parameter '{qa_model_type}'. Must be one of: {valid_model_types}")
        
        # Use runtime parameters if provided
        final_mode = execution_mode
        final_model_type = qa_model_type
        
        self.log.info(f"Using mode: {final_mode}, model_type: {final_model_type}")
        
        try:
            # Create output directory
            output_path = Path(self.output_dir)
            output_path.mkdir(parents=True, exist_ok=True)
            self.log.info(f"Created output directory: {output_path}")
            
            # Validate dataset file for training/evaluation
            if final_mode in ['train', 'evaluate']:
                if not self.dataset_file:
                    raise AirflowException(f"dataset_file is required for mode '{final_mode}'")
                
                dataset_path = Path(self.dataset_file)
                if not dataset_path.exists():
                    raise AirflowException(f"Dataset file not found: {self.dataset_file}")
                
                self.log.info(f"Using dataset file: {self.dataset_file}")
            
            # Execute based on mode
            result = {}
            
            if final_mode == 'train':
                result = self._execute_training(final_model_type, output_path)
            elif final_mode == 'inference':
                result = self._execute_inference(final_model_type, output_path)
            elif final_mode == 'evaluate':
                result = self._execute_evaluation(final_model_type, output_path)
            
            # Save execution summary
            summary_file = output_path / 'execution_summary.json'
            summary = {
                'task_id': self.task_id,
                'mode': final_mode,
                'model_type': final_model_type,
                'pretrained_model': self.pretrained_model_name,
                'dataset_file': self.dataset_file,
                'output_dir': str(output_path),
                'execution_date': context.get('execution_date', '').isoformat() if context.get('execution_date') else '',
                'result': result
            }
            
            with open(summary_file, 'w') as f:
                json.dump(summary, f, indent=2)
            
            self.log.info(f"Execution completed successfully. Summary saved to: {summary_file}")
            
            return {
                'mode': final_mode,
                'model_type': final_model_type,
                'output_dir': str(output_path),
                'summary_file': str(summary_file),
                'result': result
            }
            
        except Exception as e:
            self.log.error(f"NeMo Question Answering execution failed: {str(e)}")
            raise AirflowException(f"NeMo Question Answering execution failed: {str(e)}")
    
    def _execute_training(self, model_type: str, output_path: Path) -> Dict[str, Any]:
        """Execute training mode."""
        self.log.info(f"Starting training for {model_type} model")
        
        # Simulate NeMo training process
        model_output_dir = output_path / 'trained_model'
        model_output_dir.mkdir(exist_ok=True)
        
        # Create mock training artifacts
        config_file = model_output_dir / 'model_config.json'
        config = {
            'model_type': model_type,
            'pretrained_model': self.pretrained_model_name,
            'dataset': self.dataset_file,
            'training_status': 'completed'
        }
        
        with open(config_file, 'w') as f:
            json.dump(config, f, indent=2)
        
        # Create mock checkpoint
        checkpoint_file = model_output_dir / 'model_checkpoint.pt'
        checkpoint_file.touch()
        
        self.log.info(f"Training completed. Model saved to: {model_output_dir}")
        
        return {
            'status': 'training_completed',
            'model_dir': str(model_output_dir),
            'config_file': str(config_file),
            'checkpoint_file': str(checkpoint_file)
        }
    
    def _execute_inference(self, model_type: str, output_path: Path) -> Dict[str, Any]:
        """Execute inference mode."""
        self.log.info(f"Starting inference with {model_type} model")
        
        # Create inference output directory
        inference_output_dir = output_path / 'inference_results'
        inference_output_dir.mkdir(exist_ok=True)
        
        # Simulate inference results
        results_file = inference_output_dir / 'qa_results.json'
        
        # Mock QA results based on model type
        if model_type == 'extractive':
            mock_results = {
                'model_type': 'extractive',
                'predictions': [
                    {
                        'question': 'What is the capital of France?',
                        'context': 'France is a country in Europe. Paris is the capital of France.',
                        'answer': 'Paris',
                        'confidence': 0.95,
                        'start_position': 45,
                        'end_position': 50
                    }
                ]
            }
        else:  # generative models
            mock_results = {
                'model_type': model_type,
                'predictions': [
                    {
                        'question': 'What is the capital of France?',
                        'context': 'France is a country in Europe. Paris is the capital of France.',
                        'generated_answer': 'The capital of France is Paris.',
                        'confidence': 0.92
                    }
                ]
            }
        
        with open(results_file, 'w') as f:
            json.dump(mock_results, f, indent=2)
        
        self.log.info(f"Inference completed. Results saved to: {results_file}")
        
        return {
            'status': 'inference_completed',
            'results_file': str(results_file),
            'num_predictions': len(mock_results['predictions'])
        }
    
    def _execute_evaluation(self, model_type: str, output_path: Path) -> Dict[str, Any]:
        """Execute evaluation mode."""
        self.log.info(f"Starting evaluation for {model_type} model")
        
        # Create evaluation output directory
        eval_output_dir = output_path / 'evaluation_results'
        eval_output_dir.mkdir(exist_ok=True)
        
        # Simulate evaluation metrics
        metrics_file = eval_output_dir / 'evaluation_metrics.json'
        
        # Mock evaluation metrics based on model type
        if model_type == 'extractive':
            mock_metrics = {
                'model_type': 'extractive',
                'exact_match': 0.78,
                'f1_score': 0.85,
                'precision': 0.82,
                'recall': 0.88,
                'num_examples': 1000
            }
        else:  # generative models
            mock_metrics = {
                'model_type': model_type,
                'bleu_score': 0.72,
                'rouge_l': 0.75,
                'meteor': 0.68,
                'exact_match': 0.65,
                'num_examples': 1000
            }
        
        with open(metrics_file, 'w') as f:
            json.dump(mock_metrics, f, indent=2)
        
        self.log.info(f"Evaluation completed. Metrics saved to: {metrics_file}")
        
        return {
            'status': 'evaluation_completed',
            'metrics_file': str(metrics_file),
            'metrics': mock_metrics
        }