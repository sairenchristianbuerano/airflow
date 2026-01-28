# ============================================================================
# PYTEST TEST FILE - DO NOT PLACE IN AIRFLOW DAGS FOLDER
# ============================================================================
# This file is for running with pytest, NOT for Airflow execution.
# Place this file in: tests/ folder or any location outside dags/
#
# To run tests:
#   pytest test_rest_api_hook.py -v
#
# Required packages:
#   pip install pytest pytest-mock
# ============================================================================

"""
Tests for RestApiHook

Auto-generated test file for Airflow hook with comprehensive mocking.

WARNING: This is a pytest test file. Do NOT place in Airflow dags folder.
         Place in a 'tests/' directory instead.
"""

# Prevent Airflow from loading this as a DAG
try:
    import pytest
except ImportError:
    raise ImportError(
        "pytest is required to run this test file. "
        "Install with: pip install pytest pytest-mock\n"
        "NOTE: This file should NOT be in the Airflow dags folder."
    )

from unittest.mock import MagicMock, patch
from airflow.models import Connection

# Import the hook being tested
try:
    from rest_api_hook import RestApiHook
except ImportError:
    try:
        from custom_operators.rest_api_hook import RestApiHook
    except ImportError:
        raise ImportError(
            f"Could not import RestApiHook. "
            f"Ensure 'rest_api_hook.py' is in the Python path."
        )


class TestRestApiHook:
    """Test suite for RestApiHook"""

    def test_hook_initialization(self):
        """Test that hook can be instantiated"""
        hook = RestApiHook()
        assert hook is not None

    def test_hook_with_parameters(self):
        """Test hook initialization with custom parameters"""
        hook = RestApiHook(
            conn_id='my_api_conn',
            base_url='https://api.example.com',
            auth_type='bearer',
            retry_count=5,
            timeout=60
        )

        assert hook.conn_id == 'my_api_conn'
        assert hook.base_url == 'https://api.example.com'
        assert hook.auth_type == 'bearer'
        assert hook.retry_count == 5
        assert hook.timeout == 60

    def test_get_conn_method_exists(self):
        """Test that get_conn method is defined"""
        hook = RestApiHook()

        assert hasattr(hook, 'get_conn')
        assert callable(hook.get_conn)

    def test_make_request_method_exists(self):
        """Test that make_request method is defined"""
        hook = RestApiHook()

        assert hasattr(hook, 'make_request')
        assert callable(hook.make_request)

    def test_http_methods_exist(self):
        """Test that HTTP method shortcuts are defined"""
        hook = RestApiHook()

        assert hasattr(hook, 'get')
        assert hasattr(hook, 'post')
        assert hasattr(hook, 'put')
        assert hasattr(hook, 'delete')
        assert hasattr(hook, 'patch')

    def test_conn_name_attr(self):
        """Test that conn_name_attr is defined"""
        hook = RestApiHook()
        assert hasattr(hook, 'conn_name_attr')
        assert hook.conn_name_attr == 'conn_id'

    def test_conn_type(self):
        """Test that conn_type is defined"""
        hook = RestApiHook()
        assert hasattr(hook, 'conn_type')
        assert hook.conn_type == 'http'

    def test_hook_name(self):
        """Test that hook_name is defined"""
        hook = RestApiHook()
        assert hasattr(hook, 'hook_name')
        assert hook.hook_name == 'rest_api'

    def test_template_fields(self):
        """Test that template_fields is defined"""
        hook = RestApiHook()
        assert hasattr(hook, 'template_fields')
        assert isinstance(hook.template_fields, (list, tuple))
        assert 'endpoint' in hook.template_fields
        assert 'method' in hook.template_fields

    def test_default_headers(self):
        """Test default headers initialization"""
        hook = RestApiHook(
            default_headers={'Content-Type': 'application/json'}
        )
        assert hook.default_headers == {'Content-Type': 'application/json'}

    def test_close_method(self):
        """Test that close method is defined"""
        hook = RestApiHook()
        assert hasattr(hook, 'close')
        assert callable(hook.close)

    def test_test_connection_method(self):
        """Test that test_connection method is defined"""
        hook = RestApiHook()
        assert hasattr(hook, 'test_connection')
        assert callable(hook.test_connection)

    @patch('rest_api_hook.BaseHook.get_connection')
    def test_get_base_url_from_connection(self, mock_get_connection):
        """Test base URL extraction from connection"""
        mock_conn = MagicMock(spec=Connection)
        mock_conn.host = 'api.example.com'
        mock_conn.port = 443
        mock_conn.schema = 'https'
        mock_conn.extra_dejson = {}
        mock_get_connection.return_value = mock_conn

        hook = RestApiHook()
        base_url = hook._get_base_url(mock_conn)

        assert 'api.example.com' in base_url
        assert 'https' in base_url

    def test_get_base_url_from_parameter(self):
        """Test base URL from hook parameter takes precedence"""
        hook = RestApiHook(base_url='https://custom.api.com')
        mock_conn = MagicMock(spec=Connection)

        base_url = hook._get_base_url(mock_conn)
        assert base_url == 'https://custom.api.com'
