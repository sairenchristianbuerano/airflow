from airflow.models import BaseOperator
from airflow.exceptions import AirflowException
from typing import Dict, Any, Optional, List, Sequence, Union
import pandas as pd
import re
from pathlib import Path
import json

class DataValidationOperator(BaseOperator):
    """
    Operator for validating data quality with configurable rules including null checks, 
    range validation, and regex patterns.
    
    This operator supports various validation rules:
    - null_check: Check for null/missing values
    - range_check: Validate numeric values within specified ranges
    - regex_pattern: Validate string values against regex patterns
    - unique_check: Check for duplicate values
    - length_check: Validate string length constraints
    
    Args:
        data_source (str): Path or connection to data source (CSV, JSON, or database connection)
        validation_rules (list): List of validation rule dictionaries. Each rule should contain:
            - column: Column name to validate
            - rule_type: Type of validation (null_check, range_check, regex_pattern, unique_check, length_check)
            - parameters: Rule-specific parameters
        fail_on_error (bool): Whether to fail the task on validation errors. Default is True.
        output_report (str): Optional path to save validation report as JSON
    
    Example validation_rules:
        [
            {"column": "age", "rule_type": "range_check", "parameters": {"min": 0, "max": 120}},
            {"column": "email", "rule_type": "regex_pattern", "parameters": {"pattern": r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"}},
            {"column": "name", "rule_type": "null_check", "parameters": {}},
            {"column": "id", "rule_type": "unique_check", "parameters": {}}
        ]
    """
    
    template_fields: Sequence[str] = ['data_source', 'output_report', 'fail_on_error']
    ui_color: str = "#f0ede4"
    
    def __init__(
        self,
        data_source: str,
        validation_rules: List[Dict[str, Any]],
        fail_on_error: bool = True,
        output_report: Optional[str] = None,
        **kwargs
    ):
        super().__init__(**kwargs)
        
        # Store parameters
        self.data_source = data_source
        self.validation_rules = validation_rules
        self.fail_on_error = fail_on_error
        self.output_report = output_report
        
        # Validate non-template parameters
        if not validation_rules:
            raise AirflowException("validation_rules cannot be empty")
        
        # Validate validation rules structure
        for i, rule in enumerate(validation_rules):
            if not isinstance(rule, dict):
                raise AirflowException(f"Validation rule {i} must be a dictionary")
            
            required_keys = ['column', 'rule_type', 'parameters']
            for key in required_keys:
                if key not in rule:
                    raise AirflowException(f"Validation rule {i} missing required key: {key}")
            
            valid_rule_types = ['null_check', 'range_check', 'regex_pattern', 'unique_check', 'length_check']
            if rule['rule_type'] not in valid_rule_types:
                raise AirflowException(f"Invalid rule_type '{rule['rule_type']}' in rule {i}. Valid types: {valid_rule_types}")
        
        self.log.info(f"Initialized DataValidationOperator with {len(validation_rules)} validation rules")
    
    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute data validation logic
        
        Args:
            context: Airflow context dictionary
            
        Returns:
            Dict containing validation results and summary
            
        Raises:
            AirflowException: On validation failure or data loading errors
        """
        self.log.info(f"Executing data validation for task {self.task_id}")
        
        # Validate template fields after Jinja rendering
        if not self.data_source or not self.data_source.strip():
            raise AirflowException("data_source cannot be empty")
        
        # Load data
        try:
            data = self._load_data(self.data_source)
            self.log.info(f"Loaded data with shape: {data.shape}")
        except Exception as e:
            raise AirflowException(f"Failed to load data from {self.data_source}: {str(e)}")
        
        # Run validations
        validation_results = []
        total_errors = 0
        
        for rule in self.validation_rules:
            try:
                result = self._apply_validation_rule(data, rule)
                validation_results.append(result)
                total_errors += result['error_count']
                
                self.log.info(f"Rule '{rule['rule_type']}' on column '{rule['column']}': "
                            f"{result['error_count']} errors found")
                
            except Exception as e:
                error_msg = f"Failed to apply validation rule {rule}: {str(e)}"
                self.log.error(error_msg)
                validation_results.append({
                    'column': rule.get('column', 'unknown'),
                    'rule_type': rule.get('rule_type', 'unknown'),
                    'status': 'failed',
                    'error_count': 0,
                    'error_message': str(e),
                    'details': []
                })
        
        # Prepare summary
        summary = {
            'total_rows': len(data),
            'total_rules': len(self.validation_rules),
            'total_errors': total_errors,
            'validation_passed': total_errors == 0,
            'execution_date': context.get('execution_date', '').isoformat() if context.get('execution_date') else '',
            'task_id': self.task_id
        }
        
        # Prepare final results
        results = {
            'summary': summary,
            'validation_results': validation_results
        }
        
        # Save report if specified
        if self.output_report:
            try:
                self._save_report(results, self.output_report)
                self.log.info(f"Validation report saved to {self.output_report}")
            except Exception as e:
                self.log.warning(f"Failed to save validation report: {str(e)}")
        
        # Log summary
        self.log.info(f"Validation completed: {total_errors} total errors found across {len(self.validation_rules)} rules")
        
        # Fail task if errors found and fail_on_error is True
        if total_errors > 0 and self.fail_on_error:
            raise AirflowException(f"Data validation failed with {total_errors} errors. Set fail_on_error=False to continue on validation errors.")
        
        return results
    
    def _load_data(self, data_source: str) -> pd.DataFrame:
        """Load data from various sources"""
        data_path = Path(data_source)
        
        if data_path.suffix.lower() == '.csv':
            return pd.read_csv(data_source)
        elif data_path.suffix.lower() == '.json':
            return pd.read_json(data_source)
        elif data_path.suffix.lower() in ['.xlsx', '.xls']:
            return pd.read_excel(data_source)
        else:
            # Try to read as CSV by default
            try:
                return pd.read_csv(data_source)
            except Exception:
                raise AirflowException(f"Unsupported file format or unable to read: {data_source}")
    
    def _apply_validation_rule(self, data: pd.DataFrame, rule: Dict[str, Any]) -> Dict[str, Any]:
        """Apply a single validation rule to the data"""
        column = rule['column']
        rule_type = rule['rule_type']
        parameters = rule['parameters']
        
        if column not in data.columns:
            return {
                'column': column,
                'rule_type': rule_type,
                'status': 'failed',
                'error_count': 0,
                'error_message': f"Column '{column}' not found in data",
                'details': []
            }
        
        column_data = data[column]
        errors = []
        
        try:
            if rule_type == 'null_check':
                null_mask = column_data.isnull()
                errors = data.index[null_mask].tolist()
                
            elif rule_type == 'range_check':
                min_val = parameters.get('min')
                max_val = parameters.get('max')
                
                # Convert to numeric, errors='coerce' will set invalid parsing to NaN
                numeric_data = pd.to_numeric(column_data, errors='coerce')
                
                if min_val is not None and max_val is not None:
                    mask = (numeric_data < min_val) | (numeric_data > max_val)
                elif min_val is not None:
                    mask = numeric_data < min_val
                elif max_val is not None:
                    mask = numeric_data > max_val
                else:
                    mask = pd.Series([False] * len(numeric_data))
                
                errors = data.index[mask].tolist()
                
            elif rule_type == 'regex_pattern':
                pattern = parameters.get('pattern')
                if not pattern:
                    raise ValueError("regex_pattern rule requires 'pattern' parameter")
                
                # Apply regex to string representation
                string_data = column_data.astype(str)
                mask = ~string_data.str.match(pattern, na=False)
                errors = data.index[mask].tolist()
                
            elif rule_type == 'unique_check':
                duplicated_mask = column_data.duplicated(keep=False)
                errors = data.index[duplicated_mask].tolist()
                
            elif rule_type == 'length_check':
                min_length = parameters.get('min_length', 0)
                max_length = parameters.get('max_length', float('inf'))
                
                string_data = column_data.astype(str)
                lengths = string_data.str.len()
                mask = (lengths < min_length) | (lengths > max_length)
                errors = data.index[mask].tolist()
            
            return {
                'column': column,
                'rule_type': rule_type,
                'status': 'passed' if len(errors) == 0 else 'failed',
                'error_count': len(errors),
                'error_message': None,
                'details': errors[:100]  # Limit to first 100 error indices
            }
            
        except Exception as e:
            return {
                'column': column,
                'rule_type': rule_type,
                'status': 'failed',
                'error_count': 0,
                'error_message': f"Rule execution failed: {str(e)}",
                'details': []
            }
    
    def _save_report(self, results: Dict[str, Any], output_path: str) -> None:
        """Save validation report to file"""
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)