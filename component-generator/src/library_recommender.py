"""
Library Recommender - Phase 3

Provides intelligent recommendations for library alternatives,
native implementations, and best practices for Airflow compatibility.
"""

from typing import Dict, Any, List, Optional, Tuple
import structlog

logger = structlog.get_logger()


class LibraryRecommender:
    """Intelligent library recommendation system for Airflow components"""

    # Mapping of common libraries to their Airflow provider equivalents
    AIRFLOW_PROVIDER_MAPPINGS = {
        # HTTP/REST
        "requests": "apache-airflow-providers-http",
        "httpx": "apache-airflow-providers-http",
        "aiohttp": "apache-airflow-providers-http",

        # Databases
        "psycopg2": "apache-airflow-providers-postgres",
        "pymysql": "apache-airflow-providers-mysql",
        "mysql-connector-python": "apache-airflow-providers-mysql",
        "pymongo": "apache-airflow-providers-mongo",
        "snowflake-connector-python": "apache-airflow-providers-snowflake",
        "elasticsearch": "apache-airflow-providers-elasticsearch",

        # Cloud - AWS
        "boto3": "apache-airflow-providers-amazon",
        "botocore": "apache-airflow-providers-amazon",

        # Cloud - GCP
        "google-cloud-storage": "apache-airflow-providers-google",
        "google-cloud-bigquery": "apache-airflow-providers-google",
        "google-api-python-client": "apache-airflow-providers-google",

        # Cloud - Azure
        "azure-storage-blob": "apache-airflow-providers-microsoft-azure",
        "azure-identity": "apache-airflow-providers-microsoft-azure",

        # Messaging
        "slack-sdk": "apache-airflow-providers-slack",
        "confluent-kafka": "apache-airflow-providers-apache-kafka",

        # SSH/SFTP
        "paramiko": "apache-airflow-providers-ssh",
        "pysftp": "apache-airflow-providers-sftp",

        # Container
        "docker": "apache-airflow-providers-docker",
        "kubernetes": "apache-airflow-providers-kubernetes",

        # Data Processing
        "pyspark": "apache-airflow-providers-apache-spark",
        "databricks-sdk": "apache-airflow-providers-databricks",
    }

    # Recommended patterns for heavy ML libraries
    ML_LIBRARY_PATTERNS = {
        "tensorflow": {
            "pattern": "KubernetesPodOperator",
            "reason": "TensorFlow requires significant resources; run in isolated container",
            "example": '''
# Use KubernetesPodOperator for heavy ML workloads
from airflow.providers.kubernetes.operators.pod import KubernetesPodOperator

ml_task = KubernetesPodOperator(
    task_id='tensorflow_inference',
    image='tensorflow/tensorflow:latest',
    cmds=['python', '/scripts/inference.py'],
    namespace='ml-workloads',
    get_logs=True,
)
'''
        },
        "torch": {
            "pattern": "KubernetesPodOperator",
            "reason": "PyTorch requires GPU resources; run in isolated container",
            "example": '''
# Use KubernetesPodOperator for PyTorch workloads
from airflow.providers.kubernetes.operators.pod import KubernetesPodOperator

ml_task = KubernetesPodOperator(
    task_id='pytorch_training',
    image='pytorch/pytorch:latest',
    cmds=['python', '/scripts/train.py'],
    namespace='ml-workloads',
    resources={'limits': {'nvidia.com/gpu': 1}},
)
'''
        },
        "nemo_toolkit": {
            "pattern": "API_CALL or KubernetesPodOperator",
            "reason": "NVIDIA NeMo is heavy; use API or container",
            "example": '''
# Option 1: Use SimpleHttpOperator to call NeMo API
from airflow.providers.http.operators.http import SimpleHttpOperator

nemo_task = SimpleHttpOperator(
    task_id='nemo_qa',
    http_conn_id='nemo_api',
    endpoint='/v1/qa/generate',
    method='POST',
    data=json.dumps({{"context": context, "question": question}}),
    headers={{"Content-Type": "application/json"}},
)

# Option 2: Use KubernetesPodOperator
from airflow.providers.kubernetes.operators.pod import KubernetesPodOperator

nemo_task = KubernetesPodOperator(
    task_id='nemo_inference',
    image='nvcr.io/nvidia/nemo:latest',
    cmds=['python', '-c', 'import nemo; ...'],
    namespace='ml-workloads',
)
'''
        },
        "transformers": {
            "pattern": "KubernetesPodOperator or PythonOperator",
            "reason": "Transformers can be heavy; consider resource needs",
            "example": '''
# For small models, PythonOperator works
from airflow.operators.python import PythonOperator

def run_inference(**context):
    from transformers import pipeline
    classifier = pipeline('sentiment-analysis')
    return classifier(context['params']['text'])

task = PythonOperator(
    task_id='transformer_inference',
    python_callable=run_inference,
)
'''
        },
        "scikit-learn": {
            "pattern": "PythonOperator",
            "reason": "scikit-learn is usually lightweight enough for workers",
            "example": '''
# scikit-learn works well in PythonOperator
from airflow.operators.python import PythonOperator

def train_model(**context):
    from sklearn.ensemble import RandomForestClassifier
    model = RandomForestClassifier()
    model.fit(X_train, y_train)
    return model.score(X_test, y_test)

task = PythonOperator(
    task_id='train_model',
    python_callable=train_model,
)
'''
        },
    }

    # Native Python implementations for common operations
    NATIVE_IMPLEMENTATIONS = {
        "json_api_call": '''
def make_api_call(url: str, method: str = "GET", data: dict = None, headers: dict = None) -> dict:
    """Make HTTP API call using urllib (no external dependencies)"""
    import urllib.request
    import urllib.parse
    import json

    headers = headers or {}
    if data and method in ["POST", "PUT", "PATCH"]:
        data = json.dumps(data).encode('utf-8')
        headers['Content-Type'] = 'application/json'

    req = urllib.request.Request(url, data=data, headers=headers, method=method)

    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            return {
                "status_code": response.status,
                "data": json.loads(response.read().decode()),
                "headers": dict(response.headers)
            }
    except urllib.error.HTTPError as e:
        return {
            "status_code": e.code,
            "error": str(e),
            "data": None
        }
''',
        "csv_operations": '''
def read_csv_file(filepath: str) -> list:
    """Read CSV file into list of dicts (no pandas needed)"""
    import csv
    with open(filepath, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        return list(reader)

def write_csv_file(data: list, filepath: str, fieldnames: list = None):
    """Write list of dicts to CSV file (no pandas needed)"""
    import csv
    if not data:
        return
    fieldnames = fieldnames or list(data[0].keys())
    with open(filepath, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)
''',
        "json_file_operations": '''
def read_json_file(filepath: str) -> dict:
    """Read JSON file"""
    import json
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)

def write_json_file(data: dict, filepath: str, indent: int = 2):
    """Write dict to JSON file"""
    import json
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=indent, ensure_ascii=False)
''',
        "file_operations": '''
def read_text_file(filepath: str) -> str:
    """Read text file"""
    with open(filepath, 'r', encoding='utf-8') as f:
        return f.read()

def write_text_file(content: str, filepath: str):
    """Write text to file"""
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

def file_exists(filepath: str) -> bool:
    """Check if file exists"""
    import os
    return os.path.exists(filepath)
''',
        "basic_math": '''
def calculate_statistics(values: list) -> dict:
    """Calculate basic statistics (no numpy needed)"""
    import math

    if not values:
        return {"mean": 0, "min": 0, "max": 0, "sum": 0, "std": 0}

    n = len(values)
    total = sum(values)
    mean = total / n
    variance = sum((x - mean) ** 2 for x in values) / n
    std = math.sqrt(variance)

    return {
        "mean": mean,
        "min": min(values),
        "max": max(values),
        "sum": total,
        "std": std,
        "count": n
    }
''',
    }

    def __init__(self, library_tracker=None):
        self.logger = logger.bind(component="library_recommender")
        self.library_tracker = library_tracker

    def get_recommendations(
        self,
        library_name: str,
        functionality: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Get intelligent recommendations for a library

        Args:
            library_name: Name of the library
            functionality: What the library is being used for
            context: Additional context (component type, category, etc.)

        Returns:
            Dict with recommendations
        """
        lib_name = self._normalize_library_name(library_name)
        context = context or {}

        recommendations = {
            "library_name": lib_name,
            "airflow_provider": None,
            "use_pattern": None,
            "native_implementation": None,
            "code_example": None,
            "recommendations": []
        }

        # Check for Airflow provider mapping
        if lib_name in self.AIRFLOW_PROVIDER_MAPPINGS:
            provider = self.AIRFLOW_PROVIDER_MAPPINGS[lib_name]
            recommendations["airflow_provider"] = provider
            recommendations["recommendations"].append(
                f"Use the Airflow provider '{provider}' instead of '{lib_name}' directly. "
                f"This provides better connection management and retry handling."
            )

        # Check for ML library patterns
        if lib_name in self.ML_LIBRARY_PATTERNS:
            pattern_info = self.ML_LIBRARY_PATTERNS[lib_name]
            recommendations["use_pattern"] = pattern_info["pattern"]
            recommendations["code_example"] = pattern_info["example"]
            recommendations["recommendations"].append(
                f"Recommended pattern: {pattern_info['pattern']}. "
                f"Reason: {pattern_info['reason']}"
            )

        # Check library tracker for compatibility info
        if self.library_tracker:
            compat_info = self.library_tracker.check_library_compatibility(lib_name)
            if not compat_info.get("compatible", True):
                recommendations["recommendations"].append(
                    f"Warning: {lib_name} may not be compatible. "
                    f"{compat_info.get('recommendation', '')}"
                )

                # Get alternatives from tracker
                alt = self.library_tracker.suggest_alternative(lib_name)
                if alt:
                    recommendations["recommendations"].append(
                        f"Alternative: {alt.get('alternative_library') or alt.get('alternative_approach')}"
                    )

        # Add native implementation if available
        native_impl = self._get_native_implementation(lib_name, functionality)
        if native_impl:
            recommendations["native_implementation"] = native_impl
            recommendations["recommendations"].append(
                "A native Python implementation is available if you want to avoid external dependencies."
            )

        return recommendations

    def _normalize_library_name(self, library_name: str) -> str:
        """Normalize library name"""
        name = library_name.split(">=")[0].split("==")[0].split("<")[0].split("[")[0]
        return name.strip().lower()

    def _get_native_implementation(
        self,
        library_name: str,
        functionality: Optional[str] = None
    ) -> Optional[str]:
        """Get native Python implementation if available"""
        # Map library to functionality
        lib_to_func = {
            "requests": "json_api_call",
            "httpx": "json_api_call",
            "aiohttp": "json_api_call",
            "pandas": "csv_operations",
            "numpy": "basic_math",
        }

        func_key = lib_to_func.get(library_name)
        if func_key:
            return self.NATIVE_IMPLEMENTATIONS.get(func_key)

        return None

    def analyze_dependencies(
        self,
        dependencies: List[str]
    ) -> Dict[str, Any]:
        """
        Analyze a list of dependencies and provide recommendations

        Args:
            dependencies: List of dependency strings

        Returns:
            Analysis with recommendations for each dependency
        """
        analysis = {
            "total_dependencies": len(dependencies),
            "airflow_providers_available": 0,
            "heavy_libraries": [],
            "recommendations": [],
            "libraries": []
        }

        for dep in dependencies:
            lib_name = self._normalize_library_name(dep)
            lib_analysis = {
                "name": lib_name,
                "original": dep,
                "recommendations": []
            }

            # Check for Airflow provider
            if lib_name in self.AIRFLOW_PROVIDER_MAPPINGS:
                analysis["airflow_providers_available"] += 1
                provider = self.AIRFLOW_PROVIDER_MAPPINGS[lib_name]
                lib_analysis["airflow_provider"] = provider
                lib_analysis["recommendations"].append(
                    f"Consider using {provider} for better Airflow integration"
                )

            # Check for heavy ML libraries
            if lib_name in self.ML_LIBRARY_PATTERNS:
                analysis["heavy_libraries"].append(lib_name)
                pattern_info = self.ML_LIBRARY_PATTERNS[lib_name]
                lib_analysis["pattern"] = pattern_info["pattern"]
                lib_analysis["recommendations"].append(
                    f"Heavy library - use {pattern_info['pattern']} pattern"
                )

            analysis["libraries"].append(lib_analysis)

        # Add overall recommendations
        if analysis["heavy_libraries"]:
            analysis["recommendations"].append(
                f"Found {len(analysis['heavy_libraries'])} heavy ML libraries. "
                f"Consider using KubernetesPodOperator for resource isolation."
            )

        if analysis["airflow_providers_available"] > 0:
            analysis["recommendations"].append(
                f"{analysis['airflow_providers_available']} libraries have Airflow providers available. "
                f"Using providers gives you better connection management and retry handling."
            )

        return analysis

    def get_best_practice_for_category(self, category: str) -> Dict[str, Any]:
        """
        Get best practices for a component category

        Args:
            category: Component category (ml, http, database, etc.)

        Returns:
            Dict with best practices
        """
        best_practices = {
            "ml": {
                "description": "Machine Learning components",
                "recommendations": [
                    "Use KubernetesPodOperator for heavy ML workloads",
                    "Consider using API calls to ML services instead of running locally",
                    "Use XCom sparingly - large model outputs should go to object storage",
                    "Set appropriate timeouts for training tasks",
                ],
                "preferred_libraries": [
                    "scikit-learn (lightweight, works in workers)",
                    "transformers (via API or container for large models)",
                ],
                "avoid": [
                    "Loading large models directly in PythonOperator",
                    "Passing large tensors through XCom",
                ],
            },
            "http": {
                "description": "HTTP/REST API components",
                "recommendations": [
                    "Use SimpleHttpOperator from apache-airflow-providers-http",
                    "Configure connections in Airflow UI for credentials management",
                    "Use retry parameters for transient failures",
                    "Set appropriate timeouts",
                ],
                "preferred_libraries": [
                    "apache-airflow-providers-http",
                ],
                "avoid": [
                    "Hardcoding credentials in code",
                    "Using raw requests without retry logic",
                ],
            },
            "database": {
                "description": "Database components",
                "recommendations": [
                    "Use appropriate Airflow provider for your database",
                    "Configure connections in Airflow UI",
                    "Use connection pools for efficiency",
                    "Consider using SQL operators instead of raw queries",
                ],
                "preferred_libraries": [
                    "apache-airflow-providers-postgres",
                    "apache-airflow-providers-mysql",
                    "apache-airflow-providers-snowflake",
                ],
                "avoid": [
                    "Hardcoding database credentials",
                    "Long-running transactions that block workers",
                ],
            },
            "cloud": {
                "description": "Cloud service components",
                "recommendations": [
                    "Use official Airflow cloud providers",
                    "Configure cloud connections in Airflow UI",
                    "Use workload identity where possible",
                    "Follow least-privilege principle for IAM",
                ],
                "preferred_libraries": [
                    "apache-airflow-providers-amazon",
                    "apache-airflow-providers-google",
                    "apache-airflow-providers-microsoft-azure",
                ],
                "avoid": [
                    "Embedding cloud credentials in code",
                    "Using personal accounts for production",
                ],
            },
            "file_transfer": {
                "description": "File transfer components",
                "recommendations": [
                    "Use Airflow's SFTP/FTP providers",
                    "Configure connections securely",
                    "Use key-based authentication when possible",
                    "Validate files after transfer",
                ],
                "preferred_libraries": [
                    "apache-airflow-providers-sftp",
                    "apache-airflow-providers-ftp",
                ],
                "avoid": [
                    "Storing passwords in plain text",
                    "Transferring very large files without chunking",
                ],
            },
        }

        return best_practices.get(category, {
            "description": f"{category} components",
            "recommendations": [
                "Follow Airflow best practices",
                "Use appropriate providers when available",
                "Configure connections in Airflow UI",
            ],
            "preferred_libraries": [],
            "avoid": [],
        })

    def generate_prompt_addition(
        self,
        library_analysis: Dict[str, Any],
        category: Optional[str] = None
    ) -> str:
        """
        Generate prompt addition for code generation based on library analysis

        Args:
            library_analysis: Result from analyze_dependencies
            category: Component category

        Returns:
            Prompt addition string
        """
        prompt_parts = []

        prompt_parts.append("## Library Compatibility Notes\n")

        # Add library-specific recommendations
        for lib in library_analysis.get("libraries", []):
            if lib.get("recommendations"):
                prompt_parts.append(f"\n**{lib['name']}:**")
                for rec in lib["recommendations"]:
                    prompt_parts.append(f"- {rec}")

        # Add heavy library warnings
        if library_analysis.get("heavy_libraries"):
            prompt_parts.append("\n**Heavy Libraries Detected:**")
            prompt_parts.append("The following libraries are resource-intensive:")
            for lib in library_analysis["heavy_libraries"]:
                if lib in self.ML_LIBRARY_PATTERNS:
                    pattern = self.ML_LIBRARY_PATTERNS[lib]
                    prompt_parts.append(f"- {lib}: Use {pattern['pattern']} - {pattern['reason']}")

        # Add category best practices
        if category:
            practices = self.get_best_practice_for_category(category)
            if practices.get("recommendations"):
                prompt_parts.append(f"\n**Best Practices for {category}:**")
                for rec in practices["recommendations"][:3]:
                    prompt_parts.append(f"- {rec}")

        return "\n".join(prompt_parts)
