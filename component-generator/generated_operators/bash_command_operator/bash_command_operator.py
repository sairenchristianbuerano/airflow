from airflow.models import BaseOperator
from airflow.exceptions import AirflowException
from typing import Dict, Any, Optional, Sequence
import subprocess
import os
from pathlib import Path


class BashCommandOperator(BaseOperator):
    """
    Operator for executing bash commands with environment variables and working directory support.
    
    This operator executes bash commands in a subprocess with optional environment variables,
    working directory specification, and timeout control.
    
    Args:
        bash_command (str): Bash command to execute
        env (dict, optional): Environment variables for the command
        cwd (str, optional): Working directory for command execution
        timeout (int, optional): Command timeout in seconds
    """
    
    template_fields: Sequence[str] = ['bash_command']
    ui_color: str = "#f0ede4"
    
    def __init__(
        self,
        bash_command: str,
        env: Optional[Dict[str, str]] = None,
        cwd: Optional[str] = None,
        timeout: Optional[int] = None,
        **kwargs
    ):
        super().__init__(**kwargs)
        
        # Store parameters
        self.bash_command = bash_command
        self.env = env or {}
        self.cwd = cwd
        self.timeout = timeout
        
        # Validate non-template fields
        if self.env and not isinstance(self.env, dict):
            raise AirflowException("env parameter must be a dictionary")
            
        if self.cwd and '{{' not in str(self.cwd):
            cwd_path = Path(self.cwd)
            if not cwd_path.exists():
                raise AirflowException(f"Working directory does not exist: {self.cwd}")
            if not cwd_path.is_dir():
                raise AirflowException(f"Working directory path is not a directory: {self.cwd}")
                
        if self.timeout is not None:
            if not isinstance(self.timeout, int) or self.timeout <= 0:
                raise AirflowException("timeout must be a positive integer")
        
        self.log.info(f"Initialized BashCommandOperator with command: {bash_command}")
    
    def execute(self, context: Dict[str, Any]) -> str:
        """
        Execute the bash command with specified parameters.
        
        Args:
            context: Airflow context dict with task_instance, execution_date, etc.
            
        Returns:
            str: Command output
            
        Raises:
            AirflowException: On command failure or validation errors
        """
        self.log.info(f"Executing bash command: {self.bash_command}")
        
        # Validate template fields after Jinja rendering
        if not self.bash_command or not self.bash_command.strip():
            raise AirflowException("bash_command cannot be empty")
            
        # Validate working directory if specified
        if self.cwd:
            cwd_path = Path(self.cwd)
            if not cwd_path.exists():
                raise AirflowException(f"Working directory does not exist: {self.cwd}")
            if not cwd_path.is_dir():
                raise AirflowException(f"Working directory path is not a directory: {self.cwd}")
        
        # Prepare environment variables
        command_env = os.environ.copy()
        if self.env:
            command_env.update(self.env)
            self.log.info(f"Added environment variables: {list(self.env.keys())}")
        
        try:
            # Execute the bash command
            self.log.info(f"Running command in directory: {self.cwd or os.getcwd()}")
            
            result = subprocess.run(
                self.bash_command,
                shell=True,
                capture_output=True,
                text=True,
                cwd=self.cwd,
                env=command_env,
                timeout=self.timeout
            )
            
            # Log command output
            if result.stdout:
                self.log.info(f"Command stdout: {result.stdout}")
            if result.stderr:
                self.log.warning(f"Command stderr: {result.stderr}")
            
            # Check return code
            if result.returncode != 0:
                error_msg = f"Command failed with return code {result.returncode}"
                if result.stderr:
                    error_msg += f": {result.stderr}"
                raise AirflowException(error_msg)
            
            self.log.info("Bash command executed successfully")
            return result.stdout
            
        except subprocess.TimeoutExpired:
            raise AirflowException(f"Command timed out after {self.timeout} seconds")
        except Exception as e:
            raise AirflowException(f"Failed to execute bash command: {str(e)}")