try:
    from airflow.sdk.bases.sensor import BaseSensor
except ImportError:
    from airflow.sensors.base import BaseSensor

from airflow.exceptions import AirflowException
from typing import Dict, Any, Optional, Sequence
import requests
import json
from datetime import timedelta


class ApiHealthSensor(BaseSensor):
    """
    Sensor that monitors API endpoint health and waits for successful response before proceeding.

    This sensor performs HTTP GET requests to a specified endpoint and checks for:
    - Expected HTTP status code
    - Optional response body validation using JSON path
    - Request timeout handling

    Args:
        endpoint_url (str): API endpoint URL to monitor
        expected_status_code (int): Expected HTTP status code for healthy response (default: 200)
        request_timeout (int): Request timeout in seconds (default: 30)
        headers (dict): Optional HTTP headers to include in request
        response_check (str): Optional JSON path to check in response body
        poke_interval (int): Time in seconds between pokes (default: 60)
        timeout (int): Maximum time to wait for condition in seconds (default: 300)
        mode (str): How the sensor operates - 'poke' or 'reschedule' (default: 'poke')
    """

    template_fields: Sequence[str] = ['endpoint_url', 'expected_status_code', 'headers', 'response_check']
    ui_color: str = "#50C878"

    def __init__(
        self,
        endpoint_url: str,
        expected_status_code: int = 200,
        request_timeout: int = 30,
        headers: Optional[Dict[str, str]] = None,
        response_check: Optional[str] = None,
        poke_interval: int = 60,
        timeout: int = 300,
        mode: str = 'poke',
        **kwargs
    ):
        super().__init__(
            poke_interval=poke_interval,
            timeout=timeout,
            mode=mode,
            **kwargs
        )
        self.endpoint_url = endpoint_url
        self.expected_status_code = expected_status_code
        self.request_timeout = request_timeout
        self.headers = headers or {}
        self.response_check = response_check

    def poke(self, context: Dict[str, Any]) -> bool:
        """
        Check if API endpoint is healthy by making HTTP request.

        Args:
            context: Airflow context dictionary

        Returns:
            bool: True if API is healthy (sensor succeeds),
                  False to continue poking

        Raises:
            AirflowException: For terminal failures like invalid URL or network errors
        """
        self.log.info(f"Checking API health for endpoint: {self.endpoint_url}")

        try:
            # Validate endpoint URL
            if not self.endpoint_url or not isinstance(self.endpoint_url, str):
                raise AirflowException("endpoint_url must be a non-empty string")

            # Make HTTP request
            self.log.info(f"Making GET request to {self.endpoint_url}")
            response = requests.get(
                url=self.endpoint_url,
                headers=self.headers,
                timeout=self.request_timeout,
                allow_redirects=True
            )

            self.log.info(f"Received response with status code: {response.status_code}")

            # Check status code
            if response.status_code != self.expected_status_code:
                self.log.warning(
                    f"Status code {response.status_code} does not match expected {self.expected_status_code}"
                )
                return False

            # Check response body if response_check is provided
            if self.response_check:
                try:
                    response_json = response.json()
                    if not self._check_json_path(response_json, self.response_check):
                        self.log.warning(f"Response check failed for path: {self.response_check}")
                        return False
                except json.JSONDecodeError:
                    self.log.warning("Response is not valid JSON, cannot perform response check")
                    return False

            self.log.info("API health check passed successfully")
            return True

        except requests.exceptions.Timeout:
            self.log.warning(f"Request timeout after {self.request_timeout} seconds")
            return False

        except requests.exceptions.ConnectionError as e:
            self.log.warning(f"Connection error: {str(e)}")
            return False

        except requests.exceptions.RequestException as e:
            raise AirflowException(f"Request failed with error: {str(e)}")

        except Exception as e:
            raise AirflowException(f"Unexpected error during API health check: {str(e)}")

    def _check_json_path(self, response_json: Dict[str, Any], json_path: str) -> bool:
        """
        Check if a JSON path exists and has a truthy value in the response.

        Args:
            response_json: Parsed JSON response
            json_path: Dot-separated path to check (e.g., 'status.health')

        Returns:
            bool: True if path exists and has truthy value, False otherwise
        """
        try:
            current = response_json
            path_parts = json_path.split('.')

            for part in path_parts:
                if isinstance(current, dict) and part in current:
                    current = current[part]
                else:
                    self.log.warning(f"JSON path '{json_path}' not found in response")
                    return False

            # Check if the final value is truthy
            result = bool(current)
            self.log.info(f"JSON path '{json_path}' check result: {result}")
            return result

        except Exception as e:
            self.log.warning(f"Error checking JSON path '{json_path}': {str(e)}")
            return False
