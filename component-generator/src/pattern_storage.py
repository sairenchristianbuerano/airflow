"""
Pattern Storage - Store and retrieve learned patterns

This module manages the storage of extracted patterns in a SQLite database
and provides retrieval methods for pattern-based generation.
"""

import sqlite3
import json
from typing import Dict, List, Any, Optional
from datetime import datetime
from pathlib import Path


class PatternStorage:
    """Store and retrieve learned patterns"""

    def __init__(self, db_path: str):
        self.db_path = db_path
        self.conn = None
        self._connect()
        self._create_tables()

    def _connect(self):
        """Connect to database"""
        # Ensure directory exists
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row

    def _create_tables(self):
        """Create pattern storage tables"""
        self.conn.executescript("""
            -- Code patterns extracted from successful generations
            CREATE TABLE IF NOT EXISTS code_patterns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                component_name TEXT NOT NULL,
                pattern_type TEXT NOT NULL,  -- 'import', 'init', 'execute', etc.
                pattern_name TEXT NOT NULL,
                pattern_data TEXT NOT NULL,  -- JSON
                category TEXT,
                subcategory TEXT,
                component_type TEXT,
                complexity_range TEXT,  -- 'low' (<15), 'medium' (15-35), 'high' (35-50), 'very_high' (>50)
                success_count INTEGER DEFAULT 1,
                failure_count INTEGER DEFAULT 0,
                confidence_score REAL DEFAULT 1.0,  -- success / (success + failure)
                pattern_signature TEXT,  -- Hash for deduplication
                created_at TEXT NOT NULL,
                last_used TEXT,
                libraries_involved TEXT,  -- JSON array
                UNIQUE(pattern_signature, pattern_type)
            );

            -- Full component patterns (entire successful components)
            CREATE TABLE IF NOT EXISTS component_patterns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                component_name TEXT NOT NULL UNIQUE,
                category TEXT,
                subcategory TEXT,
                component_type TEXT,
                full_code TEXT NOT NULL,
                extracted_patterns TEXT NOT NULL,  -- JSON of all patterns
                metadata TEXT NOT NULL,  -- JSON
                success_score INTEGER,
                complexity_score REAL,
                libraries_used TEXT,  -- JSON array
                created_at TEXT NOT NULL
            );

            -- Pattern relationships (what patterns work well together)
            CREATE TABLE IF NOT EXISTS pattern_combinations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pattern_id_1 INTEGER NOT NULL,
                pattern_id_2 INTEGER NOT NULL,
                combination_success_count INTEGER DEFAULT 0,
                combination_failure_count INTEGER DEFAULT 0,
                confidence_score REAL DEFAULT 0.0,
                FOREIGN KEY(pattern_id_1) REFERENCES code_patterns(id),
                FOREIGN KEY(pattern_id_2) REFERENCES code_patterns(id),
                UNIQUE(pattern_id_1, pattern_id_2)
            );

            -- Pattern effectiveness history
            CREATE TABLE IF NOT EXISTS pattern_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pattern_id INTEGER NOT NULL,
                used_in_component TEXT NOT NULL,
                resulted_in_success BOOLEAN NOT NULL,
                error_message TEXT,
                generation_attempt INTEGER,
                timestamp TEXT NOT NULL,
                FOREIGN KEY(pattern_id) REFERENCES code_patterns(id)
            );

            -- Indexes for performance
            CREATE INDEX IF NOT EXISTS idx_pattern_type ON code_patterns(pattern_type);
            CREATE INDEX IF NOT EXISTS idx_pattern_category ON code_patterns(category);
            CREATE INDEX IF NOT EXISTS idx_pattern_component_type ON code_patterns(component_type);
            CREATE INDEX IF NOT EXISTS idx_pattern_confidence ON code_patterns(confidence_score);
            CREATE INDEX IF NOT EXISTS idx_pattern_signature ON code_patterns(pattern_signature);
            CREATE INDEX IF NOT EXISTS idx_component_category ON component_patterns(category);
            CREATE INDEX IF NOT EXISTS idx_component_type ON component_patterns(component_type);
        """)
        self.conn.commit()

    def store_component_patterns(self, component_name: str, code: str,
                                 patterns: Dict, metadata: Dict, success: bool = True):
        """
        Store all patterns from a complete component

        Args:
            component_name: Name of the component
            code: Full generated code
            patterns: Extracted patterns dictionary
            metadata: Component metadata
            success: Whether this was a successful generation
        """
        cursor = self.conn.cursor()

        # Get complexity range
        complexity = metadata.get("complexity_score", 0)
        complexity_range = self._get_complexity_range(complexity)

        # Store full component
        cursor.execute("""
            INSERT OR REPLACE INTO component_patterns (
                component_name, category, subcategory, component_type,
                full_code, extracted_patterns, metadata,
                success_score, complexity_score, libraries_used,
                created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            component_name,
            patterns["metadata"].get("category"),
            patterns["metadata"].get("subcategory"),
            patterns["metadata"].get("component_type"),
            code,
            json.dumps(patterns),
            json.dumps(metadata),
            metadata.get("success_score", 100),
            complexity,
            json.dumps(patterns["metadata"].get("libraries_used", [])),
            datetime.now().isoformat()
        ))

        # Store individual patterns
        for pattern_type, pattern_data in patterns.items():
            if pattern_type == "metadata":
                continue

            if not pattern_data:  # Skip empty patterns
                continue

            # Create pattern signature for deduplication
            pattern_signature = self._create_pattern_signature(
                pattern_type, pattern_data, patterns["metadata"]
            )

            # Check if pattern exists
            cursor.execute("""
                SELECT id, success_count, failure_count
                FROM code_patterns
                WHERE pattern_signature = ? AND pattern_type = ?
            """, (pattern_signature, pattern_type))

            result = cursor.fetchone()

            if result:
                # Update existing pattern
                pattern_id = result["id"]
                success_count = result["success_count"]
                failure_count = result["failure_count"]

                if success:
                    success_count += 1
                else:
                    failure_count += 1

                confidence = success_count / (success_count + failure_count) if (success_count + failure_count) > 0 else 0

                cursor.execute("""
                    UPDATE code_patterns
                    SET success_count = ?,
                        failure_count = ?,
                        confidence_score = ?,
                        last_used = ?
                    WHERE id = ?
                """, (success_count, failure_count, confidence,
                      datetime.now().isoformat(), pattern_id))

            else:
                # Insert new pattern
                cursor.execute("""
                    INSERT INTO code_patterns (
                        component_name, pattern_type, pattern_name, pattern_data,
                        category, subcategory, component_type, complexity_range,
                        confidence_score, pattern_signature,
                        created_at, last_used, libraries_involved
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    component_name,
                    pattern_type,
                    self._get_pattern_name(pattern_type, pattern_data),
                    json.dumps(pattern_data),
                    patterns["metadata"].get("category"),
                    patterns["metadata"].get("subcategory"),
                    patterns["metadata"].get("component_type"),
                    complexity_range,
                    1.0 if success else 0.0,
                    pattern_signature,
                    datetime.now().isoformat(),
                    datetime.now().isoformat(),
                    json.dumps(patterns["metadata"].get("libraries_used", []))
                ))
                pattern_id = cursor.lastrowid

            # Record usage history
            cursor.execute("""
                INSERT INTO pattern_history (
                    pattern_id, used_in_component,
                    resulted_in_success, generation_attempt, timestamp
                ) VALUES (?, ?, ?, ?, ?)
            """, (pattern_id, component_name, success, 1,
                  datetime.now().isoformat()))

        self.conn.commit()

    def get_best_patterns(self, category: str, component_type: str,
                         pattern_type: Optional[str] = None,
                         min_confidence: float = 0.7,
                         limit: int = 10) -> List[Dict]:
        """
        Retrieve highest-confidence patterns for similar components

        Args:
            category: Component category (e.g., 'ml', 'data')
            component_type: Type (e.g., 'operator', 'sensor')
            pattern_type: Specific pattern type (optional)
            min_confidence: Minimum confidence threshold
            limit: Maximum number of patterns to return

        Returns:
            List of pattern dictionaries
        """
        cursor = self.conn.cursor()

        query = """
            SELECT
                pattern_type,
                pattern_name,
                pattern_data,
                confidence_score,
                success_count,
                failure_count,
                libraries_involved,
                created_at,
                last_used
            FROM code_patterns
            WHERE category = ?
              AND component_type = ?
              AND confidence_score >= ?
        """
        params = [category, component_type, min_confidence]

        if pattern_type:
            query += " AND pattern_type = ?"
            params.append(pattern_type)

        query += " ORDER BY confidence_score DESC, success_count DESC LIMIT ?"
        params.append(limit)

        cursor.execute(query, params)

        patterns = []
        for row in cursor.fetchall():
            pattern = {
                "pattern_type": row["pattern_type"],
                "pattern_name": row["pattern_name"],
                "pattern_data": json.loads(row["pattern_data"]),
                "confidence_score": row["confidence_score"],
                "success_count": row["success_count"],
                "failure_count": row["failure_count"],
                "libraries_involved": json.loads(row["libraries_involved"]) if row["libraries_involved"] else [],
                "created_at": row["created_at"],
                "last_used": row["last_used"]
            }
            patterns.append(pattern)

        return patterns

    def get_similar_components(self, category: str, subcategory: Optional[str] = None,
                              min_success_score: int = 150, limit: int = 5) -> List[Dict]:
        """
        Get complete component patterns for similar components

        Args:
            category: Component category
            subcategory: Component subcategory (optional)
            min_success_score: Minimum success score
            limit: Maximum results

        Returns:
            List of component pattern dictionaries
        """
        cursor = self.conn.cursor()

        query = """
            SELECT
                component_name,
                category,
                subcategory,
                component_type,
                full_code,
                extracted_patterns,
                metadata,
                success_score,
                complexity_score,
                created_at
            FROM component_patterns
            WHERE category = ?
              AND success_score >= ?
        """
        params = [category, min_success_score]

        if subcategory:
            query += " AND subcategory = ?"
            params.append(subcategory)

        query += " ORDER BY success_score DESC, complexity_score ASC LIMIT ?"
        params.append(limit)

        cursor.execute(query, params)

        components = []
        for row in cursor.fetchall():
            component = {
                "component_name": row["component_name"],
                "category": row["category"],
                "subcategory": row["subcategory"],
                "component_type": row["component_type"],
                "full_code": row["full_code"],
                "extracted_patterns": json.loads(row["extracted_patterns"]),
                "metadata": json.loads(row["metadata"]),
                "success_score": row["success_score"],
                "complexity_score": row["complexity_score"],
                "created_at": row["created_at"]
            }
            components.append(component)

        return components

    def record_pattern_usage(self, pattern_ids: List[int], component_name: str,
                           success: bool, error: Optional[str] = None,
                           attempt: int = 1):
        """
        Record usage of patterns in a new generation

        Args:
            pattern_ids: List of pattern IDs used
            component_name: Name of component being generated
            success: Whether generation succeeded
            error: Error message if failed
            attempt: Generation attempt number
        """
        cursor = self.conn.cursor()

        for pattern_id in pattern_ids:
            cursor.execute("""
                INSERT INTO pattern_history (
                    pattern_id, used_in_component,
                    resulted_in_success, error_message,
                    generation_attempt, timestamp
                ) VALUES (?, ?, ?, ?, ?, ?)
            """, (pattern_id, component_name, success, error,
                  attempt, datetime.now().isoformat()))

            # Update pattern success/failure counts
            if success:
                cursor.execute("""
                    UPDATE code_patterns
                    SET success_count = success_count + 1,
                        confidence_score = CAST(success_count + 1 AS FLOAT) /
                                         (success_count + failure_count + 1),
                        last_used = ?
                    WHERE id = ?
                """, (datetime.now().isoformat(), pattern_id))
            else:
                cursor.execute("""
                    UPDATE code_patterns
                    SET failure_count = failure_count + 1,
                        confidence_score = CAST(success_count AS FLOAT) /
                                         (success_count + failure_count + 1),
                        last_used = ?
                    WHERE id = ?
                """, (datetime.now().isoformat(), pattern_id))

        self.conn.commit()

    def get_pattern_statistics(self) -> Dict[str, Any]:
        """Get overall pattern storage statistics"""
        cursor = self.conn.cursor()

        stats = {}

        # Total patterns
        cursor.execute("SELECT COUNT(*) as count FROM code_patterns")
        stats["total_patterns"] = cursor.fetchone()["count"]

        # Total components
        cursor.execute("SELECT COUNT(*) as count FROM component_patterns")
        stats["total_components"] = cursor.fetchone()["count"]

        # Patterns by category
        cursor.execute("""
            SELECT category, COUNT(*) as count
            FROM code_patterns
            GROUP BY category
            ORDER BY count DESC
        """)
        stats["patterns_by_category"] = {row["category"]: row["count"]
                                        for row in cursor.fetchall()}

        # High confidence patterns (>= 0.9)
        cursor.execute("""
            SELECT COUNT(*) as count
            FROM code_patterns
            WHERE confidence_score >= 0.9
        """)
        stats["high_confidence_patterns"] = cursor.fetchone()["count"]

        # Average confidence
        cursor.execute("""
            SELECT AVG(confidence_score) as avg_confidence
            FROM code_patterns
        """)
        stats["average_confidence"] = cursor.fetchone()["avg_confidence"] or 0.0

        return stats

    def _get_complexity_range(self, complexity: float) -> str:
        """Categorize complexity score into range"""
        if complexity < 15:
            return "low"
        elif complexity < 35:
            return "medium"
        elif complexity < 50:
            return "high"
        else:
            return "very_high"

    def _create_pattern_signature(self, pattern_type: str, pattern_data: Dict,
                                  metadata: Dict) -> str:
        """Create unique signature for pattern deduplication"""
        import hashlib

        # Create stable string representation
        sig_parts = [
            pattern_type,
            metadata.get("category", ""),
            metadata.get("component_type", ""),
            json.dumps(pattern_data, sort_keys=True)
        ]

        sig_str = "|".join(sig_parts)
        return hashlib.md5(sig_str.encode()).hexdigest()

    def _get_pattern_name(self, pattern_type: str, pattern_data: Dict) -> str:
        """Generate human-readable pattern name"""
        if pattern_type == "import" and "dual_imports" in pattern_data:
            return f"dual_import_{len(pattern_data['dual_imports'])}"
        elif pattern_type == "mock_execution":
            if pattern_data.get("has_mock_mode"):
                return "mock_execution_pattern"
        elif pattern_type == "parameter_ordering":
            return pattern_data.get("ordering_strategy", "unknown") + "_ordering"

        return f"{pattern_type}_pattern"

    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()

    def __del__(self):
        """Cleanup on deletion"""
        self.close()
