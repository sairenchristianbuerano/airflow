# Runtime Parameters Implementation for Airflow Component Generator

## Overview

This document details the implementation of runtime parameters support in the Airflow Component Generator. Runtime parameters allow users to input values via the Airflow UI when triggering DAGs, similar to node configuration in Flowise.

## Date: January 19, 2026

## Motivation

The user requested the ability to allow end-users to input values when running generated components, such as:
- Specifying a city name for a weather component
- Entering calculation inputs for a math component
- Providing dynamic configuration at runtime

This feature leverages Airflow's `Params` functionality to create UI forms in the "Trigger DAG" dialog.

---

## Implementation Steps

### Phase 1: Spec Format Enhancement

**File Modified:** `COMPONENT_SPEC_FORMAT.yaml`

Added `runtime_params` section to the spec format (lines 51-70):

```yaml
runtime_params:
  - name: "city"
    type: "string"
    description: "City name to fetch weather for"
    default: "Tokyo"
    enum: []  # Optional: dropdown values
  - name: "units"
    type: "string"
    default: "metric"
    enum: ["metric", "imperial"]  # Creates dropdown in UI
```

**Purpose:** Define which parameters should be configurable via UI when triggering the DAG.

---

### Phase 2: Data Model Update

**File Modified:** `component-generator/src/base_classes.py`

Added `runtime_params` field to `OperatorSpec` class (lines 42-45):

```python
runtime_params: Optional[List[Dict[str, Any]]] = Field(
    default=None,
    description="Runtime parameters configurable via Airflow UI (DAG params)"
)
```

**Issue Found:** Initially, this field was missing, causing the YAML parser to ignore runtime_params.

**Fix:** Added the field to ensure runtime_params are parsed from the spec YAML.

---

### Phase 3: Test DAG Generator

**File Modified:** `component-generator/src/test_generator.py`

Added `generate_test_dag()` method (lines 420-512) with two helper methods:

**A. `_generate_params_code()` (lines 514-568):**
- Converts runtime_params from spec into Airflow `Param()` objects
- Handles type mapping (string → str, number → number, etc.)
- Adds enum support for dropdown menus
- Generates code like:
  ```python
  params={
      'city': Param(default='Tokyo', type='str', description='City name'),
      'units': Param(default='metric', type='str', enum=["metric", "imperial"]),
  }
  ```

**B. `_generate_dag_task_params()` (lines 570-611):**
- Matches runtime_params to operator inputs
- Generates Jinja template strings for runtime params: `city="{{ params.city }}"`
- Uses default values for non-runtime params

**Issues Found & Fixed:**

1. **Issue:** Lines 528 and 576 had double curly braces `{{` causing "unhashable type: 'set'" error
   - **Root Cause:** Incorrect brace escaping in f-strings
   - **Fix:** Changed `{{` to `{` for proper Python syntax

---

### Phase 4: Operator Code Generation

**File Modified:** `component-generator/src/airflow_agent.py`

**Changes:**

1. **Runtime Params Detection** (lines 374-384):
   - Detects if spec has runtime_params
   - Adds note in prompt that parameters will be passed as Jinja templates

2. **Template Field Validation Guidelines** (lines 457-470):
   ```python
   prompt += """
   4. **Constructor (`__init__`):**
      - **CRITICAL: Template Field Validation** - For fields in `template_fields`:
        * Skip validation for Jinja template strings (containing `{{`)
        * These will be rendered at runtime, so validate in execute() instead
        * Example: `if '{{' not in str(param_value) and param_value not in valid_values:`
   """
   ```

**Purpose:** Ensure generated operators handle Jinja templates correctly in `__init__`.

**Example Generated Code:**
```python
def __init__(self, city: str, units: str = 'metric', **kwargs):
    super().__init__(**kwargs)

    # Validate units if not a template
    if '{{' not in str(units) and units not in ['metric', 'imperial']:
        raise AirflowException(f"Invalid units '{units}'")

    # Validate city if not a template
    if '{{' not in str(city) and not city.strip():
        raise AirflowException("City parameter cannot be empty")

    self.city = city
    self.units = units
```

---

### Phase 5: Validation Enhancement

**File Modified:** `component-generator/src/airflow_validator.py`

Added template field validation check (lines 380-391):

```python
if 'template_fields' in code and '__init__' in code:
    if ('raise AirflowException' in code and
        '{{' not in code and
        'execute' in code):
        warnings.append(
            "Template fields may need Jinja template handling. "
            "Consider skipping validation for '{{' strings in __init__"
        )
```

**Purpose:** Warn if generated code might not handle Jinja templates properly.

---

### Phase 6: API Response Update

**File Modified:** `component-generator/src/service.py`

Updated `/generate` endpoint response (line 141):

```python
return {
    "code": result.code,
    "documentation": result.documentation,
    "tests": result.tests,
    "test_dag": result.test_dag  # Added this field
}
```

**Purpose:** Include generated test DAG in API response.

---

## How It Works (End-to-End Flow)

### 1. Spec Definition
User creates a YAML spec with `runtime_params`:
```yaml
runtime_params:
  - name: "city"
    type: "string"
    default: "Tokyo"
```

### 2. Spec Parsing
`OperatorSpec` model parses YAML and includes `runtime_params` field.

### 3. Code Generation
- `airflow_agent.py` generates operator code with template validation:
  ```python
  if '{{' not in str(city): # Skip validation for templates
      validate(city)
  ```

### 4. Test DAG Generation
- `test_generator.py` creates DAG with:
  - `params={}` dictionary with `Param()` objects
  - Task parameters using Jinja: `city="{{ params.city }}"`

### 5. Runtime Execution
- User triggers DAG in Airflow UI
- UI form appears with input fields based on `params`
- User enters values (e.g., city="London", units="imperial")
- Airflow renders Jinja templates: `"{{ params.city }}"` → `"London"`
- Operator `execute()` runs with actual values

---

## Testing the Feature

### 1. Generate Component

```bash
python test_generate.py
```

This uses `test_weather_with_params.yaml` spec.

### 2. Deploy to Airflow

```bash
cp generated_weather_operator.py <airflow-dags-path>/
cp generated_weather_dag.py <airflow-dags-path>/test_generated_weather.py
```

### 3. Test in Airflow UI

1. Access http://localhost:8080
2. Find DAG: `test_weather_fetch_operator`
3. Click "Trigger DAG" (▶️ play button)
4. Form appears with fields:
   - **city** (text input, default: "Tokyo")
   - **units** (dropdown: "metric" or "imperial")
5. Enter values and click "Trigger"
6. View logs to see results with your input values

---

## Files Modified

| File | Lines Modified | Purpose |
|------|---------------|---------|
| `COMPONENT_SPEC_FORMAT.yaml` | 51-70 | Added runtime_params documentation |
| `base_classes.py` | 42-45 | Added runtime_params field to OperatorSpec |
| `test_generator.py` | 420-611 | Added test DAG generation with params support |
| `airflow_agent.py` | 374-384, 457-470 | Enhanced prompt for template handling |
| `airflow_validator.py` | 380-391 | Added template validation check |
| `service.py` | 141 | Added test_dag to API response |
| `documentation_generator.py` | 527-636 | Added runtime params documentation section |

---

## Key Learnings

### 1. Jinja Template Handling
**Problem:** Operators validated parameters in `__init__`, but Jinja templates like `"{{ params.city }}"` are strings at parse time, not actual values.

**Solution:** Check if parameter contains `{{` before validation:
```python
if '{{' not in str(param) and param not in valid_values:
    raise AirflowException()
```

### 2. Airflow 2.x Compatibility
Fixed deprecated syntax:
- `schedule_interval` → `schedule`
- Removed `@apply_defaults` decorator
- Removed `provide_context=True`

### 3. Docker Build Process
Changes require rebuilding Docker image:
```bash
docker-compose down
docker-compose build
docker-compose up -d
```

### 4. Spec Parsing
All fields in YAML spec must be defined in the Pydantic `OperatorSpec` model, or they'll be ignored during parsing.

---

## Future Enhancements

1. **Validation at Runtime:**
   - Move validation from `__init__` to `execute()` for template fields
   - Validate actual rendered values, not template strings

2. **Additional Param Types:**
   - Support for complex types: arrays, objects
   - File uploads via UI
   - Multi-select dropdowns

3. **Param Dependencies:**
   - Conditional parameters (show field B only if field A has certain value)
   - Dynamic defaults based on other params

4. **Enhanced Documentation:**
   - Auto-generate screenshots of UI forms
   - Interactive examples in docs

---

## Component Generator Service

**Location:** `component-generator/`
**Port:** 8095
**Endpoint:** `POST /api/airflow/component-generator/generate`

**Start Service:**
```bash
cd c:\Users\Joana\Desktop\sairen-files\github\repo\airflow
docker-compose up -d
```

**Check Health:**
```bash
curl http://localhost:8095/api/airflow/component-generator/health
```

---

## Example Generated Output

See the following files for reference:
- `generated_weather_operator.py` - Operator with template handling
- `generated_weather_dag.py` - DAG with runtime params
- `generated_weather_docs.md` - Documentation with params section
- `generated_weather_test.py` - Pytest tests

---

## Troubleshooting

### DAG Not Showing in UI
- Check Airflow scheduler logs
- Ensure DAG file is in the `dags/` directory
- Verify no syntax errors in DAG file

### Params Not Appearing in Trigger Dialog
- Ensure `params={}` is defined in DAG constructor
- Verify `Param()` objects are properly formatted
- Check Airflow UI version supports params (2.0+)

### Template Validation Error
- Ensure operator checks for `{{` before validation
- Verify fields are in `template_fields` list
- Check that task parameters use Jinja syntax: `="{{ params.name }}"`

---

## Summary

The runtime parameters feature successfully enables dynamic user input via the Airflow UI, making generated components more flexible and user-friendly. The implementation required changes across 6 files in the component generator, with careful attention to Jinja template handling and Airflow 2.x compatibility.

This feature brings Airflow component generation closer to the user experience of platforms like Flowise, where users can configure node parameters at runtime.
