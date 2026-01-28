from airflow.sensors.base import BaseSensor
from airflow.exceptions import AirflowException
from airflow.hooks.base import BaseHook
from typing import Dict, Any, Optional, Sequence
import redis


class RedisKeySensor(BaseSensor):
    """
    Sensor that waits for a key to exist in Redis with optional value checking.
    
    This sensor will poke Redis at regular intervals to check if a specified key exists.
    Optionally, it can also verify that the key contains an expected value.
    
    Args:
        key: Redis key to wait for
        expected_value: Expected value for the key (optional)
        redis_conn_id: Airflow connection ID for Redis (default: 'redis_default')
        db: Redis database number (default: 0)
        poke_interval: Time in seconds between pokes (default: 60)
        timeout: Maximum time to wait in seconds (default: 60*60*24*7)
        mode: How the sensor operates - 'poke' or 'reschedule' (default: 'poke')
    """
    
    template_fields: Sequence[str] = ['key', 'expected_value']
    ui_color: str = "#dc143c"
    
    def __init__(
        self,
        key: str,
        expected_value: Optional[str] = None,
        redis_conn_id: str = 'redis_default',
        db: int = 0,
        poke_interval: int = 60,
        timeout: int = 60 * 60 * 24 * 7,
        mode: str = 'poke',
        **kwargs
    ):
        super().__init__(
            poke_interval=poke_interval,
            timeout=timeout,
            mode=mode,
            **kwargs
        )
        self.key = key
        self.expected_value = expected_value
        self.redis_conn_id = redis_conn_id
        self.db = db
        self._redis_client = None
    
    def _get_redis_client(self) -> redis.Redis:
        """
        Get Redis client using Airflow connection.
        
        Returns:
            redis.Redis: Redis client instance
        """
        if self._redis_client is None:
            try:
                connection = BaseHook.get_connection(self.redis_conn_id)
                self._redis_client = redis.Redis(
                    host=connection.host or 'localhost',
                    port=connection.port or 6379,
                    db=self.db,
                    password=connection.password,
                    username=connection.login,
                    decode_responses=True,
                    socket_connect_timeout=10,
                    socket_timeout=10
                )
            except Exception as e:
                raise AirflowException(f"Failed to create Redis connection: {str(e)}")
        
        return self._redis_client
    
    def poke(self, context: Dict[str, Any]) -> bool:
        """
        Check if the Redis key exists and optionally matches expected value.
        
        Args:
            context: Airflow context dictionary
            
        Returns:
            bool: True if condition is met (key exists and value matches if specified),
                  False to continue poking
                  
        Raises:
            AirflowException: For connection errors or other terminal failures
        """
        if not self.key or self.key.strip() == '':
            raise AirflowException("Redis key cannot be empty")
        
        redis_client = self._get_redis_client()
        
        try:
            # Test connection
            redis_client.ping()
            
            # Check if key exists
            if not redis_client.exists(self.key):
                self.log.info(f"Key '{self.key}' does not exist in Redis")
                return False
            
            self.log.info(f"Key '{self.key}' exists in Redis")
            
            # If expected value is specified, check the value
            if self.expected_value is not None:
                actual_value = redis_client.get(self.key)
                if actual_value != self.expected_value:
                    self.log.info(
                        f"Key '{self.key}' exists but value '{actual_value}' "
                        f"does not match expected value '{self.expected_value}'"
                    )
                    return False
                
                self.log.info(
                    f"Key '{self.key}' exists with expected value '{self.expected_value}'"
                )
            
            return True
            
        except redis.ConnectionError as e:
            raise AirflowException(f"Redis connection error: {str(e)}")
        except redis.TimeoutError as e:
            raise AirflowException(f"Redis timeout error: {str(e)}")
        except redis.AuthenticationError as e:
            raise AirflowException(f"Redis authentication error: {str(e)}")
        except Exception as e:
            raise AirflowException(f"Unexpected error while checking Redis key: {str(e)}")