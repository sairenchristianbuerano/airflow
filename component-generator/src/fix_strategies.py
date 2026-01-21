"""
Fix Strategies - Phase 2

Maps error types to specific fix strategies with prompt templates.
Contains the logic for applying learned fixes during retry attempts.
"""

from typing import Dict, Any, List, Optional
import structlog

logger = structlog.get_logger()


class FixStrategyManager:
    """Manage fix strategies for different error types"""

    def __init__(self):
        self.logger = logger.bind(component="fix_strategy_manager")
        self.strategies = self._initialize_strategies()

    def _initialize_strategies(self) -> Dict[str, Dict[str, Any]]:
        """Initialize built-in fix strategies"""
        return {
            # Parameter ordering fix (our most common error!)
            "reorder_parameters": {
                "type": "syntax",
                "priority": "critical",
                "auto_fixable": True,
                "requires_code_change": True,
                "requires_spec_change": False,
                "description": "Reorder function parameters to put required params before optional",
                "prompt_addition": """
**CRITICAL FIX REQUIRED**: Parameter Ordering Error

The previous attempt failed because required parameters came after optional parameters.
This is a Python syntax error.

**You MUST ensure:**
1. ALL required parameters (no default value) come FIRST
2. ALL optional parameters (with default value) come LAST
3. Order: required params → optional params

Example CORRECT:
```python
def __init__(self, required_param: str, optional_param: str = 'default', **kwargs):
    pass
```

Example WRONG (will fail):
```python
def __init__(self, optional_param: str = 'default', required_param: str, **kwargs):
    pass  # ❌ SyntaxError!
```

Please regenerate with correct parameter ordering.
"""
            },

            # Indentation fix
            "fix_indentation": {
                "type": "syntax",
                "priority": "high",
                "auto_fixable": True,
                "requires_code_change": True,
                "description": "Fix indentation errors in Python code",
                "prompt_addition": """
**INDENTATION ERROR DETECTED**

The previous attempt had indentation errors. Python is strict about indentation.

**Rules:**
1. Use 4 spaces for each indentation level (NOT tabs)
2. All code in a block must be indented consistently
3. Function/class bodies must be indented
4. if/for/while/try blocks must be indented

Please regenerate with correct indentation (4 spaces per level).
"""
            },

            # Missing block fix
            "add_missing_block": {
                "type": "syntax",
                "priority": "high",
                "requires_code_change": True,
                "description": "Add missing try/except/finally blocks",
                "prompt_addition": """
**MISSING BLOCK ERROR**

The previous attempt had an incomplete try/except/finally structure.

**Rules:**
1. Every `try:` must have at least one `except:` or `finally:`
2. Cannot have `finally:` without `except:` or bare `except:`
3. Proper structure:
```python
try:
    # code
except SomeException as e:
    # handler
finally:
    # cleanup (optional)
```

Please regenerate with complete try/except blocks.
"""
            },

            # Import error fixes
            "add_dependency_or_mock": {
                "type": "import",
                "priority": "medium",
                "requires_code_change": True,
                "description": "Handle missing import by adding dependency or mock implementation",
                "prompt_addition": """
**IMPORT ERROR DETECTED**

The previous attempt tried to import a module that may not be available.

**Options:**
1. **Mock Mode**: Implement a mock/fallback version that works without the library
2. **Check Import**: Add try/except to gracefully handle missing imports
3. **Verify Path**: Ensure import path is correct for Airflow

**Example mock pattern:**
```python
try:
    from external_library import SomeThing
    HAS_EXTERNAL_LIB = True
except ImportError:
    HAS_EXTERNAL_LIB = False
    # Mock implementation
    class SomeThing:
        def method(self):
            self.log.warning("Library not available, using mock")
            return {"mock": True}
```

Please regenerate with import error handling.
"""
            },

            # Type error fixes
            "fix_type_hints": {
                "type": "type",
                "priority": "low",
                "requires_code_change": True,
                "description": "Fix type hint errors",
                "prompt_addition": """
**TYPE HINT ERROR**

The previous attempt had incorrect type hints.

**Common fixes:**
1. Import types from `typing` module: `Dict`, `List`, `Optional`, etc.
2. Use `Optional[Type]` for values that can be None
3. Use `Any` if type is truly dynamic
4. Use `Sequence[str]` for template_fields

Example:
```python
from typing import Dict, Any, Optional, Sequence

def method(self, param: Optional[str] = None) -> Dict[str, Any]:
    pass
```

Please regenerate with correct type hints.
"""
            },

            # Undefined name fixes
            "define_variable_or_import": {
                "type": "name",
                "priority": "high",
                "requires_code_change": True,
                "description": "Define undefined variables or add missing imports",
                "prompt_addition": """
**UNDEFINED NAME ERROR**

The previous attempt referenced a variable/function that wasn't defined.

**Common causes:**
1. Forgot to import from a module
2. Typo in variable/function name
3. Variable used before definition
4. Missing `self.` prefix for instance variables

**Fixes:**
1. Check if it needs to be imported
2. Define the variable before use
3. Add `self.` prefix if it's an instance variable
4. Fix typos in names

Please regenerate ensuring all names are defined before use.
"""
            },

            # Validation error fixes
            "review_spec": {
                "type": "validation",
                "priority": "medium",
                "requires_spec_change": True,
                "description": "Review and potentially modify the component specification",
                "prompt_addition": """
**VALIDATION ERROR**

The previous attempt failed validation. This usually means the spec is unclear or contradictory.

**Check:**
1. Are required parameters actually required?
2. Do default values match the required flag?
3. Are type hints consistent with usage?
4. Are dependencies correctly specified?

Please regenerate carefully reviewing the specification.
"""
            },

            # Generic syntax fix
            "fix_syntax": {
                "type": "syntax",
                "priority": "high",
                "requires_code_change": True,
                "description": "Fix generic syntax errors",
                "prompt_addition": """
**SYNTAX ERROR DETECTED**

The previous attempt had a Python syntax error.

**Common issues:**
1. Missing/extra parentheses, brackets, or braces
2. Missing colons after if/for/while/def/class
3. Incorrect indentation
4. Invalid Python keywords or operators

Please regenerate with valid Python syntax. Double-check:
- Matching parentheses/brackets/braces
- Colons after control structures
- Proper indentation
- Valid Python operators

"""
            },

            # Retry with more detailed prompt
            "retry_with_detailed_prompt": {
                "type": "generic",
                "priority": "low",
                "requires_code_change": True,
                "description": "Retry with more detailed error explanation",
                "prompt_addition": """
**PREVIOUS ATTEMPT FAILED**

The previous generation attempt failed. Please carefully review the error below and fix it.

**General guidelines:**
1. Follow Python syntax rules strictly
2. Ensure all imports are valid
3. Match parameter types to specifications
4. Include proper error handling
5. Follow Airflow operator patterns

Please regenerate addressing the specific error mentioned.
"""
            },

            # Add return statement
            "add_return_statement": {
                "type": "logic",
                "priority": "medium",
                "requires_code_change": True,
                "description": "Add missing return statement to execute method",
                "prompt_addition": """
**MISSING RETURN STATEMENT**

The execute() method should return a result dictionary.

**Pattern:**
```python
def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
    # ... execution logic ...

    return {
        'status': 'success',
        'result': result_data,
        'task_id': self.task_id,
        # ... other relevant data ...
    }
```

Please regenerate ensuring execute() returns a dictionary.
"""
            },

            # Runtime error fixes
            "add_zero_check": {
                "type": "runtime",
                "priority": "medium",
                "requires_code_change": True,
                "description": "Add check for division by zero",
                "prompt_addition": """
**DIVISION BY ZERO ERROR**

Add validation to prevent division by zero:

```python
if denominator == 0:
    raise AirflowException("Denominator cannot be zero")
result = numerator / denominator
```
"""
            },

            "check_key_exists": {
                "type": "runtime",
                "priority": "medium",
                "requires_code_change": True,
                "description": "Check if dictionary key exists before accessing",
                "prompt_addition": """
**KEY ERROR**

Always check if keys exist before accessing:

```python
# Option 1: Use get() with default
value = my_dict.get('key', default_value)

# Option 2: Check existence
if 'key' in my_dict:
    value = my_dict['key']
else:
    value = default_value
```
"""
            },

            "add_null_check": {
                "type": "runtime",
                "priority": "medium",
                "requires_code_change": True,
                "description": "Add null/None checks",
                "prompt_addition": """
**NULL/NONE REFERENCE ERROR**

Add None checks before accessing attributes:

```python
if value is not None:
    result = value.some_method()
else:
    result = default_value
```
"""
            }
        }

    def get_strategy(self, strategy_name: str) -> Optional[Dict[str, Any]]:
        """Get a fix strategy by name"""
        return self.strategies.get(strategy_name)

    def get_prompt_addition(
        self,
        strategy_name: str,
        error_message: Optional[str] = None,
        error_patterns: Optional[Dict] = None
    ) -> str:
        """
        Get the prompt addition for a fix strategy

        Args:
            strategy_name: Name of the strategy
            error_message: The actual error message (to include in prompt)
            error_patterns: Extracted error patterns (for context)

        Returns:
            Prompt text to add to the retry attempt
        """
        strategy = self.get_strategy(strategy_name)
        if not strategy:
            # Fallback to generic retry
            strategy = self.strategies["retry_with_detailed_prompt"]

        prompt = strategy["prompt_addition"]

        # Add the actual error message if provided
        if error_message:
            prompt += f"\n**Specific Error:**\n```\n{error_message}\n```\n"

        # Add extracted pattern info if helpful
        if error_patterns:
            classification = error_patterns.get('error_classification', {})
            if classification.get('line_number'):
                prompt += f"\n**Error Location:** Line {classification['line_number']}\n"

            # Add specific fix hints based on pattern type
            if error_patterns.get('parameter_errors'):
                param_errors = error_patterns['parameter_errors']
                if param_errors.get('missing_parameter'):
                    prompt += f"\n**Missing Parameter:** `{param_errors['missing_parameter']}`\n"
                if param_errors.get('unexpected_parameter'):
                    prompt += f"\n**Unexpected Parameter:** `{param_errors['unexpected_parameter']}`\n"

            if error_patterns.get('import_errors'):
                import_errors = error_patterns['import_errors']
                if import_errors.get('missing_module'):
                    prompt += f"\n**Missing Module:** `{import_errors['missing_module']}`\n"

            if error_patterns.get('name_errors'):
                name_errors = error_patterns['name_errors']
                if name_errors.get('undefined_name'):
                    prompt += f"\n**Undefined Name:** `{name_errors['undefined_name']}`\n"

        return prompt

    def select_best_strategy(
        self,
        error_patterns: Dict[str, Any],
        similar_errors: Optional[List[Dict]] = None
    ) -> str:
        """
        Select the best fix strategy for given error patterns

        Args:
            error_patterns: Extracted error patterns
            similar_errors: Similar errors from history (with successful fixes)

        Returns:
            Strategy name to use
        """
        # If we have historical data on similar errors, use that
        if similar_errors:
            for similar in similar_errors:
                if similar.get('strategy_name') and similar.get('effectiveness_score', 0) > 0.7:
                    self.logger.info(
                        f"Using learned strategy from similar error",
                        strategy=similar['strategy_name'],
                        effectiveness=similar['effectiveness_score']
                    )
                    return similar['strategy_name']

        # Otherwise, use extracted patterns to determine strategy
        classification = error_patterns.get('error_classification', {})
        error_type = classification.get('error_type', 'unknown')

        # Priority order based on error type
        if error_patterns.get('parameter_errors', {}).get('pattern') == 'parameter_ordering':
            return 'reorder_parameters'  # HIGHEST PRIORITY - our most common error!

        if error_patterns.get('indentation_errors', {}).get('has_indentation_error'):
            return 'fix_indentation'

        if error_patterns.get('syntax_errors', {}).get('pattern') == 'missing_block':
            return 'add_missing_block'

        if error_patterns.get('import_errors', {}).get('has_import_error'):
            return 'add_dependency_or_mock'

        if error_patterns.get('name_errors', {}).get('has_name_error'):
            return 'define_variable_or_import'

        if error_patterns.get('type_errors', {}).get('has_type_error'):
            return 'fix_type_hints'

        if error_patterns.get('syntax_errors', {}).get('has_syntax_error'):
            return 'fix_syntax'

        if error_patterns.get('validation_errors', {}).get('has_validation_error'):
            return 'review_spec'

        # Check for runtime errors
        runtime = error_patterns.get('runtime_errors', {})
        if runtime.get('runtime_error') == 'division_by_zero':
            return 'add_zero_check'
        elif runtime.get('runtime_error') == 'key_error':
            return 'check_key_exists'
        elif runtime.get('runtime_error') == 'null_reference':
            return 'add_null_check'

        # Default to generic retry
        return 'retry_with_detailed_prompt'

    def get_strategy_priority(self, strategy_name: str) -> int:
        """Get numeric priority for a strategy (higher = more urgent)"""
        strategy = self.get_strategy(strategy_name)
        if not strategy:
            return 0

        priority_map = {
            'critical': 100,
            'high': 75,
            'medium': 50,
            'low': 25
        }

        return priority_map.get(strategy.get('priority', 'low'), 0)

    def is_auto_fixable(self, strategy_name: str) -> bool:
        """Check if a strategy can be auto-fixed without human intervention"""
        strategy = self.get_strategy(strategy_name)
        return strategy.get('auto_fixable', False) if strategy else False

    def requires_spec_change(self, strategy_name: str) -> bool:
        """Check if a strategy requires changing the component specification"""
        strategy = self.get_strategy(strategy_name)
        return strategy.get('requires_spec_change', False) if strategy else False
