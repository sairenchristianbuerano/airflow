from airflow.models import BaseOperator
from airflow.exceptions import AirflowException
from airflow.providers.postgres.hooks.postgres import PostgresHook
from typing import Dict, Any, Optional, Sequence, Union
import logging

class PostgresQueryOperator(BaseOperator):
    """
    Operator for executing SQL queries on PostgreSQL databases with parameterized queries and result handling.
    
    This operator connects to a PostgreSQL database and executes SQL queries with support for
    parameterized queries, transaction control, and result handling.
    
    Args:
        sql (str): SQL query to execute
        parameters (dict, optional): Query parameters for parameterized queries
        autocommit (bool, optional): Whether to autocommit the transaction. Defaults to True
        postgres_conn_id (str, optional): Airflow connection ID for PostgreSQL. Defaults to 'postgres_default'
        database (str, optional): Database name to connect to. If not provided, uses connection default
        **kwargs: Additional arguments passed to BaseOperator
    
    Example:
        >>> operator = PostgresQueryOperator(
        ...     task_id='run_query',
        ...     sql="SELECT * FROM users WHERE city = %(city)s",
        ...     parameters={'city': 'New York'},
        ...     postgres_conn_id='my_postgres_conn'
        ... )
    """
    
    template_fields: Sequence[str] = ['sql', 'parameters']
    ui_color: str = "#336791"
    
    def __init__(
        self,
        sql: str,
        parameters: Optional[Dict[str, Any]] = None,
        autocommit: bool = True,
        postgres_conn_id: str = 'postgres_default',
        database: Optional[str] = None,
        **kwargs
    ):
        super().__init__(**kwargs)
        
        # Validate sql parameter (skip if Jinja template)
        if '{{' not in str(sql) and not sql.strip():
            raise AirflowException("SQL query cannot be empty")
        
        # Validate parameters (skip if Jinja template)
        if parameters is not None and '{{' not in str(parameters) and not isinstance(parameters, dict):
            raise AirflowException("Parameters must be a dictionary")
        
        # Validate autocommit
        if not isinstance(autocommit, bool):
            raise AirflowException("autocommit must be a boolean value")
        
        # Validate postgres_conn_id
        if not postgres_conn_id or not isinstance(postgres_conn_id, str):
            raise AirflowException("postgres_conn_id must be a non-empty string")
        
        # Validate database (skip if Jinja template)
        if database is not None and '{{' not in str(database) and not isinstance(database, str):
            raise AirflowException("database must be a string")
        
        self.sql = sql
        self.parameters = parameters or {}
        self.autocommit = autocommit
        self.postgres_conn_id = postgres_conn_id
        self.database = database
        
        self.log.info(f"Initialized PostgresQueryOperator with connection: {postgres_conn_id}")
    
    def execute(self, context: Dict[str, Any]) -> Any:
        """
        Execute the SQL query on PostgreSQL database.
        
        Args:
            context: Airflow context dict with task_instance, execution_date, etc.
        
        Returns:
            List[Dict]: Query results as list of dictionaries (for SELECT queries)
            int: Number of affected rows (for INSERT/UPDATE/DELETE queries)
        
        Raises:
            AirflowException: On connection failure or query execution error
        """
        self.log.info(f"Executing PostgresQueryOperator task: {self.task_id}")
        
        # Validate template fields after Jinja rendering
        if not self.sql or not self.sql.strip():
            raise AirflowException("SQL query cannot be empty after template rendering")
        
        if not isinstance(self.parameters, dict):
            raise AirflowException("Parameters must be a dictionary after template rendering")
        
        try:
            # Initialize PostgreSQL hook
            postgres_hook = PostgresHook(
                postgres_conn_id=self.postgres_conn_id,
                schema=self.database
            )
            
            self.log.info(f"Connecting to PostgreSQL database: {self.postgres_conn_id}")
            
            # Log query execution (without parameters for security)
            self.log.info(f"Executing SQL query: {self.sql[:100]}{'...' if len(self.sql) > 100 else ''}")
            if self.parameters:
                self.log.info(f"Using {len(self.parameters)} query parameters")
            
            # Execute query based on type
            sql_lower = self.sql.strip().lower()
            
            if sql_lower.startswith('select') or sql_lower.startswith('with'):
                # For SELECT queries, return results
                self.log.info("Executing SELECT query")
                results = postgres_hook.get_records(
                    sql=self.sql,
                    parameters=self.parameters if self.parameters else None
                )
                
                # Convert to list of dictionaries for better usability
                if results:
                    column_names = [desc[0] for desc in postgres_hook.get_cursor().description]
                    results_dict = [dict(zip(column_names, row)) for row in results]
                    self.log.info(f"Query returned {len(results_dict)} rows")
                    return results_dict
                else:
                    self.log.info("Query returned no results")
                    return []
            
            else:
                # For INSERT/UPDATE/DELETE queries, return affected row count
                self.log.info("Executing DML query")
                postgres_hook.run(
                    sql=self.sql,
                    parameters=self.parameters if self.parameters else None,
                    autocommit=self.autocommit
                )
                
                # Get affected row count
                cursor = postgres_hook.get_cursor()
                affected_rows = cursor.rowcount if cursor else 0
                
                self.log.info(f"Query affected {affected_rows} rows")
                return affected_rows
                
        except Exception as e:
            error_msg = f"Failed to execute PostgreSQL query: {str(e)}"
            self.log.error(error_msg)
            raise AirflowException(error_msg) from e
        
        finally:
            self.log.info(f"Completed PostgresQueryOperator task: {self.task_id}")