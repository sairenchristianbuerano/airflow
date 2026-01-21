"""
Library Compatibility Tracker - Phase 3

Tracks which libraries work in Airflow environment, logs usage patterns,
and provides alternatives for incompatible libraries.
"""

import sqlite3
import json
import hashlib
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
import structlog

logger = structlog.get_logger()


class LibraryTracker:
    """Track which libraries work in Airflow environment"""

    # Pre-populated known Airflow-compatible libraries
    KNOWN_AIRFLOW_COMPATIBLE = {
        # Core Airflow providers
        "apache-airflow": {"category": "core", "compatible": True},
        "apache-airflow-providers-http": {"category": "http", "compatible": True},
        "apache-airflow-providers-postgres": {"category": "database", "compatible": True},
        "apache-airflow-providers-mysql": {"category": "database", "compatible": True},
        "apache-airflow-providers-google": {"category": "cloud", "compatible": True},
        "apache-airflow-providers-amazon": {"category": "cloud", "compatible": True},
        "apache-airflow-providers-microsoft-azure": {"category": "cloud", "compatible": True},
        "apache-airflow-providers-ssh": {"category": "compute", "compatible": True},
        "apache-airflow-providers-docker": {"category": "container", "compatible": True},
        "apache-airflow-providers-kubernetes": {"category": "container", "compatible": True},
        "apache-airflow-providers-slack": {"category": "notification", "compatible": True},
        "apache-airflow-providers-smtp": {"category": "notification", "compatible": True},
        "apache-airflow-providers-sftp": {"category": "file_transfer", "compatible": True},
        "apache-airflow-providers-ftp": {"category": "file_transfer", "compatible": True},
        "apache-airflow-providers-redis": {"category": "cache", "compatible": True},
        "apache-airflow-providers-celery": {"category": "executor", "compatible": True},
        "apache-airflow-providers-elasticsearch": {"category": "search", "compatible": True},
        "apache-airflow-providers-mongo": {"category": "database", "compatible": True},
        "apache-airflow-providers-snowflake": {"category": "database", "compatible": True},
        "apache-airflow-providers-databricks": {"category": "compute", "compatible": True},
        "apache-airflow-providers-apache-spark": {"category": "compute", "compatible": True},

        # Standard Python libraries (always work)
        "requests": {"category": "http", "compatible": True},
        "urllib3": {"category": "http", "compatible": True},
        "json": {"category": "stdlib", "compatible": True},
        "os": {"category": "stdlib", "compatible": True},
        "sys": {"category": "stdlib", "compatible": True},
        "datetime": {"category": "stdlib", "compatible": True},
        "typing": {"category": "stdlib", "compatible": True},
        "logging": {"category": "stdlib", "compatible": True},
        "re": {"category": "stdlib", "compatible": True},
        "hashlib": {"category": "stdlib", "compatible": True},
        "uuid": {"category": "stdlib", "compatible": True},
        "pathlib": {"category": "stdlib", "compatible": True},
        "collections": {"category": "stdlib", "compatible": True},
        "itertools": {"category": "stdlib", "compatible": True},
        "functools": {"category": "stdlib", "compatible": True},
        "abc": {"category": "stdlib", "compatible": True},
        "dataclasses": {"category": "stdlib", "compatible": True},
        "enum": {"category": "stdlib", "compatible": True},

        # Common data libraries
        "pandas": {"category": "data", "compatible": True, "install": "pip install pandas"},
        "numpy": {"category": "data", "compatible": True, "install": "pip install numpy"},
        "pydantic": {"category": "data", "compatible": True, "install": "pip install pydantic"},
        "marshmallow": {"category": "data", "compatible": True},

        # API/HTTP libraries
        "httpx": {"category": "http", "compatible": True},
        "aiohttp": {"category": "http", "compatible": True},

        # Database libraries
        "sqlalchemy": {"category": "database", "compatible": True},
        "psycopg2": {"category": "database", "compatible": True},
        "pymysql": {"category": "database", "compatible": True},
        "pymongo": {"category": "database", "compatible": True},

        # Cloud SDKs
        "boto3": {"category": "cloud", "compatible": True},
        "google-cloud-storage": {"category": "cloud", "compatible": True},
        "azure-storage-blob": {"category": "cloud", "compatible": True},

        # ML Libraries (may need special handling)
        "scikit-learn": {"category": "ml", "compatible": True, "notes": "Heavy dependency"},
        "tensorflow": {"category": "ml", "compatible": True, "notes": "Heavy dependency, use container"},
        "torch": {"category": "ml", "compatible": True, "notes": "Heavy dependency, use container"},
        "transformers": {"category": "ml", "compatible": True, "notes": "Heavy dependency"},
    }

    # Known problematic libraries
    KNOWN_INCOMPATIBLE = {
        "nemo_toolkit": {
            "category": "ml",
            "reason": "Heavy ML framework, not typically installed in Airflow workers",
            "alternatives": ["Use API calls to NeMo service", "Use KubernetesPodOperator"]
        },
        "nvidia-nemo": {
            "category": "ml",
            "reason": "GPU-specific, requires CUDA",
            "alternatives": ["Use API calls to NeMo service", "Use KubernetesPodOperator"]
        },
        "cudf": {
            "category": "ml",
            "reason": "GPU-specific RAPIDS library",
            "alternatives": ["pandas", "dask"]
        },
        "cuml": {
            "category": "ml",
            "reason": "GPU-specific ML library",
            "alternatives": ["scikit-learn"]
        },
    }

    def __init__(self, db_path: str = "data/library_compatibility.db"):
        self.logger = logger.bind(component="library_tracker")
        self.db_path = db_path
        self.db = sqlite3.connect(db_path, check_same_thread=False)
        self.db.row_factory = sqlite3.Row
        self._create_tables()
        self._seed_known_libraries()
        self.logger.info("Library tracker initialized", db_path=db_path)

    def _create_tables(self):
        """Create library tracking tables"""
        self.db.executescript("""
            CREATE TABLE IF NOT EXISTS libraries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                library_name TEXT UNIQUE NOT NULL,
                category TEXT,
                is_airflow_compatible BOOLEAN DEFAULT 1,
                requires_extra_install BOOLEAN DEFAULT 0,
                install_command TEXT,
                airflow_version_compatibility TEXT,
                success_count INTEGER DEFAULT 0,
                failure_count INTEGER DEFAULT 0,
                compatibility_score REAL DEFAULT 1.0,
                last_tested TEXT,
                notes TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS library_alternatives (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                library_id INTEGER,
                alternative_library TEXT,
                alternative_approach TEXT,
                native_implementation TEXT,
                effectiveness_score REAL DEFAULT 0.5,
                usage_count INTEGER DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(library_id) REFERENCES libraries(id)
            );

            CREATE TABLE IF NOT EXISTS library_usage_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                library_name TEXT NOT NULL,
                component_name TEXT,
                component_type TEXT,
                import_successful BOOLEAN,
                execution_successful BOOLEAN,
                error_message TEXT,
                error_type TEXT,
                airflow_version TEXT,
                timestamp TEXT DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS library_dependencies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                library_id INTEGER,
                dependency_name TEXT,
                is_optional BOOLEAN DEFAULT 0,
                FOREIGN KEY(library_id) REFERENCES libraries(id)
            );

            CREATE INDEX IF NOT EXISTS idx_library_name ON libraries(library_name);
            CREATE INDEX IF NOT EXISTS idx_library_category ON libraries(category);
            CREATE INDEX IF NOT EXISTS idx_library_compatibility ON libraries(compatibility_score);
            CREATE INDEX IF NOT EXISTS idx_usage_library ON library_usage_log(library_name);
            CREATE INDEX IF NOT EXISTS idx_usage_timestamp ON library_usage_log(timestamp);
        """)
        self.db.commit()

    def _seed_known_libraries(self):
        """Seed database with known library information"""
        cursor = self.db.cursor()

        # Add known compatible libraries
        for lib_name, info in self.KNOWN_AIRFLOW_COMPATIBLE.items():
            cursor.execute("""
                INSERT OR IGNORE INTO libraries (
                    library_name, category, is_airflow_compatible,
                    requires_extra_install, install_command, notes,
                    compatibility_score
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                lib_name,
                info.get("category", "general"),
                True,
                info.get("install") is not None,
                info.get("install"),
                info.get("notes"),
                1.0
            ))

        # Add known incompatible libraries
        for lib_name, info in self.KNOWN_INCOMPATIBLE.items():
            cursor.execute("""
                INSERT OR IGNORE INTO libraries (
                    library_name, category, is_airflow_compatible,
                    notes, compatibility_score
                ) VALUES (?, ?, ?, ?, ?)
            """, (
                lib_name,
                info.get("category", "general"),
                False,
                info.get("reason"),
                0.0
            ))

            # Add alternatives
            lib_id = cursor.lastrowid
            if lib_id and info.get("alternatives"):
                for alt in info["alternatives"]:
                    cursor.execute("""
                        INSERT OR IGNORE INTO library_alternatives (
                            library_id, alternative_library, alternative_approach
                        ) VALUES (?, ?, ?)
                    """, (lib_id, alt, "different_library"))

        self.db.commit()

    def check_library_compatibility(self, library_name: str) -> Dict[str, Any]:
        """
        Check if library is compatible and get alternatives if not

        Args:
            library_name: Name of the library to check

        Returns:
            Dict with compatibility info and recommendations
        """
        # Normalize library name
        lib_name = self._normalize_library_name(library_name)

        cursor = self.db.cursor()
        cursor.execute("""
            SELECT * FROM libraries WHERE library_name = ?
        """, (lib_name,))

        result = cursor.fetchone()

        if not result:
            # Check if it's in our known lists but with different name
            for known_lib in list(self.KNOWN_AIRFLOW_COMPATIBLE.keys()) + list(self.KNOWN_INCOMPATIBLE.keys()):
                if lib_name in known_lib or known_lib in lib_name:
                    return self.check_library_compatibility(known_lib)

            return {
                "library_name": lib_name,
                "status": "unknown",
                "compatible": None,
                "compatibility_score": None,
                "alternatives": [],
                "recommendation": "Unknown library. Test in controlled environment first.",
                "requires_testing": True
            }

        lib_data = dict(result)

        # Get alternatives if not compatible
        alternatives = []
        if not lib_data["is_airflow_compatible"]:
            cursor.execute("""
                SELECT * FROM library_alternatives
                WHERE library_id = ?
                ORDER BY effectiveness_score DESC
            """, (lib_data["id"],))

            alternatives = [dict(row) for row in cursor.fetchall()]

        return {
            "library_name": lib_name,
            "status": "known",
            "compatible": lib_data["is_airflow_compatible"],
            "compatibility_score": lib_data["compatibility_score"],
            "category": lib_data["category"],
            "requires_extra_install": lib_data["requires_extra_install"],
            "install_command": lib_data["install_command"],
            "notes": lib_data["notes"],
            "alternatives": alternatives,
            "recommendation": self._get_recommendation(lib_data, alternatives),
            "requires_testing": False
        }

    def _normalize_library_name(self, library_name: str) -> str:
        """Normalize library name for consistent lookup"""
        # Remove version specifiers
        name = library_name.split(">=")[0].split("==")[0].split("<")[0].split("[")[0]
        # Remove leading/trailing whitespace
        name = name.strip()
        # Convert to lowercase
        return name.lower()

    def _get_recommendation(self, lib_data: Dict, alternatives: List) -> str:
        """Get recommendation for library usage"""
        if lib_data["is_airflow_compatible"]:
            if lib_data["requires_extra_install"]:
                return f"Compatible. Install with: {lib_data['install_command']}"
            return "Compatible. Use directly."

        if alternatives:
            best_alt = alternatives[0]
            if best_alt["alternative_approach"] == "native_python":
                return "Not compatible. Use native Python implementation."
            elif best_alt["alternative_library"]:
                return f"Not compatible. Consider: {best_alt['alternative_library']}"

        return "Not compatible. No known alternatives. Consider using KubernetesPodOperator or API calls."

    def log_library_usage(
        self,
        library_name: str,
        component_name: str,
        import_success: bool,
        execution_success: bool,
        error: Optional[str] = None,
        error_type: Optional[str] = None,
        component_type: str = "operator",
        airflow_version: str = "2.x"
    ):
        """
        Log library usage for learning

        Args:
            library_name: Name of the library
            component_name: Name of the component using it
            import_success: Whether the import succeeded
            execution_success: Whether execution succeeded
            error: Error message if failed
            error_type: Type of error (import, runtime, etc.)
            component_type: Type of component (operator, sensor, hook)
            airflow_version: Airflow version used
        """
        lib_name = self._normalize_library_name(library_name)
        cursor = self.db.cursor()

        # Log usage
        cursor.execute("""
            INSERT INTO library_usage_log (
                library_name, component_name, component_type,
                import_successful, execution_successful,
                error_message, error_type, airflow_version, timestamp
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            lib_name, component_name, component_type,
            import_success, execution_success,
            error, error_type, airflow_version,
            datetime.utcnow().isoformat()
        ))

        # Update library record
        cursor.execute("""
            SELECT id, success_count, failure_count FROM libraries
            WHERE library_name = ?
        """, (lib_name,))

        result = cursor.fetchone()

        if result:
            lib_id, success_count, failure_count = result
            if import_success and execution_success:
                success_count += 1
            else:
                failure_count += 1

            total = success_count + failure_count
            compatibility_score = success_count / total if total > 0 else 0.5

            cursor.execute("""
                UPDATE libraries
                SET success_count = ?,
                    failure_count = ?,
                    compatibility_score = ?,
                    is_airflow_compatible = ?,
                    last_tested = ?,
                    updated_at = ?
                WHERE id = ?
            """, (
                success_count, failure_count, compatibility_score,
                compatibility_score > 0.7,
                datetime.utcnow().isoformat(),
                datetime.utcnow().isoformat(),
                lib_id
            ))
        else:
            # New library
            is_compatible = import_success and execution_success
            cursor.execute("""
                INSERT INTO libraries (
                    library_name, is_airflow_compatible,
                    success_count, failure_count,
                    compatibility_score, last_tested
                ) VALUES (?, ?, ?, ?, ?, ?)
            """, (
                lib_name, is_compatible,
                1 if is_compatible else 0,
                0 if is_compatible else 1,
                1.0 if is_compatible else 0.0,
                datetime.utcnow().isoformat()
            ))

        self.db.commit()

        self.logger.info(
            "Library usage logged",
            library=lib_name,
            component=component_name,
            import_success=import_success,
            execution_success=execution_success
        )

    def suggest_alternative(self, library_name: str) -> Optional[Dict[str, Any]]:
        """
        Suggest alternative for incompatible library

        Args:
            library_name: Name of the library

        Returns:
            Dict with alternative info or None
        """
        lib_name = self._normalize_library_name(library_name)
        cursor = self.db.cursor()

        cursor.execute("""
            SELECT la.*, l.library_name as original_library
            FROM library_alternatives la
            JOIN libraries l ON la.library_id = l.id
            WHERE l.library_name = ?
            ORDER BY la.effectiveness_score DESC
            LIMIT 1
        """, (lib_name,))

        result = cursor.fetchone()
        if result:
            return dict(result)
        return None

    def suggest_native_implementation(
        self,
        library_name: str,
        functionality: str = ""
    ) -> Optional[str]:
        """
        Suggest native Python implementation for unsupported library

        Args:
            library_name: Name of the library
            functionality: Specific functionality needed

        Returns:
            Native Python code or None
        """
        lib_name = self._normalize_library_name(library_name)
        cursor = self.db.cursor()

        # Check for stored native implementation
        cursor.execute("""
            SELECT la.native_implementation
            FROM library_alternatives la
            JOIN libraries l ON la.library_id = l.id
            WHERE l.library_name = ?
              AND la.alternative_approach = 'native_python'
              AND la.native_implementation IS NOT NULL
            ORDER BY la.effectiveness_score DESC
            LIMIT 1
        """, (lib_name,))

        result = cursor.fetchone()
        if result and result[0]:
            return result[0]

        # Return common fallback patterns
        return self._get_native_fallback(lib_name, functionality)

    def _get_native_fallback(self, library_name: str, functionality: str) -> Optional[str]:
        """Get native Python fallback code"""
        fallbacks = {
            "requests": '''
# Native urllib fallback for requests
import urllib.request
import urllib.parse
import json

def http_request(url: str, method: str = "GET", data: dict = None, headers: dict = None):
    """Make HTTP request using urllib (requests alternative)"""
    headers = headers or {}
    if data:
        data = json.dumps(data).encode('utf-8')
        headers['Content-Type'] = 'application/json'

    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    with urllib.request.urlopen(req) as response:
        return json.loads(response.read().decode())
''',
            "pandas": '''
# Native CSV handling fallback for pandas
import csv
from typing import List, Dict

def read_csv(filepath: str) -> List[Dict]:
    """Read CSV file (pandas alternative)"""
    with open(filepath, 'r') as f:
        reader = csv.DictReader(f)
        return list(reader)

def write_csv(data: List[Dict], filepath: str):
    """Write CSV file (pandas alternative)"""
    if not data:
        return
    with open(filepath, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=data[0].keys())
        writer.writeheader()
        writer.writerows(data)
''',
            "numpy": '''
# Native math operations fallback for numpy
import math
from typing import List

def array_mean(values: List[float]) -> float:
    """Calculate mean (numpy alternative)"""
    return sum(values) / len(values) if values else 0

def array_sum(values: List[float]) -> float:
    """Calculate sum (numpy alternative)"""
    return sum(values)

def array_std(values: List[float]) -> float:
    """Calculate standard deviation (numpy alternative)"""
    if not values:
        return 0
    mean = array_mean(values)
    variance = sum((x - mean) ** 2 for x in values) / len(values)
    return math.sqrt(variance)
''',
        }

        return fallbacks.get(library_name)

    def add_alternative(
        self,
        library_name: str,
        alternative_library: Optional[str] = None,
        alternative_approach: str = "different_library",
        native_implementation: Optional[str] = None,
        effectiveness_score: float = 0.5
    ):
        """
        Add alternative for a library

        Args:
            library_name: Name of the original library
            alternative_library: Name of alternative library
            alternative_approach: Type of alternative (different_library, native_python, mock)
            native_implementation: Native Python code if applicable
            effectiveness_score: How effective this alternative is (0-1)
        """
        lib_name = self._normalize_library_name(library_name)
        cursor = self.db.cursor()

        # Get or create library record
        cursor.execute("SELECT id FROM libraries WHERE library_name = ?", (lib_name,))
        result = cursor.fetchone()

        if result:
            lib_id = result[0]
        else:
            cursor.execute("""
                INSERT INTO libraries (library_name, is_airflow_compatible)
                VALUES (?, 0)
            """, (lib_name,))
            lib_id = cursor.lastrowid

        # Add alternative
        cursor.execute("""
            INSERT INTO library_alternatives (
                library_id, alternative_library, alternative_approach,
                native_implementation, effectiveness_score
            ) VALUES (?, ?, ?, ?, ?)
        """, (lib_id, alternative_library, alternative_approach,
              native_implementation, effectiveness_score))

        self.db.commit()

        self.logger.info(
            "Alternative added",
            library=lib_name,
            alternative=alternative_library or alternative_approach
        )

    def get_library_statistics(self) -> Dict[str, Any]:
        """Get overall library compatibility statistics"""
        cursor = self.db.cursor()

        # Total libraries tracked
        cursor.execute("SELECT COUNT(*) FROM libraries")
        total_libraries = cursor.fetchone()[0]

        # Compatible vs incompatible
        cursor.execute("""
            SELECT is_airflow_compatible, COUNT(*)
            FROM libraries
            GROUP BY is_airflow_compatible
        """)
        compat_stats = {bool(row[0]): row[1] for row in cursor.fetchall()}

        # By category
        cursor.execute("""
            SELECT category, COUNT(*), AVG(compatibility_score)
            FROM libraries
            WHERE category IS NOT NULL
            GROUP BY category
            ORDER BY COUNT(*) DESC
        """)
        by_category = [
            {"category": row[0], "count": row[1], "avg_score": row[2]}
            for row in cursor.fetchall()
        ]

        # Recent usage
        cursor.execute("""
            SELECT library_name, COUNT(*) as usage_count,
                   SUM(CASE WHEN import_successful THEN 1 ELSE 0 END) as success_count
            FROM library_usage_log
            WHERE timestamp > datetime('now', '-7 days')
            GROUP BY library_name
            ORDER BY usage_count DESC
            LIMIT 10
        """)
        recent_usage = [dict(row) for row in cursor.fetchall()]

        # Most problematic libraries
        cursor.execute("""
            SELECT library_name, failure_count, success_count, compatibility_score
            FROM libraries
            WHERE failure_count > 0
            ORDER BY failure_count DESC
            LIMIT 10
        """)
        problematic = [dict(row) for row in cursor.fetchall()]

        return {
            "total_libraries": total_libraries,
            "compatible_count": compat_stats.get(True, 0),
            "incompatible_count": compat_stats.get(False, 0),
            "by_category": by_category,
            "recent_usage": recent_usage,
            "most_problematic": problematic
        }

    def get_libraries_for_category(self, category: str) -> List[Dict[str, Any]]:
        """Get all libraries in a category"""
        cursor = self.db.cursor()
        cursor.execute("""
            SELECT * FROM libraries
            WHERE category = ?
            ORDER BY compatibility_score DESC
        """, (category,))

        return [dict(row) for row in cursor.fetchall()]

    def check_dependencies(self, spec: Dict[str, Any]) -> Dict[str, Any]:
        """
        Check all dependencies in a component spec

        Args:
            spec: Component specification with dependencies

        Returns:
            Dict with compatibility analysis for all dependencies
        """
        dependencies = spec.get("dependencies", [])
        results = {
            "all_compatible": True,
            "libraries": [],
            "recommendations": [],
            "alternatives_needed": []
        }

        for dep in dependencies:
            lib_name = self._normalize_library_name(dep)
            compat = self.check_library_compatibility(lib_name)

            results["libraries"].append({
                "name": lib_name,
                "original": dep,
                **compat
            })

            if not compat.get("compatible", True):
                results["all_compatible"] = False
                results["alternatives_needed"].append(lib_name)
                results["recommendations"].append(compat["recommendation"])

        return results

    def close(self):
        """Close database connection"""
        if self.db:
            self.db.close()
