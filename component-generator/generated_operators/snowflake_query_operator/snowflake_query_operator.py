try:
    from airflow.sdk.bases.operator import BaseOperator
except ImportError:
    from airflow.models import BaseOperator

from airflow.exceptions import AirflowException
from airflow.providers.snowflake.hooks.snowflake import SnowflakeHook
from typing import Dict, Any, Optional, Sequence, Union, List
import json


class SnowflakeQueryOperator(BaseOperator):
    """
    Executes SQL queries against Snowflake data warehouse with result handling and parameterization.
    
    This operator connects to Snowflake using the specified connection ID and executes
    the provided SQL query. It supports parameterized queries and returns results as XCom.
    
    Args:
        sql (str): SQL query to execute
        parameters (Dict[str, Any], optional): Query parameters for parameterized queries. Defaults to {}.
        snowflake_conn_id (str, optional): Airflow connection ID for Snowflake. Defaults to 'snowflake_default'.
        warehouse (str, optional): Snowflake warehouse to use. Defaults to None.
        database (str, optional): Snowflake database to use. Defaults to None.
        **kwargs: Additional keyword arguments passed to BaseOperator
        
    Returns:
        List[Dict]: Query results as list of dictionaries
        
    Raises:
        AirflowException: On connection or query execution failures
    """
    
    template_fields: Sequence[str] = ['sql', 'parameters']
    ui_color: str = "#29b5e8"
    
    def __init__(
        self,
        sql: str,
        parameters: Optional[Dict[str, Any]] = None,
        snowflake_conn_id: str = 'snowflake_default',
        warehouse: Optional[str] = None,
        database: Optional[str] = None,
        **kwargs
    ):
        super().__init__(**kwargs)
        
        self.sql = sql
        self.parameters = parameters or {}
        self.snowflake_conn_id = snowflake_conn_id
        self.warehouse = warehouse
        self.database = database
        
        # Validate non-template fields
        if not isinstance(self.snowflake_conn_id, str) or not self.snowflake_conn_id.strip():
            raise AirflowException("snowflake_conn_id must be a non-empty string")
            
        # Skip validation for template fields containing Jinja templates
        if '{{' not in str(self.sql) and not isinstance(self.sql, str):
            raise AirflowException("sql must be a string")
            
        if '{{' not in str(self.parameters) and not isinstance(self.parameters, dict):
            raise AirflowException("parameters must be a dictionary")
            
        self.log.info(f"Initialized SnowflakeQueryOperator with connection: {self.snowflake_conn_id}")
        
    def execute(self, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Execute the SQL query against Snowflake and return results.
        
        Args:
            context: Airflow context dictionary containing task_instance, execution_date, etc.
            
        Returns:
            List[Dict[str, Any]]: Query results as list of dictionaries
            
        Raises:
            AirflowException: On connection or query execution failures
        """
        self.log.info(f"Executing SnowflakeQueryOperator task: {self.task_id}")
        
        # Validate template fields after Jinja rendering
        if not isinstance(self.sql, str) or not self.sql.strip():
            raise AirflowException("sql must be a non-empty string after template rendering")
            
        if not isinstance(self.parameters, dict):
            raise AirflowException("parameters must be a dictionary after template rendering")
            
        try:
            # Initialize Snowflake hook
            hook = SnowflakeHook(
                snowflake_conn_id=self.snowflake_conn_id,
                warehouse=self.warehouse,
                database=self.database
            )
            
            self.log.info(f"Connecting to Snowflake using connection: {self.snowflake_conn_id}")
            if self.warehouse:
                self.log.info(f"Using warehouse: {self.warehouse}")
            if self.database:
                self.log.info(f"Using database: {self.database}")
                
            # Execute query with parameters
            self.log.info(f"Executing SQL query: {self.sql[:100]}{'...' if len(self.sql) > 100 else ''}")
            if self.parameters:
                self.log.info(f"Using parameters: {json.dumps(self.parameters, default=str)}")
                
            # Get connection and execute query
            conn = hook.get_conn()
            cursor = conn.cursor()
            
            try:
                if self.parameters:
                    cursor.execute(self.sql, self.parameters)
                else:
                    cursor.execute(self.sql)
                    
                # Fetch results
                columns = [desc[0] for desc in cursor.description] if cursor.description else []
                rows = cursor.fetchall()
                
                # Convert to list of dictionaries
                results = []
                for row in rows:
                    row_dict = {}
                    for i, value in enumerate(row):
                        if i < len(columns):
                            row_dict[columns[i]] = value
                    results.append(row_dict)
                    
                self.log.info(f"Query executed successfully. Retrieved {len(results)} rows")
                
                # Log sample of results for debugging (first 3 rows)
                if results:
                    sample_size = min(3, len(results))
                    self.log.info(f"Sample results (first {sample_size} rows): {json.dumps(results[:sample_size], default=str, indent=2)}")
                    
                return results
                
            finally:
                cursor.close()
                conn.close()
                
        except Exception as e:
            error_msg = f"Failed to execute Snowflake query: {str(e)}"
            self.log.error(error_msg)
            raise AirflowException(error_msg) from e