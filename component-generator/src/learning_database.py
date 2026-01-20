"""
Learning database for tracking generation metrics and patterns.

SQLite-based storage for historical generation data, success patterns,
and performance metrics. Provides analytics and insights for continuous improvement.
"""

import sqlite3
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from contextlib import contextmanager
import structlog

logger = structlog.get_logger()


class LearningDatabase:
    """SQLite database for tracking generation metrics and learning patterns"""

    def __init__(self, db_path: str = None):
        # Default to platform-agnostic path
        if db_path is None:
            # Check if running in Docker (has /app/data/) or locally
            import os
            from pathlib import Path
            if os.path.exists("/app/data"):
                db_path = "/app/data/learning.db"
            else:
                # Use relative path for local development
                base_dir = Path(__file__).parent.parent
                db_path = str(base_dir / "data" / "learning.db")

        self.db_path = db_path
        self.logger = logger.bind(component="learning_database")
        self._init_database()

    @contextmanager
    def _get_connection(self):
        """Context manager for database connections"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Return rows as dictionaries
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    def _init_database(self):
        """Initialize database schema"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                # Generation history table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS generation_history (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        component_name TEXT NOT NULL,
                        component_type TEXT NOT NULL,
                        component_category TEXT,
                        component_description TEXT,
                        timestamp TEXT NOT NULL,
                        attempts_needed INTEGER NOT NULL,
                        success BOOLEAN NOT NULL,
                        total_time_seconds REAL,
                        prompt_tokens INTEGER,
                        completion_tokens INTEGER,
                        total_tokens INTEGER,
                        cost_usd REAL,
                        validation_passed BOOLEAN,
                        first_attempt_success BOOLEAN,
                        error_messages TEXT,
                        spec_complexity TEXT
                    )
                """)

                # Error patterns table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS error_patterns (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        error_type TEXT NOT NULL,
                        error_message TEXT NOT NULL,
                        solution TEXT NOT NULL,
                        frequency INTEGER DEFAULT 1,
                        last_seen TEXT NOT NULL,
                        component_contexts TEXT
                    )
                """)

                # Success patterns table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS success_patterns (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        component_category TEXT NOT NULL,
                        pattern_type TEXT NOT NULL,
                        description TEXT NOT NULL,
                        frequency INTEGER DEFAULT 1,
                        last_seen TEXT NOT NULL,
                        avg_generation_time REAL,
                        metadata TEXT
                    )
                """)

                # Create indexes for performance
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_generation_timestamp
                    ON generation_history(timestamp)
                """)
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_generation_component_name
                    ON generation_history(component_name)
                """)
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_generation_category
                    ON generation_history(component_category)
                """)
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_generation_type
                    ON generation_history(component_type)
                """)
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_error_type
                    ON error_patterns(error_type)
                """)

                self.logger.info("Learning database initialized", db_path=self.db_path)

        except Exception as e:
            self.logger.error("Failed to initialize database", error=str(e))
            raise

    def record_generation(
        self,
        component_name: str,
        component_type: str,
        component_category: str,
        component_description: str,
        attempts_needed: int,
        success: bool,
        total_time_seconds: float,
        prompt_tokens: int = 0,
        completion_tokens: int = 0,
        validation_passed: bool = False,
        first_attempt_success: bool = False,
        error_messages: List[str] = None,
        spec_complexity: str = "medium"
    ) -> int:
        """
        Record a generation attempt in the database

        Args:
            component_name: Name of the component being generated
            component_type: Type (operator, sensor, hook)
            component_category: Category (http, database, cloud, etc.)
            component_description: Brief description
            attempts_needed: Number of attempts (1-5)
            success: Whether generation succeeded
            total_time_seconds: Total generation time
            prompt_tokens: Tokens used in prompts
            completion_tokens: Tokens used in completions
            validation_passed: Whether validation succeeded
            first_attempt_success: Whether succeeded on first try
            error_messages: List of error messages if any
            spec_complexity: Complexity level (simple/medium/complex)

        Returns:
            Record ID
        """
        try:
            total_tokens = prompt_tokens + completion_tokens

            # Calculate cost (approximate Claude Sonnet 4 pricing)
            # $3 per million input tokens, $15 per million output tokens
            cost_usd = (prompt_tokens * 3.0 / 1_000_000) + (completion_tokens * 15.0 / 1_000_000)

            timestamp = datetime.now().isoformat()
            error_json = json.dumps(error_messages) if error_messages else None

            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO generation_history (
                        component_name, component_type, component_category, component_description, timestamp,
                        attempts_needed, success, total_time_seconds,
                        prompt_tokens, completion_tokens, total_tokens, cost_usd,
                        validation_passed, first_attempt_success, error_messages, spec_complexity
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    component_name, component_type, component_category, component_description, timestamp,
                    attempts_needed, success, total_time_seconds,
                    prompt_tokens, completion_tokens, total_tokens, cost_usd,
                    validation_passed, first_attempt_success, error_json, spec_complexity
                ))

                record_id = cursor.lastrowid

                self.logger.info(
                    "Generation recorded",
                    component_name=component_name,
                    component_type=component_type,
                    attempts=attempts_needed,
                    success=success,
                    cost_usd=round(cost_usd, 4)
                )

                return record_id

        except Exception as e:
            self.logger.error("Failed to record generation", error=str(e))
            raise

    def get_overall_metrics(self) -> Dict[str, Any]:
        """Get overall generation metrics"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                # Total generations and success rate
                cursor.execute("""
                    SELECT
                        COUNT(*) as total,
                        SUM(CASE WHEN success THEN 1 ELSE 0 END) as successes,
                        AVG(attempts_needed) as avg_attempts,
                        AVG(total_time_seconds) as avg_time,
                        SUM(cost_usd) as total_cost,
                        SUM(CASE WHEN first_attempt_success THEN 1 ELSE 0 END) as first_attempt_successes
                    FROM generation_history
                """)

                row = cursor.fetchone()

                total = row['total'] or 0
                successes = row['successes'] or 0
                first_attempt_successes = row['first_attempt_successes'] or 0

                success_rate = (successes / total) if total > 0 else 0.0
                first_attempt_rate = (first_attempt_successes / total) if total > 0 else 0.0

                return {
                    "total_generations": total,
                    "success_rate": round(success_rate, 3),
                    "avg_attempts": round(row['avg_attempts'] or 0, 2),
                    "avg_generation_time_seconds": round(row['avg_time'] or 0, 2),
                    "total_cost_usd": round(row['total_cost'] or 0, 4),
                    "first_attempt_success_rate": round(first_attempt_rate, 3),
                    "first_attempt_successes": first_attempt_successes
                }

        except Exception as e:
            self.logger.error("Failed to get overall metrics", error=str(e))
            return {}

    def get_category_insights(self) -> Dict[str, Any]:
        """Get insights by component category"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                cursor.execute("""
                    SELECT
                        component_category,
                        COUNT(*) as total,
                        AVG(attempts_needed) as avg_attempts,
                        SUM(CASE WHEN success THEN 1 ELSE 0 END) * 1.0 / COUNT(*) as success_rate,
                        AVG(total_time_seconds) as avg_time
                    FROM generation_history
                    WHERE component_category IS NOT NULL
                    GROUP BY component_category
                    ORDER BY total DESC
                """)

                by_category = {}
                for row in cursor.fetchall():
                    by_category[row['component_category']] = {
                        "total_generations": row['total'],
                        "success_rate": round(row['success_rate'] or 0, 3),
                        "avg_attempts": round(row['avg_attempts'] or 0, 2),
                        "avg_time_seconds": round(row['avg_time'] or 0, 2)
                    }

                # Hardest components (highest avg attempts)
                cursor.execute("""
                    SELECT component_category, AVG(attempts_needed) as avg_attempts
                    FROM generation_history
                    WHERE component_category IS NOT NULL
                    GROUP BY component_category
                    HAVING COUNT(*) >= 2
                    ORDER BY avg_attempts DESC
                    LIMIT 5
                """)

                hardest_components = [
                    {"category": row['component_category'], "avg_attempts": round(row['avg_attempts'], 2)}
                    for row in cursor.fetchall()
                ]

                # Easiest components (lowest avg attempts)
                cursor.execute("""
                    SELECT component_category, AVG(attempts_needed) as avg_attempts
                    FROM generation_history
                    WHERE component_category IS NOT NULL
                    GROUP BY component_category
                    HAVING COUNT(*) >= 2
                    ORDER BY avg_attempts ASC
                    LIMIT 5
                """)

                easiest_components = [
                    {"category": row['component_category'], "avg_attempts": round(row['avg_attempts'], 2)}
                    for row in cursor.fetchall()
                ]

                return {
                    "by_category": by_category,
                    "hardest_components": hardest_components,
                    "easiest_components": easiest_components
                }

        except Exception as e:
            self.logger.error("Failed to get category insights", error=str(e))
            return {"by_category": {}, "hardest_components": [], "easiest_components": []}

    def get_type_insights(self) -> Dict[str, Any]:
        """Get insights by component type (operator, sensor, hook)"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                cursor.execute("""
                    SELECT
                        component_type,
                        COUNT(*) as total,
                        AVG(attempts_needed) as avg_attempts,
                        SUM(CASE WHEN success THEN 1 ELSE 0 END) * 1.0 / COUNT(*) as success_rate,
                        AVG(total_time_seconds) as avg_time
                    FROM generation_history
                    GROUP BY component_type
                    ORDER BY total DESC
                """)

                by_type = {}
                for row in cursor.fetchall():
                    by_type[row['component_type']] = {
                        "total_generations": row['total'],
                        "success_rate": round(row['success_rate'] or 0, 3),
                        "avg_attempts": round(row['avg_attempts'] or 0, 2),
                        "avg_time_seconds": round(row['avg_time'] or 0, 2)
                    }

                return {"by_type": by_type}

        except Exception as e:
            self.logger.error("Failed to get type insights", error=str(e))
            return {"by_type": {}}

    def get_trends(self, days: int = 7) -> Dict[str, Any]:
        """Get performance trends over time"""
        try:
            cutoff = (datetime.now() - timedelta(days=days)).isoformat()

            with self._get_connection() as conn:
                cursor = conn.cursor()

                # Daily statistics
                cursor.execute("""
                    SELECT
                        DATE(timestamp) as date,
                        COUNT(*) as generations,
                        SUM(CASE WHEN success THEN 1 ELSE 0 END) * 1.0 / COUNT(*) as success_rate,
                        AVG(attempts_needed) as avg_attempts,
                        SUM(cost_usd) as daily_cost
                    FROM generation_history
                    WHERE timestamp >= ?
                    GROUP BY DATE(timestamp)
                    ORDER BY date DESC
                """, (cutoff,))

                daily_stats = [
                    {
                        "date": row['date'],
                        "generations": row['generations'],
                        "success_rate": round(row['success_rate'] or 0, 3),
                        "avg_attempts": round(row['avg_attempts'] or 0, 2),
                        "cost_usd": round(row['daily_cost'] or 0, 4)
                    }
                    for row in cursor.fetchall()
                ]

                # Calculate improvement vs previous period
                cursor.execute("""
                    SELECT
                        AVG(CASE WHEN success THEN 1.0 ELSE 0.0 END) as success_rate
                    FROM generation_history
                    WHERE timestamp >= ?
                """, (cutoff,))

                current_success = cursor.fetchone()['success_rate'] or 0

                previous_cutoff = (datetime.now() - timedelta(days=days*2)).isoformat()
                cursor.execute("""
                    SELECT
                        AVG(CASE WHEN success THEN 1.0 ELSE 0.0 END) as success_rate
                    FROM generation_history
                    WHERE timestamp >= ? AND timestamp < ?
                """, (previous_cutoff, cutoff))

                previous_success = cursor.fetchone()['success_rate'] or 0

                improvement = ((current_success - previous_success) * 100) if previous_success > 0 else 0

                improvement_text = f"{'+' if improvement > 0 else ''}{round(improvement, 1)}% success rate vs previous {days} days"

                return {
                    "daily_stats": daily_stats,
                    "improvement": improvement_text,
                    "current_period_success_rate": round(current_success, 3),
                    "previous_period_success_rate": round(previous_success, 3)
                }

        except Exception as e:
            self.logger.error("Failed to get trends", error=str(e))
            return {"daily_stats": [], "improvement": "N/A"}

    def get_error_analytics(self) -> Dict[str, Any]:
        """Get error analytics from database"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                # Total errors
                cursor.execute("SELECT SUM(frequency) as total FROM error_patterns")
                total_errors = cursor.fetchone()['total'] or 0

                # Unique patterns
                cursor.execute("SELECT COUNT(*) as count FROM error_patterns")
                unique_patterns = cursor.fetchone()['count'] or 0

                # Errors by type
                cursor.execute("""
                    SELECT error_type, SUM(frequency) as count
                    FROM error_patterns
                    GROUP BY error_type
                    ORDER BY count DESC
                """)

                errors_by_type = {row['error_type']: row['count'] for row in cursor.fetchall()}

                # Top errors
                cursor.execute("""
                    SELECT error_type, error_message, solution, frequency, last_seen
                    FROM error_patterns
                    ORDER BY frequency DESC
                    LIMIT 10
                """)

                top_errors = [
                    {
                        "type": row['error_type'],
                        "message": row['error_message'],
                        "solution": row['solution'],
                        "frequency": row['frequency']
                    }
                    for row in cursor.fetchall()
                ]

                # Last updated
                cursor.execute("SELECT MAX(last_seen) as last_updated FROM error_patterns")
                last_updated = cursor.fetchone()['last_updated']

                return {
                    "total_tracked_errors": total_errors,
                    "unique_error_patterns": unique_patterns,
                    "errors_by_type": errors_by_type,
                    "top_errors": top_errors,
                    "last_updated": last_updated
                }

        except Exception as e:
            self.logger.error("Failed to get error analytics", error=str(e))
            return {
                "total_tracked_errors": 0,
                "unique_error_patterns": 0,
                "errors_by_type": {},
                "top_errors": [],
                "last_updated": None
            }
