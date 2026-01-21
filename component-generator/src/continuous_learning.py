#!/usr/bin/env python3
"""
Phase 5: Continuous Learning & Self-Improvement

This module orchestrates the continuous learning loop, enabling the generator
to improve over time by:
1. Learning from every generation (success or failure)
2. Applying confidence decay to outdated patterns
3. Validating and refreshing patterns periodically
4. Collecting automated feedback
5. Providing improvement suggestions

Key Features:
- Unified learning manager for all phases
- Confidence decay mechanism for patterns
- Scheduled pattern validation
- Metrics aggregation and analysis
- Improvement recommendation engine
"""

import sqlite3
import os
import json
import re
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
import logging
import math


@dataclass
class LearningMetrics:
    """Metrics for tracking learning progress"""
    category: str
    total_generations: int = 0
    successful_generations: int = 0
    failed_generations: int = 0
    avg_attempts: float = 1.0
    avg_tokens: int = 0
    avg_time_seconds: float = 0.0
    first_attempt_success_rate: float = 0.0
    pattern_match_rate: float = 0.0
    error_reduction_rate: float = 0.0
    last_updated: str = ""


@dataclass
class ConfidenceDecayConfig:
    """Configuration for confidence decay"""
    decay_rate: float = 0.95  # Daily decay multiplier (0.95 = 5% decay/day)
    min_confidence: float = 0.1  # Minimum confidence before removal
    max_age_days: int = 90  # Maximum age before forced review
    success_boost: float = 0.1  # Confidence boost on successful use
    failure_penalty: float = 0.15  # Confidence penalty on failure


class ContinuousLearningManager:
    """
    Orchestrate continuous learning and self-improvement across all phases.

    This class integrates:
    - Phase 1: Pattern Learning (PatternStorage, PatternExtractor)
    - Phase 2: Error Learning (ErrorPatternStorage, FixStrategyManager)
    - Phase 3: Library Tracking (LibraryTracker, LibraryRecommender)
    - Phase 4: Native Fallbacks (NativeFallbackGenerator)

    And adds:
    - Confidence decay for patterns and strategies
    - Automated feedback collection
    - Pattern validation and refresh
    - Improvement recommendation engine
    """

    def __init__(
        self,
        db_path: str = None,
        pattern_storage=None,
        pattern_extractor=None,
        error_storage=None,
        error_extractor=None,
        fix_strategy_manager=None,
        library_tracker=None,
        fallback_generator=None,
        decay_config: ConfidenceDecayConfig = None
    ):
        """
        Initialize the Continuous Learning Manager.

        Args:
            db_path: Path to the learning database
            pattern_storage: Phase 1 pattern storage instance
            pattern_extractor: Phase 1 pattern extractor instance
            error_storage: Phase 2 error storage instance
            error_extractor: Phase 2 error extractor instance
            fix_strategy_manager: Phase 2 fix strategy manager
            library_tracker: Phase 3 library tracker
            fallback_generator: Phase 4 fallback generator
            decay_config: Configuration for confidence decay
        """
        self.logger = logging.getLogger(__name__)

        if db_path is None:
            db_path = os.path.join(
                os.path.dirname(__file__),
                "..", "data", "continuous_learning.db"
            )

        self.db_path = db_path
        self.decay_config = decay_config or ConfidenceDecayConfig()

        # Phase components (injected)
        self.pattern_storage = pattern_storage
        self.pattern_extractor = pattern_extractor
        self.error_storage = error_storage
        self.error_extractor = error_extractor
        self.fix_strategy_manager = fix_strategy_manager
        self.library_tracker = library_tracker
        self.fallback_generator = fallback_generator

        self._init_database()

    def _init_database(self) -> None:
        """Initialize the continuous learning database"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)

        self.db = sqlite3.connect(self.db_path, check_same_thread=False)
        self.db.row_factory = sqlite3.Row

        cursor = self.db.cursor()

        # Learning metrics by category
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS learning_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category TEXT NOT NULL,
                component_type TEXT DEFAULT 'operator',
                total_generations INTEGER DEFAULT 0,
                successful_generations INTEGER DEFAULT 0,
                failed_generations INTEGER DEFAULT 0,
                avg_attempts REAL DEFAULT 1.0,
                avg_tokens INTEGER DEFAULT 0,
                avg_time_seconds REAL DEFAULT 0.0,
                first_attempt_success_count INTEGER DEFAULT 0,
                pattern_match_count INTEGER DEFAULT 0,
                error_fixed_count INTEGER DEFAULT 0,
                last_updated TEXT DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(category, component_type)
            )
        ''')

        # Generation feedback log
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS generation_feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                component_name TEXT NOT NULL,
                component_type TEXT,
                category TEXT,
                success BOOLEAN,
                attempts INTEGER DEFAULT 1,
                prompt_tokens INTEGER DEFAULT 0,
                completion_tokens INTEGER DEFAULT 0,
                time_seconds REAL DEFAULT 0.0,
                first_attempt_success BOOLEAN DEFAULT 0,
                patterns_used INTEGER DEFAULT 0,
                errors_fixed INTEGER DEFAULT 0,
                fallbacks_used INTEGER DEFAULT 0,
                error_types TEXT,
                fix_strategies TEXT,
                libraries_used TEXT,
                metadata TEXT,
                timestamp TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Pattern confidence tracking
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS pattern_confidence (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pattern_type TEXT NOT NULL,
                pattern_name TEXT NOT NULL,
                category TEXT,
                component_type TEXT,
                confidence_score REAL DEFAULT 0.5,
                usage_count INTEGER DEFAULT 0,
                success_count INTEGER DEFAULT 0,
                failure_count INTEGER DEFAULT 0,
                last_used TEXT,
                last_decay_applied TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(pattern_type, pattern_name, category)
            )
        ''')

        # Strategy effectiveness tracking
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS strategy_effectiveness (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                strategy_name TEXT NOT NULL,
                error_type TEXT,
                category TEXT,
                effectiveness_score REAL DEFAULT 0.5,
                usage_count INTEGER DEFAULT 0,
                success_count INTEGER DEFAULT 0,
                failure_count INTEGER DEFAULT 0,
                avg_attempts_to_fix REAL DEFAULT 1.0,
                last_used TEXT,
                UNIQUE(strategy_name, error_type, category)
            )
        ''')

        # Improvement suggestions
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS improvement_suggestions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category TEXT,
                suggestion_type TEXT,
                issue TEXT,
                recommendation TEXT,
                priority TEXT DEFAULT 'medium',
                status TEXT DEFAULT 'pending',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                resolved_at TEXT
            )
        ''')

        # Scheduled tasks
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS scheduled_tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_type TEXT NOT NULL,
                last_run TEXT,
                next_run TEXT,
                interval_hours INTEGER DEFAULT 24,
                enabled BOOLEAN DEFAULT 1
            )
        ''')

        self.db.commit()

        # Initialize scheduled tasks
        self._init_scheduled_tasks()

    def _init_scheduled_tasks(self) -> None:
        """Initialize default scheduled tasks"""
        cursor = self.db.cursor()

        default_tasks = [
            ("confidence_decay", 24),  # Daily
            ("pattern_validation", 168),  # Weekly
            ("metrics_aggregation", 1),  # Hourly
            ("suggestion_generation", 24),  # Daily
            ("cleanup_old_data", 720),  # Monthly
        ]

        for task_type, interval_hours in default_tasks:
            cursor.execute('''
                INSERT OR IGNORE INTO scheduled_tasks
                (task_type, interval_hours, next_run)
                VALUES (?, ?, ?)
            ''', (task_type, interval_hours, datetime.now().isoformat()))

        self.db.commit()

    def learn_from_generation(
        self,
        component_name: str,
        component_type: str,
        category: str,
        code: str,
        spec: Dict[str, Any],
        validation_result: Dict[str, Any],
        metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Learn from a generation attempt (success or failure).

        This is the main entry point for the learning loop.

        Args:
            component_name: Name of the generated component
            component_type: Type (operator, sensor, hook)
            category: Component category (http, ml, database, etc.)
            code: Generated code
            spec: Component specification
            validation_result: Validation result dict
            metadata: Generation metadata (attempts, tokens, time, etc.)

        Returns:
            Dict with learning results and insights
        """
        success = validation_result.get("is_valid", False)
        errors = validation_result.get("errors", [])
        warnings = validation_result.get("warnings", [])

        learning_result = {
            "success": success,
            "patterns_learned": 0,
            "errors_analyzed": 0,
            "confidence_updates": 0,
            "suggestions_generated": 0,
            "insights": []
        }

        # 1. Log generation feedback
        self._log_generation_feedback(
            component_name, component_type, category,
            success, metadata, errors
        )

        # 2. Update learning metrics
        self._update_learning_metrics(
            category, component_type, success, metadata
        )

        # 3. Learn from success
        if success and self.pattern_extractor:
            patterns = self._learn_from_success(
                component_name, code, spec, metadata
            )
            learning_result["patterns_learned"] = len(patterns)
            learning_result["insights"].append(
                f"Extracted {len(patterns)} patterns from successful generation"
            )

        # 4. Learn from errors
        if not success and errors:
            error_analysis = self._learn_from_errors(
                component_name, category, code, spec, errors, metadata
            )
            learning_result["errors_analyzed"] = len(error_analysis)
            learning_result["insights"].append(
                f"Analyzed {len(error_analysis)} error patterns"
            )

        # 5. Update pattern confidence based on usage
        confidence_updates = self._update_pattern_confidence(
            category, component_type, success, metadata
        )
        learning_result["confidence_updates"] = confidence_updates

        # 6. Track library usage
        if self.library_tracker and code:
            self._track_library_usage(component_name, code, success)

        # 7. Track fallback effectiveness
        if self.fallback_generator and metadata.get("fallbacks_used"):
            self._track_fallback_effectiveness(
                metadata.get("fallbacks_used", []), success
            )

        # 8. Generate suggestions if needed
        if not success or metadata.get("attempts", 1) > 1:
            suggestions = self._generate_suggestions(
                category, component_type, errors
            )
            learning_result["suggestions_generated"] = len(suggestions)

        return learning_result

    def _log_generation_feedback(
        self,
        component_name: str,
        component_type: str,
        category: str,
        success: bool,
        metadata: Dict[str, Any],
        errors: List[str]
    ) -> None:
        """Log generation feedback to database"""
        cursor = self.db.cursor()

        cursor.execute('''
            INSERT INTO generation_feedback (
                component_name, component_type, category, success,
                attempts, prompt_tokens, completion_tokens, time_seconds,
                first_attempt_success, patterns_used, errors_fixed,
                fallbacks_used, error_types, fix_strategies, libraries_used, metadata
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            component_name,
            component_type,
            category,
            success,
            metadata.get("attempts", 1),
            metadata.get("prompt_tokens", 0),
            metadata.get("completion_tokens", 0),
            metadata.get("time_seconds", 0),
            metadata.get("first_attempt_success", success and metadata.get("attempts", 1) == 1),
            metadata.get("patterns_used", 0),
            metadata.get("errors_fixed", 0),
            len(metadata.get("fallbacks_used", [])),
            json.dumps([str(e)[:100] for e in errors[:5]]),  # First 5 errors, truncated
            json.dumps(metadata.get("fix_strategies", [])),
            json.dumps(metadata.get("libraries", [])),
            json.dumps(metadata)
        ))

        self.db.commit()

    def _update_learning_metrics(
        self,
        category: str,
        component_type: str,
        success: bool,
        metadata: Dict[str, Any]
    ) -> None:
        """Update aggregated learning metrics"""
        cursor = self.db.cursor()

        # Get current metrics
        cursor.execute('''
            SELECT * FROM learning_metrics
            WHERE category = ? AND component_type = ?
        ''', (category, component_type))

        row = cursor.fetchone()

        if row:
            # Update existing metrics
            new_total = row["total_generations"] + 1
            new_successful = row["successful_generations"] + (1 if success else 0)
            new_failed = row["failed_generations"] + (0 if success else 1)

            # Calculate rolling averages
            attempts = metadata.get("attempts", 1)
            tokens = metadata.get("prompt_tokens", 0) + metadata.get("completion_tokens", 0)
            time_sec = metadata.get("time_seconds", 0)

            new_avg_attempts = (row["avg_attempts"] * row["total_generations"] + attempts) / new_total
            new_avg_tokens = (row["avg_tokens"] * row["total_generations"] + tokens) / new_total
            new_avg_time = (row["avg_time_seconds"] * row["total_generations"] + time_sec) / new_total

            first_attempt_count = row["first_attempt_success_count"]
            if success and attempts == 1:
                first_attempt_count += 1

            cursor.execute('''
                UPDATE learning_metrics
                SET total_generations = ?,
                    successful_generations = ?,
                    failed_generations = ?,
                    avg_attempts = ?,
                    avg_tokens = ?,
                    avg_time_seconds = ?,
                    first_attempt_success_count = ?,
                    pattern_match_count = pattern_match_count + ?,
                    error_fixed_count = error_fixed_count + ?,
                    last_updated = ?
                WHERE category = ? AND component_type = ?
            ''', (
                new_total,
                new_successful,
                new_failed,
                new_avg_attempts,
                int(new_avg_tokens),
                new_avg_time,
                first_attempt_count,
                metadata.get("patterns_used", 0),
                metadata.get("errors_fixed", 0),
                datetime.now().isoformat(),
                category,
                component_type
            ))
        else:
            # Insert new metrics
            cursor.execute('''
                INSERT INTO learning_metrics (
                    category, component_type, total_generations,
                    successful_generations, failed_generations,
                    avg_attempts, avg_tokens, avg_time_seconds,
                    first_attempt_success_count, pattern_match_count, error_fixed_count
                ) VALUES (?, ?, 1, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                category,
                component_type,
                1 if success else 0,
                0 if success else 1,
                metadata.get("attempts", 1),
                metadata.get("prompt_tokens", 0) + metadata.get("completion_tokens", 0),
                metadata.get("time_seconds", 0),
                1 if success and metadata.get("attempts", 1) == 1 else 0,
                metadata.get("patterns_used", 0),
                metadata.get("errors_fixed", 0)
            ))

        self.db.commit()

    def _learn_from_success(
        self,
        component_name: str,
        code: str,
        spec: Dict[str, Any],
        metadata: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Learn patterns from successful generation"""
        patterns = []

        if self.pattern_extractor and self.pattern_storage:
            # Extract patterns
            extracted = self.pattern_extractor.extract_patterns(
                code, spec, metadata
            )

            # Store patterns
            self.pattern_storage.store_component_patterns(
                component_name=component_name,
                code=code,
                patterns=extracted,
                metadata=metadata,
                success=True
            )

            patterns = list(extracted.keys()) if isinstance(extracted, dict) else []

            # Update pattern confidence
            for pattern_type in patterns:
                self._boost_pattern_confidence(
                    pattern_type,
                    component_name,
                    spec.get("category", "general")
                )

        return patterns

    def _learn_from_errors(
        self,
        component_name: str,
        category: str,
        code: str,
        spec: Dict[str, Any],
        errors: List[str],
        metadata: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Learn from generation errors"""
        error_analyses = []

        if self.error_extractor and self.error_storage:
            for error in errors:
                # Extract error pattern
                analysis = self.error_extractor.extract_error_patterns(
                    error_message=str(error),
                    code=code,
                    spec=spec,
                    attempt_number=metadata.get("attempts", 1),
                    metadata=metadata
                )

                # Store error pattern
                self.error_storage.store_error_pattern(
                    error_message=str(error),
                    error_patterns=analysis,
                    component_name=component_name,
                    code=code,
                    spec=spec,
                    attempt_number=metadata.get("attempts", 1)
                )

                # Update strategy effectiveness
                error_type = analysis.get("error_classification", {}).get("error_type", "unknown")
                self._update_strategy_effectiveness(
                    error_type, category, success=False
                )

                error_analyses.append(analysis)

        return error_analyses

    def _update_pattern_confidence(
        self,
        category: str,
        component_type: str,
        success: bool,
        metadata: Dict[str, Any]
    ) -> int:
        """Update confidence for patterns used in this generation"""
        cursor = self.db.cursor()
        updates = 0

        patterns_used = metadata.get("patterns_used_names", [])

        for pattern_name in patterns_used:
            if success:
                # Boost confidence for successful use
                cursor.execute('''
                    UPDATE pattern_confidence
                    SET confidence_score = MIN(1.0, confidence_score + ?),
                        usage_count = usage_count + 1,
                        success_count = success_count + 1,
                        last_used = ?
                    WHERE pattern_name = ? AND category = ?
                ''', (
                    self.decay_config.success_boost,
                    datetime.now().isoformat(),
                    pattern_name,
                    category
                ))
            else:
                # Penalize confidence for failed use
                cursor.execute('''
                    UPDATE pattern_confidence
                    SET confidence_score = MAX(?, confidence_score - ?),
                        usage_count = usage_count + 1,
                        failure_count = failure_count + 1,
                        last_used = ?
                    WHERE pattern_name = ? AND category = ?
                ''', (
                    self.decay_config.min_confidence,
                    self.decay_config.failure_penalty,
                    datetime.now().isoformat(),
                    pattern_name,
                    category
                ))

            if cursor.rowcount > 0:
                updates += 1

        self.db.commit()
        return updates

    def _boost_pattern_confidence(
        self,
        pattern_type: str,
        pattern_name: str,
        category: str
    ) -> None:
        """Boost confidence for a pattern after successful use"""
        cursor = self.db.cursor()

        cursor.execute('''
            INSERT INTO pattern_confidence (
                pattern_type, pattern_name, category, confidence_score,
                usage_count, success_count, last_used
            ) VALUES (?, ?, ?, 0.6, 1, 1, ?)
            ON CONFLICT(pattern_type, pattern_name, category)
            DO UPDATE SET
                confidence_score = MIN(1.0, confidence_score + ?),
                usage_count = usage_count + 1,
                success_count = success_count + 1,
                last_used = ?
        ''', (
            pattern_type,
            pattern_name,
            category,
            datetime.now().isoformat(),
            self.decay_config.success_boost,
            datetime.now().isoformat()
        ))

        self.db.commit()

    def _update_strategy_effectiveness(
        self,
        error_type: str,
        category: str,
        success: bool,
        strategy_name: str = None
    ) -> None:
        """Update effectiveness tracking for fix strategies"""
        cursor = self.db.cursor()

        if strategy_name:
            if success:
                cursor.execute('''
                    UPDATE strategy_effectiveness
                    SET effectiveness_score = MIN(1.0, effectiveness_score + 0.1),
                        usage_count = usage_count + 1,
                        success_count = success_count + 1,
                        last_used = ?
                    WHERE strategy_name = ? AND error_type = ?
                ''', (datetime.now().isoformat(), strategy_name, error_type))
            else:
                cursor.execute('''
                    UPDATE strategy_effectiveness
                    SET effectiveness_score = MAX(0.1, effectiveness_score - 0.05),
                        usage_count = usage_count + 1,
                        failure_count = failure_count + 1,
                        last_used = ?
                    WHERE strategy_name = ? AND error_type = ?
                ''', (datetime.now().isoformat(), strategy_name, error_type))

        self.db.commit()

    def _track_library_usage(
        self,
        component_name: str,
        code: str,
        success: bool
    ) -> None:
        """Track library usage for learning"""
        if not self.library_tracker:
            return

        # Extract libraries from imports
        import_pattern = r'^(?:from\s+(\S+)|import\s+(\S+))'
        libraries = set()

        for line in code.split('\n'):
            match = re.match(import_pattern, line.strip())
            if match:
                lib = match.group(1) or match.group(2)
                if lib:
                    # Get base library name
                    base_lib = lib.split('.')[0]
                    libraries.add(base_lib)

        for lib in libraries:
            try:
                self.library_tracker.log_library_usage(
                    library_name=lib,
                    component_name=component_name,
                    import_success=True,
                    execution_success=success
                )
            except Exception as e:
                self.logger.warning(f"Failed to log library usage: {e}")

    def _track_fallback_effectiveness(
        self,
        fallbacks_used: List[Dict[str, Any]],
        success: bool
    ) -> None:
        """Track effectiveness of fallback code"""
        if not self.fallback_generator:
            return

        for fallback in fallbacks_used:
            try:
                self.fallback_generator.log_fallback_usage(
                    library_name=fallback.get("library", ""),
                    operation_type=fallback.get("operation", ""),
                    component_name=fallback.get("component", ""),
                    success=success
                )
            except Exception as e:
                self.logger.warning(f"Failed to log fallback usage: {e}")

    def _generate_suggestions(
        self,
        category: str,
        component_type: str,
        errors: List[str]
    ) -> List[Dict[str, Any]]:
        """Generate improvement suggestions based on errors"""
        suggestions = []
        cursor = self.db.cursor()

        # Analyze error patterns
        error_counts = {}
        for error in errors:
            error_type = self._classify_error_type(str(error))
            error_counts[error_type] = error_counts.get(error_type, 0) + 1

        for error_type, count in error_counts.items():
            recommendation = self._get_recommendation(error_type)

            # Check if similar suggestion exists
            cursor.execute('''
                SELECT id FROM improvement_suggestions
                WHERE category = ? AND suggestion_type = ? AND status = 'pending'
            ''', (category, error_type))

            if not cursor.fetchone():
                cursor.execute('''
                    INSERT INTO improvement_suggestions
                    (category, suggestion_type, issue, recommendation, priority)
                    VALUES (?, ?, ?, ?, ?)
                ''', (
                    category,
                    error_type,
                    f"Recurring {error_type} errors ({count} occurrences)",
                    recommendation,
                    "high" if count > 3 else "medium"
                ))

                suggestions.append({
                    "type": error_type,
                    "issue": f"Recurring {error_type} errors",
                    "recommendation": recommendation
                })

        self.db.commit()
        return suggestions

    def _classify_error_type(self, error: str) -> str:
        """Classify error into a type"""
        error_lower = error.lower()

        if "syntax" in error_lower:
            return "syntax"
        elif "import" in error_lower or "module" in error_lower:
            return "import"
        elif "indent" in error_lower:
            return "indentation"
        elif "name" in error_lower and "not defined" in error_lower:
            return "undefined_name"
        elif "type" in error_lower:
            return "type"
        elif "attribute" in error_lower:
            return "attribute"
        elif "parameter" in error_lower or "argument" in error_lower:
            return "parameter"
        else:
            return "unknown"

    def _get_recommendation(self, error_type: str) -> str:
        """Get recommendation for an error type"""
        recommendations = {
            "syntax": "Review code generation templates for common syntax issues. Consider adding syntax validation before output.",
            "import": "Check library compatibility before generation. Use native fallbacks for unavailable libraries.",
            "indentation": "Ensure consistent indentation in generated code. Use 4 spaces per level.",
            "undefined_name": "Verify all variables and functions are defined before use. Check import statements.",
            "type": "Add type validation for parameters. Ensure type hints match actual usage.",
            "attribute": "Verify object attributes exist before access. Check API documentation.",
            "parameter": "Review parameter ordering (required first, optional last). Check default values.",
            "unknown": "Review error patterns and add specific handling."
        }
        return recommendations.get(error_type, recommendations["unknown"])

    def apply_confidence_decay(self) -> Dict[str, int]:
        """
        Apply time-based confidence decay to patterns.

        Patterns that haven't been used recently have their confidence reduced,
        encouraging the system to try newer patterns.

        Returns:
            Dict with counts of affected patterns
        """
        cursor = self.db.cursor()
        now = datetime.now()

        result = {
            "patterns_decayed": 0,
            "patterns_flagged_for_review": 0,
            "patterns_removed": 0
        }

        # Get patterns that need decay
        cursor.execute('''
            SELECT id, pattern_type, pattern_name, category, confidence_score,
                   last_used, last_decay_applied
            FROM pattern_confidence
            WHERE confidence_score > ?
        ''', (self.decay_config.min_confidence,))

        rows = cursor.fetchall()

        for row in rows:
            last_decay = row["last_decay_applied"]
            if last_decay:
                last_decay_date = datetime.fromisoformat(last_decay)
            else:
                last_decay_date = datetime.fromisoformat(row["created_at"] if "created_at" in row.keys() else now.isoformat())

            # Calculate days since last decay
            days_since_decay = (now - last_decay_date).days

            if days_since_decay >= 1:
                # Apply decay
                new_confidence = row["confidence_score"] * (self.decay_config.decay_rate ** days_since_decay)
                new_confidence = max(self.decay_config.min_confidence, new_confidence)

                cursor.execute('''
                    UPDATE pattern_confidence
                    SET confidence_score = ?,
                        last_decay_applied = ?
                    WHERE id = ?
                ''', (new_confidence, now.isoformat(), row["id"]))

                result["patterns_decayed"] += 1

                # Check if pattern needs review
                last_used = row["last_used"]
                if last_used:
                    last_used_date = datetime.fromisoformat(last_used)
                    days_since_use = (now - last_used_date).days

                    if days_since_use > self.decay_config.max_age_days:
                        result["patterns_flagged_for_review"] += 1

        # Remove patterns below minimum confidence
        cursor.execute('''
            DELETE FROM pattern_confidence
            WHERE confidence_score <= ? AND usage_count > 5 AND success_count = 0
        ''', (self.decay_config.min_confidence,))

        result["patterns_removed"] = cursor.rowcount

        self.db.commit()

        self.logger.info(
            f"Confidence decay applied: {result['patterns_decayed']} decayed, "
            f"{result['patterns_flagged_for_review']} flagged, "
            f"{result['patterns_removed']} removed"
        )

        return result

    def validate_patterns(self) -> Dict[str, Any]:
        """
        Validate stored patterns and flag problematic ones.

        Returns:
            Dict with validation results
        """
        cursor = self.db.cursor()

        result = {
            "patterns_validated": 0,
            "patterns_invalid": 0,
            "patterns_low_confidence": 0,
            "recommendations": []
        }

        # Check patterns with low success rate
        cursor.execute('''
            SELECT pattern_type, pattern_name, category,
                   confidence_score, usage_count, success_count, failure_count
            FROM pattern_confidence
            WHERE usage_count > 3
        ''')

        for row in cursor.fetchall():
            result["patterns_validated"] += 1

            success_rate = row["success_count"] / row["usage_count"] if row["usage_count"] > 0 else 0

            if success_rate < 0.5:
                result["patterns_invalid"] += 1
                result["recommendations"].append({
                    "pattern": row["pattern_name"],
                    "issue": f"Low success rate ({success_rate:.0%})",
                    "action": "Review or remove pattern"
                })

            if row["confidence_score"] < 0.3:
                result["patterns_low_confidence"] += 1

        return result

    def get_learning_metrics(self, category: str = None) -> List[LearningMetrics]:
        """
        Get aggregated learning metrics.

        Args:
            category: Optional category filter

        Returns:
            List of LearningMetrics
        """
        cursor = self.db.cursor()

        if category:
            cursor.execute('''
                SELECT * FROM learning_metrics
                WHERE category = ?
                ORDER BY total_generations DESC
            ''', (category,))
        else:
            cursor.execute('''
                SELECT * FROM learning_metrics
                ORDER BY total_generations DESC
            ''')

        metrics = []
        for row in cursor.fetchall():
            total = row["total_generations"]
            metrics.append(LearningMetrics(
                category=row["category"],
                total_generations=total,
                successful_generations=row["successful_generations"],
                failed_generations=row["failed_generations"],
                avg_attempts=row["avg_attempts"],
                avg_tokens=row["avg_tokens"],
                avg_time_seconds=row["avg_time_seconds"],
                first_attempt_success_rate=row["first_attempt_success_count"] / total if total > 0 else 0,
                pattern_match_rate=row["pattern_match_count"] / total if total > 0 else 0,
                error_reduction_rate=row["error_fixed_count"] / row["failed_generations"] if row["failed_generations"] > 0 else 0,
                last_updated=row["last_updated"]
            ))

        return metrics

    def get_improvement_suggestions(
        self,
        category: str = None,
        status: str = "pending"
    ) -> List[Dict[str, Any]]:
        """
        Get improvement suggestions.

        Args:
            category: Optional category filter
            status: Filter by status (pending, in_progress, resolved)

        Returns:
            List of suggestions
        """
        cursor = self.db.cursor()

        if category:
            cursor.execute('''
                SELECT * FROM improvement_suggestions
                WHERE category = ? AND status = ?
                ORDER BY priority DESC, created_at DESC
            ''', (category, status))
        else:
            cursor.execute('''
                SELECT * FROM improvement_suggestions
                WHERE status = ?
                ORDER BY priority DESC, created_at DESC
            ''', (status,))

        return [dict(row) for row in cursor.fetchall()]

    def get_strategy_effectiveness(
        self,
        error_type: str = None
    ) -> List[Dict[str, Any]]:
        """Get effectiveness data for fix strategies"""
        cursor = self.db.cursor()

        if error_type:
            cursor.execute('''
                SELECT * FROM strategy_effectiveness
                WHERE error_type = ?
                ORDER BY effectiveness_score DESC
            ''', (error_type,))
        else:
            cursor.execute('''
                SELECT * FROM strategy_effectiveness
                ORDER BY effectiveness_score DESC
            ''')

        return [dict(row) for row in cursor.fetchall()]

    def run_scheduled_tasks(self) -> Dict[str, Any]:
        """
        Run any scheduled tasks that are due.

        Returns:
            Dict with task execution results
        """
        cursor = self.db.cursor()
        now = datetime.now()

        results = {}

        # Get due tasks
        cursor.execute('''
            SELECT id, task_type, interval_hours
            FROM scheduled_tasks
            WHERE enabled = 1 AND (next_run IS NULL OR next_run <= ?)
        ''', (now.isoformat(),))

        for row in cursor.fetchall():
            task_type = row["task_type"]

            try:
                if task_type == "confidence_decay":
                    results[task_type] = self.apply_confidence_decay()
                elif task_type == "pattern_validation":
                    results[task_type] = self.validate_patterns()
                elif task_type == "metrics_aggregation":
                    results[task_type] = {"status": "completed"}
                elif task_type == "suggestion_generation":
                    results[task_type] = {"status": "completed"}
                elif task_type == "cleanup_old_data":
                    results[task_type] = self._cleanup_old_data()

                # Update next run time
                next_run = now + timedelta(hours=row["interval_hours"])
                cursor.execute('''
                    UPDATE scheduled_tasks
                    SET last_run = ?, next_run = ?
                    WHERE id = ?
                ''', (now.isoformat(), next_run.isoformat(), row["id"]))

            except Exception as e:
                results[task_type] = {"error": str(e)}
                self.logger.error(f"Failed to run scheduled task {task_type}: {e}")

        self.db.commit()
        return results

    def _cleanup_old_data(self, days: int = 90) -> Dict[str, int]:
        """Clean up old data from the database"""
        cursor = self.db.cursor()
        cutoff = (datetime.now() - timedelta(days=days)).isoformat()

        result = {}

        # Clean old feedback logs
        cursor.execute('''
            DELETE FROM generation_feedback
            WHERE timestamp < ?
        ''', (cutoff,))
        result["feedback_deleted"] = cursor.rowcount

        # Clean resolved suggestions
        cursor.execute('''
            DELETE FROM improvement_suggestions
            WHERE status = 'resolved' AND resolved_at < ?
        ''', (cutoff,))
        result["suggestions_deleted"] = cursor.rowcount

        self.db.commit()
        return result

    def get_statistics(self) -> Dict[str, Any]:
        """Get overall continuous learning statistics"""
        cursor = self.db.cursor()

        # Total generations
        cursor.execute("SELECT COUNT(*) FROM generation_feedback")
        total_feedback = cursor.fetchone()[0]

        # Success rate
        cursor.execute('''
            SELECT COUNT(*) FROM generation_feedback WHERE success = 1
        ''')
        successful = cursor.fetchone()[0]

        # Pattern count
        cursor.execute("SELECT COUNT(*) FROM pattern_confidence")
        pattern_count = cursor.fetchone()[0]

        # Average confidence
        cursor.execute("SELECT AVG(confidence_score) FROM pattern_confidence")
        avg_confidence = cursor.fetchone()[0] or 0

        # Strategy count
        cursor.execute("SELECT COUNT(*) FROM strategy_effectiveness")
        strategy_count = cursor.fetchone()[0]

        # Pending suggestions
        cursor.execute('''
            SELECT COUNT(*) FROM improvement_suggestions WHERE status = 'pending'
        ''')
        pending_suggestions = cursor.fetchone()[0]

        # Categories covered
        cursor.execute("SELECT DISTINCT category FROM learning_metrics")
        categories = [row[0] for row in cursor.fetchall()]

        return {
            "total_generations_tracked": total_feedback,
            "success_rate": successful / total_feedback if total_feedback > 0 else 0,
            "patterns_tracked": pattern_count,
            "average_pattern_confidence": avg_confidence,
            "strategies_tracked": strategy_count,
            "pending_suggestions": pending_suggestions,
            "categories": categories,
            "category_count": len(categories)
        }

    def close(self) -> None:
        """Close database connection"""
        if hasattr(self, 'db') and self.db:
            self.db.close()


# Convenience function for creating the learning manager
def create_learning_manager(
    pattern_storage=None,
    error_storage=None,
    library_tracker=None,
    fallback_generator=None
) -> ContinuousLearningManager:
    """
    Create a ContinuousLearningManager with default configuration.

    Args:
        pattern_storage: Phase 1 pattern storage
        error_storage: Phase 2 error storage
        library_tracker: Phase 3 library tracker
        fallback_generator: Phase 4 fallback generator

    Returns:
        Configured ContinuousLearningManager
    """
    return ContinuousLearningManager(
        pattern_storage=pattern_storage,
        error_storage=error_storage,
        library_tracker=library_tracker,
        fallback_generator=fallback_generator
    )
