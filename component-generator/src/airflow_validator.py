"""
Validator for generated Airflow component code (operators, sensors, hooks)
"""

import ast
import re
from typing import List, Set, Tuple
import structlog

from src.base_classes import ValidationResult

logger = structlog.get_logger()


class AirflowComponentValidator:
    """Validates generated Airflow component code for correctness and security"""

    # Required base classes by component type
    VALID_BASE_CLASSES = {
        'operator': ['BaseOperator'],
        'sensor': ['BaseSensor'],
        'hook': ['BaseHook'],
    }

    # Valid import paths for base classes (Airflow 2.x and 3.x compatible)
    VALID_BASE_IMPORTS = {
        'BaseOperator': [
            'airflow.models',
            'airflow.models.baseoperator',
            'airflow.sdk.bases.operator',  # Airflow 3.x Task SDK
        ],
        'BaseSensor': [
            'airflow.sensors.base',
            'airflow.models',
            'airflow.sdk.bases.sensor',  # Airflow 3.x Task SDK
        ],
        'BaseHook': [
            'airflow.hooks.base',
            'airflow.models',
            'airflow.sdk.bases.hook',  # Airflow 3.x Task SDK
        ],
    }

    # Required methods by component type
    REQUIRED_METHODS = {
        'operator': ['execute'],
        'sensor': ['poke'],
        'hook': ['get_conn'],
    }

    # Recommended attributes
    RECOMMENDED_ATTRIBUTES = {
        'operator': ['template_fields', 'ui_color'],
        'sensor': ['template_fields', 'ui_color', 'poke_interval'],
        'hook': ['conn_name_attr', 'conn_type', 'hook_name'],
    }

    # Dangerous functions that should not be used
    DANGEROUS_FUNCTIONS = {
        'eval', 'exec', 'compile', '__import__',
        'os.system', 'subprocess.call'
    }

    def __init__(self):
        self.logger = logger.bind(component="airflow_validator")

    def validate(self, code: str, component_type: str = "operator") -> ValidationResult:
        """
        Validate generated Airflow component code

        Args:
            code: Generated Python code to validate
            component_type: Type of component (operator, sensor, hook)

        Returns:
            ValidationResult with detailed validation information
        """
        errors = []
        warnings = []
        security_issues = []

        # Result flags
        has_execute_method = False
        has_poke_method = False
        has_get_conn_method = False
        imports_valid = True
        inherits_correctly = False

        try:
            # 1. Check Python syntax
            syntax_errors = self._check_syntax(code)
            if syntax_errors:
                return ValidationResult(
                    valid=False,
                    errors=syntax_errors,
                    warnings=warnings,
                    security_issues=security_issues,
                    has_execute_method=False,
                    has_poke_method=False,
                    has_get_conn_method=False,
                    imports_valid=False,
                    inherits_correctly=False
                )

            # 2. Parse AST for structural validation
            tree = ast.parse(code)

            # 3. Check imports
            import_errors, import_warnings = self._check_imports(tree, component_type)
            errors.extend(import_errors)
            warnings.extend(import_warnings)
            if import_errors:
                imports_valid = False

            # 4. Check class structure
            class_info = self._check_class_structure(tree, code, component_type)
            errors.extend(class_info['errors'])
            warnings.extend(class_info['warnings'])
            inherits_correctly = class_info['inherits_correctly']
            has_execute_method = class_info['has_execute']
            has_poke_method = class_info['has_poke']
            has_get_conn_method = class_info['has_get_conn']

            # 5. Check security issues
            sec_errors, sec_warnings = self._check_security(tree, code)
            security_issues.extend(sec_errors)
            warnings.extend(sec_warnings)

            # 6. Check Airflow-specific compliance
            airflow_errors, airflow_warnings = self._check_airflow_compliance(
                tree, code, component_type
            )
            errors.extend(airflow_errors)
            warnings.extend(airflow_warnings)

            # 7. Run static analysis (mypy, ruff) - optional, non-blocking
            static_warnings = self._run_static_analysis(code)
            warnings.extend(static_warnings)

            is_valid = len(errors) == 0 and len(security_issues) == 0

            self.logger.info(
                "Validation complete",
                component_type=component_type,
                is_valid=is_valid,
                errors_count=len(errors),
                warnings_count=len(warnings),
                security_issues_count=len(security_issues)
            )

            return ValidationResult(
                valid=is_valid,
                errors=errors,
                warnings=warnings,
                security_issues=security_issues,
                has_execute_method=has_execute_method,
                has_poke_method=has_poke_method,
                has_get_conn_method=has_get_conn_method,
                imports_valid=imports_valid,
                inherits_correctly=inherits_correctly
            )

        except Exception as e:
            self.logger.error("Validation failed", error=str(e))
            return ValidationResult(
                valid=False,
                errors=[f"Validation error: {str(e)}"],
                warnings=warnings,
                security_issues=security_issues,
                has_execute_method=False,
                has_poke_method=False,
                has_get_conn_method=False,
                imports_valid=False,
                inherits_correctly=False
            )

    def _check_syntax(self, code: str) -> List[str]:
        """Check Python syntax"""
        errors = []
        try:
            ast.parse(code)
        except SyntaxError as e:
            errors.append(f"Syntax error at line {e.lineno}: {e.msg}")
        return errors

    def _check_imports(
        self,
        tree: ast.AST,
        component_type: str
    ) -> Tuple[List[str], List[str]]:
        """Check imports for required and forbidden modules"""
        errors = []
        warnings = []

        imports = set()
        has_base_import = False

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.add(alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.add(node.module)
                    # Check for base class imports
                    for alias in node.names:
                        if alias.name in ['BaseOperator', 'BaseSensor', 'BaseHook']:
                            has_base_import = True

        # Check for required base class import
        if not has_base_import:
            base_class = self.VALID_BASE_CLASSES.get(component_type, ['BaseOperator'])[0]
            valid_paths = self.VALID_BASE_IMPORTS.get(base_class, [])
            paths_str = " or ".join(valid_paths)
            warnings.append(f"Missing import for {base_class}. Should import from: {paths_str}")

        return errors, warnings

    def _check_class_structure(
        self,
        tree: ast.AST,
        code: str,
        component_type: str
    ) -> dict:
        """Check class structure for Airflow compliance"""
        errors = []
        warnings = []
        inherits_correctly = False
        has_execute = False
        has_poke = False
        has_get_conn = False

        # Find class definitions
        classes = [node for node in ast.walk(tree) if isinstance(node, ast.ClassDef)]

        if not classes:
            errors.append("No class definition found")
            return {
                'errors': errors,
                'warnings': warnings,
                'inherits_correctly': False,
                'has_execute': False,
                'has_poke': False,
                'has_get_conn': False
            }

        # Check the main class (assume first class is the component)
        main_class = classes[0]

        # Check inheritance
        valid_bases = self.VALID_BASE_CLASSES.get(component_type, ['BaseOperator'])
        for base in main_class.bases:
            base_name = None
            if isinstance(base, ast.Name):
                base_name = base.id
            elif isinstance(base, ast.Attribute):
                base_name = base.attr

            if base_name in valid_bases:
                inherits_correctly = True
                break

        if not inherits_correctly:
            errors.append(
                f"Class must inherit from {' or '.join(valid_bases)}. "
                f"Found bases: {[self._get_base_name(b) for b in main_class.bases]}"
            )

        # Check for required methods
        methods = {node.name for node in main_class.body if isinstance(node, ast.FunctionDef)}

        required_methods = self.REQUIRED_METHODS.get(component_type, ['execute'])
        for required_method in required_methods:
            if required_method in methods:
                if required_method == 'execute':
                    has_execute = True
                elif required_method == 'poke':
                    has_poke = True
                elif required_method == 'get_conn':
                    has_get_conn = True
            else:
                errors.append(f"Missing required method: {required_method}(self, context)")

        # Check method signatures
        for node in main_class.body:
            if isinstance(node, ast.FunctionDef):
                if node.name in required_methods:
                    # Check that method has correct signature (self, context for execute/poke)
                    if node.name in ['execute', 'poke']:
                        if len(node.args.args) < 2:
                            errors.append(
                                f"Method {node.name}() must have signature: "
                                f"{node.name}(self, context)"
                            )

        # Check for recommended attributes
        recommended_attrs = self.RECOMMENDED_ATTRIBUTES.get(component_type, [])
        class_attrs = set()

        for node in main_class.body:
            if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
                class_attrs.add(node.target.id)
            elif isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        class_attrs.add(target.id)

        for attr in recommended_attrs:
            if attr not in class_attrs:
                warnings.append(f"Recommended attribute '{attr}' not found")

        return {
            'errors': errors,
            'warnings': warnings,
            'inherits_correctly': inherits_correctly,
            'has_execute': has_execute,
            'has_poke': has_poke,
            'has_get_conn': has_get_conn
        }

    def _get_base_name(self, base: ast.expr) -> str:
        """Extract base class name from AST node"""
        if isinstance(base, ast.Name):
            return base.id
        elif isinstance(base, ast.Attribute):
            return base.attr
        return str(base)

    def _check_security(self, tree: ast.AST, code: str) -> Tuple[List[str], List[str]]:
        """Check for security issues"""
        errors = []
        warnings = []

        # Check for dangerous function calls
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                func_name = None
                if isinstance(node.func, ast.Name):
                    func_name = node.func.id
                elif isinstance(node.func, ast.Attribute):
                    func_name = node.func.attr

                if func_name in self.DANGEROUS_FUNCTIONS:
                    errors.append(
                        f"Dangerous function call detected: {func_name}(). "
                        f"This is a security risk and must be removed."
                    )

        # Check for shell=True in subprocess
        if 'subprocess' in code and 'shell=True' in code:
            warnings.append(
                "subprocess with shell=True detected. This can be a security risk. "
                "Consider using shell=False with a list of arguments."
            )

        # Check for hardcoded secrets/credentials
        secret_errors = self._scan_for_secrets(code)
        if secret_errors:
            errors.extend(secret_errors)

        return errors, warnings

    def _scan_for_secrets(self, code: str) -> List[str]:
        """
        Scan code for potential hardcoded secrets and credentials

        Returns list of error messages if secrets detected
        """
        errors = []

        # Patterns for common secrets
        secret_patterns = [
            (r'api_key\s*=\s*["\'](?!{{)[A-Za-z0-9_\-]{20,}["\']', 'API key'),
            (r'apikey\s*=\s*["\'](?!{{)[A-Za-z0-9_\-]{20,}["\']', 'API key'),
            (r'api[-_]?secret\s*=\s*["\'](?!{{)[A-Za-z0-9_\-]{20,}["\']', 'API secret'),
            (r'password\s*=\s*["\'](?!{{)(?!password)(?!changeme)[A-Za-z0-9!@#$%^&*]{8,}["\']', 'Password'),
            (r'passwd\s*=\s*["\'](?!{{)[A-Za-z0-9!@#$%^&*]{8,}["\']', 'Password'),
            (r'secret\s*=\s*["\'](?!{{)[A-Za-z0-9_\-]{20,}["\']', 'Secret'),
            (r'token\s*=\s*["\'](?!{{)[A-Za-z0-9_\-\.]{20,}["\']', 'Token'),
            (r'bearer\s+[A-Za-z0-9_\-\.]{20,}', 'Bearer token'),
            (r'sk-[A-Za-z0-9]{20,}', 'OpenAI/Anthropic API key'),
            (r'AKIA[0-9A-Z]{16}', 'AWS Access Key'),
            (r'["\']?aws_secret_access_key["\']?\s*[:=]\s*["\'][A-Za-z0-9/+=]{40}["\']', 'AWS Secret Key'),
            (r'-----BEGIN\s+(?:RSA\s+)?PRIVATE\s+KEY-----', 'Private key'),
            (r'mysql://[^:]+:[^@]+@', 'MySQL connection string with credentials'),
            (r'postgres://[^:]+:[^@]+@', 'PostgreSQL connection string with credentials'),
            (r'mongodb://[^:]+:[^@]+@', 'MongoDB connection string with credentials'),
        ]

        for pattern, secret_type in secret_patterns:
            matches = re.findall(pattern, code, re.IGNORECASE)
            if matches:
                errors.append(
                    f"Potential hardcoded {secret_type} detected. "
                    f"NEVER hardcode credentials in code. "
                    f"Use Airflow Connections, Variables, or environment variables instead."
                )
                break  # Only report once per code block

        return errors

    def _check_airflow_compliance(
        self,
        tree: ast.AST,
        code: str,
        component_type: str
    ) -> Tuple[List[str], List[str]]:
        """Check Airflow-specific compliance rules"""
        errors = []
        warnings = []

        # Check for proper context usage in execute/poke
        if component_type in ['operator', 'sensor']:
            # Ensure context is used properly
            if 'context[' in code and 'context.get(' not in code:
                warnings.append(
                    "Using context[] directly can raise KeyError. "
                    "Consider using context.get() for safer access."
                )

        # Check for template_fields as Sequence
        if 'template_fields' in code:
            if 'Sequence[str]' not in code and 'List[str]' not in code:
                warnings.append(
                    "template_fields should be annotated as Sequence[str] or List[str]"
                )

            # Check if template fields handle Jinja templates properly
            # Template fields should skip validation for Jinja templates in __init__
            if 'template_fields' in code and '__init__' in code:
                # Check if there's validation logic that doesn't account for templates
                if ('raise AirflowException' in code and
                    '{{' not in code and  # No Jinja template check
                    'execute' in code):  # But has execute method
                    warnings.append(
                        "Template fields may need Jinja template handling. "
                        "Consider skipping validation for '{{' strings in __init__ "
                        "and validating actual values in execute() method."
                    )

        # Check for proper type hints
        classes = [node for node in ast.walk(tree) if isinstance(node, ast.ClassDef)]
        if classes:
            main_class = classes[0]
            for node in main_class.body:
                if isinstance(node, ast.FunctionDef):
                    if node.name in ['execute', 'poke'] and not node.returns:
                        warnings.append(
                            f"Method {node.name}() should have return type annotation"
                        )

        return errors, warnings

    def _run_static_analysis(self, code: str) -> List[str]:
        """
        Run optional static analysis tools (mypy, ruff) on generated code.
        Returns warnings only - does not block validation.

        Args:
            code: Generated Python code

        Returns:
            List of warning messages from static analysis
        """
        warnings = []

        # Run mypy type checking (optional)
        mypy_warnings = self._validate_with_mypy(code)
        warnings.extend(mypy_warnings)

        # Run ruff linting (optional)
        ruff_warnings = self._validate_with_ruff(code)
        warnings.extend(ruff_warnings)

        return warnings

    def _validate_with_mypy(self, code: str) -> List[str]:
        """
        Run mypy type checking on generated code (optional, non-blocking).

        Args:
            code: Generated Python code

        Returns:
            List of type-checking warnings
        """
        warnings = []

        try:
            import subprocess
            import tempfile
            import os

            # Check if mypy is available
            try:
                subprocess.run(
                    ['mypy', '--version'],
                    capture_output=True,
                    timeout=5,
                    check=True
                )
            except (subprocess.CalledProcessError, FileNotFoundError):
                # mypy not installed, skip silently
                return warnings

            # Write code to temporary file
            with tempfile.NamedTemporaryFile(
                mode='w',
                suffix='.py',
                delete=False,
                encoding='utf-8'
            ) as f:
                f.write(code)
                temp_file = f.name

            try:
                # Run mypy with strict settings
                result = subprocess.run(
                    [
                        'mypy',
                        '--strict',
                        '--no-error-summary',
                        '--no-color-output',
                        temp_file
                    ],
                    capture_output=True,
                    text=True,
                    timeout=10
                )

                # Parse mypy output
                if result.returncode != 0 and result.stdout:
                    lines = result.stdout.strip().split('\n')
                    # Limit to first 5 type issues to avoid overwhelming output
                    for line in lines[:5]:
                        if line and ':' in line:
                            # Extract just the error message, not the file path
                            parts = line.split(':', 2)
                            if len(parts) >= 3:
                                warnings.append(f"Type hint: {parts[2].strip()}")

                    if len(lines) > 5:
                        warnings.append(f"Type hint: ... and {len(lines) - 5} more type issues")

            finally:
                # Clean up temp file
                try:
                    os.unlink(temp_file)
                except:
                    pass

        except subprocess.TimeoutExpired:
            warnings.append("Static analysis: mypy timeout (skipped)")
        except Exception as e:
            # Don't fail validation if static analysis has issues
            self.logger.debug("Mypy validation skipped", error=str(e))

        return warnings

    def _validate_with_ruff(self, code: str) -> List[str]:
        """
        Run ruff linter on generated code (optional, non-blocking).

        Args:
            code: Generated Python code

        Returns:
            List of linting warnings
        """
        warnings = []

        try:
            import subprocess
            import tempfile
            import os

            # Check if ruff is available
            try:
                subprocess.run(
                    ['ruff', '--version'],
                    capture_output=True,
                    timeout=5,
                    check=True
                )
            except (subprocess.CalledProcessError, FileNotFoundError):
                # ruff not installed, skip silently
                return warnings

            # Write code to temporary file
            with tempfile.NamedTemporaryFile(
                mode='w',
                suffix='.py',
                delete=False,
                encoding='utf-8'
            ) as f:
                f.write(code)
                temp_file = f.name

            try:
                # Run ruff check
                result = subprocess.run(
                    [
                        'ruff',
                        'check',
                        '--output-format=concise',
                        temp_file
                    ],
                    capture_output=True,
                    text=True,
                    timeout=10
                )

                # Parse ruff output
                if result.returncode != 0 and result.stdout:
                    lines = result.stdout.strip().split('\n')
                    # Limit to first 5 linting issues
                    for line in lines[:5]:
                        if line and ':' in line:
                            # Extract rule and message
                            parts = line.split(':', 2)
                            if len(parts) >= 3:
                                warnings.append(f"Code style: {parts[2].strip()}")

                    if len(lines) > 5:
                        warnings.append(f"Code style: ... and {len(lines) - 5} more style issues")

            finally:
                # Clean up temp file
                try:
                    os.unlink(temp_file)
                except:
                    pass

        except subprocess.TimeoutExpired:
            warnings.append("Static analysis: ruff timeout (skipped)")
        except Exception as e:
            # Don't fail validation if static analysis has issues
            self.logger.debug("Ruff validation skipped", error=str(e))

        return warnings


class FeasibilityChecker:
    """Check if a component spec is feasible to generate"""

    def __init__(self):
        self.logger = logger.bind(component="feasibility_checker")

    def assess_feasibility(
        self,
        spec_dict: dict,
        similar_patterns_count: int = 0
    ) -> dict:
        """
        Assess if component generation is feasible

        Args:
            spec_dict: Component specification dictionary
            similar_patterns_count: Number of similar patterns found in RAG

        Returns:
            Dictionary with feasibility assessment
        """
        issues = []
        suggestions = []
        missing_info = []

        # Check required fields
        if not spec_dict.get('name'):
            issues.append("Missing required field: name")
        if not spec_dict.get('description'):
            missing_info.append("description")
        if not spec_dict.get('category'):
            missing_info.append("category")

        # Check complexity
        complexity = "simple"
        if len(spec_dict.get('requirements', [])) > 5:
            complexity = "medium"
        if len(spec_dict.get('requirements', [])) > 10:
            complexity = "complex"

        # Check for unsupported dependencies
        dependencies = spec_dict.get('dependencies', [])
        for dep in dependencies:
            if 'airflow' not in dep.lower() and not dep.startswith('apache-airflow'):
                suggestions.append(
                    f"External dependency '{dep}' may require manual installation"
                )

        # Determine confidence
        confidence = "high"
        if issues:
            confidence = "blocked"
        elif missing_info:
            confidence = "medium"
        elif similar_patterns_count == 0:
            confidence = "low"
            suggestions.append("No similar patterns found. Generation may be less accurate.")

        feasible = len(issues) == 0

        return {
            "feasible": feasible,
            "confidence": confidence,
            "complexity": complexity,
            "issues": issues,
            "suggestions": suggestions,
            "missing_info": missing_info,
            "similar_patterns_found": similar_patterns_count
        }

