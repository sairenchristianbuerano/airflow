#!/usr/bin/env python3
"""
Phase 4: Native Python Fallback Generator

This module generates native Python implementations when external libraries
are unavailable, learns from successful fallbacks, and maintains a database
of fallback code patterns.

Key Features:
- Generate native Python code for common operations
- Learn from successful fallbacks
- Track fallback usage and effectiveness
- Build fallback code database over time
- Category-specific fallback strategies
"""

import sqlite3
import os
import json
import re
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
import logging


@dataclass
class FallbackCode:
    """Represents a fallback code implementation"""
    library_name: str
    operation_type: str
    fallback_code: str
    description: str
    category: str
    uses_stdlib_only: bool = True
    minimal_dependencies: List[str] = field(default_factory=list)
    usage_count: int = 0
    success_count: int = 0
    failure_count: int = 0
    effectiveness_score: float = 0.0


class NativeFallbackGenerator:
    """
    Generate native Python implementations when external libraries are unavailable.

    This class provides:
    1. Pre-built fallback code for common operations
    2. Dynamic fallback generation based on library usage patterns
    3. Learning from successful fallbacks
    4. Database storage for fallback code patterns
    """

    # Pre-built native implementations for common libraries
    NATIVE_FALLBACKS = {
        # HTTP Operations
        "requests": {
            "get": '''
def http_get(url: str, headers: dict = None, params: dict = None, timeout: int = 30) -> dict:
    """
    Make HTTP GET request using urllib (requests alternative).
    Returns dict with 'status_code', 'headers', 'text', 'json' keys.
    """
    import urllib.request
    import urllib.parse
    import json as json_module

    headers = headers or {}
    if params:
        url = f"{url}?{urllib.parse.urlencode(params)}"

    req = urllib.request.Request(url, headers=headers, method="GET")

    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            text = response.read().decode('utf-8')
            return {
                'status_code': response.status,
                'headers': dict(response.headers),
                'text': text,
                'json': lambda: json_module.loads(text)
            }
    except urllib.error.HTTPError as e:
        return {
            'status_code': e.code,
            'headers': dict(e.headers) if e.headers else {},
            'text': e.read().decode('utf-8') if e.fp else '',
            'json': lambda: {}
        }
''',
            "post": '''
def http_post(url: str, data: dict = None, json_data: dict = None, headers: dict = None, timeout: int = 30) -> dict:
    """
    Make HTTP POST request using urllib (requests alternative).
    Returns dict with 'status_code', 'headers', 'text', 'json' keys.
    """
    import urllib.request
    import json as json_module

    headers = headers or {}

    if json_data:
        data = json_module.dumps(json_data).encode('utf-8')
        headers['Content-Type'] = 'application/json'
    elif data:
        data = urllib.parse.urlencode(data).encode('utf-8')
        headers['Content-Type'] = 'application/x-www-form-urlencoded'

    req = urllib.request.Request(url, data=data, headers=headers, method="POST")

    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            text = response.read().decode('utf-8')
            return {
                'status_code': response.status,
                'headers': dict(response.headers),
                'text': text,
                'json': lambda: json_module.loads(text)
            }
    except urllib.error.HTTPError as e:
        return {
            'status_code': e.code,
            'headers': dict(e.headers) if e.headers else {},
            'text': e.read().decode('utf-8') if e.fp else '',
            'json': lambda: {}
        }
''',
            "request": '''
def http_request(url: str, method: str = "GET", data: dict = None, json_data: dict = None,
                 headers: dict = None, params: dict = None, timeout: int = 30) -> dict:
    """
    Generic HTTP request using urllib (requests alternative).
    Supports GET, POST, PUT, DELETE, PATCH methods.
    Returns dict with 'status_code', 'headers', 'text', 'json' keys.
    """
    import urllib.request
    import urllib.parse
    import json as json_module

    headers = headers or {}

    # Add query parameters for GET requests
    if params and method.upper() == "GET":
        url = f"{url}?{urllib.parse.urlencode(params)}"

    # Prepare request body
    body = None
    if json_data:
        body = json_module.dumps(json_data).encode('utf-8')
        headers['Content-Type'] = 'application/json'
    elif data and method.upper() != "GET":
        body = urllib.parse.urlencode(data).encode('utf-8')
        headers['Content-Type'] = 'application/x-www-form-urlencoded'

    req = urllib.request.Request(url, data=body, headers=headers, method=method.upper())

    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            text = response.read().decode('utf-8')
            return {
                'status_code': response.status,
                'headers': dict(response.headers),
                'text': text,
                'json': lambda: json_module.loads(text),
                'ok': 200 <= response.status < 300
            }
    except urllib.error.HTTPError as e:
        text = e.read().decode('utf-8') if e.fp else ''
        return {
            'status_code': e.code,
            'headers': dict(e.headers) if e.headers else {},
            'text': text,
            'json': lambda: json_module.loads(text) if text else {},
            'ok': False
        }
'''
        },

        # CSV Operations
        "pandas": {
            "read_csv": '''
def read_csv(filepath: str, delimiter: str = ',', has_header: bool = True) -> list:
    """
    Read CSV file and return list of dictionaries (pandas alternative).
    Each row is a dict with column names as keys.
    """
    import csv

    with open(filepath, 'r', newline='', encoding='utf-8') as f:
        if has_header:
            reader = csv.DictReader(f, delimiter=delimiter)
            return list(reader)
        else:
            reader = csv.reader(f, delimiter=delimiter)
            return [row for row in reader]
''',
            "to_csv": '''
def to_csv(data: list, filepath: str, delimiter: str = ',', include_header: bool = True) -> None:
    """
    Write list of dictionaries to CSV file (pandas alternative).
    Each dict in the list becomes a row.
    """
    import csv

    if not data:
        return

    with open(filepath, 'w', newline='', encoding='utf-8') as f:
        if isinstance(data[0], dict):
            writer = csv.DictWriter(f, fieldnames=data[0].keys(), delimiter=delimiter)
            if include_header:
                writer.writeheader()
            writer.writerows(data)
        else:
            writer = csv.writer(f, delimiter=delimiter)
            writer.writerows(data)
''',
            "dataframe_operations": '''
class SimpleDataFrame:
    """
    Minimal DataFrame-like operations (pandas alternative).
    Supports basic filtering, sorting, and aggregation.
    """

    def __init__(self, data: list):
        """Initialize with list of dictionaries"""
        self.data = data
        self.columns = list(data[0].keys()) if data else []

    def __len__(self):
        return len(self.data)

    def __iter__(self):
        return iter(self.data)

    def filter(self, condition_func) -> 'SimpleDataFrame':
        """Filter rows by condition function"""
        return SimpleDataFrame([row for row in self.data if condition_func(row)])

    def sort_by(self, column: str, reverse: bool = False) -> 'SimpleDataFrame':
        """Sort by column"""
        return SimpleDataFrame(sorted(self.data, key=lambda x: x.get(column), reverse=reverse))

    def select(self, columns: list) -> 'SimpleDataFrame':
        """Select specific columns"""
        return SimpleDataFrame([{k: row[k] for k in columns if k in row} for row in self.data])

    def to_list(self) -> list:
        """Convert to list of dicts"""
        return self.data

    def group_by(self, column: str) -> dict:
        """Group by column, returns dict of lists"""
        groups = {}
        for row in self.data:
            key = row.get(column)
            if key not in groups:
                groups[key] = []
            groups[key].append(row)
        return groups

    def aggregate(self, column: str, func: str = 'sum') -> float:
        """Aggregate column (sum, mean, min, max, count)"""
        values = [float(row.get(column, 0)) for row in self.data if row.get(column) is not None]
        if not values:
            return 0
        if func == 'sum':
            return sum(values)
        elif func == 'mean':
            return sum(values) / len(values)
        elif func == 'min':
            return min(values)
        elif func == 'max':
            return max(values)
        elif func == 'count':
            return len(values)
        return 0
'''
        },

        # JSON Operations
        "json": {
            "load_file": '''
def load_json_file(filepath: str) -> dict:
    """Load JSON from file"""
    import json
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)
''',
            "save_file": '''
def save_json_file(data: dict, filepath: str, indent: int = 2) -> None:
    """Save dict to JSON file"""
    import json
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=indent, default=str)
''',
            "parse": '''
def parse_json(text: str) -> dict:
    """Parse JSON string to dict"""
    import json
    return json.loads(text)
''',
            "stringify": '''
def stringify_json(data: dict, indent: int = None) -> str:
    """Convert dict to JSON string"""
    import json
    return json.dumps(data, indent=indent, default=str)
'''
        },

        # File Operations
        "pathlib": {
            "read_text": '''
def read_text_file(filepath: str, encoding: str = 'utf-8') -> str:
    """Read text file content"""
    with open(filepath, 'r', encoding=encoding) as f:
        return f.read()
''',
            "write_text": '''
def write_text_file(filepath: str, content: str, encoding: str = 'utf-8') -> None:
    """Write text content to file"""
    import os
    os.makedirs(os.path.dirname(filepath), exist_ok=True) if os.path.dirname(filepath) else None
    with open(filepath, 'w', encoding=encoding) as f:
        f.write(content)
''',
            "list_files": '''
def list_files(directory: str, pattern: str = '*') -> list:
    """List files in directory matching pattern"""
    import os
    import fnmatch

    matches = []
    for root, dirs, files in os.walk(directory):
        for filename in fnmatch.filter(files, pattern):
            matches.append(os.path.join(root, filename))
    return matches
''',
            "file_exists": '''
def file_exists(filepath: str) -> bool:
    """Check if file exists"""
    import os
    return os.path.isfile(filepath)
'''
        },

        # Date/Time Operations
        "dateutil": {
            "parse_date": '''
def parse_date(date_string: str) -> 'datetime':
    """
    Parse date string to datetime (dateutil alternative).
    Supports common formats: ISO, US, EU styles.
    """
    from datetime import datetime

    formats = [
        '%Y-%m-%d',
        '%Y-%m-%dT%H:%M:%S',
        '%Y-%m-%dT%H:%M:%SZ',
        '%Y-%m-%dT%H:%M:%S.%f',
        '%Y-%m-%dT%H:%M:%S.%fZ',
        '%Y/%m/%d',
        '%d/%m/%Y',
        '%m/%d/%Y',
        '%d-%m-%Y',
        '%Y-%m-%d %H:%M:%S',
        '%d %b %Y',
        '%d %B %Y',
    ]

    for fmt in formats:
        try:
            return datetime.strptime(date_string.strip(), fmt)
        except ValueError:
            continue

    raise ValueError(f"Unable to parse date: {date_string}")
''',
            "format_date": '''
def format_date(dt: 'datetime', format_str: str = '%Y-%m-%d') -> str:
    """Format datetime to string"""
    return dt.strftime(format_str)
''',
            "date_diff": '''
def date_diff(date1: 'datetime', date2: 'datetime', unit: str = 'days') -> float:
    """Calculate difference between two dates"""
    diff = date2 - date1
    if unit == 'days':
        return diff.days
    elif unit == 'hours':
        return diff.total_seconds() / 3600
    elif unit == 'minutes':
        return diff.total_seconds() / 60
    elif unit == 'seconds':
        return diff.total_seconds()
    return diff.days
'''
        },

        # Retry/Backoff Operations
        "tenacity": {
            "retry": '''
def retry_with_backoff(func, max_attempts: int = 3, initial_delay: float = 1.0,
                       backoff_factor: float = 2.0, exceptions: tuple = (Exception,)):
    """
    Retry function with exponential backoff (tenacity alternative).
    Returns result of successful call or raises last exception.
    """
    import time

    delay = initial_delay
    last_exception = None

    for attempt in range(max_attempts):
        try:
            return func()
        except exceptions as e:
            last_exception = e
            if attempt < max_attempts - 1:
                time.sleep(delay)
                delay *= backoff_factor

    raise last_exception
''',
            "retry_decorator": '''
def retry_decorator(max_attempts: int = 3, delay: float = 1.0, backoff: float = 2.0):
    """
    Decorator for retry with exponential backoff (tenacity alternative).
    """
    import time
    import functools

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            current_delay = delay
            last_exception = None

            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_attempts - 1:
                        time.sleep(current_delay)
                        current_delay *= backoff

            raise last_exception
        return wrapper
    return decorator
'''
        },

        # Validation Operations
        "pydantic": {
            "validate_dict": '''
def validate_dict(data: dict, schema: dict) -> tuple:
    """
    Validate dictionary against schema (pydantic alternative).
    Schema format: {'field': {'type': str/int/float/bool/list/dict, 'required': bool, 'default': value}}
    Returns (is_valid, errors, validated_data)
    """
    errors = []
    validated = {}

    for field, rules in schema.items():
        value = data.get(field)
        required = rules.get('required', False)
        expected_type = rules.get('type', str)
        default = rules.get('default')

        if value is None:
            if required:
                errors.append(f"Field '{field}' is required")
                continue
            elif default is not None:
                validated[field] = default
                continue
            else:
                continue

        # Type validation
        type_map = {
            'str': str, 'string': str,
            'int': int, 'integer': int,
            'float': float, 'number': float,
            'bool': bool, 'boolean': bool,
            'list': list, 'array': list,
            'dict': dict, 'object': dict,
        }

        if isinstance(expected_type, str):
            expected_type = type_map.get(expected_type.lower(), str)

        if not isinstance(value, expected_type):
            try:
                value = expected_type(value)
            except (ValueError, TypeError):
                errors.append(f"Field '{field}' must be {expected_type.__name__}")
                continue

        validated[field] = value

    return (len(errors) == 0, errors, validated)
'''
        },

        # Logging Operations
        "structlog": {
            "structured_logger": '''
class StructuredLogger:
    """
    Simple structured logging (structlog alternative).
    Outputs JSON-formatted log entries.
    """
    import json
    from datetime import datetime

    def __init__(self, name: str, level: str = 'INFO'):
        self.name = name
        self.level = level
        self.levels = {'DEBUG': 10, 'INFO': 20, 'WARNING': 30, 'ERROR': 40, 'CRITICAL': 50}

    def _log(self, level: str, message: str, **kwargs):
        if self.levels.get(level, 0) >= self.levels.get(self.level, 0):
            entry = {
                'timestamp': datetime.utcnow().isoformat(),
                'level': level,
                'logger': self.name,
                'message': message,
                **kwargs
            }
            print(json.dumps(entry))

    def debug(self, message: str, **kwargs):
        self._log('DEBUG', message, **kwargs)

    def info(self, message: str, **kwargs):
        self._log('INFO', message, **kwargs)

    def warning(self, message: str, **kwargs):
        self._log('WARNING', message, **kwargs)

    def error(self, message: str, **kwargs):
        self._log('ERROR', message, **kwargs)

    def critical(self, message: str, **kwargs):
        self._log('CRITICAL', message, **kwargs)
'''
        },

        # Environment/Config Operations
        "python-dotenv": {
            "load_env": '''
def load_env_file(filepath: str = '.env') -> dict:
    """
    Load environment variables from .env file (python-dotenv alternative).
    Returns dict of loaded variables.
    """
    import os

    loaded = {}

    if not os.path.exists(filepath):
        return loaded

    with open(filepath, 'r') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            if '=' in line:
                key, value = line.split('=', 1)
                key = key.strip()
                value = value.strip().strip('"').strip("'")
                os.environ[key] = value
                loaded[key] = value

    return loaded
'''
        },

        # Hashing/Encoding
        "hashlib_extended": {
            "hash_string": '''
def hash_string(text: str, algorithm: str = 'sha256') -> str:
    """Hash string using specified algorithm"""
    import hashlib

    algorithms = {
        'md5': hashlib.md5,
        'sha1': hashlib.sha1,
        'sha256': hashlib.sha256,
        'sha512': hashlib.sha512,
    }

    hasher = algorithms.get(algorithm.lower(), hashlib.sha256)
    return hasher(text.encode('utf-8')).hexdigest()
''',
            "hash_file": '''
def hash_file(filepath: str, algorithm: str = 'sha256', chunk_size: int = 8192) -> str:
    """Hash file content using specified algorithm"""
    import hashlib

    algorithms = {
        'md5': hashlib.md5,
        'sha1': hashlib.sha1,
        'sha256': hashlib.sha256,
        'sha512': hashlib.sha512,
    }

    hasher = algorithms.get(algorithm.lower(), hashlib.sha256)()

    with open(filepath, 'rb') as f:
        while chunk := f.read(chunk_size):
            hasher.update(chunk)

    return hasher.hexdigest()
'''
        },

        # Base64 Encoding
        "base64_utils": {
            "encode": '''
def base64_encode(data: str) -> str:
    """Encode string to base64"""
    import base64
    return base64.b64encode(data.encode('utf-8')).decode('utf-8')
''',
            "decode": '''
def base64_decode(encoded: str) -> str:
    """Decode base64 string"""
    import base64
    return base64.b64decode(encoded.encode('utf-8')).decode('utf-8')
'''
        },

        # Template Operations
        "jinja2": {
            "simple_template": '''
def render_template(template: str, context: dict) -> str:
    """
    Simple template rendering (Jinja2 alternative).
    Supports {{variable}} and {{variable|filter}} syntax.
    """
    import re

    def replace_var(match):
        expr = match.group(1).strip()

        # Check for filter
        if '|' in expr:
            var_name, filter_name = expr.split('|', 1)
            var_name = var_name.strip()
            filter_name = filter_name.strip()

            value = context.get(var_name, '')

            # Apply filter
            if filter_name == 'upper':
                return str(value).upper()
            elif filter_name == 'lower':
                return str(value).lower()
            elif filter_name == 'title':
                return str(value).title()
            elif filter_name == 'strip':
                return str(value).strip()
            elif filter_name == 'default':
                return str(value) if value else ''

            return str(value)

        return str(context.get(expr, ''))

    # Replace {{variable}} patterns
    result = re.sub(r'\\{\\{\\s*([^}]+)\\s*\\}\\}', replace_var, template)

    return result
'''
        },

        # UUID Generation
        "uuid_utils": {
            "generate_uuid": '''
def generate_uuid() -> str:
    """Generate UUID4 string"""
    import uuid
    return str(uuid.uuid4())
''',
            "generate_short_id": '''
def generate_short_id(length: int = 8) -> str:
    """Generate short random ID"""
    import uuid
    return uuid.uuid4().hex[:length]
'''
        },

        # Async HTTP (for aiohttp)
        "aiohttp": {
            "async_request": '''
async def async_http_request(url: str, method: str = "GET", data: dict = None,
                             headers: dict = None, timeout: int = 30) -> dict:
    """
    Async HTTP request using asyncio and urllib (aiohttp alternative).
    Note: This uses thread pool executor for actual I/O.
    """
    import asyncio
    import urllib.request
    import json as json_module
    from concurrent.futures import ThreadPoolExecutor

    def sync_request():
        headers_dict = headers or {}
        body = None

        if data and method.upper() in ("POST", "PUT", "PATCH"):
            body = json_module.dumps(data).encode('utf-8')
            headers_dict['Content-Type'] = 'application/json'

        req = urllib.request.Request(url, data=body, headers=headers_dict, method=method.upper())

        with urllib.request.urlopen(req, timeout=timeout) as response:
            text = response.read().decode('utf-8')
            return {
                'status': response.status,
                'headers': dict(response.headers),
                'text': text,
                'json': json_module.loads(text) if text else {}
            }

    loop = asyncio.get_event_loop()
    with ThreadPoolExecutor() as executor:
        return await loop.run_in_executor(executor, sync_request)
'''
        },

        # XML Operations
        "lxml": {
            "parse_xml": '''
def parse_xml(xml_string: str) -> dict:
    """
    Parse XML string to dict (lxml alternative).
    Uses built-in xml.etree.ElementTree.
    """
    import xml.etree.ElementTree as ET

    def element_to_dict(element):
        result = {}

        # Add attributes
        if element.attrib:
            result['@attributes'] = element.attrib

        # Add children
        children = list(element)
        if children:
            child_dict = {}
            for child in children:
                child_data = element_to_dict(child)
                if child.tag in child_dict:
                    if not isinstance(child_dict[child.tag], list):
                        child_dict[child.tag] = [child_dict[child.tag]]
                    child_dict[child.tag].append(child_data)
                else:
                    child_dict[child.tag] = child_data
            result.update(child_dict)

        # Add text content
        if element.text and element.text.strip():
            if result:
                result['#text'] = element.text.strip()
            else:
                return element.text.strip()

        return result

    root = ET.fromstring(xml_string)
    return {root.tag: element_to_dict(root)}
''',
            "create_xml": '''
def create_xml(data: dict, root_tag: str = 'root') -> str:
    """
    Create XML string from dict (lxml alternative).
    """
    import xml.etree.ElementTree as ET

    def dict_to_element(parent, data):
        if isinstance(data, dict):
            for key, value in data.items():
                if key.startswith('@'):
                    continue
                elif key == '#text':
                    parent.text = str(value)
                else:
                    child = ET.SubElement(parent, key)
                    dict_to_element(child, value)
        elif isinstance(data, list):
            for item in data:
                dict_to_element(parent, item)
        else:
            parent.text = str(data)

    root = ET.Element(root_tag)

    if isinstance(data, dict):
        for key, value in data.items():
            child = ET.SubElement(root, key)
            dict_to_element(child, value)

    return ET.tostring(root, encoding='unicode')
'''
        },

        # YAML Operations
        "pyyaml": {
            "load_yaml": '''
def load_yaml(yaml_string: str) -> dict:
    """
    Parse YAML string to dict (PyYAML alternative).
    Simple parser for basic YAML structures.
    """
    import re

    def parse_value(value):
        value = value.strip()

        # Boolean
        if value.lower() in ('true', 'yes', 'on'):
            return True
        if value.lower() in ('false', 'no', 'off'):
            return False

        # Null
        if value.lower() in ('null', 'none', '~', ''):
            return None

        # Number
        try:
            if '.' in value:
                return float(value)
            return int(value)
        except ValueError:
            pass

        # String (remove quotes)
        if (value.startswith('"') and value.endswith('"')) or \\
           (value.startswith("'") and value.endswith("'")):
            return value[1:-1]

        return value

    result = {}
    current_indent = 0
    stack = [(result, -1)]

    for line in yaml_string.split('\\n'):
        if not line.strip() or line.strip().startswith('#'):
            continue

        # Calculate indent
        indent = len(line) - len(line.lstrip())
        line = line.strip()

        # Pop stack for decreased indent
        while stack and indent <= stack[-1][1]:
            stack.pop()

        current_dict = stack[-1][0]

        if ':' in line:
            key, value = line.split(':', 1)
            key = key.strip()
            value = value.strip()

            if value:
                current_dict[key] = parse_value(value)
            else:
                current_dict[key] = {}
                stack.append((current_dict[key], indent))
        elif line.startswith('- '):
            # List item
            value = line[2:].strip()
            if not isinstance(current_dict, list):
                # Convert parent to list
                parent_dict = stack[-2][0] if len(stack) > 1 else result
                for k, v in list(parent_dict.items()):
                    if v is current_dict:
                        parent_dict[k] = [parse_value(value)]
                        stack[-1] = (parent_dict[k], stack[-1][1])
                        break
            else:
                current_dict.append(parse_value(value))

    return result
'''
        },

        # Caching
        "cachetools": {
            "simple_cache": '''
class SimpleCache:
    """
    Simple in-memory cache with TTL (cachetools alternative).
    """
    from datetime import datetime, timedelta

    def __init__(self, ttl_seconds: int = 300, max_size: int = 100):
        self.cache = {}
        self.ttl = ttl_seconds
        self.max_size = max_size
        self.access_times = {}

    def get(self, key: str, default=None):
        if key in self.cache:
            entry = self.cache[key]
            if datetime.utcnow() < entry['expires']:
                self.access_times[key] = datetime.utcnow()
                return entry['value']
            else:
                del self.cache[key]
                del self.access_times[key]
        return default

    def set(self, key: str, value, ttl: int = None):
        # Evict oldest if at max size
        if len(self.cache) >= self.max_size:
            oldest = min(self.access_times, key=self.access_times.get)
            del self.cache[oldest]
            del self.access_times[oldest]

        ttl = ttl or self.ttl
        self.cache[key] = {
            'value': value,
            'expires': datetime.utcnow() + timedelta(seconds=ttl)
        }
        self.access_times[key] = datetime.utcnow()

    def delete(self, key: str):
        if key in self.cache:
            del self.cache[key]
            del self.access_times[key]

    def clear(self):
        self.cache.clear()
        self.access_times.clear()
'''
        }
    }

    # Category mappings for libraries
    LIBRARY_CATEGORIES = {
        "requests": "http",
        "httpx": "http",
        "aiohttp": "http",
        "urllib3": "http",
        "pandas": "data",
        "numpy": "data",
        "json": "data",
        "pyyaml": "data",
        "lxml": "data",
        "pathlib": "file",
        "shutil": "file",
        "dateutil": "datetime",
        "arrow": "datetime",
        "pendulum": "datetime",
        "tenacity": "resilience",
        "backoff": "resilience",
        "pydantic": "validation",
        "marshmallow": "validation",
        "structlog": "logging",
        "loguru": "logging",
        "python-dotenv": "config",
        "jinja2": "template",
        "cachetools": "caching",
    }

    def __init__(self, db_path: str = None):
        """Initialize the Native Fallback Generator"""
        self.logger = logging.getLogger(__name__)

        if db_path is None:
            db_path = os.path.join(
                os.path.dirname(__file__),
                "..", "data", "fallback_code.db"
            )

        self.db_path = db_path
        self._init_database()

    def _init_database(self) -> None:
        """Initialize SQLite database for fallback code storage"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)

        self.db = sqlite3.connect(self.db_path, check_same_thread=False)
        self.db.row_factory = sqlite3.Row

        cursor = self.db.cursor()

        # Fallback code table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS fallback_code (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                library_name TEXT NOT NULL,
                operation_type TEXT NOT NULL,
                fallback_code TEXT NOT NULL,
                description TEXT,
                category TEXT,
                uses_stdlib_only BOOLEAN DEFAULT 1,
                minimal_dependencies TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(library_name, operation_type)
            )
        ''')

        # Fallback usage log
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS fallback_usage_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                library_name TEXT NOT NULL,
                operation_type TEXT NOT NULL,
                component_name TEXT,
                success BOOLEAN,
                error_message TEXT,
                timestamp TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Fallback effectiveness tracking
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS fallback_effectiveness (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                library_name TEXT NOT NULL,
                operation_type TEXT NOT NULL,
                usage_count INTEGER DEFAULT 0,
                success_count INTEGER DEFAULT 0,
                failure_count INTEGER DEFAULT 0,
                effectiveness_score REAL DEFAULT 0.0,
                last_used TEXT,
                UNIQUE(library_name, operation_type)
            )
        ''')

        # Learned fallbacks (from successful generations)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS learned_fallbacks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                library_name TEXT NOT NULL,
                operation_type TEXT NOT NULL,
                fallback_code TEXT NOT NULL,
                source_component TEXT,
                learned_from TEXT,
                confidence_score REAL DEFAULT 0.5,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(library_name, operation_type, source_component)
            )
        ''')

        self.db.commit()

        # Seed with pre-built fallbacks
        self._seed_fallbacks()

    def _seed_fallbacks(self) -> None:
        """Seed database with pre-built native fallbacks"""
        cursor = self.db.cursor()

        for library_name, operations in self.NATIVE_FALLBACKS.items():
            category = self.LIBRARY_CATEGORIES.get(library_name, "general")

            for operation_type, fallback_code in operations.items():
                try:
                    cursor.execute('''
                        INSERT OR IGNORE INTO fallback_code
                        (library_name, operation_type, fallback_code, description, category, uses_stdlib_only)
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', (
                        library_name,
                        operation_type,
                        fallback_code.strip(),
                        f"Native Python fallback for {library_name}.{operation_type}",
                        category,
                        True
                    ))

                    # Initialize effectiveness tracking
                    cursor.execute('''
                        INSERT OR IGNORE INTO fallback_effectiveness
                        (library_name, operation_type, usage_count, success_count, failure_count, effectiveness_score)
                        VALUES (?, ?, 0, 0, 0, 0.8)
                    ''', (library_name, operation_type))

                except sqlite3.Error as e:
                    self.logger.warning(f"Error seeding fallback {library_name}.{operation_type}: {e}")

        self.db.commit()

    def get_fallback(self, library_name: str, operation_type: str = None) -> Optional[Dict[str, Any]]:
        """
        Get fallback code for a library/operation.

        Args:
            library_name: Name of the library (e.g., 'requests')
            operation_type: Specific operation (e.g., 'get', 'post'). If None, returns all operations.

        Returns:
            Dict with fallback code and metadata, or None if not found
        """
        cursor = self.db.cursor()

        if operation_type:
            cursor.execute('''
                SELECT * FROM fallback_code
                WHERE library_name = ? AND operation_type = ?
            ''', (library_name, operation_type))
            row = cursor.fetchone()

            if row:
                return {
                    "library_name": row["library_name"],
                    "operation_type": row["operation_type"],
                    "fallback_code": row["fallback_code"],
                    "description": row["description"],
                    "category": row["category"],
                    "uses_stdlib_only": bool(row["uses_stdlib_only"]),
                }

            # Check learned fallbacks
            cursor.execute('''
                SELECT * FROM learned_fallbacks
                WHERE library_name = ? AND operation_type = ?
                ORDER BY confidence_score DESC
                LIMIT 1
            ''', (library_name, operation_type))
            row = cursor.fetchone()

            if row:
                return {
                    "library_name": row["library_name"],
                    "operation_type": row["operation_type"],
                    "fallback_code": row["fallback_code"],
                    "source": "learned",
                    "confidence_score": row["confidence_score"],
                }
        else:
            # Get all operations for library
            cursor.execute('''
                SELECT * FROM fallback_code
                WHERE library_name = ?
            ''', (library_name,))
            rows = cursor.fetchall()

            if rows:
                return {
                    "library_name": library_name,
                    "operations": {
                        row["operation_type"]: {
                            "fallback_code": row["fallback_code"],
                            "description": row["description"],
                        }
                        for row in rows
                    }
                }

        return None

    def get_all_fallbacks_for_library(self, library_name: str) -> List[Dict[str, Any]]:
        """Get all fallback operations for a library"""
        cursor = self.db.cursor()

        cursor.execute('''
            SELECT * FROM fallback_code
            WHERE library_name = ?
        ''', (library_name,))

        return [
            {
                "library_name": row["library_name"],
                "operation_type": row["operation_type"],
                "fallback_code": row["fallback_code"],
                "description": row["description"],
                "category": row["category"],
            }
            for row in cursor.fetchall()
        ]

    def generate_fallback_code(self, library_name: str, operations: List[str] = None,
                               context: Dict[str, Any] = None) -> str:
        """
        Generate combined fallback code for specified operations.

        Args:
            library_name: Name of the library
            operations: List of operations to include. If None, includes all.
            context: Additional context for customization

        Returns:
            Combined Python code string with all fallbacks
        """
        fallbacks = []

        # Get all available fallbacks for library
        all_fallbacks = self.get_all_fallbacks_for_library(library_name)

        if not all_fallbacks:
            # Try pre-built fallbacks directly
            if library_name in self.NATIVE_FALLBACKS:
                all_ops = self.NATIVE_FALLBACKS[library_name]
                for op_type, code in all_ops.items():
                    if operations is None or op_type in operations:
                        fallbacks.append(f"# {library_name}.{op_type} fallback\n{code.strip()}")
        else:
            for fb in all_fallbacks:
                if operations is None or fb["operation_type"] in operations:
                    fallbacks.append(
                        f"# {fb['library_name']}.{fb['operation_type']} fallback\n"
                        f"# {fb.get('description', '')}\n"
                        f"{fb['fallback_code'].strip()}"
                    )

        if fallbacks:
            header = f'''"""
Native Python fallback implementations for {library_name}
These functions provide standard library alternatives when {library_name} is unavailable.
Generated by NativeFallbackGenerator.
"""

'''
            return header + "\n\n".join(fallbacks)

        return ""

    def log_fallback_usage(self, library_name: str, operation_type: str,
                          component_name: str, success: bool,
                          error_message: str = None) -> None:
        """
        Log usage of a fallback for learning.

        Args:
            library_name: Name of the library
            operation_type: Operation type used
            component_name: Component that used the fallback
            success: Whether the fallback worked
            error_message: Error message if failed
        """
        cursor = self.db.cursor()

        # Log usage
        cursor.execute('''
            INSERT INTO fallback_usage_log
            (library_name, operation_type, component_name, success, error_message)
            VALUES (?, ?, ?, ?, ?)
        ''', (library_name, operation_type, component_name, success, error_message))

        # Update effectiveness
        if success:
            cursor.execute('''
                UPDATE fallback_effectiveness
                SET usage_count = usage_count + 1,
                    success_count = success_count + 1,
                    effectiveness_score = CAST(success_count + 1 AS REAL) / (usage_count + 1),
                    last_used = CURRENT_TIMESTAMP
                WHERE library_name = ? AND operation_type = ?
            ''', (library_name, operation_type))
        else:
            cursor.execute('''
                UPDATE fallback_effectiveness
                SET usage_count = usage_count + 1,
                    failure_count = failure_count + 1,
                    effectiveness_score = CAST(success_count AS REAL) / (usage_count + 1),
                    last_used = CURRENT_TIMESTAMP
                WHERE library_name = ? AND operation_type = ?
            ''', (library_name, operation_type))

        # Insert if not exists
        if cursor.rowcount == 0:
            cursor.execute('''
                INSERT INTO fallback_effectiveness
                (library_name, operation_type, usage_count, success_count, failure_count, effectiveness_score, last_used)
                VALUES (?, ?, 1, ?, ?, ?, CURRENT_TIMESTAMP)
            ''', (library_name, operation_type, 1 if success else 0, 0 if success else 1, 1.0 if success else 0.0))

        self.db.commit()

    def learn_fallback(self, library_name: str, operation_type: str,
                      fallback_code: str, source_component: str,
                      learned_from: str = "generation") -> bool:
        """
        Learn a new fallback from successful generation.

        Args:
            library_name: Name of the library
            operation_type: Operation type
            fallback_code: The fallback code that worked
            source_component: Component where it was used
            learned_from: Source of learning (generation, manual, etc.)

        Returns:
            True if successfully learned
        """
        cursor = self.db.cursor()

        try:
            cursor.execute('''
                INSERT OR REPLACE INTO learned_fallbacks
                (library_name, operation_type, fallback_code, source_component, learned_from, confidence_score)
                VALUES (?, ?, ?, ?, ?, 0.5)
            ''', (library_name, operation_type, fallback_code, source_component, learned_from))

            self.db.commit()
            self.logger.info(f"Learned fallback for {library_name}.{operation_type}")
            return True

        except sqlite3.Error as e:
            self.logger.error(f"Error learning fallback: {e}")
            return False

    def get_effectiveness(self, library_name: str = None) -> Dict[str, Any]:
        """
        Get effectiveness statistics for fallbacks.

        Args:
            library_name: Filter by library. If None, returns all.

        Returns:
            Dict with effectiveness statistics
        """
        cursor = self.db.cursor()

        if library_name:
            cursor.execute('''
                SELECT * FROM fallback_effectiveness
                WHERE library_name = ?
                ORDER BY effectiveness_score DESC
            ''', (library_name,))
        else:
            cursor.execute('''
                SELECT * FROM fallback_effectiveness
                ORDER BY effectiveness_score DESC
            ''')

        rows = cursor.fetchall()

        return {
            "fallbacks": [
                {
                    "library_name": row["library_name"],
                    "operation_type": row["operation_type"],
                    "usage_count": row["usage_count"],
                    "success_count": row["success_count"],
                    "failure_count": row["failure_count"],
                    "effectiveness_score": row["effectiveness_score"],
                    "last_used": row["last_used"],
                }
                for row in rows
            ],
            "total_fallbacks": len(rows),
            "average_effectiveness": sum(r["effectiveness_score"] for r in rows) / len(rows) if rows else 0,
        }

    def suggest_fallback_for_code(self, code: str, unavailable_libraries: List[str]) -> Dict[str, Any]:
        """
        Analyze code and suggest fallbacks for unavailable libraries.

        Args:
            code: The code that uses unavailable libraries
            unavailable_libraries: List of libraries that aren't available

        Returns:
            Dict with suggested fallbacks and modified code hints
        """
        suggestions = []

        for library in unavailable_libraries:
            # Get all fallbacks for this library
            fallbacks = self.get_all_fallbacks_for_library(library)

            if fallbacks:
                suggestions.append({
                    "library": library,
                    "available_fallbacks": [
                        {
                            "operation": fb["operation_type"],
                            "description": fb.get("description", ""),
                            "code_available": True,
                        }
                        for fb in fallbacks
                    ],
                    "recommendation": f"Use native Python fallbacks for {library}",
                })
            elif library in self.NATIVE_FALLBACKS:
                # Use pre-built fallbacks
                suggestions.append({
                    "library": library,
                    "available_fallbacks": [
                        {"operation": op, "code_available": True}
                        for op in self.NATIVE_FALLBACKS[library].keys()
                    ],
                    "recommendation": f"Use pre-built native fallbacks for {library}",
                })
            else:
                suggestions.append({
                    "library": library,
                    "available_fallbacks": [],
                    "recommendation": f"No fallback available for {library}. Consider using API or alternative approach.",
                })

        return {
            "unavailable_libraries": unavailable_libraries,
            "suggestions": suggestions,
            "has_fallbacks": any(s["available_fallbacks"] for s in suggestions),
        }

    def generate_prompt_addition(self, unavailable_libraries: List[str]) -> str:
        """
        Generate prompt addition for code generation with fallback guidance.

        Args:
            unavailable_libraries: Libraries that need fallbacks

        Returns:
            String to add to generation prompt
        """
        if not unavailable_libraries:
            return ""

        prompt_parts = [
            "## 📦 PHASE 4: NATIVE FALLBACK GUIDANCE",
            "",
            "The following libraries may not be available in the Airflow environment.",
            "Use native Python implementations instead:",
            "",
        ]

        for library in unavailable_libraries:
            fallbacks = self.get_all_fallbacks_for_library(library)

            if fallbacks:
                prompt_parts.append(f"### {library}")
                prompt_parts.append(f"Available native fallback operations: {', '.join(fb['operation_type'] for fb in fallbacks)}")
                prompt_parts.append("")

                # Include one example
                example = fallbacks[0]
                prompt_parts.append(f"Example ({example['operation_type']}):")
                prompt_parts.append("```python")
                prompt_parts.append(example["fallback_code"][:500] + "..." if len(example["fallback_code"]) > 500 else example["fallback_code"])
                prompt_parts.append("```")
                prompt_parts.append("")
            elif library in self.NATIVE_FALLBACKS:
                prompt_parts.append(f"### {library}")
                ops = list(self.NATIVE_FALLBACKS[library].keys())
                prompt_parts.append(f"Use standard library alternatives. Available operations: {', '.join(ops)}")
                prompt_parts.append("")

        prompt_parts.extend([
            "**Important:**",
            "- Use only Python standard library (urllib, json, csv, etc.)",
            "- Do NOT import unavailable libraries",
            "- Implement equivalent functionality using provided patterns",
            "",
        ])

        return "\n".join(prompt_parts)

    def get_statistics(self) -> Dict[str, Any]:
        """Get overall fallback statistics"""
        cursor = self.db.cursor()

        # Count fallbacks
        cursor.execute("SELECT COUNT(*) FROM fallback_code")
        total_fallbacks = cursor.fetchone()[0]

        # Count learned fallbacks
        cursor.execute("SELECT COUNT(*) FROM learned_fallbacks")
        learned_count = cursor.fetchone()[0]

        # Count usage logs
        cursor.execute("SELECT COUNT(*) FROM fallback_usage_log")
        usage_count = cursor.fetchone()[0]

        # Success rate
        cursor.execute("SELECT COUNT(*) FROM fallback_usage_log WHERE success = 1")
        success_count = cursor.fetchone()[0]

        # Libraries covered
        cursor.execute("SELECT DISTINCT library_name FROM fallback_code")
        libraries = [row[0] for row in cursor.fetchall()]

        # Categories
        cursor.execute("SELECT DISTINCT category FROM fallback_code WHERE category IS NOT NULL")
        categories = [row[0] for row in cursor.fetchall()]

        return {
            "total_fallbacks": total_fallbacks,
            "learned_fallbacks": learned_count,
            "total_usage": usage_count,
            "success_count": success_count,
            "success_rate": success_count / usage_count if usage_count > 0 else 0,
            "libraries_covered": libraries,
            "library_count": len(libraries),
            "categories": categories,
        }

    def close(self) -> None:
        """Close database connection"""
        if hasattr(self, 'db') and self.db:
            self.db.close()


# Convenience function
def get_native_fallback(library_name: str, operation: str = None) -> Optional[str]:
    """
    Convenience function to get native fallback code.

    Args:
        library_name: Name of the library
        operation: Specific operation (optional)

    Returns:
        Fallback code string or None
    """
    if library_name in NativeFallbackGenerator.NATIVE_FALLBACKS:
        ops = NativeFallbackGenerator.NATIVE_FALLBACKS[library_name]
        if operation and operation in ops:
            return ops[operation]
        elif not operation:
            return "\n\n".join(ops.values())
    return None
