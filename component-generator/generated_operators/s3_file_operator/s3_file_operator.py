from airflow.models import BaseOperator
from airflow.exceptions import AirflowException
from airflow.providers.amazon.aws.hooks.s3 import S3Hook
from typing import Dict, Any, Optional, Sequence
from pathlib import Path


class S3FileOperator(BaseOperator):
    """
    Operator for AWS S3 file operations including upload, download, copy, and delete.
    
    This operator supports various S3 operations:
    - upload: Upload a local file to S3
    - download: Download an S3 object to local file
    - copy: Copy an S3 object to another location
    - delete: Delete an S3 object
    
    Args:
        bucket_name: S3 bucket name
        key: S3 object key
        operation: Operation type (upload, download, copy, delete)
        local_path: Local file path for upload or download operations
        dest_bucket: Destination bucket for copy operation
        dest_key: Destination key for copy operation
        aws_conn_id: Airflow connection ID for AWS credentials
    """
    
    template_fields: Sequence[str] = ['bucket_name', 'key', 'operation', 'local_path', 'dest_bucket', 'dest_key']
    ui_color: str = "#ff9900"
    
    def __init__(
        self,
        bucket_name: str,
        key: str,
        operation: str,
        local_path: Optional[str] = None,
        dest_bucket: Optional[str] = None,
        dest_key: Optional[str] = None,
        aws_conn_id: str = 'aws_default',
        **kwargs
    ):
        super().__init__(**kwargs)
        
        self.bucket_name = bucket_name
        self.key = key
        self.operation = operation
        self.local_path = local_path
        self.dest_bucket = dest_bucket
        self.dest_key = dest_key
        self.aws_conn_id = aws_conn_id
        
        # Validate operation if not a template
        valid_operations = ['upload', 'download', 'copy', 'delete']
        if '{{' not in str(operation) and operation not in valid_operations:
            raise AirflowException(f"Invalid operation '{operation}'. Must be one of: {valid_operations}")
        
        self.log.info(f"Initialized S3FileOperator for operation: {operation}")
    
    def execute(self, context: Dict[str, Any]) -> Any:
        """
        Execute the S3 file operation.
        
        Args:
            context: Airflow context dictionary
            
        Returns:
            Dict containing operation result details
            
        Raises:
            AirflowException: On invalid parameters or operation failure
        """
        self.log.info(f"Executing S3FileOperator task: {self.task_id}")
        
        # Validate operation after template rendering
        valid_operations = ['upload', 'download', 'copy', 'delete']
        if self.operation not in valid_operations:
            raise AirflowException(f"Invalid operation '{self.operation}'. Must be one of: {valid_operations}")
        
        # Validate required parameters based on operation
        if self.operation in ['upload', 'download'] and not self.local_path:
            raise AirflowException(f"local_path is required for {self.operation} operation")
        
        if self.operation == 'copy':
            if not self.dest_bucket:
                raise AirflowException("dest_bucket is required for copy operation")
            if not self.dest_key:
                raise AirflowException("dest_key is required for copy operation")
        
        # Initialize S3 hook
        try:
            s3_hook = S3Hook(aws_conn_id=self.aws_conn_id)
            self.log.info(f"Connected to S3 using connection: {self.aws_conn_id}")
        except Exception as e:
            raise AirflowException(f"Failed to initialize S3 connection: {str(e)}")
        
        result = {}
        
        try:
            if self.operation == 'upload':
                result = self._upload_file(s3_hook)
            elif self.operation == 'download':
                result = self._download_file(s3_hook)
            elif self.operation == 'copy':
                result = self._copy_file(s3_hook)
            elif self.operation == 'delete':
                result = self._delete_file(s3_hook)
            
            self.log.info(f"S3 {self.operation} operation completed successfully")
            return result
            
        except Exception as e:
            raise AirflowException(f"S3 {self.operation} operation failed: {str(e)}")
    
    def _upload_file(self, s3_hook: S3Hook) -> Dict[str, Any]:
        """Upload local file to S3."""
        local_file = Path(self.local_path)
        
        if not local_file.exists():
            raise AirflowException(f"Local file does not exist: {self.local_path}")
        
        self.log.info(f"Uploading {self.local_path} to s3://{self.bucket_name}/{self.key}")
        
        s3_hook.load_file(
            filename=str(local_file),
            key=self.key,
            bucket_name=self.bucket_name,
            replace=True
        )
        
        return {
            'operation': 'upload',
            'bucket': self.bucket_name,
            'key': self.key,
            'local_path': self.local_path,
            'file_size': local_file.stat().st_size
        }
    
    def _download_file(self, s3_hook: S3Hook) -> Dict[str, Any]:
        """Download S3 object to local file."""
        if not s3_hook.check_for_key(self.key, self.bucket_name):
            raise AirflowException(f"S3 object does not exist: s3://{self.bucket_name}/{self.key}")
        
        local_file = Path(self.local_path)
        local_file.parent.mkdir(parents=True, exist_ok=True)
        
        self.log.info(f"Downloading s3://{self.bucket_name}/{self.key} to {self.local_path}")
        
        s3_hook.download_file(
            key=self.key,
            bucket_name=self.bucket_name,
            local_path=str(local_file)
        )
        
        return {
            'operation': 'download',
            'bucket': self.bucket_name,
            'key': self.key,
            'local_path': self.local_path,
            'file_size': local_file.stat().st_size
        }
    
    def _copy_file(self, s3_hook: S3Hook) -> Dict[str, Any]:
        """Copy S3 object to another location."""
        if not s3_hook.check_for_key(self.key, self.bucket_name):
            raise AirflowException(f"Source S3 object does not exist: s3://{self.bucket_name}/{self.key}")
        
        self.log.info(f"Copying s3://{self.bucket_name}/{self.key} to s3://{self.dest_bucket}/{self.dest_key}")
        
        s3_hook.copy_object(
            source_bucket_key=self.key,
            source_bucket_name=self.bucket_name,
            dest_bucket_key=self.dest_key,
            dest_bucket_name=self.dest_bucket
        )
        
        return {
            'operation': 'copy',
            'source_bucket': self.bucket_name,
            'source_key': self.key,
            'dest_bucket': self.dest_bucket,
            'dest_key': self.dest_key
        }
    
    def _delete_file(self, s3_hook: S3Hook) -> Dict[str, Any]:
        """Delete S3 object."""
        if not s3_hook.check_for_key(self.key, self.bucket_name):
            self.log.warning(f"S3 object does not exist: s3://{self.bucket_name}/{self.key}")
            return {
                'operation': 'delete',
                'bucket': self.bucket_name,
                'key': self.key,
                'status': 'not_found'
            }
        
        self.log.info(f"Deleting s3://{self.bucket_name}/{self.key}")
        
        s3_hook.delete_objects(
            bucket=self.bucket_name,
            keys=[self.key]
        )
        
        return {
            'operation': 'delete',
            'bucket': self.bucket_name,
            'key': self.key,
            'status': 'deleted'
        }