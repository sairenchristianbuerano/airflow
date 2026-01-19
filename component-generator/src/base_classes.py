"""
Base classes and data models for Airflow component generation.

Defines Pydantic models for specifications, validation results, and generated components.
"""

from typing import List, Optional, Dict, Any, Literal
from datetime import datetime
from pydantic import BaseModel, Field, field_validator
from abc import ABC, abstractmethod
import uuid


class OperatorSpec(BaseModel):
    """Specification for generating an Airflow operator"""

    name: str = Field(..., description="Operator class name (PascalCase)")
    display_name: str = Field(..., description="Human-readable display name")
    description: str = Field(..., description="Operator description")
    category: str = Field(..., description="Category: http, database, cloud, etc.")
    component_type: Literal["operator", "sensor", "hook"] = Field(
        default="operator",
        description="Type of component to generate"
    )
    platforms: List[str] = Field(default=["airflow"], description="Target platforms")

    requirements: List[str] = Field(
        default_factory=list,
        description="Functional requirements"
    )

    inputs: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Input parameters for the operator"
    )

    config_params: Optional[List[Dict[str, Any]]] = Field(
        default=None,
        description="Configuration parameters (__init__ params)"
    )

    runtime_params: Optional[List[Dict[str, Any]]] = Field(
        default=None,
        description="Runtime parameters configurable via Airflow UI (DAG params)"
    )

    dependencies: List[str] = Field(
        default_factory=list,
        description="Python package dependencies"
    )

    # Airflow-specific fields
    base_class: str = Field(
        default="BaseOperator",
        description="Base class: BaseOperator, BaseSensor, BaseHook"
    )
    template_fields: Optional[List[str]] = Field(
        default=None,
        description="Fields that support Jinja templating"
    )
    ui_color: Optional[str] = Field(
        default="#f0ede4",
        description="UI color in hex format"
    )
    ui_fgcolor: Optional[str] = Field(
        default="#000",
        description="UI foreground color in hex format"
    )

    author: str = Field(default="Airflow Component Factory", description="Author name")
    version: str = Field(default="1.0.0", description="Component version")

    # Team standard format fields (optional for backward compatibility)
    icon: Optional[str] = Field(default=None, description="Icon reference (for future UI)")
    template_ext: Optional[List[str]] = Field(
        default=None,
        description="File extensions for template fields"
    )
    outputs: Optional[List[Dict[str, Any]]] = Field(
        default=None,
        description="Output fields (for documentation)"
    )
    examples: Optional[List[Dict[str, Any]]] = Field(
        default=None,
        description="Usage examples"
    )
    implementation_hints: Optional[List[str]] = Field(
        default=None,
        description="Implementation guidance for LLM"
    )
    prerequisites: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Runtime prerequisites (services, env vars, connections)"
    )
    license: Optional[str] = Field(default="Apache 2.0", description="License type")
    documentation_url: Optional[str] = Field(
        default=None,
        description="URL to additional documentation"
    )

    @field_validator('name')
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Ensure name is PascalCase"""
        if not v[0].isupper():
            raise ValueError("Operator name must start with uppercase letter")
        if not v.replace('_', '').isalnum():
            raise ValueError("Operator name must be alphanumeric (underscores allowed)")
        return v

    @field_validator('base_class')
    @classmethod
    def validate_base_class(cls, v: str) -> str:
        """Validate base class is supported"""
        valid_bases = ["BaseOperator", "BaseSensor", "BaseHook"]
        if v not in valid_bases:
            raise ValueError(f"base_class must be one of: {valid_bases}")
        return v


class SensorSpec(OperatorSpec):
    """Specification for generating an Airflow sensor"""

    component_type: Literal["sensor"] = "sensor"
    base_class: str = "BaseSensor"
    poke_interval: int = Field(
        default=60,
        description="Time in seconds between pokes"
    )
    timeout: int = Field(
        default=60 * 60 * 24 * 7,  # 7 days
        description="Timeout in seconds"
    )
    mode: Literal["poke", "reschedule"] = Field(
        default="poke",
        description="Sensor mode: poke or reschedule"
    )


class HookSpec(OperatorSpec):
    """Specification for generating an Airflow hook"""

    component_type: Literal["hook"] = "hook"
    base_class: str = "BaseHook"
    conn_name_attr: str = Field(
        default="conn_id",
        description="Connection name attribute"
    )
    conn_type: str = Field(
        ...,
        description="Connection type (e.g., 'http', 'postgres')"
    )
    hook_name: str = Field(
        ...,
        description="Human-readable hook name"
    )


class ValidationResult(BaseModel):
    """Result of code validation"""

    valid: bool = Field(..., description="Whether validation passed")
    errors: List[str] = Field(default_factory=list, description="Validation errors")
    warnings: List[str] = Field(default_factory=list, description="Validation warnings")
    security_issues: List[str] = Field(
        default_factory=list,
        description="Security concerns found"
    )

    # AST analysis results
    has_execute_method: bool = Field(default=False, description="Has execute() method")
    has_poke_method: bool = Field(default=False, description="Has poke() method (sensors)")
    has_get_conn_method: bool = Field(default=False, description="Has get_conn() method (hooks)")
    imports_valid: bool = Field(default=True, description="All imports are valid")
    inherits_correctly: bool = Field(default=False, description="Inherits from correct base")

    def is_valid(self) -> bool:
        """Check if validation passed without critical errors"""
        return self.valid and len(self.errors) == 0 and len(self.security_issues) == 0


class GeneratedComponent(BaseModel):
    """Generated Airflow component (operator/sensor/hook)"""

    component_id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="Unique component ID"
    )
    name: str = Field(..., description="Component class name")
    component_type: str = Field(..., description="Type: operator, sensor, hook")
    code: str = Field(..., description="Generated Python code")
    documentation: str = Field(..., description="Generated documentation")
    tests: Optional[str] = Field(None, description="Generated test code")
    test_dag: Optional[str] = Field(None, description="Generated test DAG with runtime params support")

    # Metadata
    category: str = Field(..., description="Component category")
    version: str = Field(default="1.0.0", description="Component version")
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Validation results
    validation: ValidationResult = Field(..., description="Validation results")

    # Generation metrics
    attempts_needed: int = Field(default=1, description="Attempts to generate")
    generation_time_seconds: float = Field(default=0.0, description="Time to generate")
    prompt_tokens: int = Field(default=0, description="Tokens used in prompt")
    completion_tokens: int = Field(default=0, description="Tokens in completion")


class ComponentMetadata(BaseModel):
    """Metadata for registered components in the index"""

    component_id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="Unique component ID"
    )
    name: str = Field(..., description="Component class name")
    display_name: str = Field(..., description="Human-readable name")
    description: str = Field(..., description="Component description")
    category: str = Field(..., description="Category")
    component_type: str = Field(..., description="Type: operator, sensor, hook")
    platform: str = Field(default="airflow", description="Platform")

    version: str = Field(default="1.0.0", description="Version")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    author: str = Field(..., description="Author name")
    status: str = Field(default="generated", description="Status: generated, deployed, etc.")

    # Technical details
    code_size: int = Field(default=0, description="Code size in bytes")
    dependencies: List[str] = Field(default_factory=list, description="Package dependencies")
    validation_passed: bool = Field(default=False, description="Validation passed")
    deployment_status: Optional[str] = Field(None, description="Deployment status")

    # Schema
    input_schema: Optional[Dict[str, Any]] = Field(
        None,
        description="Input parameter schema"
    )
    has_config_params: bool = Field(default=False, description="Has config params")
    requirements: List[str] = Field(default_factory=list, description="Functional requirements")

    # Airflow-specific
    base_class: str = Field(default="BaseOperator", description="Base class")
    template_fields: List[str] = Field(default_factory=list, description="Template fields")


class BaseCodeGenerator(ABC):
    """Abstract base class for code generators"""

    @abstractmethod
    async def generate(self, spec: OperatorSpec) -> GeneratedComponent:
        """Generate component code from specification"""
        pass

    @abstractmethod
    def validate(self, code: str) -> ValidationResult:
        """Validate generated code"""
        pass
