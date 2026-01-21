"""
Error Pattern Storage - Phase 2

Stores error patterns in SQLite database with fix strategies and tracks
which fixes work for which errors.

Similar to pattern_storage.py but for error patterns.
"""

import sqlite3
import json
import hashlib
from typing import Dict, Any, List, Optional
from datetime import datetime
from pathlib import Path
import structlog

logger = structlog.get_logger()


class ErrorPatternStorage:
    """Store and retrieve error patterns with fix strategies"""

    def __init__(self, db_path: str = "data/error_patterns.db"):
        """
        Initialize error pattern storage

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self.logger = logger.bind(component="error_pattern_storage")

        # Ensure database directory exists
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)

        # Create tables if they don't exist
        self._create_tables()

    def _create_tables(self):
        """Create database tables for error pattern storage"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Error patterns table - stores unique error patterns
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS error_patterns (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    error_signature TEXT UNIQUE NOT NULL,
                    error_type TEXT NOT NULL,
                    error_message TEXT NOT NULL,
                    severity TEXT NOT NULL,
                    category TEXT,
                    component_type TEXT,
                    occurrence_count INTEGER DEFAULT 1,
                    fix_success_count INTEGER DEFAULT 0,
                    fix_failure_count INTEGER DEFAULT 0,
                    is_recoverable BOOLEAN DEFAULT 1,
                    auto_fixable BOOLEAN DEFAULT 0,
                    fix_confidence REAL DEFAULT 0.0,
                    pattern_data TEXT,
                    first_seen TEXT NOT NULL,
                    last_seen TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
            """)

            # Fix strategies table - stores strategies for fixing errors
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS fix_strategies (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    strategy_name TEXT UNIQUE NOT NULL,
                    strategy_type TEXT NOT NULL,
                    description TEXT,
                    prompt_template TEXT,
                    requires_code_change BOOLEAN DEFAULT 1,
                    requires_spec_change BOOLEAN DEFAULT 0,
                    success_count INTEGER DEFAULT 0,
                    failure_count INTEGER DEFAULT 0,
                    confidence_score REAL DEFAULT 0.0,
                    average_fix_time REAL DEFAULT 0.0,
                    created_at TEXT NOT NULL,
                    last_used TEXT
                )
            """)

            # Error-strategy mapping table - tracks which strategies work for which errors
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS error_strategy_mapping (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    error_pattern_id INTEGER NOT NULL,
                    strategy_id INTEGER NOT NULL,
                    success_count INTEGER DEFAULT 0,
                    failure_count INTEGER DEFAULT 0,
                    effectiveness_score REAL DEFAULT 0.0,
                    avg_attempts_to_fix REAL DEFAULT 0.0,
                    last_success TEXT,
                    last_failure TEXT,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (error_pattern_id) REFERENCES error_patterns(id),
                    FOREIGN KEY (strategy_id) REFERENCES fix_strategies(id),
                    UNIQUE(error_pattern_id, strategy_id)
                )
            """)

            # Error occurrences table - tracks individual error instances
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS error_occurrences (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    error_pattern_id INTEGER NOT NULL,
                    component_name TEXT NOT NULL,
                    category TEXT,
                    component_type TEXT,
                    attempt_number INTEGER NOT NULL,
                    error_message TEXT NOT NULL,
                    code_snippet TEXT,
                    spec_data TEXT,
                    fix_applied TEXT,
                    fix_successful BOOLEAN,
                    metadata TEXT,
                    occurred_at TEXT NOT NULL,
                    FOREIGN KEY (error_pattern_id) REFERENCES error_patterns(id)
                )
            """)

            # Create indexes for faster queries
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_error_patterns_type
                ON error_patterns(error_type)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_error_patterns_category
                ON error_patterns(category, component_type)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_error_patterns_confidence
                ON error_patterns(fix_confidence DESC)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_fix_strategies_confidence
                ON fix_strategies(confidence_score DESC)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_error_occurrences_component
                ON error_occurrences(component_name)
            """)

            conn.commit()

        self.logger.info(f"✅ Error pattern database initialized: {self.db_path}")

    def store_error_pattern(
        self,
        error_message: str,
        error_patterns: Dict[str, Any],
        component_name: str,
        code: Optional[str] = None,
        spec: Optional[Dict] = None,
        attempt_number: int = 1,
        fix_applied: Optional[str] = None,
        fix_successful: Optional[bool] = None,
        metadata: Optional[Dict] = None
    ) -> int:
        """
        Store an error pattern in the database

        Args:
            error_message: The error message
            error_patterns: Extracted error patterns
            component_name: Name of the component
            code: Generated code that failed
            spec: Component specification
            attempt_number: Which retry attempt this was
            fix_applied: Name of fix strategy applied (if any)
            fix_successful: Whether the fix worked (if applied)
            metadata: Additional metadata

        Returns:
            Error pattern ID
        """
        classification = error_patterns.get('error_classification', {})
        error_signature = classification.get('error_signature', '')
        error_type = classification.get('error_type', 'unknown')
        severity = classification.get('severity', 'medium')
        is_recoverable = classification.get('is_recoverable', True)

        context = error_patterns.get('context', {})
        category = context.get('category', 'unknown')
        component_type = context.get('component_type', 'unknown')

        now = datetime.utcnow().isoformat()

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Check if this error pattern exists
            cursor.execute("""
                SELECT id, occurrence_count FROM error_patterns
                WHERE error_signature = ?
            """, (error_signature,))

            existing = cursor.fetchone()

            if existing:
                # Update existing pattern
                pattern_id, occurrence_count = existing

                # Update counts based on fix success
                if fix_successful is True:
                    cursor.execute("""
                        UPDATE error_patterns
                        SET occurrence_count = occurrence_count + 1,
                            fix_success_count = fix_success_count + 1,
                            last_seen = ?,
                            fix_confidence = CAST(fix_success_count AS REAL) /
                                           (fix_success_count + fix_failure_count + 1)
                        WHERE id = ?
                    """, (now, pattern_id))
                elif fix_successful is False:
                    cursor.execute("""
                        UPDATE error_patterns
                        SET occurrence_count = occurrence_count + 1,
                            fix_failure_count = fix_failure_count + 1,
                            last_seen = ?,
                            fix_confidence = CAST(fix_success_count AS REAL) /
                                           (fix_success_count + fix_failure_count + 1)
                        WHERE id = ?
                    """, (now, pattern_id))
                else:
                    cursor.execute("""
                        UPDATE error_patterns
                        SET occurrence_count = occurrence_count + 1,
                            last_seen = ?
                        WHERE id = ?
                    """, (now, pattern_id))

                self.logger.info(
                    f"Updated existing error pattern",
                    pattern_id=pattern_id,
                    occurrences=occurrence_count + 1
                )
            else:
                # Insert new pattern
                cursor.execute("""
                    INSERT INTO error_patterns (
                        error_signature, error_type, error_message, severity,
                        category, component_type, is_recoverable, auto_fixable,
                        pattern_data, first_seen, last_seen, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    error_signature,
                    error_type,
                    error_message[:500],  # Truncate long messages
                    severity,
                    category,
                    component_type,
                    is_recoverable,
                    error_patterns.get('indentation_errors', {}).get('auto_fixable', False) or
                    error_patterns.get('parameter_errors', {}).get('auto_fixable', False),
                    json.dumps(error_patterns),
                    now,
                    now,
                    now
                ))

                pattern_id = cursor.lastrowid

                self.logger.info(
                    f"Stored new error pattern",
                    pattern_id=pattern_id,
                    error_type=error_type
                )

            # Store error occurrence
            cursor.execute("""
                INSERT INTO error_occurrences (
                    error_pattern_id, component_name, category, component_type,
                    attempt_number, error_message, code_snippet, spec_data,
                    fix_applied, fix_successful, metadata, occurred_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                pattern_id,
                component_name,
                category,
                component_type,
                attempt_number,
                error_message,
                code[:1000] if code else None,  # Store snippet
                json.dumps(spec) if spec else None,
                fix_applied,
                fix_successful,
                json.dumps(metadata) if metadata else None,
                now
            ))

            conn.commit()

            return pattern_id

    def get_similar_errors(
        self,
        error_type: str,
        category: Optional[str] = None,
        component_type: Optional[str] = None,
        min_confidence: float = 0.5,
        limit: int = 5
    ) -> List[Dict]:
        """
        Get similar error patterns with high fix confidence

        Args:
            error_type: Type of error to search for
            category: Component category (optional filter)
            component_type: Component type (optional filter)
            min_confidence: Minimum fix confidence score
            limit: Maximum number of results

        Returns:
            List of similar error patterns with fix strategies
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            query = """
                SELECT
                    ep.*,
                    fs.strategy_name,
                    fs.description as strategy_description,
                    fs.prompt_template,
                    esm.effectiveness_score,
                    esm.avg_attempts_to_fix
                FROM error_patterns ep
                LEFT JOIN error_strategy_mapping esm ON ep.id = esm.error_pattern_id
                LEFT JOIN fix_strategies fs ON esm.strategy_id = fs.id
                WHERE ep.error_type = ?
                  AND ep.fix_confidence >= ?
            """
            params = [error_type, min_confidence]

            if category:
                query += " AND ep.category = ?"
                params.append(category)

            if component_type:
                query += " AND ep.component_type = ?"
                params.append(component_type)

            query += " ORDER BY ep.fix_confidence DESC, esm.effectiveness_score DESC LIMIT ?"
            params.append(limit)

            cursor.execute(query, params)
            results = cursor.fetchall()

            return [dict(row) for row in results]

    def get_fix_strategy(self, error_signature: str) -> Optional[Dict]:
        """
        Get the best fix strategy for a specific error pattern

        Args:
            error_signature: Unique error signature

        Returns:
            Fix strategy details or None
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute("""
                SELECT
                    fs.*,
                    esm.effectiveness_score,
                    esm.success_count,
                    esm.failure_count,
                    esm.avg_attempts_to_fix
                FROM error_patterns ep
                JOIN error_strategy_mapping esm ON ep.id = esm.error_pattern_id
                JOIN fix_strategies fs ON esm.strategy_id = fs.id
                WHERE ep.error_signature = ?
                ORDER BY esm.effectiveness_score DESC
                LIMIT 1
            """, (error_signature,))

            result = cursor.fetchone()
            return dict(result) if result else None

    def record_fix_attempt(
        self,
        error_signature: str,
        strategy_name: str,
        success: bool,
        attempts_to_fix: int = 1
    ):
        """
        Record the result of applying a fix strategy

        Args:
            error_signature: Unique error signature
            strategy_name: Name of the fix strategy used
            success: Whether the fix worked
            attempts_to_fix: Number of attempts it took
        """
        now = datetime.utcnow().isoformat()

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Get error pattern ID
            cursor.execute("""
                SELECT id FROM error_patterns WHERE error_signature = ?
            """, (error_signature,))
            error_pattern = cursor.fetchone()

            if not error_pattern:
                self.logger.warning(f"Error pattern not found: {error_signature}")
                return

            error_pattern_id = error_pattern[0]

            # Get or create fix strategy
            cursor.execute("""
                SELECT id FROM fix_strategies WHERE strategy_name = ?
            """, (strategy_name,))
            strategy = cursor.fetchone()

            if strategy:
                strategy_id = strategy[0]

                # Update strategy stats
                if success:
                    cursor.execute("""
                        UPDATE fix_strategies
                        SET success_count = success_count + 1,
                            confidence_score = CAST(success_count + 1 AS REAL) /
                                             (success_count + failure_count + 2),
                            last_used = ?
                        WHERE id = ?
                    """, (now, strategy_id))
                else:
                    cursor.execute("""
                        UPDATE fix_strategies
                        SET failure_count = failure_count + 1,
                            confidence_score = CAST(success_count AS REAL) /
                                             (success_count + failure_count + 2),
                            last_used = ?
                        WHERE id = ?
                    """, (now, strategy_id))
            else:
                # Create new strategy
                cursor.execute("""
                    INSERT INTO fix_strategies (
                        strategy_name, strategy_type, success_count, failure_count,
                        confidence_score, created_at, last_used
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    strategy_name,
                    'auto',  # Auto-detected strategy
                    1 if success else 0,
                    0 if success else 1,
                    1.0 if success else 0.0,
                    now,
                    now
                ))
                strategy_id = cursor.lastrowid

            # Update or create mapping
            cursor.execute("""
                INSERT INTO error_strategy_mapping (
                    error_pattern_id, strategy_id, success_count, failure_count,
                    effectiveness_score, avg_attempts_to_fix, created_at, last_success, last_failure
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(error_pattern_id, strategy_id) DO UPDATE SET
                    success_count = success_count + ?,
                    failure_count = failure_count + ?,
                    effectiveness_score = CAST(success_count + ? AS REAL) /
                                        (success_count + failure_count + 2),
                    avg_attempts_to_fix = (avg_attempts_to_fix * (success_count + failure_count) + ?) /
                                         (success_count + failure_count + 1),
                    last_success = CASE WHEN ? = 1 THEN ? ELSE last_success END,
                    last_failure = CASE WHEN ? = 0 THEN ? ELSE last_failure END
            """, (
                error_pattern_id,
                strategy_id,
                1 if success else 0,
                0 if success else 1,
                1.0 if success else 0.0,
                attempts_to_fix,
                now,
                now if success else None,
                now if not success else None,
                # Update clause values
                1 if success else 0,
                0 if success else 1,
                1 if success else 0,
                attempts_to_fix,
                1 if success else 0,
                now,
                1 if success else 0,
                now
            ))

            conn.commit()

            self.logger.info(
                f"Recorded fix attempt",
                strategy=strategy_name,
                success=success,
                attempts=attempts_to_fix
            )

    def get_error_statistics(self) -> Dict[str, Any]:
        """Get statistics about error patterns"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            stats = {}

            # Total patterns
            cursor.execute("SELECT COUNT(*) FROM error_patterns")
            stats['total_patterns'] = cursor.fetchone()[0]

            # Total occurrences
            cursor.execute("SELECT SUM(occurrence_count) FROM error_patterns")
            stats['total_occurrences'] = cursor.fetchone()[0] or 0

            # By error type
            cursor.execute("""
                SELECT error_type, COUNT(*), SUM(occurrence_count), AVG(fix_confidence)
                FROM error_patterns
                GROUP BY error_type
                ORDER BY SUM(occurrence_count) DESC
            """)
            stats['by_type'] = [
                {
                    'error_type': row[0],
                    'unique_patterns': row[1],
                    'total_occurrences': row[2],
                    'avg_fix_confidence': round(row[3], 2) if row[3] else 0.0
                }
                for row in cursor.fetchall()
            ]

            # Top fixable errors
            cursor.execute("""
                SELECT error_type, error_message, fix_confidence, occurrence_count
                FROM error_patterns
                WHERE fix_confidence >= 0.7
                ORDER BY fix_confidence DESC, occurrence_count DESC
                LIMIT 10
            """)
            stats['top_fixable'] = [
                {
                    'error_type': row[0],
                    'error_message': row[1][:100],
                    'fix_confidence': round(row[2], 2),
                    'occurrences': row[3]
                }
                for row in cursor.fetchall()
            ]

            # Fix strategy performance
            cursor.execute("""
                SELECT strategy_name, success_count, failure_count, confidence_score
                FROM fix_strategies
                WHERE success_count + failure_count > 0
                ORDER BY confidence_score DESC
                LIMIT 10
            """)
            stats['top_strategies'] = [
                {
                    'strategy': row[0],
                    'successes': row[1],
                    'failures': row[2],
                    'confidence': round(row[3], 2)
                }
                for row in cursor.fetchall()
            ]

            return stats
