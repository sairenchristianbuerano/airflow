#!/usr/bin/env python3
"""
Test the /generate endpoint with various scenarios
"""

import json
import requests
import time

BASE_URL = "http://localhost:8096/api/airflow/component-generator"

def test_case(name, spec, expected_success=True):
    print(f"\n{'='*80}")
    print(f"TEST: {name}")
    print(f"{'='*80}")

    start_time = time.time()

    try:
        response = requests.post(
            f"{BASE_URL}/generate",
            json={"spec": spec},
            headers={"Content-Type": "application/json"},
            timeout=120
        )

        elapsed = time.time() - start_time

        print(f"Status Code: {response.status_code}")
        print(f"Time: {elapsed:.2f}s")

        data = response.json()

        if response.status_code == 200:
            has_code = 'code' in data and len(data.get('code', '')) > 100
            has_tests = 'tests' in data and len(data.get('tests', '')) > 100
            has_docs = 'documentation' in data and len(data.get('documentation', '')) > 1000
            has_dag = 'test_dag' in data and len(data.get('test_dag', '')) > 100

            print(f"✅ Code: {len(data.get('code', ''))} chars")
            print(f"✅ Tests: {len(data.get('tests', ''))} chars")
            print(f"✅ Documentation: {len(data.get('documentation', ''))} chars")
            print(f"✅ Test DAG: {len(data.get('test_dag', ''))} chars")

            # Save output
            filename = f"test_output_{name.replace(' ', '_').lower()}.json"
            with open(filename, 'w') as f:
                json.dump(data, f, indent=2)
            print(f"\n💾 Saved to: {filename}")

            return True
        else:
            print(f"❌ Error: {data.get('detail', 'Unknown error')}")
            return False

    except Exception as e:
        print(f"❌ Exception: {str(e)}")
        return False

# Test 1: Simple Operator
print("\n" + "="*80)
print("TESTING /generate ENDPOINT - COMPREHENSIVE TEST SUITE")
print("="*80)

test_case(
    "Simple Operator",
    """name: SimpleDataOperator
display_name: Simple Data Operator
description: A simple operator that processes data
category: custom
component_type: operator
inputs:
  - name: input_data
    type: str
    required: true
    template_field: true
"""
)

# Test 2: Operator with Runtime Params
test_case(
    "Operator with Runtime Params",
    """name: ConfigurableOperator
display_name: Configurable Operator
description: Operator with runtime UI parameters
category: custom
component_type: operator
runtime_params:
  - name: threshold
    type: number
    default: 0.5
    description: Processing threshold
  - name: mode
    type: string
    enum: ["batch", "stream"]
    default: "batch"
    description: Processing mode
inputs:
  - name: threshold
    type: float
    required: false
    default: 0.5
    template_field: true
  - name: mode
    type: str
    required: false
    default: "batch"
"""
)

# Test 3: Sensor
test_case(
    "Custom Sensor",
    """name: CustomFileSensor
display_name: Custom File Sensor
description: Sensor that checks for file existence
category: filesystem
component_type: sensor
base_class: BaseSensor
inputs:
  - name: filepath
    type: str
    required: true
    template_field: true
    description: Path to file to check
  - name: poke_interval
    type: int
    required: false
    default: 60
    description: Time between checks in seconds
"""
)

# Test 4: Hook
test_case(
    "Custom Hook",
    """name: CustomAPIHook
display_name: Custom API Hook
description: Hook for connecting to custom API
category: http
component_type: hook
base_class: BaseHook
inputs:
  - name: api_endpoint
    type: str
    required: true
    description: API endpoint URL
  - name: api_key
    type: str
    required: true
    description: API authentication key
"""
)

# Test 5: Complex Operator with Dependencies
test_case(
    "Complex Operator",
    """name: DataProcessorOperator
display_name: Data Processor Operator
description: Complex operator with multiple dependencies
category: data_processing
component_type: operator
dependencies:
  - apache-airflow-providers-postgres>=5.0.0
  - pandas>=2.0.0
  - sqlalchemy>=2.0.0
inputs:
  - name: sql_query
    type: str
    required: true
    template_field: true
  - name: postgres_conn_id
    type: str
    required: false
    default: "postgres_default"
  - name: output_format
    type: str
    required: false
    default: "json"
requirements:
  - Execute SQL query against PostgreSQL database
  - Process results with pandas
  - Support multiple output formats (json, csv, parquet)
  - Include error handling and retry logic
"""
)

# Test 6: Error Case - Invalid YAML
print(f"\n{'='*80}")
print("TEST: Invalid YAML (Expected to Fail)")
print(f"{'='*80}")

try:
    response = requests.post(
        f"{BASE_URL}/generate",
        json={"spec": "invalid: yaml: content: - - -"},
        headers={"Content-Type": "application/json"},
        timeout=30
    )
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.json()}")
except Exception as e:
    print(f"Exception: {str(e)}")

# Test 7: Error Case - Missing Required Fields
print(f"\n{'='*80}")
print("TEST: Missing Required Fields (Expected to Fail)")
print(f"{'='*80}")

try:
    response = requests.post(
        f"{BASE_URL}/generate",
        json={"spec": "name: TestOp\ncomponent_type: operator"},
        headers={"Content-Type": "application/json"},
        timeout=30
    )
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.json()}")
except Exception as e:
    print(f"Exception: {str(e)}")

print("\n" + "="*80)
print("TESTING COMPLETE!")
print("="*80)
