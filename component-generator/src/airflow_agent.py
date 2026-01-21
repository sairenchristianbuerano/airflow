"""
Airflow Component Generator using Claude AI

Generates Airflow operators, sensors, and hooks from YAML specifications.
"""

import os
import json
import yaml
import time
import httpx
from typing import Optional, Dict, Any, List
import structlog
from anthropic import Anthropic

from src.base_classes import (
    OperatorSpec,
    SensorSpec,
    HookSpec,
    GeneratedComponent,
    ValidationResult,
    BaseCodeGenerator
)
from src.airflow_validator import AirflowComponentValidator
from src.dependency_validator import DependencyValidator, get_validation_summary
from src.test_generator import TestFileGenerator
from src.documentation_generator import DocumentationGenerator
from src.error_tracker import ErrorTracker
from src.learning_database import LearningDatabase
from src.pattern_storage import PatternStorage
from src.pattern_extractor import PatternExtractor
from src.error_learning import ErrorPatternExtractor
from src.error_storage import ErrorPatternStorage
from src.fix_strategies import FixStrategyManager
from src.library_tracker import LibraryTracker
from src.library_recommender import LibraryRecommender
from src.native_fallback_generator import NativeFallbackGenerator

logger = structlog.get_logger()


class AirflowComponentGenerator(BaseCodeGenerator):
    """Generates Airflow component code using Claude AI"""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "claude-sonnet-4-20250514",
        rag_service_url: Optional[str] = None,
        max_retries: int = 4
    ):
        """
        Initialize the generator

        Args:
            api_key: Anthropic API key (defaults to ANTHROPIC_API_KEY env var)
            model: Claude model to use
            rag_service_url: URL of RAG service for pattern matching (optional)
            max_retries: Maximum number of retry attempts with fixes
        """
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("Anthropic API key is required (set ANTHROPIC_API_KEY env var)")

        self.model = model
        self.rag_service_url = rag_service_url or os.getenv("RAG_SERVICE_URL")
        self.max_retries = max_retries

        self.client = Anthropic(api_key=self.api_key)
        self.validator = AirflowComponentValidator()
        self.dependency_validator = DependencyValidator()
        self.test_generator = TestFileGenerator()
        self.doc_generator = DocumentationGenerator()
        self.error_tracker = ErrorTracker()
        self.learning_db = LearningDatabase()

        # Phase 1: Pattern learning system
        patterns_db_path = os.path.join(os.path.dirname(__file__), "..", "data", "patterns.db")
        self.pattern_storage = PatternStorage(patterns_db_path)
        self.pattern_extractor = PatternExtractor()

        # Phase 2: Error learning system
        error_db_path = os.path.join(os.path.dirname(__file__), "..", "data", "error_patterns.db")
        self.error_storage = ErrorPatternStorage(error_db_path)
        self.error_extractor = ErrorPatternExtractor()
        self.fix_strategy_manager = FixStrategyManager()

        # Phase 3: Library compatibility tracking
        library_db_path = os.path.join(os.path.dirname(__file__), "..", "data", "library_compatibility.db")
        self.library_tracker = LibraryTracker(library_db_path)
        self.library_recommender = LibraryRecommender(self.library_tracker)

        # Phase 4: Native Python fallback generation
        fallback_db_path = os.path.join(os.path.dirname(__file__), "..", "data", "fallback_code.db")
        self.fallback_generator = NativeFallbackGenerator(fallback_db_path)

        self.logger = logger.bind(component="airflow_generator")

    def _analyze_complexity(self, spec: OperatorSpec) -> str:
        """
        Analyze component complexity to determine optimal model selection.

        Simple components → claude-3-5-haiku-20241022 (fast, cheap)
        Complex components → claude-sonnet-4-20250514 (accurate, expensive)

        Args:
            spec: Component specification

        Returns:
            Model name to use for generation
        """
        complexity_score = 0

        # Factor 1: Number of inputs (each input adds complexity)
        inputs = spec.inputs if spec.inputs is not None else []
        complexity_score += len(inputs)

        # Factor 2: Runtime parameters (UI forms add complexity)
        runtime_params = spec.runtime_params if spec.runtime_params is not None else []
        complexity_score += len(runtime_params) * 1.5  # Runtime params more complex

        # Factor 3: Number of dependencies
        dependencies = spec.dependencies if spec.dependencies is not None else []
        complexity_score += len(dependencies) * 2  # External deps significantly increase complexity

        # Factor 4: Custom requirements or logic
        requirements = spec.requirements if spec.requirements is not None else []
        complexity_score += len(requirements)

        # Factor 5: Component type complexity
        component_type = getattr(spec, 'component_type', 'operator')
        if component_type == "hook":
            complexity_score += 2  # Hooks are more complex (connection handling)
        elif component_type == "sensor":
            complexity_score += 1  # Sensors moderately complex (poke logic)

        # Factor 6: Template fields (Jinja templating adds complexity)
        template_field_count = 0
        try:
            template_field_count = sum(1 for inp in inputs if isinstance(inp, dict) and inp.get('template_field', False))
        except Exception as e:
            self.logger.warning("Failed to count template fields", error=str(e))
        complexity_score += template_field_count

        # Decision thresholds
        # 0-5: Simple (basic operator with few inputs, no deps)
        # 6-12: Medium (multiple inputs, some params, few deps)
        # 13+: Complex (many inputs, runtime params, external deps, hooks)

        if complexity_score <= 5:
            selected_model = "claude-3-5-haiku-20241022"  # ~80% cost savings
            complexity_level = "simple"
        elif complexity_score <= 12:
            selected_model = self.model  # Use configured model (Sonnet by default)
            complexity_level = "medium"
        else:
            selected_model = self.model  # Always use Sonnet for complex components
            complexity_level = "complex"

        self.logger.info(
            "Complexity analysis complete",
            score=complexity_score,
            level=complexity_level,
            selected_model=selected_model,
            factors={
                "inputs": len(inputs),
                "runtime_params": len(runtime_params),
                "dependencies": len(dependencies),
                "requirements": len(requirements),
                "template_fields": template_field_count,
                "component_type": spec.component_type
            }
        )

        return selected_model

    async def generate(self, spec: OperatorSpec) -> GeneratedComponent:
        """
        Generate Airflow component code from specification

        Args:
            spec: Component specification (OperatorSpec, SensorSpec, or HookSpec)

        Returns:
            GeneratedComponent with code and validation results
        """
        self.logger.info("Starting component generation", component_name=spec.name, component_type=spec.component_type)

        # Track start time for metrics
        start_time = time.time()
        total_prompt_tokens = 0
        total_completion_tokens = 0

        # 1. Validate dependencies
        self.logger.info("=" * 80)
        self.logger.info("Validating dependencies...")
        self.logger.info("=" * 80)

        dependency_validation = self.dependency_validator.validate_dependencies(
            spec.dependencies if spec.dependencies else []
        )

        self.logger.info(
            "Dependency validation completed",
            providers=len(dependency_validation.get("airflow_providers", [])),
            common=len(dependency_validation.get("common_packages", [])),
            unknown=len(dependency_validation.get("unknown_packages", []))
        )

        # 2. Retrieve similar patterns from RAG (if available)
        similar_patterns = await self._retrieve_similar_patterns(spec)

        # 2.5 Phase 3: Check library compatibility
        library_analysis = None
        if spec.dependencies:
            self.logger.info("=" * 80)
            self.logger.info("Phase 3: Checking library compatibility...")
            self.logger.info("=" * 80)

            library_analysis = self.library_tracker.check_dependencies(spec.__dict__)

            if not library_analysis.get("all_compatible", True):
                self.logger.warning(
                    "Some dependencies may not be compatible",
                    incompatible=library_analysis.get("alternatives_needed", [])
                )
                for rec in library_analysis.get("recommendations", []):
                    self.logger.info(f"  Recommendation: {rec}")
            else:
                self.logger.info("All dependencies appear compatible")

        # 2.6 Phase 4: Generate native fallback suggestions for incompatible libraries
        fallback_suggestions = None
        if library_analysis and library_analysis.get("alternatives_needed"):
            self.logger.info("=" * 80)
            self.logger.info("Phase 4: Generating native fallback suggestions...")
            self.logger.info("=" * 80)

            unavailable_libs = library_analysis.get("alternatives_needed", [])
            fallback_suggestions = self.fallback_generator.suggest_fallback_for_code(
                code="",  # We don't have code yet
                unavailable_libraries=unavailable_libs
            )

            if fallback_suggestions.get("has_fallbacks"):
                self.logger.info(
                    "Native fallbacks available",
                    libraries_with_fallbacks=len([s for s in fallback_suggestions.get("suggestions", []) if s.get("available_fallbacks")])
                )
            else:
                self.logger.warning(
                    "No native fallbacks available for some libraries",
                    unavailable=unavailable_libs
                )

        # 3. Generate code with retries (Phase 2: Error Learning Integration)
        code = None
        validation_result = None
        attempts = 0
        last_error_patterns = None
        last_fix_strategy = None
        error_signature = None

        for attempt in range(1, self.max_retries + 1):
            attempts = attempt
            self.logger.info(f"\n{'=' * 80}")
            self.logger.info(f"Generation Attempt {attempt}/{self.max_retries}")
            self.logger.info(f"{'=' * 80}\n")

            try:
                # Generate code (pass error patterns for retry with learned fixes)
                generated_code, prompt_tokens, completion_tokens = await self._generate_code(
                    spec,
                    dependency_validation,
                    similar_patterns,
                    validation_result,  # Pass previous validation for retry context
                    last_error_patterns,  # Phase 2: Pass error patterns
                    last_fix_strategy,  # Phase 2: Pass fix strategy
                    library_analysis,  # Phase 3: Pass library compatibility analysis
                    fallback_suggestions  # Phase 4: Pass native fallback suggestions
                )

                total_prompt_tokens += prompt_tokens
                total_completion_tokens += completion_tokens

                # Validate generated code
                validation_result = self.validator.validate(
                    generated_code,
                    component_type=spec.component_type
                )

                if validation_result.is_valid():
                    code = generated_code
                    self.logger.info(
                        f"✅ Generation successful on attempt {attempt}",
                        component_name=spec.name
                    )

                    # Phase 2: Record successful fix if this was a retry
                    if attempt > 1 and error_signature and last_fix_strategy:
                        self.error_storage.record_fix_attempt(
                            error_signature=error_signature,
                            strategy_name=last_fix_strategy,
                            success=True,
                            attempts_to_fix=attempt - 1
                        )
                        self.logger.info(
                            f"📚 Recorded successful fix strategy",
                            strategy=last_fix_strategy
                        )

                    break
                else:
                    self.logger.warning(
                        f"❌ Validation failed on attempt {attempt}",
                        errors=len(validation_result.errors),
                        warnings=len(validation_result.warnings)
                    )

                    # Track errors (legacy)
                    if validation_result.errors:
                        self.error_tracker.track_error(
                            validation_result.errors,
                            spec.name,
                            attempt
                        )

                    # Phase 2: Extract error patterns and select fix strategy
                    error_message = "; ".join(validation_result.errors)
                    last_error_patterns = self.error_extractor.extract_error_patterns(
                        error_message=error_message,
                        code=generated_code,
                        spec=spec.dict(),
                        attempt_number=attempt,
                        metadata={
                            "prompt_tokens": prompt_tokens,
                            "completion_tokens": completion_tokens
                        }
                    )

                    # Get error signature for tracking
                    error_signature = last_error_patterns.get('error_classification', {}).get('error_signature')

                    # Store error pattern in database
                    self.error_storage.store_error_pattern(
                        error_message=error_message,
                        error_patterns=last_error_patterns,
                        component_name=spec.name,
                        code=generated_code,
                        spec=spec.dict(),
                        attempt_number=attempt
                    )

                    # Look up similar errors with successful fixes
                    error_type = last_error_patterns.get('error_classification', {}).get('error_type', 'unknown')
                    similar_errors = self.error_storage.get_similar_errors(
                        error_type=error_type,
                        category=spec.category,
                        component_type=spec.component_type,
                        min_confidence=0.5
                    )

                    # Select best fix strategy
                    last_fix_strategy = self.fix_strategy_manager.select_best_strategy(
                        error_patterns=last_error_patterns,
                        similar_errors=similar_errors
                    )

                    self.logger.info(
                        f"🔧 Phase 2: Selected fix strategy for retry",
                        strategy=last_fix_strategy,
                        error_type=error_type,
                        similar_errors_found=len(similar_errors)
                    )

                    # Record failed fix attempt if this was a retry with a strategy
                    if attempt > 1 and error_signature and last_fix_strategy:
                        self.error_storage.record_fix_attempt(
                            error_signature=error_signature,
                            strategy_name=last_fix_strategy,
                            success=False
                        )

            except Exception as e:
                self.logger.error(f"Error during generation attempt {attempt}", error=str(e))
                if attempt == self.max_retries:
                    raise

        # Final validation check
        if not code or not validation_result or not validation_result.is_valid():
            raise ValueError(
                f"Failed to generate valid component after {self.max_retries} attempts. "
                f"Last errors: {validation_result.errors if validation_result else 'Unknown'}"
            )

        # 4. Generate tests
        self.logger.info("Generating tests...")
        test_code = self.test_generator.generate_test_file(
            spec.name,
            spec.component_type,
            spec.dict()
        )

        # 4.5. Generate test DAG with runtime params support
        self.logger.info("Generating test DAG with runtime params support...")
        test_dag = self.test_generator.generate_test_dag(
            spec.name,
            spec.component_type,
            spec.dict()
        )

        # 5. Generate documentation
        self.logger.info("Generating documentation...")
        documentation = self.doc_generator.generate_documentation(
            spec.name,
            spec.component_type,
            spec.dict(),
            code
        )

        # 6. Calculate metrics
        total_time = time.time() - start_time
        first_attempt_success = (attempts == 1)

        # 7. Record generation in learning database
        self.learning_db.record_generation(
            component_name=spec.name,
            component_type=spec.component_type,
            component_category=spec.category,
            component_description=spec.description,
            attempts_needed=attempts,
            success=True,
            total_time_seconds=total_time,
            prompt_tokens=total_prompt_tokens,
            completion_tokens=total_completion_tokens,
            validation_passed=True,
            first_attempt_success=first_attempt_success,
            error_messages=None,
            spec_complexity="medium"  # Could be calculated based on spec
        )

        # 7.5. Phase 1: Extract and store patterns from successful generation
        try:
            self.logger.info("📚 Extracting patterns from successful generation...")

            # Extract patterns using Phase 1 pattern extractor
            metadata = {
                "attempts": attempts,
                "total_time": total_time,
                "tokens": total_prompt_tokens + total_completion_tokens,
                "first_attempt_success": first_attempt_success
            }

            patterns = self.pattern_extractor.extract_patterns(code, spec.dict(), metadata)

            # Store patterns in database
            self.pattern_storage.store_component_patterns(
                component_name=spec.name,
                code=code,
                patterns=patterns,
                metadata=metadata,
                success=True
            )

            self.logger.info(
                "✅ Patterns extracted and stored successfully",
                pattern_types=len(patterns)
            )

        except Exception as e:
            self.logger.warning("Failed to extract/store patterns", error=str(e))

        # 7.6. Phase 3: Log successful library usage for learning
        if spec.dependencies:
            try:
                self.logger.info("📚 Logging library usage for learning...")
                for dep in spec.dependencies:
                    self.library_tracker.log_library_usage(
                        library_name=dep,
                        component_name=spec.name,
                        import_success=True,
                        execution_success=True,
                        component_type=spec.component_type
                    )
                self.logger.info(
                    "✅ Library usage logged",
                    libraries=len(spec.dependencies)
                )
            except Exception as e:
                self.logger.warning("Failed to log library usage", error=str(e))

        # 7.7. Phase 4: Log successful fallback usage for learning
        if fallback_suggestions and fallback_suggestions.get("has_fallbacks"):
            try:
                self.logger.info("📚 Logging fallback usage for learning...")
                for suggestion in fallback_suggestions.get("suggestions", []):
                    library_name = suggestion.get("library", "")
                    for fallback in suggestion.get("available_fallbacks", []):
                        operation = fallback.get("operation", "unknown")
                        self.fallback_generator.log_fallback_usage(
                            library_name=library_name,
                            operation_type=operation,
                            component_name=spec.name,
                            success=True  # Since generation succeeded
                        )
                self.logger.info("✅ Fallback usage logged")
            except Exception as e:
                self.logger.warning("Failed to log fallback usage", error=str(e))

        # 8. Create final component
        component = GeneratedComponent(
            name=spec.name,
            component_type=spec.component_type,
            code=code,
            documentation=documentation,
            tests=test_code,
            test_dag=test_dag,
            category=spec.category,
            version=spec.version,
            validation=validation_result,
            attempts_needed=attempts,
            generation_time_seconds=total_time,
            prompt_tokens=total_prompt_tokens,
            completion_tokens=total_completion_tokens
        )

        self.logger.info(
            "Component generation complete",
            component_name=spec.name,
            attempts=attempts,
            time_seconds=round(total_time, 2),
            tokens=total_prompt_tokens + total_completion_tokens
        )

        return component

    async def _retrieve_similar_patterns(self, spec: OperatorSpec) -> List[Dict]:
        """
        Retrieve similar patterns from local pattern database (Phase 1 integration)

        Uses the PatternStorage to find high-confidence patterns from successful
        component generations that match the category and component type.
        """
        try:
            self.logger.info(
                "Retrieving similar patterns from local database...",
                category=spec.category,
                component_type=spec.component_type
            )

            # Get best patterns for this category/type
            patterns = self.pattern_storage.get_best_patterns(
                category=spec.category,
                component_type=spec.component_type,
                min_confidence=0.7,  # Only use patterns with 70%+ success rate
                limit=5  # Top 5 most successful patterns
            )

            # Get similar complete components for reference
            similar_components = self.pattern_storage.get_similar_components(
                category=spec.category,
                subcategory=spec.subcategory if hasattr(spec, 'subcategory') else None,
                min_success_score=150,  # High-quality components only
                limit=2  # Top 2 similar components
            )

            self.logger.info(
                f"✅ Retrieved {len(patterns)} patterns and {len(similar_components)} similar components",
                patterns=len(patterns),
                components=len(similar_components)
            )

            # Format patterns for prompt injection
            formatted_patterns = {
                "code_patterns": patterns,
                "similar_components": similar_components
            }

            return [formatted_patterns] if patterns or similar_components else []

        except Exception as e:
            self.logger.warning("Error retrieving patterns from local database", error=str(e))
            # Fallback to external RAG service if available
            if self.rag_service_url:
                return await self._retrieve_from_external_rag(spec)
            return []

    async def _retrieve_from_external_rag(self, spec: OperatorSpec) -> List[Dict]:
        """Fallback: Retrieve patterns from external RAG service"""
        try:
            self.logger.info("Falling back to external RAG service...")

            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    f"{self.rag_service_url}/api/airflow/patterns/similar",
                    json={
                        "description": spec.description,
                        "category": spec.category,
                        "component_type": spec.component_type,
                        "n_results": 3
                    }
                )

                if response.status_code == 200:
                    data = response.json()
                    patterns = data.get("results", [])
                    self.logger.info(f"Retrieved {len(patterns)} patterns from external RAG")
                    return patterns
                else:
                    self.logger.warning(
                        "Failed to retrieve patterns from external RAG",
                        status_code=response.status_code
                    )
                    return []

        except Exception as e:
            self.logger.warning("Error retrieving patterns from external RAG", error=str(e))
            return []

    async def _generate_code(
        self,
        spec: OperatorSpec,
        dependency_validation: Dict[str, Any],
        similar_patterns: List[Dict],
        previous_validation: Optional[ValidationResult] = None,
        error_patterns: Optional[Dict[str, Any]] = None,  # Phase 2
        fix_strategy: Optional[str] = None,  # Phase 2
        library_analysis: Optional[Dict[str, Any]] = None,  # Phase 3
        fallback_suggestions: Optional[Dict[str, Any]] = None  # Phase 4
    ) -> tuple[str, int, int]:
        """
        Generate code using Claude AI

        Args:
            spec: Component specification
            dependency_validation: Validated dependencies
            similar_patterns: Similar patterns from Phase 1
            previous_validation: Previous validation result (for retry)
            error_patterns: Phase 2 - Extracted error patterns from last attempt
            fix_strategy: Phase 2 - Selected fix strategy for retry
            library_analysis: Phase 3 - Library compatibility analysis
            fallback_suggestions: Phase 4 - Native fallback suggestions

        Returns:
            Tuple of (code, prompt_tokens, completion_tokens)
        """
        # Analyze complexity to select optimal model
        selected_model = self._analyze_complexity(spec)

        # Build comprehensive prompt (Phase 2: Include fix strategy if on retry)
        prompt = self._build_prompt(
            spec,
            dependency_validation,
            similar_patterns,
            previous_validation,
            error_patterns,  # Phase 2
            fix_strategy,  # Phase 2
            library_analysis,  # Phase 3
            fallback_suggestions  # Phase 4
        )

        self.logger.debug("Sending request to Claude API...", model=selected_model)

        # Call Claude API with prompt caching for cost optimization
        # Cache the system prompt (generation guidelines) to reduce costs by 50-70%
        response = self.client.messages.create(
            model=selected_model,
            max_tokens=4096,
            temperature=0.0,  # Deterministic output
            system=[
                {
                    "type": "text",
                    "text": "You are an expert Python developer specializing in Apache Airflow. Generate production-quality Airflow component code following all best practices and standards.",
                    "cache_control": {"type": "ephemeral"}  # Cache this system prompt
                }
            ],
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            timeout=60.0  # 60 second timeout to prevent hanging
        )

        # Extract code from response
        code = response.content[0].text

        # Clean up code (remove markdown markers if present)
        code = self._clean_code(code)

        prompt_tokens = response.usage.input_tokens
        completion_tokens = response.usage.output_tokens

        self.logger.info(
            "Claude API response received",
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            code_length=len(code)
        )

        return code, prompt_tokens, completion_tokens

    def _build_prompt(
        self,
        spec: OperatorSpec,
        dependency_validation: Dict[str, Any],
        similar_patterns: List[Dict],
        previous_validation: Optional[ValidationResult] = None,
        error_patterns: Optional[Dict[str, Any]] = None,  # Phase 2
        fix_strategy: Optional[str] = None,  # Phase 2
        library_analysis: Optional[Dict[str, Any]] = None,  # Phase 3
        fallback_suggestions: Optional[Dict[str, Any]] = None  # Phase 4
    ) -> str:
        """Build comprehensive prompt for Claude (Phase 2: Includes fix strategy, Phase 3: Library recommendations, Phase 4: Native fallbacks)"""

        component_type = spec.component_type
        base_class = spec.base_class

        # Start with system context
        prompt = f"""You are an expert Python developer specializing in Apache Airflow. Generate production-quality Airflow {component_type} code.

# Component Specification

**Name:** {spec.name}
**Type:** {component_type}
**Category:** {spec.category}
**Description:** {spec.description}
**Base Class:** {base_class}

"""

        # Add requirements
        if spec.requirements:
            prompt += "## Requirements\n\n"
            for req in spec.requirements:
                prompt += f"- {req}\n"
            prompt += "\n"

        # Add input parameters
        if spec.inputs:
            # CRITICAL FIX: Sort inputs to ensure valid Python parameter ordering
            # Python requires: required (no default) -> required (with default) -> optional (with default)
            required_no_default = []
            required_with_default = []
            optional_params = []

            for inp in spec.inputs:
                is_required = inp.get('required', False)
                has_default = 'default' in inp

                if is_required and not has_default:
                    # Truly required parameter (no default value)
                    required_no_default.append(inp)
                elif is_required and has_default:
                    # Contradictory: required=true but has default value
                    # This is logically optional but marked as required
                    self.logger.warning(
                        "Parameter has required=true but also has default value - treating as required with default",
                        param_name=inp.get('name'),
                        default_value=inp.get('default')
                    )
                    required_with_default.append(inp)
                else:
                    # Optional parameter (required=false)
                    optional_params.append(inp)

            # Reorder: required (no default) -> required (with default) -> optional
            sorted_inputs = required_no_default + required_with_default + optional_params

            prompt += "## Input Parameters\n\n"
            prompt += "**IMPORTANT**: Parameters are ordered to ensure valid Python syntax:\n"
            prompt += "1. Required parameters without defaults first\n"
            prompt += "2. Required parameters with defaults second\n"
            prompt += "3. Optional parameters with defaults last\n\n"

            for inp in sorted_inputs:
                required = "Required" if inp.get('required', False) else "Optional"
                has_default = 'default' in inp
                prompt += f"- **{inp['name']}** ({inp.get('type', 'str')}): {required}"
                if has_default:
                    default_val = inp.get('default')
                    # Format default value for display
                    if isinstance(default_val, str):
                        prompt += f" (default: '{default_val}')"
                    else:
                        prompt += f" (default: {default_val})"
                prompt += "\n"
                if 'description' in inp:
                    prompt += f"  {inp['description']}\n"
            prompt += "\n"

        # Add runtime parameters (for user input via UI)
        runtime_params = spec.dict().get('runtime_params', [])
        if runtime_params:
            prompt += "## Runtime Parameters (User Input via UI)\n\n"
            prompt += "**NOTE**: These parameters will be passed as Jinja templates (e.g., `{{ params.city }}`) in DAGs\n"
            prompt += "**IMPORTANT**: Your operator MUST handle Jinja template strings in `__init__` and validate actual values in `execute()`\n\n"
            for param in runtime_params:
                prompt += f"- **{param['name']}** ({param.get('type', 'string')}): {param.get('description', '')}\n"
                if param.get('enum'):
                    prompt += f"  Allowed values: {param['enum']}\n"
            prompt += "\n"

        # Add config parameters
        if spec.config_params:
            prompt += "## Configuration Parameters\n\n"
            for param in spec.config_params:
                prompt += f"- **{param['name']}** ({param.get('type', 'str')})\n"
                if 'description' in param:
                    prompt += f"  {param['description']}\n"
            prompt += "\n"

        # Add dependency information
        if dependency_validation.get("airflow_providers"):
            prompt += "## Airflow Providers\n\n"
            for provider in dependency_validation["airflow_providers"]:
                prompt += f"- {provider['provider_package']}: {provider['description']}\n"
            prompt += "\n"

        # Add learned patterns from Phase 1 (Pattern Learning System)
        if similar_patterns:
            prompt += "## 🎓 Learned Patterns from Successful Components\n\n"
            prompt += "**Use these proven patterns to increase success rate:**\n\n"

            # Extract patterns from our structured format
            for pattern_group in similar_patterns:
                if isinstance(pattern_group, dict):
                    # Code patterns (structural, import, etc.)
                    code_patterns = pattern_group.get('code_patterns', [])
                    if code_patterns:
                        prompt += "### Proven Code Patterns\n\n"
                        for pattern in code_patterns[:5]:  # Top 5 patterns
                            pattern_type = pattern.get('pattern_type', 'unknown')
                            pattern_name = pattern.get('pattern_name', 'unnamed')
                            confidence = pattern.get('confidence_score', 0) * 100
                            pattern_data = json.loads(pattern.get('pattern_data', '{}'))

                            prompt += f"**{pattern_type.upper()} Pattern** ({pattern_name}) - Confidence: {confidence:.0f}%\n"

                            # Inject pattern-specific guidance
                            if pattern_type == 'import':
                                dual_imports = pattern_data.get('dual_imports', [])
                                if dual_imports:
                                    prompt += "  - **Use dual imports for Airflow 2.x/3.x compatibility:**\n"
                                    for di in dual_imports:
                                        prompt += f"    ```python\n    try:\n        from {di['primary']}\n    except ImportError:\n        from {di['fallback']}\n    ```\n"

                            elif pattern_type == 'template_fields':
                                template_fields = pattern_data.get('template_fields', [])
                                if template_fields:
                                    prompt += f"  - **Declare template_fields:** {', '.join(template_fields)}\n"
                                validation = pattern_data.get('validation_pattern')
                                if validation:
                                    prompt += f"  - **Template validation pattern:** `{validation}`\n"

                            elif pattern_type == 'parameter_ordering':
                                prompt += f"  - **Ordering strategy:** {pattern_data.get('ordering_strategy', 'standard')}\n"
                                prompt += f"  - **Required params first:** {pattern_data.get('required_first', True)}\n"

                            elif pattern_type == 'runtime_params':
                                access_pattern = pattern_data.get('access_pattern')
                                if access_pattern:
                                    prompt += f"  - **Access runtime params:** `{access_pattern}`\n"

                            elif pattern_type == 'error_handling':
                                exception_type = pattern_data.get('exception_type', 'AirflowException')
                                prompt += f"  - **Use {exception_type} for errors**\n"

                            prompt += "\n"

                    # Similar complete components for reference
                    similar_components = pattern_group.get('similar_components', [])
                    if similar_components:
                        prompt += "### Similar Successful Components (for reference)\n\n"
                        for comp in similar_components[:2]:  # Top 2 components
                            comp_name = comp.get('component_name', 'Unknown')
                            success_score = comp.get('success_score', 0)
                            complexity = comp.get('complexity_score', 0)
                            code_snippet = comp.get('complete_code', '')[:800]  # First 800 chars

                            prompt += f"**{comp_name}** (Success Score: {success_score}, Complexity: {complexity})\n"
                            prompt += f"```python\n{code_snippet}...\n```\n\n"

            prompt += "\n"

        # Add previous validation errors for retry
        if previous_validation and previous_validation.errors:
            prompt += "## Previous Validation Errors (FIX THESE)\n\n"
            for error in previous_validation.errors:
                prompt += f"- ❌ {error}\n"
            prompt += "\n"

        # Phase 2: Add fix strategy prompt from learned patterns
        if fix_strategy and error_patterns:
            prompt += "## 🔧 PHASE 2: LEARNED FIX STRATEGY\n\n"
            prompt += f"**Strategy:** `{fix_strategy}`\n\n"

            # Get detailed fix instructions from strategy manager
            fix_prompt = self.fix_strategy_manager.get_prompt_addition(
                strategy_name=fix_strategy,
                error_message="; ".join(previous_validation.errors) if previous_validation else None,
                error_patterns=error_patterns
            )
            prompt += fix_prompt
            prompt += "\n"

            # Add severity information
            severity = error_patterns.get('error_classification', {}).get('severity', 'medium')
            is_auto_fixable = self.fix_strategy_manager.is_auto_fixable(fix_strategy)

            prompt += f"**Severity:** {severity.upper()}\n"
            prompt += f"**Auto-fixable:** {'Yes' if is_auto_fixable else 'No'}\n"
            prompt += "\n"

        # Phase 3: Add library compatibility notes
        if library_analysis and not library_analysis.get("all_compatible", True):
            prompt += "## 📚 PHASE 3: LIBRARY COMPATIBILITY NOTES\n\n"
            prompt += "**Warning:** Some requested libraries may not be compatible with Airflow.\n\n"

            for lib_info in library_analysis.get("libraries", []):
                if not lib_info.get("compatible", True):
                    lib_name = lib_info.get("name", "unknown")
                    recommendation = lib_info.get("recommendation", "")
                    prompt += f"**{lib_name}:** {recommendation}\n"

                    # Add alternatives if available
                    alternatives = lib_info.get("alternatives", [])
                    if alternatives:
                        prompt += f"  - Alternatives: {', '.join([a.get('alternative_library', a.get('alternative_approach', '')) for a in alternatives[:3]])}\n"

            prompt += "\n**Please ensure you:**\n"
            prompt += "1. Use compatible libraries or Airflow providers when available\n"
            prompt += "2. For heavy ML libraries, consider using KubernetesPodOperator or API calls\n"
            prompt += "3. Add proper error handling for optional imports\n"
            prompt += "\n"

            # Add library recommender suggestions
            lib_prompt = self.library_recommender.generate_prompt_addition(
                library_analysis,
                category=spec.category
            )
            if lib_prompt:
                prompt += lib_prompt
                prompt += "\n"

        # Phase 4: Add native fallback code for unavailable libraries
        if fallback_suggestions and fallback_suggestions.get("has_fallbacks"):
            prompt += "## 🔧 PHASE 4: NATIVE PYTHON FALLBACK CODE\n\n"
            prompt += "**The following native Python implementations are available for unavailable libraries:**\n\n"

            for suggestion in fallback_suggestions.get("suggestions", []):
                library_name = suggestion.get("library", "")
                available_fallbacks = suggestion.get("available_fallbacks", [])

                if available_fallbacks:
                    prompt += f"### {library_name} Fallbacks\n\n"

                    # Get actual fallback code
                    for fb in available_fallbacks[:3]:  # Limit to 3 operations per library
                        operation = fb.get("operation", "")
                        fallback_data = self.fallback_generator.get_fallback(library_name, operation)

                        if fallback_data:
                            fallback_code = fallback_data.get("fallback_code", "")
                            if fallback_code:
                                # Truncate if too long
                                code_preview = fallback_code[:600] + "..." if len(fallback_code) > 600 else fallback_code
                                prompt += f"**{operation}:**\n```python\n{code_preview}\n```\n\n"

            prompt += "**Instructions:**\n"
            prompt += "- Use these native implementations instead of importing unavailable libraries\n"
            prompt += "- These use only Python standard library (no external dependencies)\n"
            prompt += "- Adapt the fallback code to your specific use case\n"
            prompt += "\n"

        # Add generation guidelines
        import_module = ""
        if component_type == "operator":
            import_module = "airflow.models"
        elif component_type == "sensor":
            import_module = "airflow.sensors.base"
        elif component_type == "hook":
            import_module = "airflow.hooks.base"

        prompt += f"""
# Generation Guidelines

## Code Structure

Generate a complete, production-ready Airflow {component_type} with:

1. **Imports (CRITICAL - Use ONLY These Official Imports with Airflow 2.x/3.x Compatibility):**

   **Base Class Import (Dual Compatibility for Airflow 2.x and 3.x):**
   ```python
   try:
       # Airflow 3.x Task SDK (new import path)
       from airflow.sdk.bases.{component_type} import {base_class}
   except ImportError:
       # Airflow 2.x fallback (legacy import path)
       from {import_module} import {base_class}
   ```

   **Other Required Imports:**
   - `from airflow.exceptions import AirflowException` ✅ REQUIRED for error handling
   - `from typing import Dict, Any, Optional, List, Sequence, Union` ✅
   - Only use Airflow providers listed above in the "Airflow Providers" section
   - Only use Python packages from the standard library or commonly available packages
   - Use `from pathlib import Path` for file paths (modern Python)
   - Use `from datetime import datetime, timedelta` for dates

   **NEVER import from:**
   - ❌ Random external packages not listed in dependencies
   - ❌ Deprecated Airflow modules (e.g., airflow.utils.decorators.apply_defaults)
   - ❌ Custom/unknown Airflow extensions

2. **Class Definition:**
   - Class name: `{spec.name}`
   - Inherit from `{base_class}`
   - Add comprehensive docstring with description and parameter docs

3. **Class Attributes (REQUIRED):**
   - `template_fields: Sequence[str] = ['field1', 'field2']` - List of Jinja2-templatable fields
   - `ui_color: str = "{spec.ui_color or '#f0ede4'}"` - Hex color for Airflow UI
"""

        if component_type == "sensor":
            prompt += "   - `poke_interval: int` - Seconds between poke attempts\n"
            prompt += "   - `timeout: int` - Maximum wait time in seconds\n"
            prompt += "   - `mode: str` - 'poke' or 'reschedule'\n"
        elif component_type == "hook":
            prompt += f"   - `conn_name_attr: str = '{spec.conn_name_attr if hasattr(spec, 'conn_name_attr') else 'conn_id'}'`\n"
            prompt += f"   - `conn_type: str = '{spec.conn_type if hasattr(spec, 'conn_type') else 'generic'}'`\n"
            prompt += f"   - `hook_name: str = '{spec.hook_name if hasattr(spec, 'hook_name') else spec.name}'`\n"

        prompt += """
"""

        if component_type == "operator":
            prompt += """
4. **Constructor (`__init__`):**
   - Accept all input parameters with proper type hints
   - Call `super().__init__(**kwargs)` FIRST
   - **CRITICAL: Template Field Validation** - For fields in `template_fields`:
     * Skip validation for Jinja template strings (containing `{{`)
     * These will be rendered at runtime, so validate in execute() instead
     * Example: `if '{{' not in str(param_value) and param_value not in valid_values:`
   - For non-template fields: Validate and raise AirflowException if invalid
   - Store parameters as instance variables
   - Log initialization with self.log.info()

5. **Execute Method (REQUIRED):**
   - **IMPORTANT**: Validate template field values HERE (after Jinja rendering)
   - All template_fields are rendered by Airflow before execute() runs
   ```python
   def execute(self, context: Dict[str, Any]) -> Any:
       \"\"\"
       Execute operator logic

       Args:
           context: Airflow context dict with task_instance, execution_date, etc.

       Returns:
           Any: Value to push to XCom (optional)

       Raises:
           AirflowException: On failure
       \"\"\"
       self.log.info(f"Executing {self.task_id}")
       # Implementation here
       # Use context.get('key', default) for safe access
       # Return value will be pushed to XCom automatically
       return result
   ```
"""
        elif component_type == "sensor":
            prompt += """
4. **Constructor (`__init__`):**
   - Accept all input parameters with type hints
   - Accept sensor-specific params: poke_interval, timeout, mode
   - Call `super().__init__(**kwargs)` FIRST
   - Store parameters as instance variables

5. **Poke Method (REQUIRED):**
   ```python
   def poke(self, context: Dict[str, Any]) -> bool:
       \"\"\"
       Check if condition is met

       Args:
           context: Airflow context dictionary

       Returns:
           bool: True if condition met (sensor succeeds),
                 False to continue poking

       Raises:
           AirflowException: For terminal failure
       \"\"\"
       self.log.info(f"Poking for condition: {self.task_id}")
       # Check condition
       # Return True when condition is met, False to retry
       return condition_met
   ```
"""
        elif component_type == "hook":
            prompt += """
4. **Constructor (`__init__`):**
   - Accept conn_id parameter (connection ID)
   - Call `super().__init__()`
   - Initialize self._connection = None for lazy loading

5. **Get Connection Method (REQUIRED):**
   ```python
   def get_conn(self) -> Any:
       \"\"\"
       Get or create connection

       Returns:
           Connection object or client instance

       Raises:
           AirflowException: If connection cannot be established
       \"\"\"
       if self._connection is not None:
           return self._connection

       # Get Airflow connection
       conn = BaseHook.get_connection(self.conn_id)

       # Create actual connection/client
       self._connection = self._create_client(conn)

       self.log.info(f"Connected to {conn.host}")
       return self._connection

   def _create_client(self, conn: Connection) -> Any:
       \"\"\"Create client from Airflow connection\"\"\"
       # Implementation to create actual client
       pass
   ```
"""

        prompt += """
## Security & Best Practices (MANDATORY)

**Security - NEVER Do:**
- ❌ NEVER use eval(), exec(), compile(), __import__()
- ❌ NEVER use os.system() or subprocess with shell=True
- ❌ NEVER execute untrusted code or user input
- ❌ NEVER expose credentials in logs

**Security - Always Do:**
- ✅ Use ast.literal_eval() for safe string-to-Python conversion
- ✅ Validate and sanitize all user inputs
- ✅ Use parameterized queries for SQL (never string formatting)
- ✅ Get credentials from Airflow connections (BaseHook.get_connection())

**Code Quality:**
- ✅ Add type hints for ALL parameters and return values
- ✅ Write comprehensive docstrings (class, methods, complex logic)
- ✅ Use proper error handling with try/except blocks
- ✅ Raise AirflowException for task failures
- ✅ Log operations: self.log.info(), self.log.warning(), self.log.error()

**Airflow Best Practices:**
- ✅ Use context.get('key', default) for safe context access (not context['key'])
- ✅ Return values from execute() to push to XCom automatically
- ✅ Use BaseHook.get_connection() to get connection details
- ✅ Store connection in self._connection for lazy initialization in hooks
- ✅ Make template_fields list all fields that should support Jinja2 templates

## Output Format (CRITICAL)

Return ONLY the Python code with NO markdown formatting, NO explanations, NO code blocks.

**CORRECT:** Start directly with imports like `from airflow.models import BaseOperator`
**WRONG:** Starting with ```python or any explanation text

The code must be complete, syntactically correct, and ready to save as a .py file.
"""

        return prompt

    def _clean_code(self, code: str) -> str:
        """Clean generated code by removing markdown markers"""
        # Remove markdown code blocks
        code = code.strip()

        if code.startswith("```python"):
            code = code[len("```python"):].strip()
        elif code.startswith("```"):
            code = code[3:].strip()

        if code.endswith("```"):
            code = code[:-3].strip()

        return code

    def validate(self, code: str) -> ValidationResult:
        """Validate generated code (implements BaseCodeGenerator)"""
        return self.validator.validate(code, component_type="operator")
