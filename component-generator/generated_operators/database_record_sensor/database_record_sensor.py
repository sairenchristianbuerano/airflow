from airflow.sensors.base import BaseSensor
from airflow.hooks.base import BaseHook
from airflow.exceptions import AirflowException
from typing import Dict, Any, Optional, Sequence
import sqlparse

class DatabaseRecordSensor(BaseSensor):
    """
    Sensor that waits for a record to exist in a database table based on SQL condition.
    
    This sensor polls a database table and checks if records matching the specified
    SQL condition exist. The sensor succeeds when the expected number of records
    is found.
    
    Args:
        table (str): Database table name to query
        sql_condition (str): SQL WHERE condition to check for records
        conn_id (str, optional): Airflow connection ID for database. Defaults to 'default_db'
        expected_count (int, optional): Minimum number of records expected. Defaults to 1
        poke_interval (int, optional): Time in seconds between pokes. Defaults to 60
        timeout (int, optional): Time in seconds before timing out. Defaults to 3600
        mode (str, optional): How the sensor operates ('poke' or 'reschedule'). Defaults to 'poke'
    """
    
    template_fields: Sequence[str] = ['table', 'sql_condition', 'conn_id']
    ui_color: str = "#87CEEB"
    
    def __init__(
        self,
        table: str,
        sql_condition: str,
        conn_id: str = 'default_db',
        expected_count: int = 1,
        poke_interval: int = 60,
        timeout: int = 3600,
        mode: str = 'poke',
        **kwargs
    ):
        super().__init__(
            poke_interval=poke_interval,
            timeout=timeout,
            mode=mode,
            **kwargs
        )
        self.table = table
        self.sql_condition = sql_condition
        self.conn_id = conn_id
        self.expected_count = expected_count
        self._hook = None
    
    def _get_hook(self):
        """Get database hook based on connection type."""
        if self._hook is None:
            try:
                connection = BaseHook.get_connection(self.conn_id)
                conn_type = connection.conn_type.lower()
                
                if conn_type == 'postgres':
                    from airflow.providers.postgres.hooks.postgres import PostgresHook
                    self._hook = PostgresHook(postgres_conn_id=self.conn_id)
                elif conn_type == 'mysql':
                    from airflow.providers.mysql.hooks.mysql import MySqlHook
                    self._hook = MySqlHook(mysql_conn_id=self.conn_id)
                elif conn_type == 'sqlite':
                    from airflow.providers.sqlite.hooks.sqlite import SqliteHook
                    self._hook = SqliteHook(sqlite_conn_id=self.conn_id)
                elif conn_type in ['mssql', 'sqlserver']:
                    from airflow.providers.microsoft.mssql.hooks.mssql import MsSqlHook
                    self._hook = MsSqlHook(mssql_conn_id=self.conn_id)
                else:
                    raise AirflowException(f"Unsupported database connection type: {conn_type}")
                    
            except Exception as e:
                raise AirflowException(f"Failed to create database hook: {str(e)}")
                
        return self._hook
    
    def _validate_inputs(self):
        """Validate input parameters."""
        if not self.table or not isinstance(self.table, str):
            raise AirflowException("Parameter 'table' must be a non-empty string")
            
        if not self.sql_condition or not isinstance(self.sql_condition, str):
            raise AirflowException("Parameter 'sql_condition' must be a non-empty string")
            
        if not isinstance(self.expected_count, int) or self.expected_count < 0:
            raise AirflowException("Parameter 'expected_count' must be a non-negative integer")
    
    def _sanitize_table_name(self, table_name: str) -> str:
        """Sanitize table name to prevent SQL injection."""
        # Remove any characters that aren't alphanumeric, underscore, or dot
        import re
        sanitized = re.sub(r'[^a-zA-Z0-9_.]', '', table_name)
        if not sanitized:
            raise AirflowException(f"Invalid table name after sanitization: {table_name}")
        return sanitized
    
    def _validate_sql_condition(self, condition: str) -> str:
        """Validate and sanitize SQL condition."""
        try:
            # Parse the SQL condition to check for basic syntax
            parsed = sqlparse.parse(condition)
            if not parsed:
                raise AirflowException("Invalid SQL condition syntax")
                
            # Check for dangerous keywords
            dangerous_keywords = ['DROP', 'DELETE', 'UPDATE', 'INSERT', 'CREATE', 'ALTER', 'TRUNCATE']
            condition_upper = condition.upper()
            for keyword in dangerous_keywords:
                if keyword in condition_upper:
                    raise AirflowException(f"Dangerous SQL keyword '{keyword}' not allowed in condition")
                    
            return condition
            
        except Exception as e:
            raise AirflowException(f"SQL condition validation failed: {str(e)}")
    
    def poke(self, context: Dict[str, Any]) -> bool:
        """
        Check if the specified condition is met in the database table.
        
        Args:
            context: Airflow context dictionary
            
        Returns:
            bool: True if condition is met (sensor succeeds), False to continue poking
            
        Raises:
            AirflowException: For terminal failures
        """
        self.log.info(f"Poking for records in table '{self.table}' with condition: {self.sql_condition}")
        
        try:
            # Validate inputs
            self._validate_inputs()
            
            # Sanitize table name and validate SQL condition
            safe_table = self._sanitize_table_name(self.table)
            safe_condition = self._validate_sql_condition(self.sql_condition)
            
            # Get database hook
            hook = self._get_hook()
            
            # Build and execute query
            sql_query = f"SELECT COUNT(*) FROM {safe_table} WHERE {safe_condition}"
            self.log.info(f"Executing query: {sql_query}")
            
            result = hook.get_first(sql_query)
            
            if result is None:
                self.log.warning("Query returned no results")
                return False
                
            record_count = result[0] if isinstance(result, (list, tuple)) else result
            
            if not isinstance(record_count, (int, float)):
                raise AirflowException(f"Expected numeric count, got: {type(record_count)}")
                
            record_count = int(record_count)
            self.log.info(f"Found {record_count} records, expected at least {self.expected_count}")
            
            if record_count >= self.expected_count:
                self.log.info(f"Condition met! Found {record_count} records (>= {self.expected_count})")
                return True
            else:
                self.log.info(f"Condition not met. Found {record_count} records (< {self.expected_count}). Will retry...")
                return False
                
        except AirflowException:
            raise
        except Exception as e:
            self.log.error(f"Unexpected error during database check: {str(e)}")
            raise AirflowException(f"Database record sensor failed: {str(e)}")