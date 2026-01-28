from airflow.sensors.base import BaseSensor
from airflow.providers.amazon.aws.hooks.s3 import S3Hook
from airflow.exceptions import AirflowException
from typing import Dict, Any, Optional, Sequence
from datetime import datetime, timedelta
import fnmatch


class S3KeySensor(BaseSensor):
    """
    Sensor that waits for a key to appear in an S3 bucket.
    
    This sensor polls an S3 bucket for the existence of a specific key.
    It supports wildcard matching and custom check functions for flexible
    key detection patterns.
    
    Args:
        bucket_name (str): S3 bucket name to monitor
        bucket_key (str): S3 key to wait for
        wildcard_match (bool): Whether to use wildcard matching for key. Defaults to False
        aws_conn_id (str): Airflow connection ID for AWS. Defaults to 'aws_default'
        check_fn (str): Custom check function name. Defaults to None
        poke_interval (int): Time in seconds between pokes. Defaults to 60
        timeout (int): Maximum time to wait in seconds. Defaults to 3600
        mode (str): How the sensor operates ('poke' or 'reschedule'). Defaults to 'poke'
    """
    
    template_fields: Sequence[str] = ['bucket_name', 'bucket_key']
    ui_color: str = "#f0ede4"
    
    def __init__(
        self,
        bucket_name: str,
        bucket_key: str,
        wildcard_match: bool = False,
        aws_conn_id: str = 'aws_default',
        check_fn: Optional[str] = None,
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
        self.bucket_name = bucket_name
        self.bucket_key = bucket_key
        self.wildcard_match = wildcard_match
        self.aws_conn_id = aws_conn_id
        self.check_fn = check_fn
        self._s3_hook = None
    
    @property
    def s3_hook(self) -> S3Hook:
        """Lazy initialization of S3Hook"""
        if self._s3_hook is None:
            self._s3_hook = S3Hook(aws_conn_id=self.aws_conn_id)
        return self._s3_hook
    
    def poke(self, context: Dict[str, Any]) -> bool:
        """
        Check if the S3 key exists in the specified bucket.
        
        Args:
            context: Airflow context dictionary
            
        Returns:
            bool: True if key exists (sensor succeeds), False to continue poking
            
        Raises:
            AirflowException: For terminal failures like invalid bucket or connection issues
        """
        try:
            self.log.info(f"Poking for S3 key: s3://{self.bucket_name}/{self.bucket_key}")
            
            # Validate bucket exists
            if not self.s3_hook.check_for_bucket(self.bucket_name):
                raise AirflowException(f"Bucket '{self.bucket_name}' does not exist or is not accessible")
            
            # Check for key existence
            if self.wildcard_match:
                return self._check_wildcard_key()
            else:
                return self._check_exact_key()
                
        except AirflowException:
            raise
        except Exception as e:
            self.log.error(f"Error checking S3 key: {str(e)}")
            raise AirflowException(f"Failed to check S3 key: {str(e)}")
    
    def _check_exact_key(self) -> bool:
        """Check for exact key match"""
        key_exists = self.s3_hook.check_for_key(
            key=self.bucket_key,
            bucket_name=self.bucket_name
        )
        
        if key_exists:
            self.log.info(f"Found S3 key: s3://{self.bucket_name}/{self.bucket_key}")
            
            if self.check_fn:
                return self._apply_custom_check()
            return True
        else:
            self.log.info(f"S3 key not found: s3://{self.bucket_name}/{self.bucket_key}")
            return False
    
    def _check_wildcard_key(self) -> bool:
        """Check for wildcard key match"""
        try:
            # List keys with prefix to optimize search
            prefix = self._get_prefix_from_wildcard(self.bucket_key)
            keys = self.s3_hook.list_keys(
                bucket_name=self.bucket_name,
                prefix=prefix
            )
            
            if not keys:
                self.log.info(f"No keys found with prefix: {prefix}")
                return False
            
            # Check for wildcard matches
            matching_keys = [key for key in keys if fnmatch.fnmatch(key, self.bucket_key)]
            
            if matching_keys:
                self.log.info(f"Found {len(matching_keys)} matching keys for pattern: {self.bucket_key}")
                self.log.info(f"First matching key: s3://{self.bucket_name}/{matching_keys[0]}")
                
                if self.check_fn:
                    return self._apply_custom_check(matching_keys[0])
                return True
            else:
                self.log.info(f"No keys match wildcard pattern: {self.bucket_key}")
                return False
                
        except Exception as e:
            self.log.error(f"Error during wildcard key search: {str(e)}")
            raise AirflowException(f"Failed to search for wildcard keys: {str(e)}")
    
    def _get_prefix_from_wildcard(self, wildcard_key: str) -> str:
        """Extract prefix from wildcard pattern for efficient S3 listing"""
        # Find the first wildcard character
        wildcard_chars = ['*', '?', '[']
        first_wildcard_pos = len(wildcard_key)
        
        for char in wildcard_chars:
            pos = wildcard_key.find(char)
            if pos != -1 and pos < first_wildcard_pos:
                first_wildcard_pos = pos
        
        # Return prefix up to the first wildcard
        prefix = wildcard_key[:first_wildcard_pos]
        
        # Remove trailing partial directory name if wildcard is in filename
        if '/' in prefix:
            prefix = '/'.join(prefix.split('/')[:-1])
            if prefix and not prefix.endswith('/'):
                prefix += '/'
        
        return prefix
    
    def _apply_custom_check(self, key: Optional[str] = None) -> bool:
        """Apply custom check function if specified"""
        if not self.check_fn:
            return True
            
        try:
            check_key = key or self.bucket_key
            
            # Get object metadata for custom checks
            obj_info = self.s3_hook.head_object(
                key=check_key,
                bucket_name=self.bucket_name
            )
            
            # Apply basic built-in check functions
            if self.check_fn == 'check_size_gt_zero':
                size = obj_info.get('ContentLength', 0)
                result = size > 0
                self.log.info(f"Custom check 'check_size_gt_zero': size={size}, result={result}")
                return result
            elif self.check_fn == 'check_modified_today':
                last_modified = obj_info.get('LastModified')
                if last_modified:
                    today = datetime.now().date()
                    result = last_modified.date() == today
                    self.log.info(f"Custom check 'check_modified_today': modified={last_modified}, result={result}")
                    return result
                return False
            else:
                self.log.warning(f"Unknown check function: {self.check_fn}. Skipping custom check.")
                return True
                
        except Exception as e:
            self.log.error(f"Error applying custom check function '{self.check_fn}': {str(e)}")
            raise AirflowException(f"Custom check function failed: {str(e)}")