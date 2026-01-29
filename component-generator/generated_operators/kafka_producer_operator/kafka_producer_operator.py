try:
    from airflow.sdk.bases.operator import BaseOperator
except ImportError:
    from airflow.models import BaseOperator

from airflow.exceptions import AirflowException
from airflow.hooks.base import BaseHook
from typing import Dict, Any, Optional, Sequence
import json
import logging
from kafka import KafkaProducer


class KafkaProducerOperator(BaseOperator):
    """
    Publishes messages to Apache Kafka topics with support for partitioning and serialization.
    
    This operator connects to a Kafka cluster and publishes messages to specified topics.
    It supports message key-based partitioning and handles JSON serialization of message payloads.
    
    Args:
        topic (str): Kafka topic to publish to
        message (str): Message payload to publish
        key (str, optional): Optional message key for partitioning
        kafka_conn_id (str): Airflow connection ID for Kafka bootstrap servers
        **kwargs: Additional arguments passed to BaseOperator
    
    Example:
        >>> kafka_task = KafkaProducerOperator(
        ...     task_id='publish_to_kafka',
        ...     topic='user_events',
        ...     message='{"user_id": 123, "action": "login"}',
        ...     key='user_123',
        ...     kafka_conn_id='kafka_default'
        ... )
    """
    
    template_fields: Sequence[str] = ['topic', 'message', 'key']
    ui_color: str = "#232f3e"
    
    def __init__(
        self,
        topic: str,
        message: str,
        key: Optional[str] = None,
        kafka_conn_id: str = 'kafka_default',
        **kwargs
    ):
        super().__init__(**kwargs)
        
        # Store parameters
        self.topic = topic
        self.message = message
        self.key = key
        self.kafka_conn_id = kafka_conn_id
        self._producer = None
        self._connection = None
        
        # Validate non-template parameters
        if not kafka_conn_id:
            raise AirflowException("kafka_conn_id cannot be empty")
        
        # Validate template fields only if they don't contain Jinja templates
        if '{{' not in str(topic) and not topic:
            raise AirflowException("topic cannot be empty")
        
        if '{{' not in str(message) and not message:
            raise AirflowException("message cannot be empty")
        
        self.log.info(f"Initialized KafkaProducerOperator for topic: {topic}")
    
    def _get_connection(self):
        """Get Kafka connection details from Airflow connection."""
        if self._connection is None:
            try:
                self._connection = BaseHook.get_connection(self.kafka_conn_id)
                self.log.info(f"Retrieved connection: {self.kafka_conn_id}")
            except Exception as e:
                raise AirflowException(f"Failed to get connection {self.kafka_conn_id}: {str(e)}")
        return self._connection
    
    def _get_producer(self):
        """Get or create Kafka producer instance."""
        if self._producer is None:
            connection = self._get_connection()
            
            # Parse bootstrap servers from connection
            if connection.host:
                bootstrap_servers = f"{connection.host}:{connection.port or 9092}"
            else:
                raise AirflowException(f"No host specified in connection {self.kafka_conn_id}")
            
            # Producer configuration
            producer_config = {
                'bootstrap_servers': bootstrap_servers,
                'value_serializer': lambda v: json.dumps(v).encode('utf-8') if isinstance(v, (dict, list)) else str(v).encode('utf-8'),
                'key_serializer': lambda k: str(k).encode('utf-8') if k is not None else None,
                'acks': 'all',
                'retries': 3,
                'retry_backoff_ms': 100
            }
            
            # Add authentication if provided in connection
            if connection.login and connection.password:
                producer_config.update({
                    'security_protocol': 'SASL_PLAINTEXT',
                    'sasl_mechanism': 'PLAIN',
                    'sasl_plain_username': connection.login,
                    'sasl_plain_password': connection.password
                })
            
            try:
                self._producer = KafkaProducer(**producer_config)
                self.log.info(f"Created Kafka producer for {bootstrap_servers}")
            except Exception as e:
                raise AirflowException(f"Failed to create Kafka producer: {str(e)}")
        
        return self._producer
    
    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the Kafka message publishing operation.
        
        Args:
            context: Airflow context dict with task_instance, execution_date, etc.
        
        Returns:
            Dict[str, Any]: Information about the published message
        
        Raises:
            AirflowException: On publishing failure
        """
        self.log.info(f"Executing {self.task_id}")
        
        # Validate template fields after Jinja rendering
        if not self.topic:
            raise AirflowException("topic cannot be empty after template rendering")
        
        if not self.message:
            raise AirflowException("message cannot be empty after template rendering")
        
        # Parse message if it's JSON string
        try:
            if isinstance(self.message, str) and (self.message.strip().startswith('{') or self.message.strip().startswith('[')):
                message_payload = json.loads(self.message)
            else:
                message_payload = self.message
        except json.JSONDecodeError as e:
            self.log.warning(f"Failed to parse message as JSON, using as string: {str(e)}")
            message_payload = self.message
        
        producer = self._get_producer()
        
        try:
            self.log.info(f"Publishing message to topic '{self.topic}' with key '{self.key}'")
            
            # Send message to Kafka
            future = producer.send(
                topic=self.topic,
                value=message_payload,
                key=self.key
            )
            
            # Wait for the message to be sent and get metadata
            record_metadata = future.get(timeout=30)
            
            result = {
                'topic': record_metadata.topic,
                'partition': record_metadata.partition,
                'offset': record_metadata.offset,
                'timestamp': record_metadata.timestamp,
                'key': self.key,
                'message_size': len(str(message_payload))
            }
            
            self.log.info(f"Successfully published message to {result['topic']}:{result['partition']}:{result['offset']}")
            
            return result
            
        except Exception as e:
            raise AirflowException(f"Failed to publish message to Kafka: {str(e)}")
        
        finally:
            # Ensure all messages are sent before closing
            if self._producer:
                try:
                    self._producer.flush(timeout=10)
                except Exception as e:
                    self.log.warning(f"Failed to flush producer: {str(e)}")
    
    def on_kill(self):
        """Clean up resources when task is killed."""
        if self._producer:
            try:
                self._producer.close(timeout=5)
                self.log.info("Closed Kafka producer")
            except Exception as e:
                self.log.warning(f"Error closing Kafka producer: {str(e)}")
