"""
Dependency validator for Airflow components.

Validates that required Airflow provider packages and dependencies are available
and provides recommendations for unsupported packages.
"""

from typing import Dict, List, Tuple, Any
import structlog

logger = structlog.get_logger()


# Airflow provider packages mapping (from official Apache Airflow repository)
# Maps dependency keywords to official provider packages
# Source: ~/Desktop/sairen-files/github/env/airflow/providers/
AIRFLOW_PROVIDERS = {
    # Cloud Providers - AWS
    "amazon": {
        "package": "apache-airflow-providers-amazon",
        "description": "Amazon Web Services (AWS) integration",
        "services": ["s3", "ec2", "emr", "redshift", "sagemaker", "lambda", "ecs", "glue", "athena", "dynamodb"]
    },
    "aws": {
        "package": "apache-airflow-providers-amazon",
        "description": "Amazon Web Services (AWS) integration (alias)",
        "services": ["s3", "ec2", "emr", "redshift", "sagemaker", "lambda", "ecs"]
    },

    # Cloud Providers - Google
    "google": {
        "package": "apache-airflow-providers-google",
        "description": "Google Cloud Platform (GCP) integration",
        "services": ["gcs", "bigquery", "dataflow", "compute", "cloud-sql", "dataproc", "cloud-functions"]
    },
    "gcp": {
        "package": "apache-airflow-providers-google",
        "description": "Google Cloud Platform (GCP) integration (alias)",
        "services": ["gcs", "bigquery", "dataflow"]
    },

    # Cloud Providers - Azure
    "azure": {
        "package": "apache-airflow-providers-microsoft-azure",
        "description": "Microsoft Azure integration",
        "services": ["blob", "datalake", "cosmosdb", "azureml", "synapse", "datafactory"]
    },
    "microsoft": {
        "package": "apache-airflow-providers-microsoft-azure",
        "description": "Microsoft Azure integration (alias)",
        "services": ["blob", "datalake", "cosmosdb"]
    },

    # Cloud Providers - Alibaba
    "alibaba": {
        "package": "apache-airflow-providers-alibaba",
        "description": "Alibaba Cloud integration"
    },

    # Databases - SQL
    "postgres": {
        "package": "apache-airflow-providers-postgres",
        "description": "PostgreSQL database integration"
    },
    "postgresql": {
        "package": "apache-airflow-providers-postgres",
        "description": "PostgreSQL database integration (alias)"
    },
    "mysql": {
        "package": "apache-airflow-providers-mysql",
        "description": "MySQL database integration"
    },
    "sqlite": {
        "package": "apache-airflow-providers-sqlite",
        "description": "SQLite database integration"
    },
    "oracle": {
        "package": "apache-airflow-providers-oracle",
        "description": "Oracle database integration"
    },
    "mssql": {
        "package": "apache-airflow-providers-microsoft-mssql",
        "description": "Microsoft SQL Server integration"
    },
    "teradata": {
        "package": "apache-airflow-providers-teradata",
        "description": "Teradata database integration"
    },
    "vertica": {
        "package": "apache-airflow-providers-vertica",
        "description": "Vertica database integration"
    },
    "presto": {
        "package": "apache-airflow-providers-presto",
        "description": "Presto database integration"
    },
    "trino": {
        "package": "apache-airflow-providers-trino",
        "description": "Trino database integration"
    },
    "exasol": {
        "package": "apache-airflow-providers-exasol",
        "description": "Exasol database integration"
    },

    # Databases - NoSQL
    "mongodb": {
        "package": "apache-airflow-providers-mongo",
        "description": "MongoDB database integration"
    },
    "mongo": {
        "package": "apache-airflow-providers-mongo",
        "description": "MongoDB database integration (alias)"
    },
    "redis": {
        "package": "apache-airflow-providers-redis",
        "description": "Redis database integration"
    },
    "elasticsearch": {
        "package": "apache-airflow-providers-elasticsearch",
        "description": "Elasticsearch integration"
    },
    "opensearch": {
        "package": "apache-airflow-providers-opensearch",
        "description": "OpenSearch integration"
    },
    "cassandra": {
        "package": "apache-airflow-providers-apache-cassandra",
        "description": "Apache Cassandra integration"
    },
    "neo4j": {
        "package": "apache-airflow-providers-neo4j",
        "description": "Neo4j graph database integration"
    },
    "arangodb": {
        "package": "apache-airflow-providers-arangodb",
        "description": "ArangoDB integration"
    },
    "couchbase": {
        "package": "apache-airflow-providers-couchbase",
        "description": "Couchbase integration"
    },
    "influxdb": {
        "package": "apache-airflow-providers-influxdb",
        "description": "InfluxDB time-series database"
    },

    # Vector Databases & AI
    "pinecone": {
        "package": "apache-airflow-providers-pinecone",
        "description": "Pinecone vector database"
    },
    "weaviate": {
        "package": "apache-airflow-providers-weaviate",
        "description": "Weaviate vector database"
    },
    "qdrant": {
        "package": "apache-airflow-providers-qdrant",
        "description": "Qdrant vector database"
    },
    "pgvector": {
        "package": "apache-airflow-providers-pgvector",
        "description": "PostgreSQL with pgvector extension"
    },
    "openai": {
        "package": "apache-airflow-providers-openai",
        "description": "OpenAI API integration"
    },
    "cohere": {
        "package": "apache-airflow-providers-cohere",
        "description": "Cohere AI integration"
    },

    # HTTP & APIs
    "http": {
        "package": "apache-airflow-providers-http",
        "description": "HTTP/REST API integration"
    },
    "grpc": {
        "package": "apache-airflow-providers-grpc",
        "description": "gRPC integration"
    },
    "jdbc": {
        "package": "apache-airflow-providers-jdbc",
        "description": "JDBC integration"
    },
    "odbc": {
        "package": "apache-airflow-providers-odbc",
        "description": "ODBC integration"
    },
    "imap": {
        "package": "apache-airflow-providers-imap",
        "description": "IMAP email integration"
    },
    "smtp": {
        "package": "apache-airflow-providers-smtp",
        "description": "SMTP email integration"
    },

    # Communication & Notifications
    "slack": {
        "package": "apache-airflow-providers-slack",
        "description": "Slack integration"
    },
    "telegram": {
        "package": "apache-airflow-providers-telegram",
        "description": "Telegram integration"
    },
    "discord": {
        "package": "apache-airflow-providers-discord",
        "description": "Discord integration"
    },
    "opsgenie": {
        "package": "apache-airflow-providers-opsgenie",
        "description": "Opsgenie incident management"
    },
    "pagerduty": {
        "package": "apache-airflow-providers-pagerduty",
        "description": "PagerDuty integration"
    },
    "sendgrid": {
        "package": "apache-airflow-providers-sendgrid",
        "description": "SendGrid email service"
    },
    "apprise": {
        "package": "apache-airflow-providers-apprise",
        "description": "Apprise notification service"
    },

    # Version Control & CI/CD
    "github": {
        "package": "apache-airflow-providers-github",
        "description": "GitHub integration"
    },
    "git": {
        "package": "apache-airflow-providers-git",
        "description": "Git integration"
    },
    "jenkins": {
        "package": "apache-airflow-providers-jenkins",
        "description": "Jenkins CI/CD integration"
    },

    # Data Processing & Analytics
    "spark": {
        "package": "apache-airflow-providers-apache-spark",
        "description": "Apache Spark integration"
    },
    "kafka": {
        "package": "apache-airflow-providers-apache-kafka",
        "description": "Apache Kafka integration"
    },
    "flink": {
        "package": "apache-airflow-providers-apache-flink",
        "description": "Apache Flink integration"
    },
    "databricks": {
        "package": "apache-airflow-providers-databricks",
        "description": "Databricks integration"
    },
    "snowflake": {
        "package": "apache-airflow-providers-snowflake",
        "description": "Snowflake data warehouse"
    },
    "dbt": {
        "package": "apache-airflow-providers-dbt",
        "description": "dbt (data build tool) integration"
    },
    "tableau": {
        "package": "apache-airflow-providers-tableau",
        "description": "Tableau integration"
    },

    # Container & Orchestration
    "docker": {
        "package": "apache-airflow-providers-docker",
        "description": "Docker integration"
    },
    "kubernetes": {
        "package": "apache-airflow-providers-cncf-kubernetes",
        "description": "Kubernetes integration"
    },
    "celery": {
        "package": "apache-airflow-providers-celery",
        "description": "Celery executor integration"
    },
    "singularity": {
        "package": "apache-airflow-providers-singularity",
        "description": "Singularity container integration"
    },

    # File Transfer & Storage
    "ftp": {
        "package": "apache-airflow-providers-ftp",
        "description": "FTP integration"
    },
    "sftp": {
        "package": "apache-airflow-providers-sftp",
        "description": "SFTP integration"
    },
    "ssh": {
        "package": "apache-airflow-providers-ssh",
        "description": "SSH integration"
    },
    "samba": {
        "package": "apache-airflow-providers-samba",
        "description": "Samba/SMB integration"
    },

    # Data Quality & Observability
    "datadog": {
        "package": "apache-airflow-providers-datadog",
        "description": "Datadog monitoring"
    },
    "openlineage": {
        "package": "apache-airflow-providers-openlineage",
        "description": "OpenLineage data lineage"
    },

    # Business Tools
    "salesforce": {
        "package": "apache-airflow-providers-salesforce",
        "description": "Salesforce CRM integration"
    },
    "segment": {
        "package": "apache-airflow-providers-segment",
        "description": "Segment analytics"
    },
    "zendesk": {
        "package": "apache-airflow-providers-zendesk",
        "description": "Zendesk support integration"
    },
    "asana": {
        "package": "apache-airflow-providers-asana",
        "description": "Asana project management"
    },
    "atlassian": {
        "package": "apache-airflow-providers-atlassian",
        "description": "Atlassian (Jira, Confluence)"
    },

    # Other Services
    "airbyte": {
        "package": "apache-airflow-providers-airbyte",
        "description": "Airbyte ELT integration"
    },
    "hashicorp": {
        "package": "apache-airflow-providers-hashicorp",
        "description": "HashiCorp Vault integration"
    },
    "papermill": {
        "package": "apache-airflow-providers-papermill",
        "description": "Papermill Jupyter notebook execution"
    },
    "yandex": {
        "package": "apache-airflow-providers-yandex",
        "description": "Yandex Cloud integration"
    },
    "ydb": {
        "package": "apache-airflow-providers-ydb",
        "description": "Yandex Database integration"
    },
    "openfaas": {
        "package": "apache-airflow-providers-openfaas",
        "description": "OpenFaaS serverless functions"
    },
    "edge3": {
        "package": "apache-airflow-providers-edge3",
        "description": "Edge computing integration"
    },
    "keycloak": {
        "package": "apache-airflow-providers-keycloak",
        "description": "Keycloak authentication"
    },
    "facebook": {
        "package": "apache-airflow-providers-facebook",
        "description": "Facebook Ads integration"
    },
    "dingding": {
        "package": "apache-airflow-providers-dingding",
        "description": "DingTalk integration"
    },
    "cloudant": {
        "package": "apache-airflow-providers-cloudant",
        "description": "IBM Cloudant integration"
    },

    # Standard Providers (pre-installed with Airflow core)
    "common-compat": {
        "package": "apache-airflow-providers-common-compat",
        "description": "Common compatibility utilities (pre-installed)"
    },
    "common-io": {
        "package": "apache-airflow-providers-common-io",
        "description": "Common I/O utilities (pre-installed)"
    },
    "common-sql": {
        "package": "apache-airflow-providers-common-sql",
        "description": "Common SQL utilities (pre-installed)"
    },
    "standard": {
        "package": "apache-airflow-providers-standard",
        "description": "Standard operators and sensors (pre-installed)"
    },
}


# Common Python packages supported by Airflow (from official airflow-core dependencies)
# Source: ~/Desktop/sairen-files/github/env/airflow/airflow-core/pyproject.toml
COMMON_PACKAGES = {
    # HTTP & Network
    "requests": {"description": "HTTP library (>=2.32.0)", "min_version": "2.32.0", "alternative": None},
    "httpx": {"description": "Modern HTTP client (>=0.25.0)", "min_version": "0.25.0", "alternative": None},
    "aiohttp": {"description": "Async HTTP client (>=3.12.14)", "min_version": "3.12.14", "alternative": None},
    "requests-toolbelt": {"description": "Requests utilities (>=1.0.0)", "min_version": "1.0.0", "alternative": None},
    "asgiref": {"description": "ASGI utilities (>=2.3.0)", "min_version": "2.3.0", "alternative": None},

    # Data Processing
    "pandas": {"description": "Data manipulation (>=2.1.2)", "min_version": "2.1.2", "alternative": None},
    "numpy": {"description": "Numerical computing", "min_version": None, "alternative": None},

    # Serialization & Parsing
    "json": {"description": "JSON handling (stdlib)", "min_version": None, "alternative": None},
    "pyyaml": {"description": "YAML parsing (>=6.0.3)", "min_version": "6.0.3", "alternative": None},
    "yaml": {"description": "YAML handling", "min_version": None, "alternative": "pyyaml"},
    "msgspec": {"description": "Fast serialization (>=0.19.0)", "min_version": "0.19.0", "alternative": None},
    "jsonschema": {"description": "JSON schema validation (>=4.19.1)", "min_version": "4.19.1", "alternative": None},

    # Templating
    "jinja2": {"description": "Templating (>=3.1.5)", "min_version": "3.1.5", "alternative": None},

    # Date & Time
    "python-dateutil": {"description": "Date utilities (>=2.7.0)", "min_version": "2.7.0", "alternative": None},
    "pendulum": {"description": "DateTime library (>=3.1.0)", "min_version": "3.1.0", "alternative": None},

    # Database & SQL
    "sqlalchemy": {"description": "SQL toolkit (>=2.0.36)", "min_version": "2.0.36", "alternative": None},
    "sqlalchemy-jsonfield": {"description": "JSON field support (>=1.0)", "min_version": "1.0", "alternative": None},
    "psycopg2-binary": {"description": "PostgreSQL adapter (>=2.9.9)", "min_version": "2.9.9", "alternative": None},
    "asyncpg": {"description": "Async PostgreSQL (>=0.30.0)", "min_version": "0.30.0", "alternative": None},

    # Cloud SDKs
    "boto3": {"description": "AWS SDK", "min_version": None, "alternative": None},
    "google-cloud-storage": {"description": "GCS client", "min_version": None, "alternative": None},
    "azure-storage-blob": {"description": "Azure Blob client", "min_version": None, "alternative": None},

    # Validation & Type Checking
    "pydantic": {"description": "Data validation (>=2.11.0)", "min_version": "2.11.0", "alternative": None},
    "attrs": {"description": "Classes without boilerplate (>=22.1.0)", "min_version": "22.1.0", "alternative": None},
    "typing-extensions": {"description": "Type hints backport (>=4.14.1)", "min_version": "4.14.1", "alternative": None},

    # Logging & Monitoring
    "structlog": {"description": "Structured logging (>=25.4.0)", "min_version": "25.4.0", "alternative": None},
    "colorlog": {"description": "Colored logging (>=6.8.2)", "min_version": "6.8.2", "alternative": None},
    "opentelemetry-api": {"description": "OpenTelemetry API (>=1.27.0)", "min_version": "1.27.0", "alternative": None},

    # Security
    "cryptography": {"description": "Cryptographic recipes (>=41.0.0)", "min_version": "41.0.0", "alternative": None},
    "pyjwt": {"description": "JSON Web Tokens (>=2.10.0)", "min_version": "2.10.0", "alternative": None},

    # Utilities
    "packaging": {"description": "Package metadata (>=25.0)", "min_version": "25.0", "alternative": None},
    "pathspec": {"description": "Path pattern matching (>=0.9.0)", "min_version": "0.9.0", "alternative": None},
    "python-slugify": {"description": "Slugify strings (>=5.0)", "min_version": "5.0", "alternative": None},
    "tabulate": {"description": "Pretty-print tables (>=0.9.0)", "min_version": "0.9.0", "alternative": None},
    "tenacity": {"description": "Retry library (>=8.3.0)", "min_version": "8.3.0", "alternative": None},
    "dill": {"description": "Extended pickling (>=0.2.2)", "min_version": "0.2.2", "alternative": None},
    "psutil": {"description": "System utilities (>=5.8.0)", "min_version": "5.8.0", "alternative": None},
    "argcomplete": {"description": "Shell completion (>=1.10)", "min_version": "1.10", "alternative": None},
    "cron-descriptor": {"description": "Cron expression descriptions (>=1.2.24)", "min_version": "1.2.24", "alternative": None},
    "croniter": {"description": "Cron iteration (>=2.0.2)", "min_version": "2.0.2", "alternative": None},
    "natsort": {"description": "Natural sorting (>=8.4.0)", "min_version": "8.4.0", "alternative": None},

    # FastAPI & Web
    "fastapi": {"description": "Web framework (>=0.128.0)", "min_version": "0.128.0", "alternative": None},
    "uvicorn": {"description": "ASGI server (>=0.37.0)", "min_version": "0.37.0", "alternative": None},
    "starlette": {"description": "ASGI toolkit (>=0.45.0)", "min_version": "0.45.0", "alternative": None},

    # Standard Library (always available)
    "os": {"description": "Operating system interface (stdlib)", "min_version": None, "alternative": None},
    "sys": {"description": "System parameters (stdlib)", "min_version": None, "alternative": None},
    "logging": {"description": "Logging facility (stdlib)", "min_version": None, "alternative": None},
    "pathlib": {"description": "Path handling (stdlib)", "min_version": None, "alternative": None},
    "datetime": {"description": "Date/time handling (stdlib)", "min_version": None, "alternative": None},
    "typing": {"description": "Type hints (stdlib)", "min_version": None, "alternative": None},
    "re": {"description": "Regular expressions (stdlib)", "min_version": None, "alternative": None},
    "io": {"description": "I/O operations (stdlib)", "min_version": None, "alternative": None},
    "collections": {"description": "Container datatypes (stdlib)", "min_version": None, "alternative": None},
    "functools": {"description": "Higher-order functions (stdlib)", "min_version": None, "alternative": None},
    "itertools": {"description": "Iterator functions (stdlib)", "min_version": None, "alternative": None},
    "contextlib": {"description": "Context managers (stdlib)", "min_version": None, "alternative": None},
    "abc": {"description": "Abstract base classes (stdlib)", "min_version": None, "alternative": None},
    "dataclasses": {"description": "Data classes (stdlib)", "min_version": None, "alternative": None},
    "enum": {"description": "Enumerations (stdlib)", "min_version": None, "alternative": None},
    "uuid": {"description": "UUID generation (stdlib)", "min_version": None, "alternative": None},
    "time": {"description": "Time access (stdlib)", "min_version": None, "alternative": None},
    "subprocess": {"description": "Subprocess management (stdlib)", "min_version": None, "alternative": None},
    "shutil": {"description": "File operations (stdlib)", "min_version": None, "alternative": None},
    "tempfile": {"description": "Temporary files (stdlib)", "min_version": None, "alternative": None},
    "base64": {"description": "Base64 encoding (stdlib)", "min_version": None, "alternative": None},
    "hashlib": {"description": "Hash functions (stdlib)", "min_version": None, "alternative": None},
    "hmac": {"description": "HMAC message authentication (stdlib)", "min_version": None, "alternative": None},
    "urllib": {"description": "URL handling (stdlib)", "min_version": None, "alternative": None},
}


class DependencyValidator:
    """Validates Airflow component dependencies"""

    def __init__(self):
        self.logger = logger.bind(component="dependency_validator")

    def validate_dependencies(self, dependencies: List[str]) -> Dict[str, Any]:
        """
        Validate list of dependencies for Airflow component

        Args:
            dependencies: List of dependency strings

        Returns:
            Dictionary with validation results and recommendations
        """
        results = {
            "valid": True,
            "airflow_providers": [],
            "common_packages": [],
            "unknown_packages": [],
            "warnings": [],
            "recommendations": []
        }

        for dep in dependencies:
            dep_lower = dep.lower().strip()

            # Check if it's an Airflow provider
            provider_found = False
            for key, info in AIRFLOW_PROVIDERS.items():
                if key in dep_lower or info["package"] in dep_lower:
                    results["airflow_providers"].append({
                        "dependency": dep,
                        "provider_package": info["package"],
                        "description": info["description"]
                    })
                    provider_found = True
                    break

            if provider_found:
                continue

            # Check if it's a common package
            common_found = False
            for package, info in COMMON_PACKAGES.items():
                if package in dep_lower:
                    results["common_packages"].append({
                        "dependency": dep,
                        "description": info["description"],
                        "min_version": info.get("min_version"),
                        "alternative": info.get("alternative")
                    })
                    common_found = True
                    break

            if common_found:
                continue

            # Unknown package - add warning
            results["unknown_packages"].append(dep)
            results["warnings"].append(
                f"Unknown package '{dep}' - may require manual installation"
            )

        # Generate recommendations
        if results["airflow_providers"]:
            provider_list = [p["provider_package"] for p in results["airflow_providers"]]
            results["recommendations"].append(
                f"Install provider packages: {', '.join(provider_list)}"
            )

        if results["unknown_packages"]:
            results["recommendations"].append(
                f"Verify these packages are available: {', '.join(results['unknown_packages'])}"
            )

        self.logger.info(
            "Dependencies validated",
            total=len(dependencies),
            providers=len(results["airflow_providers"]),
            common=len(results["common_packages"]),
            unknown=len(results["unknown_packages"])
        )

        return results

    def suggest_provider(self, category: str, keywords: List[str] = None) -> List[Dict[str, str]]:
        """
        Suggest Airflow providers based on category and keywords

        Args:
            category: Component category (http, database, cloud, etc.)
            keywords: Optional list of keywords to match

        Returns:
            List of suggested providers
        """
        suggestions = []

        category_lower = category.lower()

        # Direct category matches
        if category_lower in AIRFLOW_PROVIDERS:
            info = AIRFLOW_PROVIDERS[category_lower]
            suggestions.append({
                "provider": info["package"],
                "description": info["description"],
                "match_reason": f"Category match: {category}"
            })

        # Keyword matches
        if keywords:
            for keyword in keywords:
                keyword_lower = keyword.lower()
                for key, info in AIRFLOW_PROVIDERS.items():
                    if key in keyword_lower or keyword_lower in key:
                        if info["package"] not in [s["provider"] for s in suggestions]:
                            suggestions.append({
                                "provider": info["package"],
                                "description": info["description"],
                                "match_reason": f"Keyword match: {keyword}"
                            })

                    # Check services if available
                    if "services" in info:
                        for service in info["services"]:
                            if service in keyword_lower or keyword_lower in service:
                                if info["package"] not in [s["provider"] for s in suggestions]:
                                    suggestions.append({
                                        "provider": info["package"],
                                        "description": info["description"],
                                        "match_reason": f"Service match: {service}"
                                    })

        return suggestions

    def get_provider_info(self, provider_key: str) -> Dict[str, Any]:
        """
        Get detailed information about an Airflow provider

        Args:
            provider_key: Provider key (e.g., 'amazon', 'google')

        Returns:
            Provider information dictionary
        """
        return AIRFLOW_PROVIDERS.get(provider_key.lower(), {})

    def list_all_providers(self) -> List[Dict[str, str]]:
        """
        List all available Airflow providers

        Returns:
            List of all provider information
        """
        return [
            {
                "key": key,
                "package": info["package"],
                "description": info["description"],
                "services": info.get("services", [])
            }
            for key, info in AIRFLOW_PROVIDERS.items()
        ]


def get_validation_summary(validation_result: Dict[str, Any]) -> str:
    """
    Generate human-readable summary of dependency validation

    Args:
        validation_result: Result from DependencyValidator.validate_dependencies()

    Returns:
        Formatted summary string
    """
    summary_parts = []

    if validation_result["airflow_providers"]:
        summary_parts.append(
            f"Airflow Providers ({len(validation_result['airflow_providers'])}): " +
            ", ".join([p["provider_package"] for p in validation_result["airflow_providers"]])
        )

    if validation_result["common_packages"]:
        summary_parts.append(
            f"Common Packages ({len(validation_result['common_packages'])}): " +
            ", ".join([p["dependency"] for p in validation_result["common_packages"]])
        )

    if validation_result["unknown_packages"]:
        summary_parts.append(
            f"Unknown Packages ({len(validation_result['unknown_packages'])}): " +
            ", ".join(validation_result["unknown_packages"])
        )

    if validation_result["warnings"]:
        summary_parts.append(
            "Warnings: " + "; ".join(validation_result["warnings"])
        )

    return "\n".join(summary_parts) if summary_parts else "No dependencies specified"
