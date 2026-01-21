"""
Pattern Extractor - Automatically extract reusable patterns from generated code

This module analyzes successful component generations and extracts patterns
that can be reused in future generations.
"""

import re
import ast
from typing import Dict, List, Any
from datetime import datetime


class PatternExtractor:
    """Automatically extract patterns from generated code"""

    def __init__(self):
        self.logger = self._setup_logger()

    def _setup_logger(self):
        import structlog
        return structlog.get_logger(__name__)

    def extract_patterns(self, code: str, spec: Dict, metadata: Dict) -> Dict[str, Any]:
        """
        Extract all learnable patterns from successful generation

        Args:
            code: Generated component code
            spec: Component specification
            metadata: Generation metadata (cost, time, etc.)

        Returns:
            Dictionary of extracted patterns
        """
        self.logger.info("Extracting patterns from successful generation",
                        component_name=spec.get("name"))

        patterns = {
            "structural": self._extract_structural_patterns(code),
            "import": self._extract_import_patterns(code),
            "initialization": self._extract_init_patterns(code),
            "execution": self._extract_execution_patterns(code),
            "error_handling": self._extract_error_handling_patterns(code),
            "template_fields": self._extract_template_patterns(code),
            "parameter_ordering": self._extract_parameter_ordering(code),
            "mock_execution": self._extract_mock_patterns(code),
            "logging": self._extract_logging_patterns(code),
            "validation": self._extract_validation_patterns(code),
            "runtime_params": self._extract_runtime_param_patterns(code),
        }

        # Store metadata
        patterns["metadata"] = {
            "category": spec.get("category"),
            "subcategory": spec.get("subcategory"),
            "component_type": spec.get("component_type"),
            "complexity": metadata.get("complexity_score"),
            "success_score": metadata.get("success_score"),
            "libraries_used": self._extract_libraries(code),
            "inputs_count": len(spec.get("inputs", [])),
            "runtime_params_count": len(spec.get("runtime_params", [])),
            "extracted_at": datetime.now().isoformat()
        }

        self.logger.info("Pattern extraction complete",
                        patterns_extracted=len([p for p in patterns.values() if p]),
                        component_name=spec.get("name"))

        return patterns

    def _extract_structural_patterns(self, code: str) -> Dict[str, str]:
        """Extract class structure patterns"""
        patterns = {}

        # Extract class definition
        class_match = re.search(r"class\s+(\w+)\(([^)]+)\):", code)
        if class_match:
            patterns["class_name"] = class_match.group(1)
            patterns["base_class"] = class_match.group(2)
            patterns["class_definition"] = class_match.group(0)

        # Extract template_fields
        template_match = re.search(r"template_fields:\s*Sequence\[str\]\s*=\s*\[([^\]]+)\]", code)
        if template_match:
            patterns["template_fields_declaration"] = template_match.group(0)

        # Extract ui_color
        color_match = re.search(r"ui_color:\s*str\s*=\s*['\"]([^'\"]+)['\"]", code)
        if color_match:
            patterns["ui_color"] = color_match.group(1)

        return patterns

    def _extract_import_patterns(self, code: str) -> Dict[str, Any]:
        """Extract import patterns with fallbacks"""
        imports = {
            "dual_imports": [],
            "standard_imports": [],
            "conditional_imports": [],
            "all_imports": []
        }

        # Find try/except import patterns (dual imports for Airflow 2.x/3.x)
        dual_pattern = r"try:\s+from ([^\n]+)\nexcept ImportError:\s+from ([^\n]+)"
        for match in re.finditer(dual_pattern, code):
            imports["dual_imports"].append({
                "primary": match.group(1).strip(),
                "fallback": match.group(2).strip(),
                "pattern": "try_except_import"
            })

        # Find all import statements
        import_lines = [line.strip() for line in code.split('\n')
                       if line.strip().startswith(('import ', 'from '))]
        imports["all_imports"] = import_lines[:20]  # Limit to first 20

        # Categorize imports
        for imp in import_lines:
            if 'airflow' in imp:
                imports["standard_imports"].append(imp)

        return imports

    def _extract_init_patterns(self, code: str) -> Dict[str, Any]:
        """Extract __init__ method patterns"""
        patterns = {}

        # Find __init__ method
        init_match = re.search(
            r"def __init__\(self,(.*?)\)\s*->\s*None:",
            code,
            re.DOTALL
        )

        if init_match:
            params_str = init_match.group(1)
            patterns["full_signature"] = init_match.group(0)

            # Parse parameters
            params = [p.strip() for p in params_str.split(',') if p.strip()]
            patterns["parameters"] = params
            patterns["parameter_count"] = len(params)

            # Find super().__init__ call
            super_match = re.search(r"super\(\).__init__\([^)]*\)", code)
            if super_match:
                patterns["super_call"] = super_match.group(0)

        return patterns

    def _extract_execution_patterns(self, code: str) -> Dict[str, Any]:
        """Extract execute method patterns"""
        patterns = {}

        # Find execute method
        exec_match = re.search(
            r"def execute\(self,\s*context[^)]*\)([^:]*):(.{0,2000})",
            code,
            re.DOTALL
        )

        if exec_match:
            patterns["signature"] = exec_match.group(0)[:200]  # First 200 chars

            # Check for mode-based execution
            if re.search(r"if\s+self\.mode\s*==", code):
                patterns["has_mode_switching"] = True

                # Extract mode handlers
                modes = re.findall(r"if\s+self\.mode\s*==\s*['\"](\w+)['\"]", code)
                patterns["supported_modes"] = list(set(modes))

            # Check for return statement
            if re.search(r"return\s+", code):
                patterns["has_return"] = True

        return patterns

    def _extract_error_handling_patterns(self, code: str) -> Dict[str, Any]:
        """Extract error handling patterns"""
        patterns = {
            "has_try_except": False,
            "exception_types": [],
            "uses_airflow_exception": False,
            "validation_checks": []
        }

        # Check for try/except blocks
        if re.search(r"try:", code):
            patterns["has_try_except"] = True

            # Extract exception types
            exceptions = re.findall(r"except\s+(\w+)", code)
            patterns["exception_types"] = list(set(exceptions))

        # Check for AirflowException
        if "AirflowException" in code:
            patterns["uses_airflow_exception"] = True

        # Find validation checks
        validations = re.findall(
            r"if\s+not\s+self\.(\w+):|if\s+self\.(\w+)\s*is\s*None:",
            code
        )
        if validations:
            patterns["validation_checks"] = [v[0] or v[1] for v in validations]

        return patterns

    def _extract_template_patterns(self, code: str) -> Dict[str, Any]:
        """Extract template field patterns"""
        patterns = {}

        # Find template_fields declaration
        template_match = re.search(
            r"template_fields:\s*Sequence\[str\]\s*=\s*\[([^\]]+)\]",
            code
        )

        if template_match:
            # Extract field names
            fields_str = template_match.group(1)
            fields = [f.strip().strip("'\"") for f in fields_str.split(',')]
            patterns["template_fields"] = fields
            patterns["template_field_count"] = len(fields)

        # Check for Jinja template usage
        if "{{" in code or "{%" in code:
            patterns["uses_jinja_templates"] = True

        return patterns

    def _extract_parameter_ordering(self, code: str) -> Dict[str, Any]:
        """Extract parameter ordering strategy"""
        patterns = {
            "ordering_strategy": "unknown",
            "required_first": False,
            "optional_last": False
        }

        init_match = re.search(r"def __init__\(self,(.*?)\)\s*->", code, re.DOTALL)
        if not init_match:
            return patterns

        params_str = init_match.group(1)
        params = [p.strip() for p in params_str.split(',') if p.strip() and p.strip() != '**kwargs']

        required_params = []
        optional_params = []

        for param in params:
            if '=' in param:
                optional_params.append(param)
            else:
                required_params.append(param)

        # Check ordering
        if required_params and optional_params:
            # Find positions
            last_required_idx = -1
            first_optional_idx = len(params)

            for i, param in enumerate(params):
                if '=' not in param and param != '**kwargs':
                    last_required_idx = i
                elif '=' in param and first_optional_idx == len(params):
                    first_optional_idx = i

            if last_required_idx < first_optional_idx:
                patterns["ordering_strategy"] = "correct"
                patterns["required_first"] = True
                patterns["optional_last"] = True
            else:
                patterns["ordering_strategy"] = "incorrect"

        patterns["required_params"] = required_params
        patterns["optional_params"] = optional_params

        return patterns

    def _extract_mock_patterns(self, code: str) -> Dict[str, Any]:
        """Extract mock execution patterns"""
        patterns = {
            "has_mock_mode": False,
            "has_dependency_check": False,
            "mock_method_name": None
        }

        # Check for mock execution
        if "_mock_execute" in code or "_mock_" in code.lower():
            patterns["has_mock_mode"] = True

            # Find mock method
            mock_method = re.search(r"def (_mock_\w+)\(", code)
            if mock_method:
                patterns["mock_method_name"] = mock_method.group(1)

        # Check for dependency availability check (HAS_XXX pattern)
        has_check = re.search(r"(HAS_\w+)\s*=\s*(True|False)", code)
        if has_check:
            patterns["has_dependency_check"] = True
            patterns["dependency_check_variable"] = has_check.group(1)

        # Check for conditional execution based on dependency
        if re.search(r"if\s+not\s+HAS_\w+:", code):
            patterns["uses_conditional_execution"] = True

        return patterns

    def _extract_logging_patterns(self, code: str) -> Dict[str, Any]:
        """Extract logging patterns"""
        patterns = {
            "uses_logging": False,
            "log_levels": [],
            "log_count": 0
        }

        # Find logging statements
        log_statements = re.findall(r"self\.log\.(info|warning|error|debug)\(", code)

        if log_statements:
            patterns["uses_logging"] = True
            patterns["log_levels"] = list(set(log_statements))
            patterns["log_count"] = len(log_statements)

        return patterns

    def _extract_validation_patterns(self, code: str) -> Dict[str, Any]:
        """Extract validation patterns"""
        patterns = {
            "has_input_validation": False,
            "validated_fields": [],
            "validation_style": None
        }

        # Check for validation
        if re.search(r"if\s+not\s+", code) or re.search(r"if.*is\s+None", code):
            patterns["has_input_validation"] = True

            # Find validated fields
            validations = re.findall(
                r"if\s+not\s+self\.(\w+)|if\s+self\.(\w+)\s+is\s+None",
                code
            )
            patterns["validated_fields"] = list(set([v[0] or v[1] for v in validations]))

        # Check for raising exceptions on validation failure
        if "raise AirflowException" in code:
            patterns["validation_style"] = "exception"
        elif "self.log.error" in code or "self.log.warning" in code:
            patterns["validation_style"] = "logging"

        return patterns

    def _extract_runtime_param_patterns(self, code: str) -> Dict[str, Any]:
        """Extract runtime parameter patterns"""
        patterns = {
            "uses_runtime_params": False,
            "param_count": 0,
            "param_types": []
        }

        # Check if code mentions Param
        if "Param(" in code:
            patterns["uses_runtime_params"] = True

            # Find Param declarations
            param_matches = re.findall(
                r"Param\([^)]*type\s*=\s*['\"](\w+)['\"]",
                code
            )
            patterns["param_types"] = list(set(param_matches))
            patterns["param_count"] = len(param_matches)

        return patterns

    def _extract_libraries(self, code: str) -> List[str]:
        """Extract all libraries used in code"""
        libraries = set()

        # Find all imports
        import_pattern = r"(?:from|import)\s+([\w\.]+)"
        for match in re.finditer(import_pattern, code):
            lib = match.group(1).split('.')[0]
            # Exclude standard library and airflow
            if lib not in ['airflow', 'typing', 'datetime', 'os', 'sys', 're', 'json']:
                libraries.add(lib)

        return list(libraries)

    def calculate_pattern_signature(self, patterns: Dict) -> str:
        """Calculate a signature hash for the pattern set"""
        import hashlib
        import json

        # Create a stable string representation
        signature_data = {
            "category": patterns["metadata"].get("category"),
            "component_type": patterns["metadata"].get("component_type"),
            "has_mock": patterns.get("mock_execution", {}).get("has_mock_mode", False),
            "has_runtime_params": patterns.get("runtime_params", {}).get("uses_runtime_params", False),
            "parameter_ordering": patterns.get("parameter_ordering", {}).get("ordering_strategy"),
        }

        # Create hash
        sig_str = json.dumps(signature_data, sort_keys=True)
        return hashlib.md5(sig_str.encode()).hexdigest()
