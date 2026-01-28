from airflow.models import BaseOperator
from airflow.exceptions import AirflowException
from typing import Dict, Any, Optional, Sequence, Union
import requests
from requests.auth import HTTPBasicAuth, HTTPDigestAuth
import json


class HttpRequestOperator(BaseOperator):
    """
    Operator for making HTTP requests with support for all methods, headers, authentication, and response handling.
    
    This operator can make HTTP requests to any URL with configurable method, headers, data, timeout,
    and SSL verification. It supports various authentication methods and provides comprehensive
    response handling and logging.
    
    :param url: URL to send request to
    :type url: str
    :param method: HTTP method (GET, POST, PUT, DELETE, PATCH)
    :type method: str
    :param headers: HTTP headers to include in the request
    :type headers: dict
    :param data: Request body data (will be JSON serialized if dict)
    :type data: dict
    :param timeout: Request timeout in seconds
    :type timeout: int
    :param verify_ssl: Whether to verify SSL certificates
    :type verify_ssl: bool
    :param auth_type: Authentication type ('basic', 'digest', 'bearer')
    :type auth_type: str
    :param username: Username for authentication
    :type username: str
    :param password: Password for authentication
    :type password: str
    :param token: Bearer token for authentication
    :type token: str
    :param expected_status_codes: List of expected HTTP status codes for success
    :type expected_status_codes: list
    """
    
    template_fields: Sequence[str] = ['url', 'method', 'headers', 'data']
    ui_color: str = "#4CAF50"
    
    def __init__(
        self,
        url: str,
        method: str = 'GET',
        headers: Optional[Dict[str, str]] = None,
        data: Optional[Union[Dict[str, Any], str]] = None,
        timeout: int = 30,
        verify_ssl: bool = True,
        auth_type: Optional[str] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
        token: Optional[str] = None,
        expected_status_codes: Optional[list] = None,
        **kwargs
    ):
        super().__init__(**kwargs)
        
        # Store all parameters
        self.url = url
        self.method = method.upper() if method else 'GET'
        self.headers = headers or {}
        self.data = data
        self.timeout = timeout
        self.verify_ssl = verify_ssl
        self.auth_type = auth_type
        self.username = username
        self.password = password
        self.token = token
        self.expected_status_codes = expected_status_codes or [200, 201, 202, 204]
        
        # Validate non-template fields
        if not isinstance(self.timeout, int) or self.timeout <= 0:
            raise AirflowException("timeout must be a positive integer")
        
        if not isinstance(self.verify_ssl, bool):
            raise AirflowException("verify_ssl must be a boolean")
        
        # Validate method if not a template
        valid_methods = ['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'HEAD', 'OPTIONS']
        if '{{' not in str(self.method) and self.method not in valid_methods:
            raise AirflowException(f"method must be one of {valid_methods}")
        
        # Validate auth_type if provided
        if self.auth_type and '{{' not in str(self.auth_type):
            valid_auth_types = ['basic', 'digest', 'bearer']
            if self.auth_type not in valid_auth_types:
                raise AirflowException(f"auth_type must be one of {valid_auth_types}")
        
        self.log.info(f"Initialized HttpRequestOperator for {self.method} request")
    
    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the HTTP request
        
        Args:
            context: Airflow context dict with task_instance, execution_date, etc.
            
        Returns:
            Dict[str, Any]: Response data including status_code, headers, and content
            
        Raises:
            AirflowException: On request failure or invalid response
        """
        self.log.info(f"Executing HTTP {self.method} request to {self.url}")
        
        # Validate template fields after rendering
        valid_methods = ['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'HEAD', 'OPTIONS']
        if self.method not in valid_methods:
            raise AirflowException(f"Invalid method '{self.method}'. Must be one of {valid_methods}")
        
        if not self.url or not isinstance(self.url, str):
            raise AirflowException("url must be a non-empty string")
        
        if not self.url.startswith(('http://', 'https://')):
            raise AirflowException("url must start with http:// or https://")
        
        try:
            # Prepare request parameters
            request_kwargs = {
                'timeout': self.timeout,
                'verify': self.verify_ssl,
                'headers': self.headers.copy() if self.headers else {}
            }
            
            # Handle authentication
            if self.auth_type:
                if self.auth_type == 'basic':
                    if not self.username or not self.password:
                        raise AirflowException("username and password required for basic auth")
                    request_kwargs['auth'] = HTTPBasicAuth(self.username, self.password)
                elif self.auth_type == 'digest':
                    if not self.username or not self.password:
                        raise AirflowException("username and password required for digest auth")
                    request_kwargs['auth'] = HTTPDigestAuth(self.username, self.password)
                elif self.auth_type == 'bearer':
                    if not self.token:
                        raise AirflowException("token required for bearer auth")
                    request_kwargs['headers']['Authorization'] = f'Bearer {self.token}'
            
            # Handle request data
            if self.data:
                if self.method in ['POST', 'PUT', 'PATCH']:
                    if isinstance(self.data, dict):
                        request_kwargs['json'] = self.data
                        if 'Content-Type' not in request_kwargs['headers']:
                            request_kwargs['headers']['Content-Type'] = 'application/json'
                    else:
                        request_kwargs['data'] = self.data
                else:
                    self.log.warning(f"Data provided for {self.method} request, adding as query parameters")
                    if isinstance(self.data, dict):
                        request_kwargs['params'] = self.data
            
            # Log request details (without sensitive data)
            safe_headers = {k: v for k, v in request_kwargs['headers'].items() 
                          if k.lower() not in ['authorization', 'x-api-key']}
            self.log.info(f"Request details - Method: {self.method}, Headers: {safe_headers}")
            
            # Make the HTTP request
            response = requests.request(
                method=self.method,
                url=self.url,
                **request_kwargs
            )
            
            # Log response details
            self.log.info(f"Response received - Status: {response.status_code}, "
                         f"Content-Length: {len(response.content)}")
            
            # Check if status code is expected
            if response.status_code not in self.expected_status_codes:
                error_msg = (f"HTTP request failed with status {response.status_code}. "
                           f"Expected one of {self.expected_status_codes}. "
                           f"Response: {response.text[:500]}")
                self.log.error(error_msg)
                raise AirflowException(error_msg)
            
            # Prepare response data
            response_data = {
                'status_code': response.status_code,
                'headers': dict(response.headers),
                'url': response.url,
                'elapsed_seconds': response.elapsed.total_seconds()
            }
            
            # Try to parse JSON response, fallback to text
            try:
                response_data['json'] = response.json()
                self.log.info("Response parsed as JSON")
            except (ValueError, json.JSONDecodeError):
                response_data['text'] = response.text
                self.log.info("Response stored as text")
            
            self.log.info(f"HTTP request completed successfully in {response_data['elapsed_seconds']:.2f} seconds")
            return response_data
            
        except requests.exceptions.Timeout:
            error_msg = f"HTTP request timed out after {self.timeout} seconds"
            self.log.error(error_msg)
            raise AirflowException(error_msg)
        
        except requests.exceptions.ConnectionError as e:
            error_msg = f"Connection error: {str(e)}"
            self.log.error(error_msg)
            raise AirflowException(error_msg)
        
        except requests.exceptions.SSLError as e:
            error_msg = f"SSL error: {str(e)}"
            self.log.error(error_msg)
            raise AirflowException(error_msg)
        
        except requests.exceptions.RequestException as e:
            error_msg = f"HTTP request failed: {str(e)}"
            self.log.error(error_msg)
            raise AirflowException(error_msg)
        
        except Exception as e:
            error_msg = f"Unexpected error during HTTP request: {str(e)}"
            self.log.error(error_msg)
            raise AirflowException(error_msg)