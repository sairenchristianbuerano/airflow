"""
Error Learning System - Phase 2

Extracts patterns from failed component generations, classifies errors,
and learns fix strategies to improve future generations.

Similar to pattern_extractor.py but focused on failures instead of successes.
"""

import re
import json
import hashlib
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
import structlog

logger = structlog.get_logger()


class ErrorPatternExtractor:
    """Extract learnable patterns from failed component generations"""

    def __init__(self):
        self.logger = logger.bind(component="error_pattern_extractor")

    def extract_error_patterns(
        self,
        error_message: str,
        code: Optional[str],
        spec: Dict[str, Any],
        attempt_number: int,
        metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Extract all learnable patterns from a failed generation

        Args:
            error_message: The error message from validation
            code: The generated code that failed (if available)
            spec: The component specification
            attempt_number: Which retry attempt this was
            metadata: Additional metadata (tokens, time, etc.)

        Returns:
            Dict containing all extracted error patterns
        """
        self.logger.info(
            "Extracting error patterns",
            error_type=self._classify_error_type(error_message),
            attempt=attempt_number
        )

        patterns = {
            "error_classification": self._classify_error(error_message, code),
            "syntax_errors": self._extract_syntax_errors(error_message, code),
            "import_errors": self._extract_import_errors(error_message, code),
            "parameter_errors": self._extract_parameter_errors(error_message, code),
            "validation_errors": self._extract_validation_errors(error_message),
            "type_errors": self._extract_type_errors(error_message, code),
            "indentation_errors": self._extract_indentation_errors(error_message, code),
            "name_errors": self._extract_name_errors(error_message, code),
            "attribute_errors": self._extract_attribute_errors(error_message, code),
            "runtime_errors": self._extract_runtime_errors(error_message),
            "logic_errors": self._extract_logic_errors(error_message, code),
            "context": self._extract_error_context(error_message, code, spec),
            "metadata": {
                "attempt_number": attempt_number,
                "component_name": spec.get('name', 'unknown'),
                "category": spec.get('category', 'unknown'),
                "complexity": len(spec.get('inputs', [])) + len(spec.get('runtime_params', [])),
                "extracted_at": datetime.utcnow().isoformat(),
                **metadata
            }
        }

        return patterns

    def _classify_error_type(self, error_message: str) -> str:
        """Quick error type classification"""
        error_lower = error_message.lower()

        if 'syntax error' in error_lower or 'invalid syntax' in error_lower:
            return 'syntax'
        elif 'import' in error_lower or 'no module named' in error_lower or 'cannot import' in error_lower:
            return 'import'
        elif 'parameter' in error_lower or 'argument' in error_lower:
            return 'parameter'
        elif 'type' in error_lower:
            return 'type'
        elif 'indentation' in error_lower:
            return 'indentation'
        elif 'name' in error_lower and ('not defined' in error_lower or 'undefined' in error_lower):
            return 'name'
        elif 'attribute' in error_lower:
            return 'attribute'
        elif 'validation' in error_lower:
            return 'validation'
        else:
            return 'unknown'

    def _classify_error(self, error_message: str, code: Optional[str]) -> Dict[str, Any]:
        """Detailed error classification with severity and category"""
        error_type = self._classify_error_type(error_message)

        # Determine severity
        severity = 'medium'
        if 'syntax error' in error_message.lower():
            severity = 'high'  # Syntax errors are critical
        elif 'warning' in error_message.lower():
            severity = 'low'
        elif 'critical' in error_message.lower() or 'fatal' in error_message.lower():
            severity = 'critical'

        # Extract line number if available
        line_number = None
        line_match = re.search(r'line (\d+)', error_message, re.IGNORECASE)
        if line_match:
            line_number = int(line_match.group(1))

        return {
            "error_type": error_type,
            "severity": severity,
            "line_number": line_number,
            "is_recoverable": self._is_recoverable(error_type),
            "requires_code_change": error_type in ['syntax', 'parameter', 'indentation', 'name'],
            "requires_spec_change": error_type in ['validation'],
            "error_signature": self._generate_error_signature(error_message)
        }

    def _is_recoverable(self, error_type: str) -> bool:
        """Determine if this error type is typically recoverable through retry"""
        recoverable_types = ['parameter', 'indentation', 'name', 'type', 'syntax']
        return error_type in recoverable_types

    def _generate_error_signature(self, error_message: str) -> str:
        """Generate a unique signature for this error pattern"""
        # Remove line numbers and specific values to generalize the pattern
        normalized = re.sub(r'\d+', 'N', error_message)
        normalized = re.sub(r"'[^']+'", "'VALUE'", normalized)
        normalized = re.sub(r'"[^"]+"', '"VALUE"', normalized)

        return hashlib.md5(normalized.encode()).hexdigest()[:16]

    def _extract_syntax_errors(self, error_message: str, code: Optional[str]) -> Dict[str, Any]:
        """Extract syntax error patterns"""
        if 'syntax error' not in error_message.lower():
            return {}

        patterns = {
            "has_syntax_error": True,
            "error_message": error_message
        }

        # Common syntax error patterns
        if 'parameter without a default follows parameter with a default' in error_message:
            patterns['pattern'] = 'parameter_ordering'
            patterns['fix_strategy'] = 'reorder_parameters'
            patterns['description'] = 'Required parameters must come before optional parameters'

        elif 'expected' in error_message.lower() and 'block' in error_message.lower():
            patterns['pattern'] = 'missing_block'
            patterns['fix_strategy'] = 'add_missing_block'
            patterns['description'] = 'Missing try/except/finally block'

        elif 'invalid syntax' in error_message.lower():
            patterns['pattern'] = 'invalid_syntax'
            patterns['fix_strategy'] = 'fix_syntax'

            # Try to identify specific syntax issues
            if '(' in error_message or ')' in error_message:
                patterns['specific_issue'] = 'parenthesis_mismatch'
            elif '[' in error_message or ']' in error_message:
                patterns['specific_issue'] = 'bracket_mismatch'
            elif '{' in error_message or '}' in error_message:
                patterns['specific_issue'] = 'brace_mismatch'
            elif ':' in error_message:
                patterns['specific_issue'] = 'colon_issue'

        # Extract line number
        line_match = re.search(r'line (\d+)', error_message)
        if line_match:
            patterns['line_number'] = int(line_match.group(1))

        return patterns

    def _extract_import_errors(self, error_message: str, code: Optional[str]) -> Dict[str, Any]:
        """Extract import error patterns"""
        error_lower = error_message.lower()

        # Check for import-related errors
        is_import_error = (
            'import' in error_lower or
            'no module named' in error_lower or
            'cannot import' in error_lower or
            'modulenotfounderror' in error_lower
        )

        if not is_import_error:
            return {}

        patterns = {
            "has_import_error": True
        }

        # Extract module name
        module_match = re.search(r"No module named ['\"]?([^'\"]+)['\"]?", error_message, re.IGNORECASE)
        if module_match:
            patterns['missing_module'] = module_match.group(1).strip()
            patterns['fix_strategy'] = 'add_dependency_or_mock'

        # Check for import from issues
        import_from_match = re.search(r"cannot import name ['\"]([^'\"]+)['\"]", error_message, re.IGNORECASE)
        if import_from_match:
            patterns['missing_import'] = import_from_match.group(1)
            patterns['fix_strategy'] = 'check_import_path'

        return patterns

    def _extract_parameter_errors(self, error_message: str, code: Optional[str]) -> Dict[str, Any]:
        """Extract parameter-related error patterns"""
        if 'parameter' not in error_message.lower() and 'argument' not in error_message.lower():
            return {}

        patterns = {
            "has_parameter_error": True
        }

        # Parameter ordering error (our most common issue!)
        if 'parameter without a default follows parameter with a default' in error_message:
            patterns['pattern'] = 'parameter_ordering'
            patterns['fix_strategy'] = 'reorder_parameters'
            patterns['priority'] = 'high'
            patterns['auto_fixable'] = True

        # Missing required parameter
        elif 'required positional argument' in error_message.lower():
            param_match = re.search(r"'([^']+)'", error_message)
            if param_match:
                patterns['missing_parameter'] = param_match.group(1)
                patterns['fix_strategy'] = 'add_parameter'

        # Too many parameters
        elif 'too many' in error_message.lower() and 'argument' in error_message.lower():
            patterns['pattern'] = 'excess_parameters'
            patterns['fix_strategy'] = 'remove_excess_parameters'

        # Unexpected keyword argument
        elif 'unexpected keyword argument' in error_message.lower():
            param_match = re.search(r"'([^']+)'", error_message)
            if param_match:
                patterns['unexpected_parameter'] = param_match.group(1)
                patterns['fix_strategy'] = 'remove_or_rename_parameter'

        return patterns

    def _extract_validation_errors(self, error_message: str) -> Dict[str, Any]:
        """Extract validation error patterns"""
        if 'validation' not in error_message.lower():
            return {}

        patterns = {
            "has_validation_error": True,
            "error_message": error_message
        }

        # Validation errors usually indicate spec issues
        patterns['fix_strategy'] = 'review_spec'
        patterns['requires_spec_change'] = True

        return patterns

    def _extract_type_errors(self, error_message: str, code: Optional[str]) -> Dict[str, Any]:
        """Extract type-related error patterns"""
        if 'type' not in error_message.lower():
            return {}

        patterns = {
            "has_type_error": True
        }

        # Type hint errors
        if 'type hint' in error_message.lower():
            patterns['pattern'] = 'type_hint_error'
            patterns['fix_strategy'] = 'fix_type_hints'

        # Type mismatch
        elif 'expected' in error_message.lower() and 'got' in error_message.lower():
            patterns['pattern'] = 'type_mismatch'
            patterns['fix_strategy'] = 'convert_type'

        return patterns

    def _extract_indentation_errors(self, error_message: str, code: Optional[str]) -> Dict[str, Any]:
        """Extract indentation error patterns"""
        if 'indentation' not in error_message.lower() and 'indent' not in error_message.lower():
            return {}

        patterns = {
            "has_indentation_error": True,
            "fix_strategy": "fix_indentation",
            "auto_fixable": True,
            "priority": "high"
        }

        # Extract line number
        line_match = re.search(r'line (\d+)', error_message)
        if line_match:
            patterns['line_number'] = int(line_match.group(1))

        return patterns

    def _extract_name_errors(self, error_message: str, code: Optional[str]) -> Dict[str, Any]:
        """Extract name/undefined variable error patterns"""
        if 'name' not in error_message.lower() or 'not defined' not in error_message.lower():
            return {}

        patterns = {
            "has_name_error": True
        }

        # Extract undefined name
        name_match = re.search(r"name ['\"]([^'\"]+)['\"] is not defined", error_message)
        if name_match:
            patterns['undefined_name'] = name_match.group(1)
            patterns['fix_strategy'] = 'define_variable_or_import'

        return patterns

    def _extract_attribute_errors(self, error_message: str, code: Optional[str]) -> Dict[str, Any]:
        """Extract attribute error patterns"""
        if 'attribute' not in error_message.lower():
            return {}

        patterns = {
            "has_attribute_error": True
        }

        # Extract object and attribute
        attr_match = re.search(r"object has no attribute ['\"]([^'\"]+)['\"]", error_message)
        if attr_match:
            patterns['missing_attribute'] = attr_match.group(1)
            patterns['fix_strategy'] = 'check_object_type'

        return patterns

    def _extract_runtime_errors(self, error_message: str) -> Dict[str, Any]:
        """Extract runtime error patterns"""
        patterns = {}

        # Check for common runtime errors
        if 'division by zero' in error_message.lower():
            patterns['runtime_error'] = 'division_by_zero'
            patterns['fix_strategy'] = 'add_zero_check'

        elif 'key error' in error_message.lower():
            patterns['runtime_error'] = 'key_error'
            patterns['fix_strategy'] = 'check_key_exists'

        elif 'index error' in error_message.lower():
            patterns['runtime_error'] = 'index_error'
            patterns['fix_strategy'] = 'check_list_bounds'

        elif 'null' in error_message.lower() or 'none' in error_message.lower():
            patterns['runtime_error'] = 'null_reference'
            patterns['fix_strategy'] = 'add_null_check'

        return patterns

    def _extract_logic_errors(self, error_message: str, code: Optional[str]) -> Dict[str, Any]:
        """Extract logic error patterns"""
        patterns = {}

        # Logic errors are harder to detect from just error messages
        # These usually come from validation or runtime issues

        if code:
            # Check for common logic issues
            if 'return' not in code:
                patterns['missing_return'] = True
                patterns['fix_strategy'] = 'add_return_statement'

        return patterns

    def _extract_error_context(
        self,
        error_message: str,
        code: Optional[str],
        spec: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Extract contextual information about the error"""
        context = {
            "component_name": spec.get('name', 'unknown'),
            "component_type": spec.get('component_type', 'unknown'),
            "category": spec.get('category', 'unknown'),
            "num_inputs": len(spec.get('inputs', [])),
            "num_runtime_params": len(spec.get('runtime_params', [])),
            "has_dependencies": bool(spec.get('dependencies', [])),
            "code_length": len(code) if code else 0
        }

        # Check if error is related to specific libraries
        if code:
            for dep in spec.get('dependencies', []):
                dep_name = dep.split('>=')[0].split('[')[0].strip()
                if dep_name in error_message or dep_name in code:
                    context['related_dependency'] = dep_name
                    break

        return context

    def calculate_error_severity(self, patterns: Dict[str, Any]) -> str:
        """Calculate overall error severity based on extracted patterns"""
        classification = patterns.get('error_classification', {})
        severity = classification.get('severity', 'medium')

        # Adjust based on recoverability
        if not classification.get('is_recoverable', True):
            if severity == 'medium':
                severity = 'high'
            elif severity == 'low':
                severity = 'medium'

        return severity

    def suggest_fix_strategy(self, patterns: Dict[str, Any]) -> str:
        """Suggest the best fix strategy based on extracted patterns"""
        # Priority order: syntax > parameter > import > others

        if patterns.get('syntax_errors', {}).get('fix_strategy'):
            return patterns['syntax_errors']['fix_strategy']

        if patterns.get('parameter_errors', {}).get('fix_strategy'):
            return patterns['parameter_errors']['fix_strategy']

        if patterns.get('import_errors', {}).get('fix_strategy'):
            return patterns['import_errors']['fix_strategy']

        if patterns.get('indentation_errors', {}).get('fix_strategy'):
            return patterns['indentation_errors']['fix_strategy']

        if patterns.get('name_errors', {}).get('fix_strategy'):
            return patterns['name_errors']['fix_strategy']

        # Default: generic retry with more detailed prompt
        return 'retry_with_detailed_prompt'
