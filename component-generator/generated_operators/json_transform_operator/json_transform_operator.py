from airflow.models import BaseOperator
from airflow.exceptions import AirflowException
from typing import Dict, Any, Sequence
import json
import jmespath


class JsonTransformOperator(BaseOperator):
    """
    Operator for transforming JSON data using JMESPath expressions.
    
    This operator takes a JSON string and applies a JMESPath expression to transform
    or extract data from it. JMESPath is a query language for JSON that allows you
    to declaratively specify how to extract elements from a JSON document.
    
    Args:
        input_json (str): Input JSON string to transform
        expression (str): JMESPath expression to apply to the JSON data
        
    Returns:
        Any: The result of applying the JMESPath expression to the input JSON
        
    Example:
        >>> operator = JsonTransformOperator(
        ...     task_id='transform_json',
        ...     input_json='{"users": [{"name": "John", "age": 30}, {"name": "Jane", "age": 25}]}',
        ...     expression='users[?age > `27`].name'
        ... )
    """
    
    template_fields: Sequence[str] = ['input_json', 'expression']
    ui_color: str = "#f0ede4"
    
    def __init__(
        self,
        input_json: str,
        expression: str,
        **kwargs
    ):
        super().__init__(**kwargs)
        
        # Store parameters
        self.input_json = input_json
        self.expression = expression
        
        # Validate non-template parameters or template parameters that don't contain Jinja
        if '{{' not in str(input_json):
            if not input_json or not input_json.strip():
                raise AirflowException("input_json cannot be empty")
            
            # Validate JSON format
            try:
                json.loads(input_json)
            except json.JSONDecodeError as e:
                raise AirflowException(f"Invalid JSON format in input_json: {e}")
        
        if '{{' not in str(expression):
            if not expression or not expression.strip():
                raise AirflowException("expression cannot be empty")
        
        self.log.info(f"Initialized JsonTransformOperator with task_id: {self.task_id}")
    
    def execute(self, context: Dict[str, Any]) -> Any:
        """
        Execute the JSON transformation using JMESPath expression.
        
        Args:
            context: Airflow context dict with task_instance, execution_date, etc.
            
        Returns:
            Any: The result of applying the JMESPath expression to the input JSON
            
        Raises:
            AirflowException: On JSON parsing errors or JMESPath expression errors
        """
        self.log.info(f"Executing JsonTransformOperator: {self.task_id}")
        
        # Validate template fields after Jinja rendering
        if not self.input_json or not str(self.input_json).strip():
            raise AirflowException("input_json cannot be empty after template rendering")
            
        if not self.expression or not str(self.expression).strip():
            raise AirflowException("expression cannot be empty after template rendering")
        
        try:
            # Parse input JSON
            self.log.info("Parsing input JSON data")
            json_data = json.loads(self.input_json)
            
            # Apply JMESPath expression
            self.log.info(f"Applying JMESPath expression: {self.expression}")
            result = jmespath.search(self.expression, json_data)
            
            self.log.info(f"JSON transformation completed successfully")
            self.log.info(f"Result type: {type(result).__name__}")
            
            return result
            
        except json.JSONDecodeError as e:
            error_msg = f"Failed to parse input JSON: {e}"
            self.log.error(error_msg)
            raise AirflowException(error_msg)
            
        except jmespath.exceptions.JMESPathError as e:
            error_msg = f"Invalid JMESPath expression '{self.expression}': {e}"
            self.log.error(error_msg)
            raise AirflowException(error_msg)
            
        except Exception as e:
            error_msg = f"Unexpected error during JSON transformation: {e}"
            self.log.error(error_msg)
            raise AirflowException(error_msg)