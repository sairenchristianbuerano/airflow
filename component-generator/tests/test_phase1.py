"""
Comprehensive Phase 1 Test Suite
Tests all component-generator functionality to ensure it's 100% solid before Phase 2
"""

import requests
import json
import time
from typing import Dict, Any

# Configuration
BASE_URL = "http://localhost:8095/api/airflow/component-generator"
TIMEOUT = 120

class TestResults:
    """Track test results"""
    def __init__(self):
        self.total = 0
        self.passed = 0
        self.failed = 0
        self.failures = []

    def add_pass(self, test_name: str):
        self.total += 1
        self.passed += 1
        print(f"✅ PASS: {test_name}")

    def add_fail(self, test_name: str, error: str):
        self.total += 1
        self.failed += 1
        self.failures.append((test_name, error))
        print(f"❌ FAIL: {test_name} - {error}")

    def print_summary(self):
        print("\n" + "="*80)
        print("TEST SUMMARY")
        print("="*80)
        print(f"Total Tests: {self.total}")
        print(f"Passed: {self.passed} ✅")
        print(f"Failed: {self.failed} ❌")
        print(f"Success Rate: {(self.passed/self.total*100):.1f}%")

        if self.failures:
            print("\nFailed Tests:")
            for test_name, error in self.failures:
                print(f"  - {test_name}: {error}")

        print("="*80)
        return self.failed == 0


results = TestResults()


def test_health_endpoint():
    """Test 1: Health endpoint responds correctly"""
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"

        data = response.json()
        assert data["status"] == "healthy", "Service not healthy"
        assert "version" in data, "Version missing"
        assert "model" in data, "Model info missing"

        results.add_pass("Health Endpoint")
    except Exception as e:
        results.add_fail("Health Endpoint", str(e))


def test_sample_operator_generation():
    """Test 2: Generate sample operator"""
    try:
        response = requests.post(
            f"{BASE_URL}/generate/sample",
            timeout=TIMEOUT
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"

        data = response.json()
        assert "code" in data, "Code not in response"
        assert "documentation" in data, "Documentation not in response"
        assert "tests" in data, "Tests not in response"

        # Verify code contains expected patterns
        code = data["code"]
        assert "class" in code, "No class definition in code"
        assert "def execute" in code, "No execute method in code"
        assert "BaseOperator" in code, "Not inheriting from BaseOperator"

        # Verify documentation is comprehensive
        docs = data["documentation"]
        assert len(docs) > 500, "Documentation too short"
        assert "Installation" in docs, "Missing installation section"
        assert "Examples" in docs, "Missing examples section"

        # Verify tests are generated
        tests = data["tests"]
        assert "def test_" in tests, "No test functions"
        assert "pytest" in tests or "import pytest" in tests, "Not using pytest"

        results.add_pass("Sample Operator Generation")
    except Exception as e:
        results.add_fail("Sample Operator Generation", str(e))


def test_custom_operator_generation():
    """Test 3: Generate custom operator from YAML spec"""
    try:
        # Simple custom operator spec
        yaml_spec = """
name: TestOperator
display_name: "Test Operator"
description: "Simple test operator for validation"
category: test
component_type: operator

inputs:
  - name: test_param
    type: str
    description: "Test parameter"
    required: true
    template_field: true

dependencies:
  - "apache-airflow>=2.0.0"

base_class: "BaseOperator"
template_fields: ["test_param"]
ui_color: "#f4a460"
"""

        response = requests.post(
            f"{BASE_URL}/generate",
            json={"spec": yaml_spec},
            timeout=TIMEOUT
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"

        data = response.json()
        assert "code" in data, "Code not in response"
        assert "TestOperator" in data["code"], "Operator name not in generated code"

        results.add_pass("Custom Operator Generation")
    except Exception as e:
        results.add_fail("Custom Operator Generation", str(e))


def test_sensor_generation():
    """Test 4: Generate sensor component"""
    try:
        yaml_spec = """
name: TestSensor
display_name: "Test Sensor"
description: "Simple test sensor"
category: test
component_type: sensor

inputs:
  - name: condition
    type: str
    required: true

base_class: "BaseSensor"
poke_interval: 30
timeout: 600
mode: "poke"
"""

        response = requests.post(
            f"{BASE_URL}/generate",
            json={"spec": yaml_spec},
            timeout=TIMEOUT
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"

        data = response.json()
        code = data["code"]
        assert "TestSensor" in code, "Sensor name not in code"
        assert "def poke" in code, "No poke method"
        assert "BaseSensor" in code, "Not inheriting from BaseSensor"

        results.add_pass("Sensor Generation")
    except Exception as e:
        results.add_fail("Sensor Generation", str(e))


def test_analytics_metrics():
    """Test 5: Analytics metrics endpoint"""
    try:
        response = requests.get(f"{BASE_URL}/analytics/metrics", timeout=5)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"

        data = response.json()
        assert "total_generations" in data, "Missing total_generations"
        assert "success_rate" in data, "Missing success_rate"
        assert "avg_attempts" in data, "Missing avg_attempts"

        # Should have at least 2 generations from previous tests
        assert data["total_generations"] >= 2, "Not tracking generations"

        results.add_pass("Analytics Metrics")
    except Exception as e:
        results.add_fail("Analytics Metrics", str(e))


def test_analytics_insights():
    """Test 6: Analytics insights endpoint"""
    try:
        response = requests.get(f"{BASE_URL}/analytics/insights", timeout=5)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"

        data = response.json()
        assert "category_insights" in data, "Missing category_insights"
        assert "type_insights" in data, "Missing type_insights"

        results.add_pass("Analytics Insights")
    except Exception as e:
        results.add_fail("Analytics Insights", str(e))


def test_analytics_trends():
    """Test 7: Analytics trends endpoint"""
    try:
        response = requests.get(f"{BASE_URL}/analytics/trends?days=7", timeout=5)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"

        data = response.json()
        assert "daily_stats" in data, "Missing daily_stats"
        assert len(data["daily_stats"]) > 0, "No daily stats"

        results.add_pass("Analytics Trends")
    except Exception as e:
        results.add_fail("Analytics Trends", str(e))


def test_analytics_errors():
    """Test 8: Analytics errors endpoint"""
    try:
        response = requests.get(f"{BASE_URL}/analytics/errors", timeout=5)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"

        data = response.json()
        assert "total_tracked_errors" in data, "Missing total_tracked_errors"
        assert "errors_by_type" in data, "Missing errors_by_type"

        results.add_pass("Analytics Errors")
    except Exception as e:
        results.add_fail("Analytics Errors", str(e))


def test_feasibility_assessment():
    """Test 9: Feasibility assessment endpoint"""
    try:
        yaml_spec = """
name: SimpleOperator
description: "A simple operator"
category: test
component_type: operator
base_class: "BaseOperator"
"""

        response = requests.post(
            f"{BASE_URL}/assess",
            json={"spec": yaml_spec},
            timeout=10
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"

        data = response.json()
        assert "feasible" in data, "Missing feasible field"
        assert "confidence" in data, "Missing confidence field"
        assert "complexity" in data, "Missing complexity field"

        results.add_pass("Feasibility Assessment")
    except Exception as e:
        results.add_fail("Feasibility Assessment", str(e))


def test_team_standard_format():
    """Test 10: Verify team standard format fields are supported"""
    try:
        # Spec with team standard format fields
        yaml_spec = """
name: StandardFormatOperator
display_name: "Standard Format Operator"
description: "Tests team standard format support"
category: test
component_type: operator

icon: "box"
template_ext: [".json"]

inputs:
  - name: input_value
    type: str
    required: true

examples:
  - description: "Basic usage"
    code: "StandardFormatOperator(task_id='test')"

implementation_hints:
  - "Use self.log for logging"
  - "Validate inputs in __init__"

prerequisites:
  environment_variables:
    - name: "API_KEY"
      required: false

license: "Apache 2.0"
"""

        response = requests.post(
            f"{BASE_URL}/generate",
            json={"spec": yaml_spec},
            timeout=TIMEOUT
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"

        data = response.json()
        assert "code" in data, "Code not generated"
        assert "StandardFormatOperator" in data["code"], "Operator not in code"

        results.add_pass("Team Standard Format Support")
    except Exception as e:
        results.add_fail("Team Standard Format Support", str(e))


def main():
    """Run all tests"""
    print("="*80)
    print("PHASE 1 COMPREHENSIVE TEST SUITE")
    print("Testing Airflow Component Generator Service")
    print("="*80)
    print()

    # Check if service is accessible
    try:
        requests.get(f"{BASE_URL}/health", timeout=5)
    except requests.exceptions.ConnectionError:
        print("❌ ERROR: Cannot connect to service at", BASE_URL)
        print("Make sure the service is running: docker-compose up -d")
        return False

    print("Running tests...\n")

    # Run all tests
    test_health_endpoint()
    test_sample_operator_generation()
    test_custom_operator_generation()
    test_sensor_generation()
    test_analytics_metrics()
    test_analytics_insights()
    test_analytics_trends()
    test_analytics_errors()
    test_feasibility_assessment()
    test_team_standard_format()

    # Print summary
    success = results.print_summary()

    if success:
        print("\n✅ All tests passed! Phase 1 is 100% SOLID!")
        print("Ready to proceed to Phase 2: Component Index Service with ChromaDB RAG")
    else:
        print("\n❌ Some tests failed. Please review and fix issues before Phase 2.")

    return success


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
