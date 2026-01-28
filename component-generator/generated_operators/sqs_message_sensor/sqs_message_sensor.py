from airflow.sensors.base import BaseSensor
from airflow.exceptions import AirflowException
from airflow.providers.amazon.aws.hooks.sqs import SqsHook
from typing import Dict, Any, Optional, Sequence
from datetime import datetime, timedelta


class SqsMessageSensor(BaseSensor):
    """
    Sensor that waits for a message to arrive in an AWS SQS queue.
    
    This sensor polls an SQS queue at regular intervals and succeeds when
    at least one message is available in the queue.
    
    Args:
        queue_url: SQS queue URL to monitor
        max_messages: Maximum number of messages to receive (1-10)
        wait_time_seconds: Long polling wait time in seconds (0-20)
        visibility_timeout: Message visibility timeout in seconds
        aws_conn_id: Airflow connection ID for AWS credentials
        poke_interval: Time in seconds between pokes
        timeout: Maximum time to wait for messages
        mode: Sensor mode ('poke' or 'reschedule')
    """
    
    template_fields: Sequence[str] = ['queue_url']
    ui_color: str = "#ff9900"
    
    def __init__(
        self,
        queue_url: str,
        max_messages: int = 1,
        wait_time_seconds: int = 0,
        visibility_timeout: Optional[int] = None,
        aws_conn_id: str = 'aws_default',
        poke_interval: int = 30,
        timeout: int = 60 * 60 * 24,
        mode: str = 'poke',
        **kwargs
    ):
        super().__init__(
            poke_interval=poke_interval,
            timeout=timeout,
            mode=mode,
            **kwargs
        )
        self.queue_url = queue_url
        self.max_messages = max_messages
        self.wait_time_seconds = wait_time_seconds
        self.visibility_timeout = visibility_timeout
        self.aws_conn_id = aws_conn_id
        self._sqs_hook = None
    
    def _get_sqs_hook(self) -> SqsHook:
        """Get SQS hook with lazy initialization."""
        if self._sqs_hook is None:
            self._sqs_hook = SqsHook(aws_conn_id=self.aws_conn_id)
        return self._sqs_hook
    
    def poke(self, context: Dict[str, Any]) -> bool:
        """
        Check if messages are available in the SQS queue.
        
        Args:
            context: Airflow context dictionary
            
        Returns:
            bool: True if messages are available, False to continue poking
            
        Raises:
            AirflowException: For terminal failures like invalid queue URL
        """
        try:
            self.log.info(f"Checking for messages in SQS queue: {self.queue_url}")
            
            # Validate parameters
            if not self.queue_url:
                raise AirflowException("queue_url parameter is required")
            
            if not isinstance(self.max_messages, int) or not (1 <= self.max_messages <= 10):
                raise AirflowException("max_messages must be an integer between 1 and 10")
            
            if not isinstance(self.wait_time_seconds, int) or not (0 <= self.wait_time_seconds <= 20):
                raise AirflowException("wait_time_seconds must be an integer between 0 and 20")
            
            sqs_hook = self._get_sqs_hook()
            
            # Prepare receive message parameters
            receive_params = {
                'QueueUrl': self.queue_url,
                'MaxNumberOfMessages': self.max_messages,
                'WaitTimeSeconds': self.wait_time_seconds
            }
            
            if self.visibility_timeout is not None:
                if not isinstance(self.visibility_timeout, int) or self.visibility_timeout < 0:
                    raise AirflowException("visibility_timeout must be a non-negative integer")
                receive_params['VisibilityTimeout'] = self.visibility_timeout
            
            # Check for messages
            response = sqs_hook.conn.receive_message(**receive_params)
            messages = response.get('Messages', [])
            
            if messages:
                self.log.info(f"Found {len(messages)} message(s) in queue {self.queue_url}")
                
                # Log message details (without exposing sensitive data)
                for i, message in enumerate(messages):
                    message_id = message.get('MessageId', 'unknown')
                    receipt_handle = message.get('ReceiptHandle', '')[:20] + '...' if message.get('ReceiptHandle') else 'none'
                    self.log.info(f"Message {i+1}: ID={message_id}, ReceiptHandle={receipt_handle}")
                
                return True
            else:
                self.log.info(f"No messages found in queue {self.queue_url}, continuing to poke")
                return False
                
        except Exception as e:
            if "NonExistentQueue" in str(e) or "QueueDoesNotExist" in str(e):
                raise AirflowException(f"SQS queue does not exist: {self.queue_url}")
            elif "AccessDenied" in str(e):
                raise AirflowException(f"Access denied to SQS queue: {self.queue_url}")
            elif "InvalidParameterValue" in str(e):
                raise AirflowException(f"Invalid parameter value for SQS operation: {str(e)}")
            else:
                self.log.error(f"Error checking SQS queue {self.queue_url}: {str(e)}")
                raise AirflowException(f"Failed to check SQS queue: {str(e)}")