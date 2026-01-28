from airflow.hooks.base import BaseHook
from airflow.models import Connection
from airflow.exceptions import AirflowException
from typing import Dict, Any, Optional, Sequence, Union
import requests
import time
import base64
from urllib.parse import urljoin


class RestApiHook(BaseHook):
    """
    Hook for connecting to REST APIs with authentication, retry logic, and response handling.

    This hook provides a standardized way to interact with REST APIs, supporting various
    authentication methods, automatic retries, and comprehensive error handling.

    :param conn_id: Connection ID for the REST API
    :param base_url: Base URL for the REST API
    :param auth_type: Authentication type (none, basic, bearer, api_key)
    :param default_headers: Default headers to include in all requests
    :param retry_count: Number of retries for failed requests
    :param timeout: Request timeout in seconds
    """

    template_fields: Sequence[str] = ['endpoint', 'method']
    ui_color: str = "#f0ede4"
    conn_name_attr: str = 'conn_id'
    conn_type: str = 'http'
    hook_name: str = 'rest_api'

    def __init__(
        self,
        conn_id: str = 'rest_api_default',
        base_url: Optional[str] = None,
        auth_type: str = 'none',
        default_headers: Optional[Dict[str, str]] = None,
        retry_count: int = 3,
        timeout: int = 30
    ):
        super().__init__()
        self.conn_id = conn_id
        self.base_url = base_url
        self.auth_type = auth_type
        self.default_headers = default_headers or {}
        self.retry_count = retry_count
        self.timeout = timeout
        self._connection = None
        self._session = None

    def get_conn(self) -> requests.Session:
        """
        Get or create HTTP session with authentication and default headers.

        Returns:
            requests.Session: Configured session object

        Raises:
            AirflowException: If connection cannot be established
        """
        if self._session is not None:
            return self._session

        try:
            conn = BaseHook.get_connection(self.conn_id)
            self._session = self._create_session(conn)
            self.log.info(f"Connected to REST API at {self._get_base_url(conn)}")
            return self._session
        except Exception as e:
            raise AirflowException(f"Failed to create REST API connection: {str(e)}")

    def _create_session(self, conn: Connection) -> requests.Session:
        """
        Create and configure requests session from Airflow connection.

        :param conn: Airflow connection object
        :return: Configured requests session
        """
        session = requests.Session()

        # Set default headers
        session.headers.update(self.default_headers)

        # Configure authentication
        auth_type = conn.extra_dejson.get('auth_type', self.auth_type)

        if auth_type == 'basic' and conn.login and conn.password:
            session.auth = (conn.login, conn.password)
        elif auth_type == 'bearer' and conn.password:
            session.headers['Authorization'] = f'Bearer {conn.password}'
        elif auth_type == 'api_key':
            api_key = conn.password or conn.extra_dejson.get('api_key')
            api_key_header = conn.extra_dejson.get('api_key_header', 'X-API-Key')
            if api_key:
                session.headers[api_key_header] = api_key

        # Set additional headers from connection
        extra_headers = conn.extra_dejson.get('headers', {})
        if extra_headers:
            session.headers.update(extra_headers)

        return session

    def _get_base_url(self, conn: Connection) -> str:
        """
        Get base URL from connection or hook parameter.

        :param conn: Airflow connection object
        :return: Base URL string
        """
        if self.base_url:
            return self.base_url

        if conn.host:
            scheme = conn.schema or 'https'
            port = f':{conn.port}' if conn.port else ''
            return f'{scheme}://{conn.host}{port}'

        raise AirflowException("No base URL provided in connection or hook parameters")

    def make_request(
        self,
        endpoint: str,
        method: str = 'GET',
        data: Optional[Union[Dict[str, Any], str]] = None,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        json_data: Optional[Dict[str, Any]] = None
    ) -> requests.Response:
        """
        Make HTTP request to the API with retry logic.

        :param endpoint: API endpoint path
        :param method: HTTP method (GET, POST, PUT, DELETE, etc.)
        :param data: Request body data
        :param params: URL parameters
        :param headers: Additional headers for this request
        :param json_data: JSON data to send in request body
        :return: Response object
        :raises: AirflowException if request fails after all retries
        """
        session = self.get_conn()
        conn = BaseHook.get_connection(self.conn_id)
        base_url = self._get_base_url(conn)

        url = urljoin(base_url.rstrip('/') + '/', endpoint.lstrip('/'))

        # Prepare request parameters
        request_kwargs = {
            'timeout': self.timeout,
            'params': params
        }

        if headers:
            request_kwargs['headers'] = headers

        if json_data is not None:
            request_kwargs['json'] = json_data
        elif data is not None:
            request_kwargs['data'] = data

        # Retry logic
        last_exception = None
        for attempt in range(self.retry_count + 1):
            try:
                self.log.info(f"Making {method} request to {url} (attempt {attempt + 1})")
                response = session.request(method.upper(), url, **request_kwargs)

                # Check for HTTP errors
                if response.status_code >= 400:
                    error_msg = f"HTTP {response.status_code}: {response.text}"
                    if response.status_code >= 500 and attempt < self.retry_count:
                        self.log.warning(f"Server error, retrying: {error_msg}")
                        time.sleep(2 ** attempt)  # Exponential backoff
                        continue
                    else:
                        raise AirflowException(error_msg)

                self.log.info(f"Request successful: {response.status_code}")
                return response

            except requests.exceptions.RequestException as e:
                last_exception = e
                if attempt < self.retry_count:
                    self.log.warning(f"Request failed, retrying: {str(e)}")
                    time.sleep(2 ** attempt)  # Exponential backoff
                else:
                    break

        raise AirflowException(f"Request failed after {self.retry_count + 1} attempts: {str(last_exception)}")

    def get(self, endpoint: str, **kwargs) -> requests.Response:
        """Make GET request to the API."""
        return self.make_request(endpoint, 'GET', **kwargs)

    def post(self, endpoint: str, **kwargs) -> requests.Response:
        """Make POST request to the API."""
        return self.make_request(endpoint, 'POST', **kwargs)

    def put(self, endpoint: str, **kwargs) -> requests.Response:
        """Make PUT request to the API."""
        return self.make_request(endpoint, 'PUT', **kwargs)

    def delete(self, endpoint: str, **kwargs) -> requests.Response:
        """Make DELETE request to the API."""
        return self.make_request(endpoint, 'DELETE', **kwargs)

    def patch(self, endpoint: str, **kwargs) -> requests.Response:
        """Make PATCH request to the API."""
        return self.make_request(endpoint, 'PATCH', **kwargs)

    def test_connection(self) -> bool:
        """
        Test the API connection.

        :return: True if connection is successful, False otherwise
        """
        try:
            session = self.get_conn()
            conn = BaseHook.get_connection(self.conn_id)
            base_url = self._get_base_url(conn)

            # Try to make a simple request to test connectivity
            test_endpoint = conn.extra_dejson.get('test_endpoint', '/')
            response = session.get(urljoin(base_url, test_endpoint), timeout=10)

            self.log.info(f"Connection test successful: {response.status_code}")
            return True

        except Exception as e:
            self.log.error(f"Connection test failed: {str(e)}")
            return False

    def close(self):
        """Close the HTTP session."""
        if self._session:
            self._session.close()
            self._session = None
            self.log.info("REST API session closed")
