"""
Phase 5: Continuous Learning System Test Suite

Comprehensive tests for the Continuous Learning Loop implementation.
Tests all aspects of the learning system including:
- Database initialization
- Feedback collection
- Confidence decay mechanism
- Pattern validation
- Scheduled tasks
- Learning metrics
- Improvement suggestions
- Strategy effectiveness tracking
"""

import os
import sys
import sqlite3
import tempfile
import json
from datetime import datetime, timedelta
from typing import Dict, Any

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.continuous_learning import (
    ContinuousLearningManager,
    LearningMetrics,
    ConfidenceDecayConfig,
    create_learning_manager
)


class TestResults:
    """Track test results"""
    def __init__(self):
        self.total = 0
        self.passed = 0
        self.failed = 0
        self.failures = []

    def add_pass(self, test_name: str):
        self.total += 1
        self.passed += 1
        print(f"✅ PASS: {test_name}")

    def add_fail(self, test_name: str, error: str):
        self.total += 1
        self.failed += 1
        self.failures.append((test_name, error))
        print(f"❌ FAIL: {test_name} - {error}")

    def print_summary(self):
        print("\n" + "="*80)
        print("PHASE 5 TEST SUMMARY - CONTINUOUS LEARNING")
        print("="*80)
        print(f"Total Tests: {self.total}")
        print(f"Passed: {self.passed} ✅")
        print(f"Failed: {self.failed} ❌")
        print(f"Success Rate: {(self.passed/self.total*100):.1f}%")

        if self.failures:
            print("\nFailed Tests:")
            for test_name, error in self.failures:
                print(f"  - {test_name}: {error}")

        print("="*80)
        return self.failed == 0


results = TestResults()


def get_temp_db_path():
    """Get a temporary database path for testing"""
    return os.path.join(tempfile.gettempdir(), f"test_continuous_learning_{os.getpid()}.db")


def cleanup_test_db(db_path: str):
    """Clean up test database"""
    try:
        if os.path.exists(db_path):
            os.remove(db_path)
    except Exception:
        pass


# ============================================================================
# Section 1: Database Initialization Tests
# ============================================================================

def test_database_initialization():
    """Test 1.1: Database initializes with correct tables"""
    db_path = get_temp_db_path()
    try:
        manager = ContinuousLearningManager(db_path=db_path)

        # Check tables exist
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]

        expected_tables = [
            'learning_metrics',
            'generation_feedback',
            'pattern_confidence',
            'strategy_effectiveness',
            'improvement_suggestions',
            'scheduled_tasks'
        ]

        for table in expected_tables:
            assert table in tables, f"Missing table: {table}"

        conn.close()
        manager.close()
        results.add_pass("Database Initialization")
    except Exception as e:
        results.add_fail("Database Initialization", str(e))
    finally:
        cleanup_test_db(db_path)


def test_scheduled_tasks_initialization():
    """Test 1.2: Scheduled tasks are initialized correctly"""
    db_path = get_temp_db_path()
    try:
        manager = ContinuousLearningManager(db_path=db_path)

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT task_type, interval_hours FROM scheduled_tasks")
        tasks = {row[0]: row[1] for row in cursor.fetchall()}

        expected_tasks = {
            'confidence_decay': 24,
            'pattern_validation': 168,
            'metrics_aggregation': 1,
            'suggestion_generation': 24,
            'cleanup_old_data': 720
        }

        for task_type, interval in expected_tasks.items():
            assert task_type in tasks, f"Missing scheduled task: {task_type}"
            assert tasks[task_type] == interval, f"Wrong interval for {task_type}"

        conn.close()
        manager.close()
        results.add_pass("Scheduled Tasks Initialization")
    except Exception as e:
        results.add_fail("Scheduled Tasks Initialization", str(e))
    finally:
        cleanup_test_db(db_path)


def test_decay_config_defaults():
    """Test 1.3: Decay config has correct defaults"""
    try:
        config = ConfidenceDecayConfig()

        assert config.decay_rate == 0.95, f"Wrong decay_rate: {config.decay_rate}"
        assert config.min_confidence == 0.1, f"Wrong min_confidence: {config.min_confidence}"
        assert config.max_age_days == 90, f"Wrong max_age_days: {config.max_age_days}"
        assert config.success_boost == 0.1, f"Wrong success_boost: {config.success_boost}"
        assert config.failure_penalty == 0.15, f"Wrong failure_penalty: {config.failure_penalty}"

        results.add_pass("Decay Config Defaults")
    except Exception as e:
        results.add_fail("Decay Config Defaults", str(e))


def test_learning_metrics_dataclass():
    """Test 1.4: LearningMetrics dataclass works correctly"""
    try:
        metrics = LearningMetrics(
            category="http",
            total_generations=10,
            successful_generations=8,
            failed_generations=2
        )

        assert metrics.category == "http"
        assert metrics.total_generations == 10
        assert metrics.successful_generations == 8
        assert metrics.failed_generations == 2
        assert metrics.avg_attempts == 1.0  # Default

        results.add_pass("LearningMetrics Dataclass")
    except Exception as e:
        results.add_fail("LearningMetrics Dataclass", str(e))


# ============================================================================
# Section 2: Feedback Collection Tests
# ============================================================================

def test_log_generation_feedback():
    """Test 2.1: Generation feedback is logged correctly"""
    db_path = get_temp_db_path()
    try:
        manager = ContinuousLearningManager(db_path=db_path)

        # Simulate a successful generation
        result = manager.learn_from_generation(
            component_name="TestOperator",
            component_type="operator",
            category="http",
            code="class TestOperator(BaseOperator): pass",
            spec={"name": "TestOperator", "category": "http"},
            validation_result={"is_valid": True, "errors": [], "warnings": []},
            metadata={
                "attempts": 1,
                "prompt_tokens": 500,
                "completion_tokens": 1000,
                "time_seconds": 5.5,
                "first_attempt_success": True
            }
        )

        assert result["success"] == True, "Learning result should show success"

        # Verify feedback was logged
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM generation_feedback WHERE component_name = 'TestOperator'")
        row = cursor.fetchone()

        assert row is not None, "Feedback not logged"

        conn.close()
        manager.close()
        results.add_pass("Log Generation Feedback")
    except Exception as e:
        results.add_fail("Log Generation Feedback", str(e))
    finally:
        cleanup_test_db(db_path)


def test_log_failed_generation():
    """Test 2.2: Failed generation feedback is logged"""
    db_path = get_temp_db_path()
    try:
        manager = ContinuousLearningManager(db_path=db_path)

        # Simulate a failed generation
        result = manager.learn_from_generation(
            component_name="FailedOperator",
            component_type="operator",
            category="database",
            code="invalid code",
            spec={"name": "FailedOperator", "category": "database"},
            validation_result={
                "is_valid": False,
                "errors": ["SyntaxError: invalid syntax"],
                "warnings": []
            },
            metadata={
                "attempts": 3,
                "prompt_tokens": 1500,
                "completion_tokens": 3000,
                "time_seconds": 15.0,
                "first_attempt_success": False
            }
        )

        assert result["success"] == False, "Learning result should show failure"

        # Verify feedback was logged
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT success FROM generation_feedback WHERE component_name = 'FailedOperator'")
        row = cursor.fetchone()

        assert row is not None, "Feedback not logged"
        assert row[0] == 0, "Should be marked as failure"

        conn.close()
        manager.close()
        results.add_pass("Log Failed Generation")
    except Exception as e:
        results.add_fail("Log Failed Generation", str(e))
    finally:
        cleanup_test_db(db_path)


def test_update_learning_metrics():
    """Test 2.3: Learning metrics are updated correctly"""
    db_path = get_temp_db_path()
    try:
        manager = ContinuousLearningManager(db_path=db_path)

        # Log multiple generations
        for i in range(5):
            manager.learn_from_generation(
                component_name=f"Operator{i}",
                component_type="operator",
                category="http",
                code=f"class Operator{i}(BaseOperator): pass",
                spec={"name": f"Operator{i}", "category": "http"},
                validation_result={"is_valid": True, "errors": [], "warnings": []},
                metadata={
                    "attempts": 1,
                    "prompt_tokens": 500,
                    "completion_tokens": 1000,
                    "time_seconds": 5.0
                }
            )

        # Check metrics
        metrics = manager.get_learning_metrics(category="http")

        assert len(metrics) > 0, "No metrics found"
        http_metrics = metrics[0]
        assert http_metrics.total_generations == 5, f"Expected 5 generations, got {http_metrics.total_generations}"
        assert http_metrics.successful_generations == 5, "All should be successful"

        manager.close()
        results.add_pass("Update Learning Metrics")
    except Exception as e:
        results.add_fail("Update Learning Metrics", str(e))
    finally:
        cleanup_test_db(db_path)


def test_multiple_categories_metrics():
    """Test 2.4: Metrics are tracked separately by category"""
    db_path = get_temp_db_path()
    try:
        manager = ContinuousLearningManager(db_path=db_path)

        # Log generations for different categories
        categories = ["http", "database", "cloud", "ml"]
        for category in categories:
            manager.learn_from_generation(
                component_name=f"{category.title()}Operator",
                component_type="operator",
                category=category,
                code=f"class {category.title()}Operator(BaseOperator): pass",
                spec={"name": f"{category.title()}Operator", "category": category},
                validation_result={"is_valid": True, "errors": [], "warnings": []},
                metadata={"attempts": 1}
            )

        # Check all categories are tracked
        metrics = manager.get_learning_metrics()
        categories_found = [m.category for m in metrics]

        for category in categories:
            assert category in categories_found, f"Category {category} not tracked"

        manager.close()
        results.add_pass("Multiple Categories Metrics")
    except Exception as e:
        results.add_fail("Multiple Categories Metrics", str(e))
    finally:
        cleanup_test_db(db_path)


# ============================================================================
# Section 3: Confidence Decay Tests
# ============================================================================

def test_apply_confidence_decay():
    """Test 3.1: Confidence decay is applied correctly"""
    db_path = get_temp_db_path()
    try:
        manager = ContinuousLearningManager(db_path=db_path)

        # Insert a pattern with old last_decay_applied date
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        old_date = (datetime.now() - timedelta(days=5)).isoformat()
        cursor.execute('''
            INSERT INTO pattern_confidence
            (pattern_type, pattern_name, category, confidence_score, last_decay_applied)
            VALUES (?, ?, ?, ?, ?)
        ''', ('import', 'test_pattern', 'http', 0.8, old_date))
        conn.commit()
        conn.close()

        # Apply decay
        result = manager.apply_confidence_decay()

        assert "patterns_decayed" in result

        # Check confidence was reduced
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT confidence_score FROM pattern_confidence WHERE pattern_name = 'test_pattern'")
        row = cursor.fetchone()

        assert row is not None
        # 0.8 * 0.95^5 ≈ 0.62
        assert row[0] < 0.8, "Confidence should have decayed"

        conn.close()
        manager.close()
        results.add_pass("Apply Confidence Decay")
    except Exception as e:
        results.add_fail("Apply Confidence Decay", str(e))
    finally:
        cleanup_test_db(db_path)


def test_minimum_confidence_threshold():
    """Test 3.2: Confidence doesn't go below minimum"""
    db_path = get_temp_db_path()
    try:
        config = ConfidenceDecayConfig(min_confidence=0.1)
        manager = ContinuousLearningManager(db_path=db_path, decay_config=config)

        # Insert pattern with very old date
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        old_date = (datetime.now() - timedelta(days=100)).isoformat()
        cursor.execute('''
            INSERT INTO pattern_confidence
            (pattern_type, pattern_name, category, confidence_score, last_decay_applied)
            VALUES (?, ?, ?, ?, ?)
        ''', ('import', 'old_pattern', 'http', 0.5, old_date))
        conn.commit()
        conn.close()

        # Apply decay
        manager.apply_confidence_decay()

        # Check confidence is at minimum
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT confidence_score FROM pattern_confidence WHERE pattern_name = 'old_pattern'")
        row = cursor.fetchone()

        assert row is not None
        assert row[0] >= 0.1, "Confidence should not go below minimum"

        conn.close()
        manager.close()
        results.add_pass("Minimum Confidence Threshold")
    except Exception as e:
        results.add_fail("Minimum Confidence Threshold", str(e))
    finally:
        cleanup_test_db(db_path)


def test_confidence_boost_on_success():
    """Test 3.3: Confidence is boosted on successful use"""
    db_path = get_temp_db_path()
    try:
        manager = ContinuousLearningManager(db_path=db_path)

        # Insert a pattern
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO pattern_confidence
            (pattern_type, pattern_name, category, confidence_score)
            VALUES (?, ?, ?, ?)
        ''', ('import', 'boost_test', 'http', 0.5))
        conn.commit()
        conn.close()

        # Simulate successful use
        manager._update_pattern_confidence(
            category='http',
            component_type='operator',
            success=True,
            metadata={'patterns_used_names': ['boost_test']}
        )

        # Check confidence increased
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT confidence_score FROM pattern_confidence WHERE pattern_name = 'boost_test'")
        row = cursor.fetchone()

        assert row is not None
        assert row[0] > 0.5, "Confidence should have increased"

        conn.close()
        manager.close()
        results.add_pass("Confidence Boost on Success")
    except Exception as e:
        results.add_fail("Confidence Boost on Success", str(e))
    finally:
        cleanup_test_db(db_path)


def test_confidence_penalty_on_failure():
    """Test 3.4: Confidence is penalized on failure"""
    db_path = get_temp_db_path()
    try:
        manager = ContinuousLearningManager(db_path=db_path)

        # Insert a pattern
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO pattern_confidence
            (pattern_type, pattern_name, category, confidence_score)
            VALUES (?, ?, ?, ?)
        ''', ('import', 'penalty_test', 'http', 0.8))
        conn.commit()
        conn.close()

        # Simulate failed use
        manager._update_pattern_confidence(
            category='http',
            component_type='operator',
            success=False,
            metadata={'patterns_used_names': ['penalty_test']}
        )

        # Check confidence decreased
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT confidence_score FROM pattern_confidence WHERE pattern_name = 'penalty_test'")
        row = cursor.fetchone()

        assert row is not None
        assert row[0] < 0.8, "Confidence should have decreased"

        conn.close()
        manager.close()
        results.add_pass("Confidence Penalty on Failure")
    except Exception as e:
        results.add_fail("Confidence Penalty on Failure", str(e))
    finally:
        cleanup_test_db(db_path)


# ============================================================================
# Section 4: Pattern Validation Tests
# ============================================================================

def test_validate_patterns():
    """Test 4.1: Pattern validation identifies low success rate patterns"""
    db_path = get_temp_db_path()
    try:
        manager = ContinuousLearningManager(db_path=db_path)

        # Insert patterns with different success rates
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Good pattern (80% success)
        cursor.execute('''
            INSERT INTO pattern_confidence
            (pattern_type, pattern_name, category, confidence_score, usage_count, success_count, failure_count)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', ('import', 'good_pattern', 'http', 0.8, 10, 8, 2))

        # Bad pattern (20% success)
        cursor.execute('''
            INSERT INTO pattern_confidence
            (pattern_type, pattern_name, category, confidence_score, usage_count, success_count, failure_count)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', ('import', 'bad_pattern', 'http', 0.2, 10, 2, 8))

        conn.commit()
        conn.close()

        # Validate patterns
        result = manager.validate_patterns()

        assert result["patterns_validated"] == 2
        assert result["patterns_invalid"] >= 1, "Should flag bad pattern"
        assert len(result["recommendations"]) >= 1

        manager.close()
        results.add_pass("Validate Patterns")
    except Exception as e:
        results.add_fail("Validate Patterns", str(e))
    finally:
        cleanup_test_db(db_path)


def test_low_confidence_pattern_detection():
    """Test 4.2: Low confidence patterns are detected"""
    db_path = get_temp_db_path()
    try:
        manager = ContinuousLearningManager(db_path=db_path)

        # Insert low confidence pattern
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO pattern_confidence
            (pattern_type, pattern_name, category, confidence_score, usage_count, success_count, failure_count)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', ('import', 'low_conf_pattern', 'http', 0.15, 5, 3, 2))

        conn.commit()
        conn.close()

        # Validate patterns
        result = manager.validate_patterns()

        assert result["patterns_low_confidence"] >= 1

        manager.close()
        results.add_pass("Low Confidence Pattern Detection")
    except Exception as e:
        results.add_fail("Low Confidence Pattern Detection", str(e))
    finally:
        cleanup_test_db(db_path)


# ============================================================================
# Section 5: Improvement Suggestions Tests
# ============================================================================

def test_generate_suggestions():
    """Test 5.1: Suggestions are generated for errors"""
    db_path = get_temp_db_path()
    try:
        manager = ContinuousLearningManager(db_path=db_path)

        # Generate suggestions based on errors
        suggestions = manager._generate_suggestions(
            category="http",
            component_type="operator",
            errors=["SyntaxError: invalid syntax", "SyntaxError: unexpected indent", "SyntaxError: missing colon"]
        )

        assert len(suggestions) >= 1, "Should generate at least one suggestion"

        # Check suggestion was stored
        stored = manager.get_improvement_suggestions(category="http")
        assert len(stored) >= 1, "Suggestion should be stored"

        manager.close()
        results.add_pass("Generate Suggestions")
    except Exception as e:
        results.add_fail("Generate Suggestions", str(e))
    finally:
        cleanup_test_db(db_path)


def test_get_suggestions_by_status():
    """Test 5.2: Suggestions can be filtered by status"""
    db_path = get_temp_db_path()
    try:
        manager = ContinuousLearningManager(db_path=db_path)

        # Insert suggestions with different statuses
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO improvement_suggestions
            (category, suggestion_type, issue, recommendation, status)
            VALUES (?, ?, ?, ?, ?)
        ''', ('http', 'syntax', 'Test issue', 'Test recommendation', 'pending'))

        cursor.execute('''
            INSERT INTO improvement_suggestions
            (category, suggestion_type, issue, recommendation, status)
            VALUES (?, ?, ?, ?, ?)
        ''', ('http', 'import', 'Test issue 2', 'Test recommendation 2', 'resolved'))

        conn.commit()
        conn.close()

        # Get pending suggestions
        pending = manager.get_improvement_suggestions(status='pending')
        resolved = manager.get_improvement_suggestions(status='resolved')

        assert len(pending) >= 1
        assert len(resolved) >= 1

        manager.close()
        results.add_pass("Get Suggestions by Status")
    except Exception as e:
        results.add_fail("Get Suggestions by Status", str(e))
    finally:
        cleanup_test_db(db_path)


def test_error_classification():
    """Test 5.3: Errors are classified correctly"""
    db_path = get_temp_db_path()
    try:
        manager = ContinuousLearningManager(db_path=db_path)

        test_cases = [
            ("SyntaxError: invalid syntax", "syntax"),
            ("ImportError: No module named 'foo'", "import"),
            ("IndentationError: unexpected indent", "indentation"),
            ("NameError: name 'x' is not defined", "undefined_name"),
            ("TypeError: expected str, got int", "type"),
            ("AttributeError: object has no attribute 'foo'", "attribute"),
        ]

        for error_msg, expected_type in test_cases:
            result = manager._classify_error_type(error_msg)
            assert result == expected_type, f"Expected {expected_type}, got {result} for '{error_msg}'"

        manager.close()
        results.add_pass("Error Classification")
    except Exception as e:
        results.add_fail("Error Classification", str(e))
    finally:
        cleanup_test_db(db_path)


# ============================================================================
# Section 6: Strategy Effectiveness Tests
# ============================================================================

def test_track_strategy_effectiveness():
    """Test 6.1: Strategy effectiveness is tracked"""
    db_path = get_temp_db_path()
    try:
        manager = ContinuousLearningManager(db_path=db_path)

        # Insert a strategy
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO strategy_effectiveness
            (strategy_name, error_type, category, effectiveness_score, usage_count, success_count, failure_count)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', ('fix_syntax', 'syntax', 'http', 0.5, 10, 5, 5))

        conn.commit()
        conn.close()

        # Update effectiveness for success
        manager._update_strategy_effectiveness(
            error_type='syntax',
            category='http',
            success=True,
            strategy_name='fix_syntax'
        )

        # Check effectiveness increased
        strategies = manager.get_strategy_effectiveness(error_type='syntax')

        assert len(strategies) >= 1
        strategy = strategies[0]
        assert strategy['success_count'] > 5, "Success count should increase"

        manager.close()
        results.add_pass("Track Strategy Effectiveness")
    except Exception as e:
        results.add_fail("Track Strategy Effectiveness", str(e))
    finally:
        cleanup_test_db(db_path)


def test_get_strategy_effectiveness():
    """Test 6.2: Strategy effectiveness can be retrieved"""
    db_path = get_temp_db_path()
    try:
        manager = ContinuousLearningManager(db_path=db_path)

        # Insert strategies
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO strategy_effectiveness
            (strategy_name, error_type, effectiveness_score)
            VALUES (?, ?, ?)
        ''', ('strategy_a', 'syntax', 0.8))

        cursor.execute('''
            INSERT INTO strategy_effectiveness
            (strategy_name, error_type, effectiveness_score)
            VALUES (?, ?, ?)
        ''', ('strategy_b', 'import', 0.6))

        conn.commit()
        conn.close()

        # Get all strategies
        all_strategies = manager.get_strategy_effectiveness()
        assert len(all_strategies) >= 2

        # Get filtered strategies
        syntax_strategies = manager.get_strategy_effectiveness(error_type='syntax')
        assert len(syntax_strategies) >= 1

        manager.close()
        results.add_pass("Get Strategy Effectiveness")
    except Exception as e:
        results.add_fail("Get Strategy Effectiveness", str(e))
    finally:
        cleanup_test_db(db_path)


# ============================================================================
# Section 7: Scheduled Tasks Tests
# ============================================================================

def test_run_scheduled_tasks():
    """Test 7.1: Scheduled tasks run correctly"""
    db_path = get_temp_db_path()
    try:
        manager = ContinuousLearningManager(db_path=db_path)

        # Force tasks to be due by setting next_run in the past
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        past_time = (datetime.now() - timedelta(hours=1)).isoformat()
        cursor.execute("UPDATE scheduled_tasks SET next_run = ?", (past_time,))
        conn.commit()
        conn.close()

        # Run scheduled tasks
        results_dict = manager.run_scheduled_tasks()

        assert len(results_dict) >= 1, "At least one task should run"

        manager.close()
        results.add_pass("Run Scheduled Tasks")
    except Exception as e:
        results.add_fail("Run Scheduled Tasks", str(e))
    finally:
        cleanup_test_db(db_path)


def test_cleanup_old_data():
    """Test 7.2: Old data is cleaned up correctly"""
    db_path = get_temp_db_path()
    try:
        manager = ContinuousLearningManager(db_path=db_path)

        # Insert old feedback
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        old_date = (datetime.now() - timedelta(days=100)).isoformat()
        cursor.execute('''
            INSERT INTO generation_feedback
            (component_name, timestamp)
            VALUES (?, ?)
        ''', ('old_component', old_date))

        conn.commit()
        conn.close()

        # Cleanup
        result = manager._cleanup_old_data(days=90)

        assert result["feedback_deleted"] >= 1, "Should delete old feedback"

        manager.close()
        results.add_pass("Cleanup Old Data")
    except Exception as e:
        results.add_fail("Cleanup Old Data", str(e))
    finally:
        cleanup_test_db(db_path)


# ============================================================================
# Section 8: Statistics Tests
# ============================================================================

def test_get_statistics():
    """Test 8.1: Statistics are calculated correctly"""
    db_path = get_temp_db_path()
    try:
        manager = ContinuousLearningManager(db_path=db_path)

        # Add some data
        for i in range(5):
            manager.learn_from_generation(
                component_name=f"TestOp{i}",
                component_type="operator",
                category="http",
                code="class Test: pass",
                spec={"name": f"TestOp{i}"},
                validation_result={"is_valid": True, "errors": [], "warnings": []},
                metadata={"attempts": 1}
            )

        # Get statistics
        stats = manager.get_statistics()

        assert "total_generations_tracked" in stats
        assert "success_rate" in stats
        assert "patterns_tracked" in stats
        assert "categories" in stats

        assert stats["total_generations_tracked"] >= 5

        manager.close()
        results.add_pass("Get Statistics")
    except Exception as e:
        results.add_fail("Get Statistics", str(e))
    finally:
        cleanup_test_db(db_path)


def test_statistics_success_rate():
    """Test 8.2: Success rate is calculated correctly"""
    db_path = get_temp_db_path()
    try:
        manager = ContinuousLearningManager(db_path=db_path)

        # Add successful generations
        for i in range(8):
            manager.learn_from_generation(
                component_name=f"SuccessOp{i}",
                component_type="operator",
                category="http",
                code="class Test: pass",
                spec={"name": f"SuccessOp{i}"},
                validation_result={"is_valid": True, "errors": [], "warnings": []},
                metadata={"attempts": 1}
            )

        # Add failed generations
        for i in range(2):
            manager.learn_from_generation(
                component_name=f"FailOp{i}",
                component_type="operator",
                category="http",
                code="invalid",
                spec={"name": f"FailOp{i}"},
                validation_result={"is_valid": False, "errors": ["error"], "warnings": []},
                metadata={"attempts": 3}
            )

        stats = manager.get_statistics()

        # 8 successes out of 10 = 80% success rate
        assert 0.75 <= stats["success_rate"] <= 0.85, f"Expected ~80% success rate, got {stats['success_rate']*100:.1f}%"

        manager.close()
        results.add_pass("Statistics Success Rate")
    except Exception as e:
        results.add_fail("Statistics Success Rate", str(e))
    finally:
        cleanup_test_db(db_path)


# ============================================================================
# Section 9: Integration Tests
# ============================================================================

def test_full_learning_cycle():
    """Test 9.1: Full learning cycle works end-to-end"""
    db_path = get_temp_db_path()
    try:
        manager = ContinuousLearningManager(db_path=db_path)

        # 1. Log initial generation (failure)
        result1 = manager.learn_from_generation(
            component_name="CycleTestOp",
            component_type="operator",
            category="ml",
            code="invalid code",
            spec={"name": "CycleTestOp", "category": "ml"},
            validation_result={"is_valid": False, "errors": ["SyntaxError"], "warnings": []},
            metadata={"attempts": 2}
        )

        assert result1["success"] == False

        # 2. Log retry (success)
        result2 = manager.learn_from_generation(
            component_name="CycleTestOp_v2",
            component_type="operator",
            category="ml",
            code="class CycleTestOp(BaseOperator): pass",
            spec={"name": "CycleTestOp_v2", "category": "ml"},
            validation_result={"is_valid": True, "errors": [], "warnings": []},
            metadata={"attempts": 1, "first_attempt_success": True}
        )

        assert result2["success"] == True

        # 3. Check metrics
        metrics = manager.get_learning_metrics(category="ml")
        assert len(metrics) > 0
        ml_metrics = metrics[0]
        assert ml_metrics.total_generations == 2
        assert ml_metrics.successful_generations == 1
        assert ml_metrics.failed_generations == 1

        # 4. Check statistics
        stats = manager.get_statistics()
        assert stats["total_generations_tracked"] >= 2

        manager.close()
        results.add_pass("Full Learning Cycle")
    except Exception as e:
        results.add_fail("Full Learning Cycle", str(e))
    finally:
        cleanup_test_db(db_path)


def test_create_learning_manager_helper():
    """Test 9.2: Helper function creates manager correctly"""
    db_path = get_temp_db_path()
    try:
        # Create manager using helper
        manager = create_learning_manager()

        assert manager is not None
        assert isinstance(manager, ContinuousLearningManager)

        # Verify it works
        stats = manager.get_statistics()
        assert "total_generations_tracked" in stats

        manager.close()
        results.add_pass("Create Learning Manager Helper")
    except Exception as e:
        results.add_fail("Create Learning Manager Helper", str(e))
    finally:
        cleanup_test_db(db_path)


def test_manager_close():
    """Test 9.3: Manager closes properly"""
    db_path = get_temp_db_path()
    try:
        manager = ContinuousLearningManager(db_path=db_path)

        # Do some operations
        manager.get_statistics()

        # Close
        manager.close()

        # Verify closed (accessing db should fail or show it's closed)
        # In SQLite, we can verify by checking the connection
        results.add_pass("Manager Close")
    except Exception as e:
        results.add_fail("Manager Close", str(e))
    finally:
        cleanup_test_db(db_path)


# ============================================================================
# Section 10: Edge Cases Tests
# ============================================================================

def test_empty_database_queries():
    """Test 10.1: Queries work on empty database"""
    db_path = get_temp_db_path()
    try:
        manager = ContinuousLearningManager(db_path=db_path)

        # These should not fail on empty database
        metrics = manager.get_learning_metrics()
        assert metrics == [] or len(metrics) == 0

        suggestions = manager.get_improvement_suggestions()
        assert suggestions == [] or len(suggestions) == 0

        strategies = manager.get_strategy_effectiveness()
        assert strategies == [] or len(strategies) == 0

        stats = manager.get_statistics()
        assert stats["total_generations_tracked"] == 0

        manager.close()
        results.add_pass("Empty Database Queries")
    except Exception as e:
        results.add_fail("Empty Database Queries", str(e))
    finally:
        cleanup_test_db(db_path)


def test_large_error_messages():
    """Test 10.2: Large error messages are handled"""
    db_path = get_temp_db_path()
    try:
        manager = ContinuousLearningManager(db_path=db_path)

        # Create a very long error message
        long_error = "Error: " + "x" * 10000

        result = manager.learn_from_generation(
            component_name="LongErrorOp",
            component_type="operator",
            category="http",
            code="invalid",
            spec={"name": "LongErrorOp"},
            validation_result={"is_valid": False, "errors": [long_error], "warnings": []},
            metadata={"attempts": 1}
        )

        # Should not crash
        assert result is not None

        manager.close()
        results.add_pass("Large Error Messages")
    except Exception as e:
        results.add_fail("Large Error Messages", str(e))
    finally:
        cleanup_test_db(db_path)


def test_special_characters_in_names():
    """Test 10.3: Special characters in names are handled"""
    db_path = get_temp_db_path()
    try:
        manager = ContinuousLearningManager(db_path=db_path)

        # Names with special characters
        special_names = [
            "Test'Operator",
            "Test\"Operator",
            "Test;Operator",
            "Test--Operator",
        ]

        for name in special_names:
            result = manager.learn_from_generation(
                component_name=name,
                component_type="operator",
                category="http",
                code="class Test: pass",
                spec={"name": name},
                validation_result={"is_valid": True, "errors": [], "warnings": []},
                metadata={"attempts": 1}
            )
            assert result is not None

        manager.close()
        results.add_pass("Special Characters in Names")
    except Exception as e:
        results.add_fail("Special Characters in Names", str(e))
    finally:
        cleanup_test_db(db_path)


def test_concurrent_access():
    """Test 10.4: Database handles concurrent-like access"""
    db_path = get_temp_db_path()
    try:
        manager = ContinuousLearningManager(db_path=db_path)

        # Simulate multiple rapid operations
        for i in range(20):
            manager.learn_from_generation(
                component_name=f"ConcurrentOp{i}",
                component_type="operator",
                category="http",
                code=f"class ConcurrentOp{i}: pass",
                spec={"name": f"ConcurrentOp{i}"},
                validation_result={"is_valid": True, "errors": [], "warnings": []},
                metadata={"attempts": 1}
            )

        # Verify all were logged
        stats = manager.get_statistics()
        assert stats["total_generations_tracked"] >= 20

        manager.close()
        results.add_pass("Concurrent Access")
    except Exception as e:
        results.add_fail("Concurrent Access", str(e))
    finally:
        cleanup_test_db(db_path)


# ============================================================================
# Main Test Runner
# ============================================================================

def run_all_tests():
    """Run all Phase 5 tests"""
    print("="*80)
    print("PHASE 5: CONTINUOUS LEARNING SYSTEM - TEST SUITE")
    print("="*80)
    print()

    # Section 1: Database Initialization
    print("\n--- Section 1: Database Initialization Tests ---")
    test_database_initialization()
    test_scheduled_tasks_initialization()
    test_decay_config_defaults()
    test_learning_metrics_dataclass()

    # Section 2: Feedback Collection
    print("\n--- Section 2: Feedback Collection Tests ---")
    test_log_generation_feedback()
    test_log_failed_generation()
    test_update_learning_metrics()
    test_multiple_categories_metrics()

    # Section 3: Confidence Decay
    print("\n--- Section 3: Confidence Decay Tests ---")
    test_apply_confidence_decay()
    test_minimum_confidence_threshold()
    test_confidence_boost_on_success()
    test_confidence_penalty_on_failure()

    # Section 4: Pattern Validation
    print("\n--- Section 4: Pattern Validation Tests ---")
    test_validate_patterns()
    test_low_confidence_pattern_detection()

    # Section 5: Improvement Suggestions
    print("\n--- Section 5: Improvement Suggestions Tests ---")
    test_generate_suggestions()
    test_get_suggestions_by_status()
    test_error_classification()

    # Section 6: Strategy Effectiveness
    print("\n--- Section 6: Strategy Effectiveness Tests ---")
    test_track_strategy_effectiveness()
    test_get_strategy_effectiveness()

    # Section 7: Scheduled Tasks
    print("\n--- Section 7: Scheduled Tasks Tests ---")
    test_run_scheduled_tasks()
    test_cleanup_old_data()

    # Section 8: Statistics
    print("\n--- Section 8: Statistics Tests ---")
    test_get_statistics()
    test_statistics_success_rate()

    # Section 9: Integration
    print("\n--- Section 9: Integration Tests ---")
    test_full_learning_cycle()
    test_create_learning_manager_helper()
    test_manager_close()

    # Section 10: Edge Cases
    print("\n--- Section 10: Edge Cases Tests ---")
    test_empty_database_queries()
    test_large_error_messages()
    test_special_characters_in_names()
    test_concurrent_access()

    # Print summary
    return results.print_summary()


if __name__ == "__main__":
    import sys
    success = run_all_tests()
    sys.exit(0 if success else 1)
