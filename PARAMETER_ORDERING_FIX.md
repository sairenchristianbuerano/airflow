# Parameter Ordering Fix

## Problem Statement

The code generator was producing Python syntax errors when component specifications contained parameters with `required: true` and a `default` value. This resulted in errors like:

```
Syntax error: parameter without a default follows parameter with a default
```

### Example of Problematic YAML

```yaml
inputs:
  - name: mode
    type: str
    required: true
    default: "inference"  # ❌ Contradictory: required but has default

  - name: dataset_file
    type: str
    required: false
    default: ""
```

This would generate invalid Python:
```python
def __init__(self, mode, dataset_file=""):  # ❌ Invalid! Required param after optional
```

## Root Cause

Python requires function parameters to follow a specific order:
1. Required parameters WITHOUT defaults
2. Required parameters WITH defaults (or optional parameters)
3. Keyword-only parameters

The generator was not reordering parameters before generating code, causing syntax errors when the YAML spec had:
- Parameters marked `required: true` with `default` values (logically contradictory)
- Optional parameters appearing before required parameters

## Solution

### Implementation

Modified `component-generator/src/airflow_agent.py` in the `_build_prompt` method (lines 454-505) to:

1. **Classify parameters into three groups:**
   - `required_no_default`: Truly required (required=true, no default)
   - `required_with_default`: Contradictory (required=true, has default)
   - `optional_params`: Optional (required=false)

2. **Reorder before prompt generation:**
   ```python
   sorted_inputs = required_no_default + required_with_default + optional_params
   ```

3. **Log warnings for contradictions:**
   ```python
   self.logger.warning(
       "Parameter has required=true but also has default value",
       param_name=inp.get('name'),
       default_value=inp.get('default')
   )
   ```

4. **Add guidance to prompt:**
   The prompt now explicitly tells Claude the parameter ordering to ensure valid Python syntax.

### Code Changes

**File:** `component-generator/src/airflow_agent.py`

```python
# Add input parameters
if spec.inputs:
    # CRITICAL FIX: Sort inputs to ensure valid Python parameter ordering
    required_no_default = []
    required_with_default = []
    optional_params = []

    for inp in spec.inputs:
        is_required = inp.get('required', False)
        has_default = 'default' in inp

        if is_required and not has_default:
            required_no_default.append(inp)
        elif is_required and has_default:
            # Log warning for contradictory specification
            self.logger.warning(...)
            required_with_default.append(inp)
        else:
            optional_params.append(inp)

    # Reorder: required (no default) -> required (with default) -> optional
    sorted_inputs = required_no_default + required_with_default + optional_params

    # Add to prompt with ordering guidance
    ...
```

## Testing

### Test Case 1: Parameter Ordering

**YAML:**
```yaml
name: TestParamOrderingOperator
inputs:
  - name: required_with_default
    type: str
    required: true
    default: "test_value"
  - name: optional_param
    type: str
    required: false
    default: "optional"
  - name: another_required_default
    type: int
    required: true
    default: 42
```

**Result:** ✅ SUCCESS
- Generated valid Python code
- Parameters properly ordered with all defaults
- Warnings logged for contradictory `required: true` + `default`

**Generated Code:**
```python
def __init__(
    self,
    required_with_default: str = 'test_value',
    another_required_default: int = 42,
    optional_param: Optional[str] = 'optional',
    **kwargs
):
```

### Test Case 2: Simplified NeMo Component

**YAML:** 5 inputs with `required: true` and `default` values

**Result:** ✅ SUCCESS
- Complexity score: 24.0
- Generated on first attempt
- 11,464 characters of valid code
- 0 validation errors
- Cost: $0.0522

## Warnings in Logs

When the fix detects contradictory specifications, it logs:

```
2026-01-20 11:54:13 [warning] Parameter has required=true but also has default value - treating as required with default
  component=airflow_generator
  default_value=test_value
  param_name=required_with_default
```

## Best Practices

### For Component Specification Authors

1. **Avoid contradictions:**
   - If a parameter has a default value, set `required: false`
   - If a parameter is truly required (no default), set `required: true` without `default`

2. **Recommended patterns:**
   ```yaml
   # ✅ Good: Truly required (no default)
   - name: api_key
     type: str
     required: true

   # ✅ Good: Optional with default
   - name: timeout
     type: int
     required: false
     default: 30

   # ⚠️ Works but contradictory (logs warning)
   - name: mode
     type: str
     required: true
     default: "production"
   ```

3. **Order doesn't matter in YAML:**
   - The generator will automatically reorder parameters
   - You can write them in any order in the YAML spec

## Impact

### Before Fix
- ❌ Components with contradictory specs failed to generate
- ❌ Syntax errors: "parameter without a default follows parameter with a default"
- ❌ Required manual YAML editing to fix

### After Fix
- ✅ Automatic parameter reordering
- ✅ Warning logs for contradictions
- ✅ Valid Python code generated
- ✅ Handles all parameter ordering scenarios

## Related Files

- `component-generator/src/airflow_agent.py` - Main fix implementation
- `component_spec_simple.yaml` - Simplified NeMo component (working example)
- `test_param_ordering.yaml` - Test case for parameter ordering
- `test_param_result.json` - Successful generation result

## Future Improvements

1. **Spec validation:** Add validation step to warn users about contradictory `required: true` + `default` in YAML
2. **Auto-fix suggestions:** Suggest `required: false` when default values are present
3. **Documentation:** Update component specification guide with parameter ordering best practices
