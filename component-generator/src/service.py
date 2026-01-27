"""
FastAPI service for Airflow Component Generator

REST API service for Airflow custom component generation.
Endpoint prefix: /api/airflow/component-generator/*
"""

import os
import yaml
from typing import Optional
from contextlib import asynccontextmanager
from pathlib import Path
import structlog
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from src.airflow_agent import AirflowComponentGenerator
from src.airflow_validator import FeasibilityChecker
from src.base_classes import OperatorSpec, SensorSpec, HookSpec
from src import __version__

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    # Look for .env file in parent directory (repo root)
    env_path = Path(__file__).parent.parent.parent / '.env'
    if env_path.exists():
        load_dotenv(env_path)
        logger_temp = structlog.get_logger()
        logger_temp.info("Loaded environment variables from .env file", path=str(env_path))
except ImportError:
    # python-dotenv not installed, skip
    pass

logger = structlog.get_logger()

# Generator instances
generator: Optional[AirflowComponentGenerator] = None
feasibility_checker: Optional[FeasibilityChecker] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan - startup and shutdown"""
    # Startup
    global generator, feasibility_checker

    logger.info("Starting Airflow Component Generator service")

    # Initialize generator
    rag_service_url = os.getenv("RAG_SERVICE_URL", "http://localhost:8096")

    generator = AirflowComponentGenerator(rag_service_url=rag_service_url)
    feasibility_checker = FeasibilityChecker()

    logger.info("Airflow Component Generator and Feasibility Checker initialized")

    yield

    # Shutdown
    logger.info("Shutting down Airflow Component Generator")


# FastAPI app
app = FastAPI(
    title="Airflow Component Generator",
    version=__version__,
    description="Generate custom Airflow operators, sensors, and hooks from YAML specifications",
    lifespan=lifespan
)

# CORS Configuration
cors_origins = os.getenv("CORS_ORIGINS", '["http://localhost:8095", "http://localhost:8096", "http://localhost:3000"]')
# Parse JSON string to list
import json
allowed_origins = json.loads(cors_origins) if isinstance(cors_origins, str) else cors_origins

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)


class GenerateRequest(BaseModel):
    """Request model for component generation"""
    spec: str


@app.get("/api/airflow/component-generator/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "airflow-component-generator",
        "version": __version__,
        "model": os.getenv("CLAUDE_MODEL", "claude-sonnet-4-20250514")
    }


@app.post("/api/airflow/component-generator/generate")
async def generate_component_endpoint(request: GenerateRequest):
    """
    Generate custom Airflow component from YAML specification

    Request body:
    {
        "spec": "<YAML specification string>"
    }

    Response:
    {
        "code": "<Generated Python code>",
        "documentation": "<Component usage documentation>",
        "tests": "<Generated pytest tests>"
    }
    """
    if not generator:
        raise HTTPException(status_code=503, detail="Generator not initialized")

    try:
        # Parse YAML specification
        logger.info("Parsing component specification from YAML")
        spec_dict = yaml.safe_load(request.spec)

        # Determine component type and create appropriate spec
        component_type = spec_dict.get('component_type', 'operator')

        if component_type == 'sensor':
            spec = SensorSpec(**spec_dict)
        elif component_type == 'hook':
            spec = HookSpec(**spec_dict)
        else:
            spec = OperatorSpec(**spec_dict)

        logger.info("Generating Airflow component", component_name=spec.name, component_type=component_type)
        result = await generator.generate(spec)

        logger.info(
            "Component generated successfully",
            component_name=spec.name,
            component_type=component_type,
            code_size=len(result.code),
            is_valid=result.validation.is_valid()
        )

        # Return response
        return {
            "code": result.code,
            "documentation": result.documentation,
            "tests": result.tests,
            "test_dag": result.test_dag
        }

    except yaml.YAMLError as e:
        logger.error("YAML parsing failed", error=str(e))
        raise HTTPException(status_code=400, detail=f"Invalid YAML: {str(e)}")
    except Exception as e:
        logger.error("Component generation failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/airflow/component-generator/generate/sample")
async def generate_sample_component_endpoint():
    """
    Generate a sample Airflow operator using built-in specification

    No request body required. Uses a pre-defined sample specification
    to demonstrate the component generation capabilities.

    Response:
    {
        "code": "<Generated Python code>",
        "documentation": "<Component usage documentation>",
        "tests": "<Generated pytest tests>"
    }
    """
    if not generator:
        raise HTTPException(status_code=503, detail="Generator not initialized")

    try:
        # Load sample specification from file (Simplified NeMo Question Answering component)
        sample_spec_path = os.path.join(
            os.path.dirname(__file__),
            "..",
            "..",
            "component_spec_simple.yaml"
        )

        if not os.path.exists(sample_spec_path):
            # Create sample spec if it doesn't exist
            sample_spec_yaml = """name: SampleHttpOperator
display_name: "Sample HTTP Operator"
description: "Make HTTP GET requests to external APIs and return JSON responses"
category: http
component_type: operator
platforms:
  - airflow

requirements:
  - "Send HTTP GET requests to specified endpoints"
  - "Parse and return JSON responses"
  - "Support custom headers"
  - "Handle connection timeouts"

inputs:
  - name: endpoint
    type: str
    description: "HTTP endpoint URL"
    required: true
    template_field: true

  - name: headers
    type: Dict[str, str]
    description: "Custom HTTP headers"
    required: false
    default: "{}"

config_params:
  - name: http_conn_id
    type: str
    description: "Airflow connection ID for HTTP"
    default: "http_default"

  - name: timeout
    type: int
    description: "Request timeout in seconds"
    default: "30"

runtime_params: []

dependencies:
  - "apache-airflow-providers-http>=4.0.0"

base_class: "BaseOperator"
template_fields: ["endpoint"]
ui_color: "#f4a460"
ui_fgcolor: "#000"

author: "Airflow Component Factory"
version: "1.0.0"
"""
        else:
            with open(sample_spec_path, "r") as f:
                sample_spec_yaml = f.read()

        logger.info("Generating sample operator from built-in specification")
        spec_dict = yaml.safe_load(sample_spec_yaml)

        # Create OperatorSpec
        spec = OperatorSpec(**spec_dict)

        logger.info("Generating sample Airflow operator", component_name=spec.name)
        result = await generator.generate(spec)

        logger.info(
            "Sample operator generated successfully",
            component_name=spec.name,
            code_size=len(result.code),
            is_valid=result.validation.is_valid()
        )

        # Return response
        return {
            "code": result.code,
            "documentation": result.documentation,
            "tests": result.tests
        }

    except yaml.YAMLError as e:
        logger.error("Sample YAML parsing failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Invalid sample YAML: {str(e)}")
    except Exception as e:
        logger.error("Sample component generation failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/airflow/component-generator/assess")
async def assess_feasibility_endpoint(request: GenerateRequest):
    """
    Assess feasibility of generating an Airflow component before attempting generation

    Request body:
    {
        "spec": "<YAML specification string>"
    }

    Returns feasibility analysis including:
    - Whether generation is feasible
    - Confidence level (high/medium/low/blocked)
    - Complexity assessment
    - Issues found
    - Suggestions for improvement
    - Missing information needed
    - Number of similar patterns found (if RAG enabled)
    """
    if not feasibility_checker or not generator:
        raise HTTPException(status_code=503, detail="Services not initialized")

    try:
        # Parse YAML specification
        logger.info("Parsing component specification from YAML for assessment")
        spec_dict = yaml.safe_load(request.spec)

        # Try to retrieve similar patterns
        similar_patterns_count = 0
        if generator.rag_service_url:
            try:
                import httpx
                async with httpx.AsyncClient(timeout=5.0) as client:
                    response = await client.post(
                        f"{generator.rag_service_url}/api/airflow/patterns/similar",
                        json={
                            "description": spec_dict.get("description", ""),
                            "category": spec_dict.get("category", ""),
                            "n_results": 3
                        }
                    )
                    if response.status_code == 200:
                        data = response.json()
                        similar_patterns_count = data.get("results_count", 0)
            except Exception as e:
                logger.warning("Failed to retrieve patterns for assessment", error=str(e))

        # Assess feasibility
        assessment = feasibility_checker.assess_feasibility(
            spec_dict,
            similar_patterns_count=similar_patterns_count
        )

        logger.info(
            "Feasibility assessment complete",
            feasible=assessment["feasible"],
            confidence=assessment["confidence"],
            complexity=assessment["complexity"]
        )

        return assessment

    except yaml.YAMLError as e:
        logger.error("YAML parsing failed", error=str(e))
        raise HTTPException(status_code=400, detail=f"Invalid YAML: {str(e)}")
    except Exception as e:
        logger.error("Feasibility assessment failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/airflow/component-generator/analytics/metrics")
async def get_metrics():
    """Get overall generation metrics"""
    if not generator:
        raise HTTPException(status_code=503, detail="Generator not initialized")

    try:
        metrics = generator.learning_db.get_overall_metrics()
        return metrics
    except Exception as e:
        logger.error("Failed to get metrics", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/airflow/component-generator/analytics/insights")
async def get_insights():
    """Get category insights"""
    if not generator:
        raise HTTPException(status_code=503, detail="Generator not initialized")

    try:
        category_insights = generator.learning_db.get_category_insights()
        type_insights = generator.learning_db.get_type_insights()

        return {
            "category_insights": category_insights,
            "type_insights": type_insights
        }
    except Exception as e:
        logger.error("Failed to get insights", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/airflow/component-generator/analytics/trends")
async def get_trends(days: int = 7):
    """Get performance trends over time"""
    if not generator:
        raise HTTPException(status_code=503, detail="Generator not initialized")

    try:
        trends = generator.learning_db.get_trends(days=days)
        return trends
    except Exception as e:
        logger.error("Failed to get trends", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/airflow/component-generator/analytics/errors")
async def get_error_analytics():
    """Get error analytics"""
    if not generator:
        raise HTTPException(status_code=503, detail="Generator not initialized")

    try:
        error_analytics = generator.error_tracker.get_analytics()
        return error_analytics
    except Exception as e:
        logger.error("Failed to get error analytics", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


# Phase 5: Continuous Learning Endpoints

@app.get("/api/airflow/component-generator/analytics/learning")
async def get_learning_statistics():
    """
    Get Phase 5 continuous learning statistics

    Returns overall learning statistics including:
    - Total generations tracked
    - Success rate
    - Patterns tracked with average confidence
    - Strategies tracked
    - Pending improvement suggestions
    - Categories covered
    """
    if not generator:
        raise HTTPException(status_code=503, detail="Generator not initialized")

    try:
        stats = generator.continuous_learning.get_statistics()
        return {
            "status": "success",
            "learning_statistics": stats
        }
    except Exception as e:
        logger.error("Failed to get learning statistics", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/airflow/component-generator/analytics/learning/metrics")
async def get_learning_metrics(category: str = None):
    """
    Get learning metrics by category

    Query params:
    - category (optional): Filter by category

    Returns metrics for each category including:
    - Total/successful/failed generations
    - Average attempts, tokens, time
    - First-attempt success rate
    - Pattern match rate
    - Error reduction rate
    """
    if not generator:
        raise HTTPException(status_code=503, detail="Generator not initialized")

    try:
        metrics = generator.continuous_learning.get_learning_metrics(category=category)
        return {
            "status": "success",
            "metrics": [
                {
                    "category": m.category,
                    "total_generations": m.total_generations,
                    "successful_generations": m.successful_generations,
                    "failed_generations": m.failed_generations,
                    "avg_attempts": round(m.avg_attempts, 2),
                    "avg_tokens": m.avg_tokens,
                    "avg_time_seconds": round(m.avg_time_seconds, 2),
                    "first_attempt_success_rate": round(m.first_attempt_success_rate * 100, 1),
                    "pattern_match_rate": round(m.pattern_match_rate * 100, 1),
                    "error_reduction_rate": round(m.error_reduction_rate * 100, 1),
                    "last_updated": m.last_updated
                }
                for m in metrics
            ]
        }
    except Exception as e:
        logger.error("Failed to get learning metrics", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/airflow/component-generator/analytics/suggestions")
async def get_improvement_suggestions(category: str = None, status: str = "pending"):
    """
    Get improvement suggestions from the continuous learning system

    Query params:
    - category (optional): Filter by category
    - status: Filter by status (pending, in_progress, resolved). Default: pending

    Returns suggestions for improving the generator based on:
    - Recurring error patterns
    - Low success rate categories
    - Pattern validation issues
    """
    if not generator:
        raise HTTPException(status_code=503, detail="Generator not initialized")

    try:
        suggestions = generator.continuous_learning.get_improvement_suggestions(
            category=category,
            status=status
        )
        return {
            "status": "success",
            "count": len(suggestions),
            "suggestions": suggestions
        }
    except Exception as e:
        logger.error("Failed to get suggestions", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/airflow/component-generator/analytics/strategies")
async def get_strategy_effectiveness(error_type: str = None):
    """
    Get fix strategy effectiveness data

    Query params:
    - error_type (optional): Filter by error type

    Returns effectiveness data for fix strategies including:
    - Strategy name and error type
    - Effectiveness score
    - Usage count, success/failure counts
    - Average attempts to fix
    """
    if not generator:
        raise HTTPException(status_code=503, detail="Generator not initialized")

    try:
        strategies = generator.continuous_learning.get_strategy_effectiveness(
            error_type=error_type
        )
        return {
            "status": "success",
            "count": len(strategies),
            "strategies": strategies
        }
    except Exception as e:
        logger.error("Failed to get strategy effectiveness", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/airflow/component-generator/analytics/learning/decay")
async def trigger_confidence_decay():
    """
    Manually trigger confidence decay for patterns

    Applies time-based confidence decay to patterns that haven't
    been used recently, encouraging the system to try newer patterns.

    Returns counts of patterns decayed, flagged for review, and removed.
    """
    if not generator:
        raise HTTPException(status_code=503, detail="Generator not initialized")

    try:
        result = generator.continuous_learning.apply_confidence_decay()
        return {
            "status": "success",
            "result": result
        }
    except Exception as e:
        logger.error("Failed to apply confidence decay", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/airflow/component-generator/analytics/learning/validate")
async def trigger_pattern_validation():
    """
    Manually trigger pattern validation

    Validates stored patterns and flags problematic ones based on
    success rate and confidence score.

    Returns validation results with recommendations.
    """
    if not generator:
        raise HTTPException(status_code=503, detail="Generator not initialized")

    try:
        result = generator.continuous_learning.validate_patterns()
        return {
            "status": "success",
            "result": result
        }
    except Exception as e:
        logger.error("Failed to validate patterns", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/airflow/component-generator/analytics/learning/tasks")
async def run_scheduled_tasks():
    """
    Manually run scheduled maintenance tasks

    Executes any due scheduled tasks including:
    - confidence_decay (daily)
    - pattern_validation (weekly)
    - metrics_aggregation (hourly)
    - suggestion_generation (daily)
    - cleanup_old_data (monthly)

    Returns results for each task executed.
    """
    if not generator:
        raise HTTPException(status_code=503, detail="Generator not initialized")

    try:
        result = generator.continuous_learning.run_scheduled_tasks()
        return {
            "status": "success",
            "tasks_executed": len(result),
            "results": result
        }
    except Exception as e:
        logger.error("Failed to run scheduled tasks", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


# Phase 6: Production Optimization Endpoints

@app.get("/api/airflow/component-generator/dashboard")
async def get_dashboard():
    """
    Get comprehensive dashboard data for monitoring.

    Returns aggregated data including:
    - System health status
    - Performance metrics
    - Cache statistics
    - Rate limiting stats
    - Active alerts
    """
    if not generator:
        raise HTTPException(status_code=503, detail="Generator not initialized")

    try:
        dashboard_data = generator.optimizer.get_dashboard()
        return {
            "status": "success",
            "dashboard": dashboard_data
        }
    except Exception as e:
        logger.error("Failed to get dashboard data", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/airflow/component-generator/health/detailed")
async def get_detailed_health():
    """
    Get detailed health status with component checks.

    Returns:
    - Overall health status (healthy/degraded)
    - Individual component status
    - Active alerts with details
    - System resource usage
    """
    if not generator:
        raise HTTPException(status_code=503, detail="Generator not initialized")

    try:
        health = generator.optimizer.get_health()
        return {
            "status": health.status,
            "healthy": health.healthy,
            "components": health.components,
            "alerts": health.alerts,
            "metrics": health.metrics,
            "last_check": health.last_check
        }
    except Exception as e:
        logger.error("Failed to get health status", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/airflow/component-generator/optimizer/stats")
async def get_optimizer_statistics():
    """
    Get production optimizer statistics.

    Returns comprehensive stats including:
    - Cache hit/miss rates
    - Rate limiter stats
    - Performance metrics
    - Current health status
    """
    if not generator:
        raise HTTPException(status_code=503, detail="Generator not initialized")

    try:
        stats = generator.optimizer.get_statistics()
        return {
            "status": "success",
            "optimizer_statistics": stats
        }
    except Exception as e:
        logger.error("Failed to get optimizer stats", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/airflow/component-generator/cache/invalidate")
async def invalidate_cache(category: str = None):
    """
    Invalidate cached patterns.

    Query params:
    - category (optional): If provided, invalidates only that category.
                          If not provided, clears entire cache.

    Returns count of entries cleared.
    """
    if not generator:
        raise HTTPException(status_code=503, detail="Generator not initialized")

    try:
        cleared = generator.optimizer.invalidate_cache(category=category)
        return {
            "status": "success",
            "entries_cleared": cleared,
            "category": category or "all"
        }
    except Exception as e:
        logger.error("Failed to invalidate cache", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/airflow/component-generator/performance")
async def get_performance_metrics():
    """
    Get real-time performance metrics.

    Returns:
    - Total generations count
    - Success/failure rates
    - Average generation time
    - Token usage stats
    - Cost tracking
    - Throughput (generations/hour)
    """
    if not generator:
        raise HTTPException(status_code=503, detail="Generator not initialized")

    try:
        metrics = generator.optimizer.metrics.get_metrics()
        return {
            "status": "success",
            "performance": {
                "total_generations": metrics["total_generations"],
                "successful": metrics["successful_generations"],
                "failed": metrics["failed_generations"],
                "success_rate_percent": round(metrics["success_rate"] * 100, 1),
                "avg_generation_time_seconds": round(metrics["avg_generation_time"], 2),
                "avg_tokens_per_generation": int(metrics["avg_tokens"]),
                "avg_retries": round(metrics["avg_retries"], 2),
                "total_cost_usd": round(metrics["total_cost_usd"], 4),
                "uptime_hours": round(metrics["uptime_seconds"] / 3600, 2),
                "throughput_per_hour": round(metrics["generations_per_hour"], 1)
            }
        }
    except Exception as e:
        logger.error("Failed to get performance metrics", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


# Run with uvicorn
if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "8095"))
    uvicorn.run(app, host="0.0.0.0", port=port)
