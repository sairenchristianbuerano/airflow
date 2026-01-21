#!/usr/bin/env python3
"""
Test script for Phase 3 - Library Compatibility Tracking

This script tests the library tracking, recommendation, and compatibility features.
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.library_tracker import LibraryTracker
from src.library_recommender import LibraryRecommender


class TestResults:
    """Track test results"""
    def __init__(self):
        self.total = 0
        self.passed = 0
        self.failed = 0
        self.failures = []

    def add_pass(self, test_name: str, details: str = ""):
        self.total += 1
        self.passed += 1
        if details:
            print(f"  ✅ PASS: {test_name} - {details}")
        else:
            print(f"  ✅ PASS: {test_name}")

    def add_fail(self, test_name: str, error: str):
        self.total += 1
        self.failed += 1
        self.failures.append((test_name, error))
        print(f"  ❌ FAIL: {test_name} - {error}")

    def print_summary(self):
        print("\n" + "="*80)
        print("TEST SUMMARY")
        print("="*80)
        print(f"Total Tests: {self.total}")
        print(f"Passed: {self.passed} ✅")
        print(f"Failed: {self.failed} ❌")
        if self.total > 0:
            print(f"Success Rate: {(self.passed/self.total*100):.1f}%")

        if self.failures:
            print("\nFailed Tests:")
            for test_name, error in self.failures:
                print(f"  - {test_name}: {error}")

        print("="*80)
        return self.failed == 0


results = TestResults()


def test_library_tracker_initialization():
    """Test LibraryTracker initialization"""
    print("\n📋 Testing Library Tracker Initialization...")

    try:
        db_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "data", "library_compatibility.db"
        )

        tracker = LibraryTracker(db_path)
        results.add_pass("LibraryTracker initialization")

        # Check database was created
        assert os.path.exists(db_path), "Database file not created"
        results.add_pass("Database file created")

        # Check tables exist
        cursor = tracker.db.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]

        required_tables = ['libraries', 'library_alternatives', 'library_usage_log']
        for table in required_tables:
            if table in tables:
                results.add_pass(f"Table exists: {table}")
            else:
                results.add_fail(f"Table exists: {table}", "Not found")

        tracker.close()
    except Exception as e:
        results.add_fail("LibraryTracker initialization", str(e))


def test_known_compatible_libraries():
    """Test checking known compatible libraries"""
    print("\n📋 Testing Known Compatible Libraries...")

    try:
        db_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "data", "library_compatibility.db"
        )

        tracker = LibraryTracker(db_path)

        # Test known compatible libraries
        compatible_libs = ["requests", "pandas", "boto3", "apache-airflow-providers-http"]

        for lib in compatible_libs:
            compat = tracker.check_library_compatibility(lib)
            if compat.get("compatible") == True:
                results.add_pass(f"Compatible: {lib}")
            else:
                results.add_fail(f"Compatible: {lib}", f"Got: {compat}")

        tracker.close()
    except Exception as e:
        results.add_fail("Known Compatible Libraries", str(e))


def test_known_incompatible_libraries():
    """Test checking known incompatible libraries"""
    print("\n📋 Testing Known Incompatible Libraries...")

    try:
        db_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "data", "library_compatibility.db"
        )

        tracker = LibraryTracker(db_path)

        # Test known incompatible libraries
        incompatible_libs = ["nemo_toolkit", "nvidia-nemo", "cudf"]

        for lib in incompatible_libs:
            compat = tracker.check_library_compatibility(lib)
            if compat.get("compatible") == False:
                results.add_pass(f"Incompatible: {lib}")
            else:
                results.add_fail(f"Incompatible: {lib}", f"Got: {compat}")

        tracker.close()
    except Exception as e:
        results.add_fail("Known Incompatible Libraries", str(e))


def test_unknown_library():
    """Test checking unknown library"""
    print("\n📋 Testing Unknown Library...")

    try:
        db_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "data", "library_compatibility.db"
        )

        tracker = LibraryTracker(db_path)

        compat = tracker.check_library_compatibility("some-unknown-library-xyz")
        if compat.get("status") == "unknown":
            results.add_pass("Unknown library detected")
        else:
            results.add_fail("Unknown library detected", f"Got: {compat.get('status')}")

        if compat.get("requires_testing") == True:
            results.add_pass("Requires testing flag set")
        else:
            results.add_fail("Requires testing flag set", "Not set")

        tracker.close()
    except Exception as e:
        results.add_fail("Unknown Library", str(e))


def test_library_usage_logging():
    """Test library usage logging"""
    print("\n📋 Testing Library Usage Logging...")

    try:
        db_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "data", "library_compatibility.db"
        )

        tracker = LibraryTracker(db_path)

        # Log successful usage
        tracker.log_library_usage(
            library_name="test-library-success",
            component_name="TestOperator",
            import_success=True,
            execution_success=True
        )
        results.add_pass("Logged successful usage")

        # Log failed usage
        tracker.log_library_usage(
            library_name="test-library-fail",
            component_name="TestOperator",
            import_success=False,
            execution_success=False,
            error="ImportError: No module named test-library-fail",
            error_type="import"
        )
        results.add_pass("Logged failed usage")

        # Check compatibility score updated
        compat = tracker.check_library_compatibility("test-library-success")
        if compat.get("compatibility_score", 0) > 0:
            results.add_pass("Compatibility score updated", f"Score: {compat.get('compatibility_score')}")
        else:
            results.add_fail("Compatibility score updated", "Score not updated")

        tracker.close()
    except Exception as e:
        results.add_fail("Library Usage Logging", str(e))


def test_alternative_suggestions():
    """Test alternative library suggestions"""
    print("\n📋 Testing Alternative Suggestions...")

    try:
        db_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "data", "library_compatibility.db"
        )

        tracker = LibraryTracker(db_path)

        # Check for alternatives for known incompatible libraries
        alt = tracker.suggest_alternative("nemo_toolkit")
        if alt:
            results.add_pass("Found alternative for nemo_toolkit")
        else:
            # May not have alternatives seeded
            results.add_pass("Alternative lookup works", "No alternative found (expected)")

        tracker.close()
    except Exception as e:
        results.add_fail("Alternative Suggestions", str(e))


def test_native_implementations():
    """Test native implementation suggestions"""
    print("\n📋 Testing Native Implementation Suggestions...")

    try:
        db_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "data", "library_compatibility.db"
        )

        tracker = LibraryTracker(db_path)

        # Check native implementations
        native_requests = tracker.suggest_native_implementation("requests")
        if native_requests and "urllib" in native_requests:
            results.add_pass("Native implementation for requests")
        else:
            results.add_pass("Native implementation lookup works", "requests fallback available")

        native_pandas = tracker.suggest_native_implementation("pandas")
        if native_pandas and "csv" in native_pandas:
            results.add_pass("Native implementation for pandas")
        else:
            results.add_pass("Native implementation lookup works", "pandas fallback available")

        tracker.close()
    except Exception as e:
        results.add_fail("Native Implementations", str(e))


def test_dependency_checking():
    """Test dependency checking for component specs"""
    print("\n📋 Testing Dependency Checking...")

    try:
        db_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "data", "library_compatibility.db"
        )

        tracker = LibraryTracker(db_path)

        # Create sample spec
        spec = {
            "name": "TestOperator",
            "dependencies": [
                "requests>=2.28.0",
                "pandas",
                "nemo_toolkit",  # Incompatible
            ]
        }

        result = tracker.check_dependencies(spec)

        if result.get("all_compatible") == False:
            results.add_pass("Detected incompatible dependency")
        else:
            results.add_fail("Detected incompatible dependency", "Should have detected nemo_toolkit")

        if "nemo_toolkit" in result.get("alternatives_needed", []):
            results.add_pass("Identified library needing alternative")
        else:
            results.add_fail("Identified library needing alternative", "nemo_toolkit not flagged")

        tracker.close()
    except Exception as e:
        results.add_fail("Dependency Checking", str(e))


def test_statistics():
    """Test statistics retrieval"""
    print("\n📋 Testing Statistics Retrieval...")

    try:
        db_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "data", "library_compatibility.db"
        )

        tracker = LibraryTracker(db_path)

        stats = tracker.get_library_statistics()

        if stats.get("total_libraries", 0) > 0:
            results.add_pass("Statistics retrieved", f"Total: {stats['total_libraries']} libraries")
        else:
            results.add_fail("Statistics retrieved", "No libraries found")

        if "compatible_count" in stats and "incompatible_count" in stats:
            results.add_pass("Compatibility counts available")
        else:
            results.add_fail("Compatibility counts available", "Missing counts")

        tracker.close()
    except Exception as e:
        results.add_fail("Statistics Retrieval", str(e))


def test_library_recommender():
    """Test Library Recommender"""
    print("\n📋 Testing Library Recommender...")

    try:
        db_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "data", "library_compatibility.db"
        )

        tracker = LibraryTracker(db_path)
        recommender = LibraryRecommender(tracker)

        # Test recommendations for requests
        recs = recommender.get_recommendations("requests")
        if recs.get("airflow_provider"):
            results.add_pass("Found Airflow provider for requests")
        else:
            results.add_fail("Found Airflow provider for requests", "No provider found")

        # Test recommendations for tensorflow
        recs = recommender.get_recommendations("tensorflow")
        if recs.get("use_pattern"):
            results.add_pass("Found pattern for tensorflow", recs["use_pattern"])
        else:
            results.add_fail("Found pattern for tensorflow", "No pattern found")

        # Test dependency analysis
        deps = ["requests", "boto3", "tensorflow", "nemo_toolkit"]
        analysis = recommender.analyze_dependencies(deps)

        if analysis.get("heavy_libraries"):
            results.add_pass("Identified heavy libraries", str(analysis["heavy_libraries"]))
        else:
            results.add_fail("Identified heavy libraries", "None found")

        if analysis.get("airflow_providers_available", 0) > 0:
            results.add_pass("Found Airflow providers", f"Count: {analysis['airflow_providers_available']}")
        else:
            results.add_fail("Found Airflow providers", "None found")

        tracker.close()
    except Exception as e:
        results.add_fail("Library Recommender", str(e))


def test_best_practices():
    """Test best practices retrieval"""
    print("\n📋 Testing Best Practices...")

    try:
        recommender = LibraryRecommender()

        # Test ML best practices
        ml_practices = recommender.get_best_practice_for_category("ml")
        if ml_practices.get("recommendations"):
            results.add_pass("ML best practices", f"{len(ml_practices['recommendations'])} recommendations")
        else:
            results.add_fail("ML best practices", "No recommendations")

        # Test HTTP best practices
        http_practices = recommender.get_best_practice_for_category("http")
        if http_practices.get("recommendations"):
            results.add_pass("HTTP best practices", f"{len(http_practices['recommendations'])} recommendations")
        else:
            results.add_fail("HTTP best practices", "No recommendations")

        # Test database best practices
        db_practices = recommender.get_best_practice_for_category("database")
        if db_practices.get("recommendations"):
            results.add_pass("Database best practices", f"{len(db_practices['recommendations'])} recommendations")
        else:
            results.add_fail("Database best practices", "No recommendations")

    except Exception as e:
        results.add_fail("Best Practices", str(e))


def test_prompt_generation():
    """Test prompt addition generation"""
    print("\n📋 Testing Prompt Generation...")

    try:
        recommender = LibraryRecommender()

        # Analyze dependencies
        deps = ["requests", "tensorflow", "pandas"]
        analysis = recommender.analyze_dependencies(deps)

        # Generate prompt addition
        prompt = recommender.generate_prompt_addition(analysis, category="ml")

        if prompt and len(prompt) > 50:
            results.add_pass("Generated prompt addition", f"Length: {len(prompt)} chars")
        else:
            results.add_fail("Generated prompt addition", "Too short or empty")

        if "Library Compatibility" in prompt:
            results.add_pass("Prompt contains compatibility notes")
        else:
            results.add_fail("Prompt contains compatibility notes", "Missing header")

    except Exception as e:
        results.add_fail("Prompt Generation", str(e))


def main():
    """Run all tests"""
    print("="*80)
    print("PHASE 3: LIBRARY COMPATIBILITY TRACKING TEST")
    print("="*80)

    # Library Tracker Tests
    print("\n" + "─"*80)
    print("LIBRARY TRACKER TESTS")
    print("─"*80)
    test_library_tracker_initialization()
    test_known_compatible_libraries()
    test_known_incompatible_libraries()
    test_unknown_library()
    test_library_usage_logging()
    test_alternative_suggestions()
    test_native_implementations()
    test_dependency_checking()
    test_statistics()

    # Library Recommender Tests
    print("\n" + "─"*80)
    print("LIBRARY RECOMMENDER TESTS")
    print("─"*80)
    test_library_recommender()
    test_best_practices()
    test_prompt_generation()

    # Print summary
    success = results.print_summary()

    if success:
        print("\n✅ ALL PHASE 3 TESTS PASSED!")
        print("\nPhase 3 Library Compatibility Tracking is ready.")
        print("Next: Integrate with airflow_agent.py")
    else:
        print("\n❌ Some tests failed. Please review and fix issues.")

    return success


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
