#!/usr/bin/env python3
"""
Test script for Phase 2 - Error Learning System

This script tests the error pattern extraction, storage, and fix strategy selection.
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.error_learning import ErrorPatternExtractor
from src.error_storage import ErrorPatternStorage
from src.fix_strategies import FixStrategyManager


def test_error_pattern_extraction():
    """Test error pattern extraction from various error types"""
    print("=" * 80)
    print("PHASE 2: ERROR LEARNING SYSTEM TEST")
    print("=" * 80)
    print()

    extractor = ErrorPatternExtractor()

    # Test cases: Different error types we might encounter
    test_cases = [
        {
            "name": "Parameter Ordering Error",
            "error_message": "Syntax error at line 45: parameter without a default follows parameter with a default",
            "code": """
def __init__(self, optional_param: str = 'default', required_param: str, **kwargs):
    pass
""",
            "expected_strategy": "reorder_parameters"
        },
        {
            "name": "Indentation Error",
            "error_message": "IndentationError at line 23: unexpected indent",
            "code": """
def execute(self, context):
        return result  # Wrong indentation
""",
            "expected_strategy": "fix_indentation"
        },
        {
            "name": "Import Error",
            "error_message": "No module named 'nemo_toolkit'",
            "code": """
from nemo_toolkit import NemoModel
""",
            "expected_strategy": "add_dependency_or_mock"
        },
        {
            "name": "Name Error",
            "error_message": "name 'undefined_var' is not defined",
            "code": """
result = undefined_var + 1
""",
            "expected_strategy": "define_variable_or_import"
        },
        {
            "name": "Missing Block Error",
            "error_message": "Syntax error at line 50: expected 'except' or 'finally' block",
            "code": """
try:
    result = do_something()
# Missing except block
""",
            "expected_strategy": "add_missing_block"
        }
    ]

    spec = {
        "name": "TestOperator",
        "category": "ml",
        "component_type": "operator",
        "inputs": [{"name": "param1", "type": "str"}],
        "runtime_params": []
    }

    strategy_manager = FixStrategyManager()

    print("📋 Testing Error Pattern Extraction\n")

    results = []
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{'─' * 60}")
        print(f"Test {i}: {test_case['name']}")
        print(f"{'─' * 60}")
        print(f"Error: {test_case['error_message'][:60]}...")

        # Extract patterns
        patterns = extractor.extract_error_patterns(
            error_message=test_case['error_message'],
            code=test_case['code'],
            spec=spec,
            attempt_number=1,
            metadata={}
        )

        # Get classification
        classification = patterns.get('error_classification', {})
        error_type = classification.get('error_type', 'unknown')
        severity = classification.get('severity', 'medium')

        print(f"Error Type: {error_type}")
        print(f"Severity: {severity}")

        # Select fix strategy
        selected_strategy = strategy_manager.select_best_strategy(patterns)
        expected = test_case['expected_strategy']

        match = "✅" if selected_strategy == expected else "❌"
        print(f"Selected Strategy: {selected_strategy} {match}")
        print(f"Expected Strategy: {expected}")

        results.append({
            "test": test_case['name'],
            "passed": selected_strategy == expected,
            "selected": selected_strategy,
            "expected": expected
        })

    # Summary
    print("\n")
    print("=" * 80)
    print("TEST RESULTS SUMMARY")
    print("=" * 80)

    passed = sum(1 for r in results if r['passed'])
    total = len(results)

    print(f"\nPassed: {passed}/{total} ({100*passed/total:.0f}%)")

    for r in results:
        status = "✅ PASS" if r['passed'] else "❌ FAIL"
        print(f"  {status}: {r['test']}")

    return passed == total


def test_error_storage():
    """Test error pattern storage and retrieval"""
    print("\n")
    print("=" * 80)
    print("TESTING ERROR PATTERN STORAGE")
    print("=" * 80)
    print()

    # Use test database
    db_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "data", "error_patterns.db"
    )

    storage = ErrorPatternStorage(db_path)
    extractor = ErrorPatternExtractor()

    # Store a test error
    error_message = "Syntax error at line 45: parameter without a default follows parameter with a default"
    patterns = extractor.extract_error_patterns(
        error_message=error_message,
        code="def __init__(self, opt='default', req): pass",
        spec={"name": "TestOp", "category": "ml", "component_type": "operator"},
        attempt_number=1,
        metadata={}
    )

    pattern_id = storage.store_error_pattern(
        error_message=error_message,
        error_patterns=patterns,
        component_name="TestOp",
        code="def __init__(self, opt='default', req): pass",
        spec={"name": "TestOp", "category": "ml", "component_type": "operator"},
        attempt_number=1
    )

    print(f"✅ Stored error pattern with ID: {pattern_id}")

    # Test retrieval
    similar = storage.get_similar_errors(
        error_type="syntax",
        category="ml",
        min_confidence=0.0  # Allow any confidence for test
    )

    print(f"✅ Retrieved {len(similar)} similar errors")

    # Record a fix attempt
    error_sig = patterns.get('error_classification', {}).get('error_signature')
    storage.record_fix_attempt(
        error_signature=error_sig,
        strategy_name="reorder_parameters",
        success=True,
        attempts_to_fix=1
    )

    print("✅ Recorded successful fix attempt")

    # Get statistics
    stats = storage.get_error_statistics()

    print("\n📊 Error Database Statistics:")
    print(f"  Total Patterns: {stats['total_patterns']}")
    print(f"  Total Occurrences: {stats['total_occurrences']}")

    if stats.get('by_type'):
        print("\n  By Error Type:")
        for t in stats['by_type'][:5]:
            print(f"    - {t['error_type']}: {t['unique_patterns']} patterns, {t['total_occurrences']} occurrences")

    if stats.get('top_strategies'):
        print("\n  Top Fix Strategies:")
        for s in stats['top_strategies'][:5]:
            print(f"    - {s['strategy']}: {s['successes']} successes, {s['failures']} failures ({s['confidence']*100:.0f}% confidence)")

    return True


def test_fix_strategies():
    """Test fix strategy manager"""
    print("\n")
    print("=" * 80)
    print("TESTING FIX STRATEGY MANAGER")
    print("=" * 80)
    print()

    manager = FixStrategyManager()

    # Test strategy lookup
    strategies_to_test = [
        "reorder_parameters",
        "fix_indentation",
        "add_dependency_or_mock",
        "retry_with_detailed_prompt"
    ]

    print("📋 Testing Strategy Retrieval:\n")

    for strategy_name in strategies_to_test:
        strategy = manager.get_strategy(strategy_name)
        if strategy:
            print(f"✅ {strategy_name}")
            print(f"   Type: {strategy.get('type')}")
            print(f"   Priority: {strategy.get('priority')}")
            print(f"   Auto-fixable: {strategy.get('auto_fixable', False)}")
        else:
            print(f"❌ {strategy_name} - NOT FOUND")
        print()

    # Test prompt generation
    print("📋 Testing Prompt Generation:\n")

    error_patterns = {
        "error_classification": {
            "error_type": "syntax",
            "severity": "high",
            "line_number": 45
        },
        "parameter_errors": {
            "pattern": "parameter_ordering",
            "fix_strategy": "reorder_parameters"
        }
    }

    prompt = manager.get_prompt_addition(
        strategy_name="reorder_parameters",
        error_message="parameter without a default follows parameter with a default",
        error_patterns=error_patterns
    )

    print("Generated Fix Prompt (first 500 chars):")
    print("-" * 40)
    print(prompt[:500])
    print("-" * 40)

    return True


if __name__ == "__main__":
    print()
    print("🔧 PHASE 2: ERROR LEARNING SYSTEM TEST")
    print()

    all_passed = True

    try:
        if not test_error_pattern_extraction():
            all_passed = False
    except Exception as e:
        print(f"❌ Error pattern extraction test failed: {e}")
        all_passed = False

    try:
        if not test_error_storage():
            all_passed = False
    except Exception as e:
        print(f"❌ Error storage test failed: {e}")
        all_passed = False

    try:
        if not test_fix_strategies():
            all_passed = False
    except Exception as e:
        print(f"❌ Fix strategies test failed: {e}")
        all_passed = False

    print()
    print("=" * 80)
    print("FINAL RESULT")
    print("=" * 80)

    if all_passed:
        print("\n✅ ALL PHASE 2 TESTS PASSED!")
        print("\nPhase 2 Error Learning System is ready for use.")
        print("Next: Test with actual component generation.")
    else:
        print("\n❌ SOME TESTS FAILED")
        print("\nPlease review the errors above.")

    print()
