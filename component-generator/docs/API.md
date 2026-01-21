# Airflow Component Generator API Documentation

**Base URL:** `http://localhost:8095/api/airflow/component-generator`
**Version:** 0.1.0
**Model:** Claude Sonnet 4 (with Haiku for simple components)

---

## Table of Contents

- [Authentication](#authentication)
- [Endpoints](#endpoints)
  - [Health Check](#1-health-check)
  - [Generate Component](#2-generate-component)
  - [Generate Sample Component](#3-generate-sample-component)
  - [Assess Feasibility](#4-assess-feasibility)
  - [Analytics - Metrics](#5-analytics---metrics)
  - [Analytics - Insights](#6-analytics---insights)
  - [Analytics - Trends](#7-analytics---trends)
  - [Analytics - Errors](#8-analytics---errors)
- [Data Models](#data-models)
- [Error Handling](#error-handling)
- [Examples](#examples)

---

## Authentication

Currently, the API does not require authentication. All endpoints are publicly accessible.

---

## Endpoints

### 1. Health Check

**Endpoint:** `GET /health`

**Description:** Check if the service is running and healthy.

**Request:** No parameters required.

**Response:**

```json
{
  "status": "healthy",
  "service": "airflow-component-generator",
  "version": "0.1.0",
  "model": "claude-sonnet-4-20250514"
}
```

**Status Codes:**
- `200 OK` - Service is healthy

**Example:**

```bash
curl http://localhost:8095/api/airflow/component-generator/health
```

---

### 2. Generate Component

**Endpoint:** `POST /generate`

**Description:** Generate a custom Airflow component (operator, sensor, or hook) from a YAML specification with Phase 2 enhancements including:
- Enhanced test generation with XCom mocking and edge cases
- Comprehensive troubleshooting documentation (20k+ characters)
- Model routing by complexity (Haiku for simple, Sonnet for complex)
- Optional static analysis (mypy, ruff)

**Request Body:**

```json
{
  "spec": "<YAML specification string>"
}
```

**YAML Specification Format:**

#### Operator Specification

```yaml
name: "MyCustomOperator"                    # Required: PascalCase class name
display_name: "My Custom Operator"          # Required: Human-readable name
description: "Description of the operator"  # Required: Brief description
category: "custom"                          # Required: Category (custom, http, database, etc.)
component_type: "operator"                  # Required: "operator", "sensor", or "hook"

# Optional: Base class (defaults to BaseOperator)
base_class: "BaseOperator"

# Optional: Inputs (operator parameters)
inputs:
  - name: "input_param"
    type: "str"
    required: true
    default: "default_value"
    template_field: true              # Enable Jinja templating
    description: "Parameter description"

# Optional: Runtime parameters (UI form fields)
runtime_params:
  - name: "threshold"
    type: "number"                    # JSON schema types: string, number, boolean, array, object
    default: 0.5
    description: "Processing threshold"
  - name: "mode"
    type: "string"
    enum: ["batch", "stream"]
    default: "batch"
    description: "Processing mode"

# Optional: Python dependencies
dependencies:
  - "apache-airflow-providers-postgres>=5.0.0"
  - "pandas>=2.0.0"

# Optional: Natural language requirements
requirements:
  - "Execute SQL query against PostgreSQL"
  - "Process results with pandas"
  - "Support multiple output formats"

# Optional: Template configuration
template_fields: ["input_param"]
template_ext: [".sql", ".json"]
```

#### Sensor Specification

```yaml
name: "MyCustomSensor"
display_name: "My Custom Sensor"
description: "Sensor that waits for a condition"
category: "custom"
component_type: "sensor"
base_class: "BaseSensor"

inputs:
  - name: "condition_param"
    type: "str"
    required: true
    template_field: true
  - name: "poke_interval"
    type: "int"
    default: 60
    description: "Time between poke attempts in seconds"
```

#### Hook Specification

```yaml
name: "MyCustomHook"
display_name: "My Custom Hook"
description: "Hook for connecting to custom service"
category: "custom"
component_type: "hook"
base_class: "BaseHook"
conn_type: "custom_service"          # Required for hooks
hook_name: "custom_service_default"  # Required for hooks

inputs:
  - name: "api_endpoint"
    type: "str"
    required: true
```

**Response:**

```json
{
  "code": "<Generated Python operator/sensor/hook code>",
  "tests": "<Generated pytest test file with Phase 2 enhancements>",
  "documentation": "<Comprehensive usage documentation with troubleshooting>",
  "test_dag": "<Test DAG file with runtime params support>"
}
```

**Status Codes:**
- `200 OK` - Component generated successfully
- `400 Bad Request` - Invalid YAML or missing required fields
- `500 Internal Server Error` - Generation failed after retries

**Performance:**
- Simple components: ~15-20 seconds (uses Haiku model)
- Medium components: ~20-30 seconds (uses Sonnet model)
- Complex components: ~30-40 seconds (uses Sonnet model)

**Example:**

```bash
curl -X POST http://localhost:8095/api/airflow/component-generator/generate \
  -H "Content-Type: application/json" \
  -d '{
    "spec": "name: SimpleOperator\ndisplay_name: Simple Operator\ndescription: A simple operator\ncategory: custom\ncomponent_type: operator\ninputs:\n  - name: message\n    type: str\n    required: true\n    template_field: true"
  }'
```

**Phase 2 Enhancements:**

Generated tests include:
- ✅ Realistic TaskInstance mock with XCom storage (`_xcom_storage`)
- ✅ `test_xcom_push` and `test_xcom_pull` tests
- ✅ `test_template_rendering` for Jinja templates
- ✅ `test_edge_case_none_values` and `test_edge_case_empty_context`
- ✅ Comprehensive Airflow context fixture (15+ context variables)

Generated documentation includes:
- ✅ Troubleshooting section (import errors, runtime issues, XCom problems)
- ✅ Performance considerations
- ✅ Security best practices
- ✅ Advanced debugging techniques
- ✅ Quick reference debugging checklist

---

### 3. Generate Sample Component

**Endpoint:** `POST /generate/sample`

**Description:** Generate a sample component using a pre-defined specification to demonstrate capabilities.

**Request Body:**

```json
{}
```

**Response:**

```json
{
  "code": "<Generated sample operator code>",
  "tests": "<Generated test file>",
  "documentation": "<Usage documentation>",
  "test_dag": "<Test DAG file>"
}
```

**Status Codes:**
- `200 OK` - Sample component generated successfully
- `500 Internal Server Error` - Generation failed

**Example:**

```bash
curl -X POST http://localhost:8095/api/airflow/component-generator/generate/sample \
  -H "Content-Type: application/json" \
  -d '{}'
```

---

### 4. Assess Feasibility

**Endpoint:** `POST /assess`

**Description:** Assess the feasibility of generating a component before actual generation. Provides confidence level, complexity analysis, and potential issues.

**Request Body:**

```json
{
  "spec": "<YAML specification string>"
}
```

**Response:**

```json
{
  "feasible": true,
  "confidence": "high",
  "complexity": "medium",
  "issues": [],
  "suggestions": [
    "Consider adding error handling for API failures",
    "Add connection pooling for better performance"
  ],
  "missing_info": [],
  "similar_patterns_found": 5
}
```

**Response Fields:**
- `feasible` (boolean): Whether the component can be generated
- `confidence` (string): "high", "medium", "low", or "blocked"
- `complexity` (string): "simple", "medium", or "complex"
- `issues` (array): Blocking issues that prevent generation
- `suggestions` (array): Recommendations for improvement
- `missing_info` (array): Missing information that would improve generation
- `similar_patterns_found` (integer): Number of similar patterns found in RAG

**Status Codes:**
- `200 OK` - Assessment completed
- `400 Bad Request` - Invalid YAML
- `500 Internal Server Error` - Assessment failed

**Example:**

```bash
curl -X POST http://localhost:8095/api/airflow/component-generator/assess \
  -H "Content-Type: application/json" \
  -d '{
    "spec": "name: ComplexOperator\ndisplay_name: Complex Operator\ndescription: A complex operator\ncategory: custom\ncomponent_type: operator"
  }'
```

---

### 5. Analytics - Metrics

**Endpoint:** `GET /analytics/metrics`

**Description:** Get overall generation metrics including success rate, average generation time, and token usage.

**Request:** No parameters required.

**Response:**

```json
{
  "total_generations": 42,
  "successful_generations": 38,
  "failed_generations": 4,
  "success_rate": 90.48,
  "average_generation_time": 18.5,
  "average_attempts": 1.2,
  "total_prompt_tokens": 50000,
  "total_completion_tokens": 30000,
  "average_prompt_tokens": 1190,
  "average_completion_tokens": 714
}
```

**Status Codes:**
- `200 OK` - Metrics retrieved successfully
- `500 Internal Server Error` - Failed to retrieve metrics

**Example:**

```bash
curl http://localhost:8095/api/airflow/component-generator/analytics/metrics
```

---

### 6. Analytics - Insights

**Endpoint:** `GET /analytics/insights`

**Description:** Get insights by component category and type including generation counts and success rates.

**Request:** No parameters required.

**Response:**

```json
{
  "by_category": [
    {
      "category": "custom",
      "count": 20,
      "avg_time": 16.2,
      "success_rate": 95.0
    },
    {
      "category": "http",
      "count": 10,
      "avg_time": 18.5,
      "success_rate": 90.0
    }
  ],
  "by_type": [
    {
      "type": "operator",
      "count": 30,
      "avg_time": 17.1,
      "success_rate": 93.3
    },
    {
      "type": "sensor",
      "count": 8,
      "avg_time": 15.8,
      "success_rate": 87.5
    },
    {
      "type": "hook",
      "count": 4,
      "avg_time": 20.3,
      "success_rate": 100.0
    }
  ]
}
```

**Status Codes:**
- `200 OK` - Insights retrieved successfully
- `500 Internal Server Error` - Failed to retrieve insights

**Example:**

```bash
curl http://localhost:8095/api/airflow/component-generator/analytics/insights
```

---

### 7. Analytics - Trends

**Endpoint:** `GET /analytics/trends`

**Description:** Get performance trends over time including generation counts, success rates, and average times.

**Query Parameters:**
- `days` (integer, optional): Number of days to include in trends (default: 7)

**Request:**

```
GET /analytics/trends?days=30
```

**Response:**

```json
{
  "period_days": 30,
  "daily_trends": [
    {
      "date": "2026-01-20",
      "generations": 5,
      "success_rate": 100.0,
      "avg_time": 16.5
    },
    {
      "date": "2026-01-19",
      "generations": 8,
      "success_rate": 87.5,
      "avg_time": 18.2
    }
  ]
}
```

**Status Codes:**
- `200 OK` - Trends retrieved successfully
- `500 Internal Server Error` - Failed to retrieve trends

**Example:**

```bash
curl "http://localhost:8095/api/airflow/component-generator/analytics/trends?days=7"
```

---

### 8. Analytics - Errors

**Endpoint:** `GET /analytics/errors`

**Description:** Get error analytics including most common errors, error patterns, and their frequencies.

**Request:** No parameters required.

**Response:**

```json
{
  "total_errors": 12,
  "unique_patterns": 4,
  "most_common_errors": [
    {
      "pattern": "ImportError: No module named 'custom_package'",
      "count": 5,
      "percentage": 41.67,
      "example": "ImportError: No module named 'custom_package'"
    },
    {
      "pattern": "Validation error: Missing required field 'execute' method",
      "count": 3,
      "percentage": 25.0,
      "example": "Validation error: Missing required field 'execute' method"
    }
  ]
}
```

**Status Codes:**
- `200 OK` - Error analytics retrieved successfully
- `500 Internal Server Error` - Failed to retrieve error analytics

**Example:**

```bash
curl http://localhost:8095/api/airflow/component-generator/analytics/errors
```

---

## Data Models

### Component Specification (YAML)

All component types share these common fields:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | Yes | Component class name (PascalCase) |
| `display_name` | string | Yes | Human-readable name |
| `description` | string | Yes | Brief description of the component |
| `category` | string | Yes | Category (custom, http, database, cloud, etc.) |
| `component_type` | string | Yes | "operator", "sensor", or "hook" |
| `base_class` | string | No | Base class to extend (default: BaseOperator/BaseSensor/BaseHook) |
| `inputs` | array | No | Input parameters for the component |
| `runtime_params` | array | No | UI form fields for DAG trigger |
| `dependencies` | array | No | Python package dependencies |
| `requirements` | array | No | Natural language functional requirements |
| `template_fields` | array | No | Fields that support Jinja templating |
| `template_ext` | array | No | File extensions for template files |

#### Hook-Specific Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `conn_type` | string | Yes | Airflow connection type |
| `hook_name` | string | Yes | Default hook name |

#### Input Parameter

```yaml
- name: "param_name"           # Required
  type: "str"                  # Required: str, int, float, bool, list, dict, Optional[...], etc.
  required: true               # Optional: default false
  default: "value"             # Optional: default value
  template_field: true         # Optional: enable Jinja templating (default false)
  description: "Description"   # Optional: parameter description
```

#### Runtime Parameter

```yaml
- name: "ui_param"             # Required
  type: "string"               # Required: JSON schema types (string, number, boolean, array, object)
  default: "value"             # Optional: default value
  description: "Description"   # Optional: shown in Airflow UI
  enum: ["opt1", "opt2"]       # Optional: dropdown options
```

### Generated Component Response

```typescript
{
  code: string;           // Generated Python component code
  tests: string;          // Generated pytest test file with Phase 2 enhancements
  documentation: string;  // Comprehensive documentation with troubleshooting
  test_dag: string;       // Test DAG file with runtime params support
}
```

### Feasibility Assessment Response

```typescript
{
  feasible: boolean;                // Can the component be generated?
  confidence: string;               // "high" | "medium" | "low" | "blocked"
  complexity: string;               // "simple" | "medium" | "complex"
  issues: string[];                 // Blocking issues
  suggestions: string[];            // Recommendations
  missing_info: string[];           // Missing information
  similar_patterns_found: number;   // Number of similar patterns in RAG
}
```

---

## Error Handling

### HTTP Status Codes

| Code | Meaning | Description |
|------|---------|-------------|
| 200 | OK | Request successful |
| 400 | Bad Request | Invalid YAML or missing required fields |
| 500 | Internal Server Error | Generation failed after retries or internal error |
| 503 | Service Unavailable | Generator not initialized |

### Error Response Format

```json
{
  "detail": "Error message describing what went wrong"
}
```

### Common Errors

#### 400 Bad Request - Invalid YAML

```json
{
  "detail": "Invalid YAML: mapping values are not allowed here..."
}
```

#### 500 Internal Server Error - Missing Required Fields

```json
{
  "detail": "3 validation errors for OperatorSpec\ndisplay_name\n  Field required..."
}
```

#### 500 Internal Server Error - Generation Failed

```json
{
  "detail": "Failed to generate valid component after 4 attempts. Last errors: [...]"
}
```

---

## Examples

### Example 1: Simple Operator

**Request:**

```bash
curl -X POST http://localhost:8095/api/airflow/component-generator/generate \
  -H "Content-Type: application/json" \
  -d '{
    "spec": "name: HelloWorldOperator\ndisplay_name: Hello World Operator\ndescription: Prints a hello message\ncategory: custom\ncomponent_type: operator\ninputs:\n  - name: message\n    type: str\n    required: true\n    template_field: true\n    default: Hello, World!"
  }'
```

**Response:**

```json
{
  "code": "from airflow.models import BaseOperator\nfrom airflow.utils.decorators import apply_defaults\n...",
  "tests": "import pytest\nfrom unittest.mock import MagicMock\n...",
  "documentation": "# HelloWorldOperator\n\n## Overview\n...",
  "test_dag": "from airflow import DAG\nfrom datetime import datetime\n..."
}
```

### Example 2: Operator with Runtime Parameters

**Request:**

```bash
curl -X POST http://localhost:8095/api/airflow/component-generator/generate \
  -H "Content-Type: application/json" \
  -d '{
    "spec": "name: DataProcessorOperator\ndisplay_name: Data Processor\ndescription: Process data with configurable threshold\ncategory: data_processing\ncomponent_type: operator\nruntime_params:\n  - name: threshold\n    type: number\n    default: 0.5\n    description: Processing threshold\n  - name: mode\n    type: string\n    enum: [\"batch\", \"stream\"]\n    default: batch\n    description: Processing mode\ninputs:\n  - name: threshold\n    type: float\n    required: false\n    default: 0.5\n  - name: mode\n    type: str\n    required: false\n    default: batch"
  }'
```

### Example 3: Custom Sensor

**Request:**

```bash
curl -X POST http://localhost:8095/api/airflow/component-generator/generate \
  -H "Content-Type: application/json" \
  -d '{
    "spec": "name: CustomFileSensor\ndisplay_name: Custom File Sensor\ndescription: Waits for file to appear\ncategory: filesystem\ncomponent_type: sensor\nbase_class: BaseSensor\ninputs:\n  - name: filepath\n    type: str\n    required: true\n    template_field: true\n  - name: poke_interval\n    type: int\n    default: 60"
  }'
```

### Example 4: Assess Feasibility Before Generation

**Request:**

```bash
curl -X POST http://localhost:8095/api/airflow/component-generator/assess \
  -H "Content-Type: application/json" \
  -d '{
    "spec": "name: ComplexOperator\ndisplay_name: Complex Operator\ndescription: A complex operator with many dependencies\ncategory: data_processing\ncomponent_type: operator\ndependencies:\n  - apache-airflow-providers-postgres>=5.0.0\n  - pandas>=2.0.0\n  - sqlalchemy>=2.0.0\nrequirements:\n  - Execute SQL queries\n  - Process results with pandas\n  - Support multiple output formats"
  }'
```

**Response:**

```json
{
  "feasible": true,
  "confidence": "high",
  "complexity": "complex",
  "issues": [],
  "suggestions": [
    "Consider adding connection pooling for PostgreSQL",
    "Add error handling for SQL execution failures"
  ],
  "missing_info": [],
  "similar_patterns_found": 3
}
```

### Example 5: Get Generation Metrics

**Request:**

```bash
curl http://localhost:8095/api/airflow/component-generator/analytics/metrics
```

**Response:**

```json
{
  "total_generations": 42,
  "successful_generations": 38,
  "failed_generations": 4,
  "success_rate": 90.48,
  "average_generation_time": 18.5,
  "average_attempts": 1.2,
  "total_prompt_tokens": 50000,
  "total_completion_tokens": 30000,
  "average_prompt_tokens": 1190,
  "average_completion_tokens": 714
}
```

---

## Best Practices

### 1. Always Assess Before Generating

Use the `/assess` endpoint to check feasibility before generating complex components.

### 2. Use Runtime Parameters for User Input

Define `runtime_params` for values that should be configurable via the Airflow UI when triggering DAGs.

### 3. Enable Template Fields

Set `template_field: true` for inputs that should support Jinja templating (e.g., file paths, SQL queries).

### 4. Specify Dependencies

Always list all required Python packages in the `dependencies` field to ensure proper environment setup.

### 5. Provide Clear Requirements

Use the `requirements` field to describe functional requirements in natural language for better code generation.

### 6. Monitor Performance

Use the analytics endpoints to track success rates and identify patterns in failures.

---

## Rate Limits

Currently, there are no rate limits enforced. However, each generation request takes 15-40 seconds depending on complexity.

---

## Support

For issues or questions:
- GitHub: [github.com/anthropics/claude-code/issues](https://github.com/anthropics/claude-code/issues)
- Documentation: See `README.md` and `PHASE2_ACTIVATION_GUIDE.md`

---

## Changelog

### Version 0.1.0 (2026-01-20)

**Phase 2 Enhancements:**
- ✅ Enhanced test generation with XCom mocking, template rendering tests, and edge cases
- ✅ Comprehensive troubleshooting documentation (20k+ characters)
- ✅ Model routing by complexity (Haiku for simple components = 80% cost savings)
- ✅ Optional static analysis integration (mypy, ruff)
- ✅ Improved error handling and null safety
- ✅ Platform-agnostic database paths (Windows/Linux/Mac/Docker)
- ✅ Environment variable loading from .env files

**Initial Release:**
- Component generation for operators, sensors, and hooks
- YAML-based specification format
- Test file generation with pytest
- Documentation generation
- DAG file generation with runtime params support
- Feasibility assessment
- Analytics endpoints (metrics, insights, trends, errors)
- Multi-layer validation (syntax, imports, structure, security, Airflow compliance)
- Error tracking and learning system
- RAG service integration (optional)
