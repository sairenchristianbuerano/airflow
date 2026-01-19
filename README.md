# Airflow Component Factory

Backend services for generating and managing custom Apache Airflow components (operators, sensors, hooks).

**Version:** 0.1.0
**Platform:** Apache Airflow 2.0+
**Python:** 3.11+

---

## 📋 Overview

This repository contains two microservices for Apache Airflow component generation:

1. **Component Generator** (Port 8095) - Generates custom Airflow operators, sensors, and hooks from YAML specifications using Claude AI
2. **Component Index** (Port 8096) - Tracks and manages generated components with semantic pattern search (RAG)

The Component Index provides both component registry functionality and semantic search over Airflow component patterns to help generate better, more consistent code.

---

## 🚀 Quick Start - Docker

### Prerequisites

- Docker & Docker Compose
- Anthropic API key (for Claude)

### 1. Set Environment Variables

Create a `.env` file:

```bash
# Required: Claude API key for code generation
ANTHROPIC_API_KEY=your_api_key_here

# Optional: Claude model selection (default shown)
CLAUDE_MODEL=claude-sonnet-4-20250514
```

### 2. Start Services

```bash
# Build and start both services
docker-compose up -d

# Check logs
docker-compose logs -f

# Verify services are healthy
curl http://localhost:8095/api/airflow/component-generator/health
curl http://localhost:8096/api/airflow/component-index/health
```

---

## 📡 API Endpoints

### Component Generator (Port 8095)

```bash
# Health check
GET /api/airflow/component-generator/health

# Generate component from YAML spec
POST /api/airflow/component-generator/generate

# Generate sample operator
POST /api/airflow/component-generator/generate/sample

# Assess feasibility
POST /api/airflow/component-generator/assess

# Analytics
GET /api/airflow/component-generator/analytics/metrics
GET /api/airflow/component-generator/analytics/insights
GET /api/airflow/component-generator/analytics/trends?days=7
GET /api/airflow/component-generator/analytics/errors
```

---

## 📝 YAML Specification Format

### Operator Example

```yaml
name: CustomHttpOperator
display_name: "Custom HTTP Operator"
description: "Make HTTP requests with custom configuration"
category: http
component_type: operator

inputs:
  - name: endpoint
    type: str
    description: "API endpoint URL"
    required: true
    template_field: true

dependencies:
  - "apache-airflow-providers-http>=4.0.0"

base_class: "BaseOperator"
template_fields: ["endpoint"]
ui_color: "#f4a460"
```

See [component-generator/sample_operator_spec.yaml](component-generator/sample_operator_spec.yaml) for complete example.

---

## 🎯 Features

- ✅ **AI-Powered Generation**: Claude Sonnet 4.5
- ✅ **Multi-Component Support**: Operators, Sensors, Hooks
- ✅ **AST Validation**: Code correctness & security
- ✅ **Dependency Management**: 30+ Airflow providers
- ✅ **Auto-Documentation**: Comprehensive Markdown docs
- ✅ **Test Generation**: Pytest test files
- ✅ **Error Learning**: Continuous improvement
- ✅ **Metrics Tracking**: SQLite analytics

---

## 📊 Generated Output

For each component:

1. **Python Code**: Production-ready Airflow component
2. **Documentation**: Markdown with examples & guides
3. **Tests**: Pytest test file

---

## 📈 Progress

**Status:** Phase 1 Complete ✅

See [PROGRESS.md](PROGRESS.md) for details.

---

## 📄 License

Apache 2.0

---

🚀 *Make Airflow component development effortless with AI!*