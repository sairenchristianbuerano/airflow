#!/usr/bin/env python3
"""
Test script for Phase 4 - Native Python Fallback Generation

This script tests the native fallback generator, database operations,
learning mechanisms, and integration with the generation pipeline.
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.native_fallback_generator import NativeFallbackGenerator, get_native_fallback


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


def test_fallback_generator_initialization():
    """Test NativeFallbackGenerator initialization"""
    print("\n📋 Testing Fallback Generator Initialization...")

    try:
        db_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "data", "fallback_code.db"
        )

        generator = NativeFallbackGenerator(db_path)
        results.add_pass("NativeFallbackGenerator initialization")

        # Check database was created
        assert os.path.exists(db_path), "Database file not created"
        results.add_pass("Database file created")

        # Check tables exist
        cursor = generator.db.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]

        required_tables = ['fallback_code', 'fallback_usage_log', 'fallback_effectiveness', 'learned_fallbacks']
        for table in required_tables:
            if table in tables:
                results.add_pass(f"Table exists: {table}")
            else:
                results.add_fail(f"Table exists: {table}", "Not found")

        generator.close()
    except Exception as e:
        results.add_fail("NativeFallbackGenerator initialization", str(e))


def test_prebuilt_fallbacks():
    """Test pre-built native fallbacks"""
    print("\n📋 Testing Pre-built Native Fallbacks...")

    try:
        db_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "data", "fallback_code.db"
        )

        generator = NativeFallbackGenerator(db_path)

        # Test requests fallback
        requests_fallback = generator.get_fallback("requests", "get")
        if requests_fallback and "http_get" in requests_fallback.get("fallback_code", ""):
            results.add_pass("Requests GET fallback available")
        else:
            results.add_fail("Requests GET fallback", "Not found or invalid")

        requests_post = generator.get_fallback("requests", "post")
        if requests_post and "http_post" in requests_post.get("fallback_code", ""):
            results.add_pass("Requests POST fallback available")
        else:
            results.add_fail("Requests POST fallback", "Not found or invalid")

        # Test pandas fallback
        pandas_fallback = generator.get_fallback("pandas", "read_csv")
        if pandas_fallback and "csv" in pandas_fallback.get("fallback_code", ""):
            results.add_pass("Pandas read_csv fallback available")
        else:
            results.add_fail("Pandas read_csv fallback", "Not found or invalid")

        # Test JSON fallback
        json_fallback = generator.get_fallback("json", "load_file")
        if json_fallback:
            results.add_pass("JSON load_file fallback available")
        else:
            results.add_fail("JSON load_file fallback", "Not found")

        # Test dateutil fallback
        dateutil_fallback = generator.get_fallback("dateutil", "parse_date")
        if dateutil_fallback and "parse_date" in dateutil_fallback.get("fallback_code", ""):
            results.add_pass("Dateutil parse_date fallback available")
        else:
            results.add_fail("Dateutil parse_date fallback", "Not found or invalid")

        # Test pydantic fallback
        pydantic_fallback = generator.get_fallback("pydantic", "validate_dict")
        if pydantic_fallback and "validate_dict" in pydantic_fallback.get("fallback_code", ""):
            results.add_pass("Pydantic validate_dict fallback available")
        else:
            results.add_fail("Pydantic validate_dict fallback", "Not found or invalid")

        generator.close()
    except Exception as e:
        results.add_fail("Pre-built Fallbacks", str(e))


def test_get_all_fallbacks_for_library():
    """Test getting all fallbacks for a library"""
    print("\n📋 Testing Get All Fallbacks for Library...")

    try:
        db_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "data", "fallback_code.db"
        )

        generator = NativeFallbackGenerator(db_path)

        # Get all requests fallbacks
        requests_fallbacks = generator.get_all_fallbacks_for_library("requests")
        if len(requests_fallbacks) >= 2:
            results.add_pass("Get all requests fallbacks", f"Found {len(requests_fallbacks)} operations")
        else:
            results.add_fail("Get all requests fallbacks", f"Expected >= 2, got {len(requests_fallbacks)}")

        # Get all pandas fallbacks
        pandas_fallbacks = generator.get_all_fallbacks_for_library("pandas")
        if len(pandas_fallbacks) >= 2:
            results.add_pass("Get all pandas fallbacks", f"Found {len(pandas_fallbacks)} operations")
        else:
            results.add_fail("Get all pandas fallbacks", f"Expected >= 2, got {len(pandas_fallbacks)}")

        generator.close()
    except Exception as e:
        results.add_fail("Get All Fallbacks for Library", str(e))


def test_generate_fallback_code():
    """Test generating combined fallback code"""
    print("\n📋 Testing Generate Fallback Code...")

    try:
        db_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "data", "fallback_code.db"
        )

        generator = NativeFallbackGenerator(db_path)

        # Generate all requests fallbacks
        code = generator.generate_fallback_code("requests")
        if code and "http_get" in code and "http_post" in code:
            results.add_pass("Generate requests fallback code")
        else:
            results.add_fail("Generate requests fallback code", "Missing functions")

        # Generate specific operations only
        code_specific = generator.generate_fallback_code("requests", operations=["get"])
        if code_specific and "http_get" in code_specific:
            results.add_pass("Generate specific operation fallback")
        else:
            results.add_fail("Generate specific operation fallback", "Missing function")

        generator.close()
    except Exception as e:
        results.add_fail("Generate Fallback Code", str(e))


def test_fallback_usage_logging():
    """Test fallback usage logging"""
    print("\n📋 Testing Fallback Usage Logging...")

    try:
        db_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "data", "fallback_code.db"
        )

        generator = NativeFallbackGenerator(db_path)

        # Log successful usage
        generator.log_fallback_usage(
            library_name="requests",
            operation_type="get",
            component_name="TestOperator",
            success=True
        )
        results.add_pass("Logged successful fallback usage")

        # Log failed usage
        generator.log_fallback_usage(
            library_name="requests",
            operation_type="post",
            component_name="TestOperator",
            success=False,
            error_message="Connection timeout"
        )
        results.add_pass("Logged failed fallback usage")

        # Check effectiveness was updated
        effectiveness = generator.get_effectiveness("requests")
        if effectiveness.get("fallbacks"):
            results.add_pass("Effectiveness tracking updated")
        else:
            results.add_fail("Effectiveness tracking updated", "No data found")

        generator.close()
    except Exception as e:
        results.add_fail("Fallback Usage Logging", str(e))


def test_learn_fallback():
    """Test learning new fallbacks"""
    print("\n📋 Testing Learn Fallback...")

    try:
        db_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "data", "fallback_code.db"
        )

        generator = NativeFallbackGenerator(db_path)

        # Learn a new fallback
        learned = generator.learn_fallback(
            library_name="custom-library",
            operation_type="custom_operation",
            fallback_code="def custom_fallback(): return 'learned'",
            source_component="TestComponent",
            learned_from="test"
        )

        if learned:
            results.add_pass("Learned new fallback")
        else:
            results.add_fail("Learned new fallback", "Learning failed")

        # Verify it can be retrieved
        fallback = generator.get_fallback("custom-library", "custom_operation")
        if fallback and "learned" in fallback.get("fallback_code", ""):
            results.add_pass("Retrieved learned fallback")
        else:
            results.add_fail("Retrieved learned fallback", "Not found")

        generator.close()
    except Exception as e:
        results.add_fail("Learn Fallback", str(e))


def test_suggest_fallback_for_code():
    """Test suggesting fallbacks for unavailable libraries"""
    print("\n📋 Testing Suggest Fallback for Code...")

    try:
        db_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "data", "fallback_code.db"
        )

        generator = NativeFallbackGenerator(db_path)

        # Suggest fallbacks for unavailable libraries
        suggestions = generator.suggest_fallback_for_code(
            code="import requests; import pandas",
            unavailable_libraries=["requests", "pandas", "unknown-lib"]
        )

        if suggestions.get("has_fallbacks"):
            results.add_pass("Suggestions have fallbacks")
        else:
            results.add_fail("Suggestions have fallbacks", "No fallbacks available")

        # Check requests suggestions
        requests_suggestion = next(
            (s for s in suggestions.get("suggestions", []) if s.get("library") == "requests"),
            None
        )
        if requests_suggestion and requests_suggestion.get("available_fallbacks"):
            results.add_pass("Requests fallback suggestions")
        else:
            results.add_fail("Requests fallback suggestions", "Not found")

        # Check pandas suggestions
        pandas_suggestion = next(
            (s for s in suggestions.get("suggestions", []) if s.get("library") == "pandas"),
            None
        )
        if pandas_suggestion and pandas_suggestion.get("available_fallbacks"):
            results.add_pass("Pandas fallback suggestions")
        else:
            results.add_fail("Pandas fallback suggestions", "Not found")

        # Check unknown library handled gracefully
        unknown_suggestion = next(
            (s for s in suggestions.get("suggestions", []) if s.get("library") == "unknown-lib"),
            None
        )
        if unknown_suggestion and not unknown_suggestion.get("available_fallbacks"):
            results.add_pass("Unknown library handled gracefully")
        else:
            results.add_fail("Unknown library handled", "Unexpected behavior")

        generator.close()
    except Exception as e:
        results.add_fail("Suggest Fallback for Code", str(e))


def test_generate_prompt_addition():
    """Test generating prompt addition for code generation"""
    print("\n📋 Testing Generate Prompt Addition...")

    try:
        db_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "data", "fallback_code.db"
        )

        generator = NativeFallbackGenerator(db_path)

        # Generate prompt for unavailable libraries
        prompt = generator.generate_prompt_addition(["requests", "pandas"])

        if prompt and "PHASE 4" in prompt:
            results.add_pass("Prompt contains Phase 4 header")
        else:
            results.add_fail("Prompt contains Phase 4 header", "Missing header")

        if "requests" in prompt.lower():
            results.add_pass("Prompt mentions requests")
        else:
            results.add_fail("Prompt mentions requests", "Not found")

        if "pandas" in prompt.lower():
            results.add_pass("Prompt mentions pandas")
        else:
            results.add_fail("Prompt mentions pandas", "Not found")

        if len(prompt) > 100:
            results.add_pass("Prompt has sufficient content", f"{len(prompt)} chars")
        else:
            results.add_fail("Prompt has sufficient content", f"Only {len(prompt)} chars")

        generator.close()
    except Exception as e:
        results.add_fail("Generate Prompt Addition", str(e))


def test_statistics():
    """Test statistics retrieval"""
    print("\n📋 Testing Statistics...")

    try:
        db_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "data", "fallback_code.db"
        )

        generator = NativeFallbackGenerator(db_path)

        stats = generator.get_statistics()

        if stats.get("total_fallbacks", 0) > 0:
            results.add_pass("Total fallbacks count", f"{stats['total_fallbacks']} fallbacks")
        else:
            results.add_fail("Total fallbacks count", "No fallbacks found")

        if stats.get("library_count", 0) > 0:
            results.add_pass("Library count", f"{stats['library_count']} libraries")
        else:
            results.add_fail("Library count", "No libraries found")

        if stats.get("libraries_covered"):
            results.add_pass("Libraries list available")
        else:
            results.add_fail("Libraries list available", "Empty list")

        if stats.get("categories"):
            results.add_pass("Categories available", f"{len(stats['categories'])} categories")
        else:
            results.add_fail("Categories available", "Empty list")

        generator.close()
    except Exception as e:
        results.add_fail("Statistics", str(e))


def test_convenience_function():
    """Test convenience function get_native_fallback"""
    print("\n📋 Testing Convenience Function...")

    try:
        # Test getting specific operation
        code = get_native_fallback("requests", "get")
        if code and "http_get" in code:
            results.add_pass("get_native_fallback specific operation")
        else:
            results.add_fail("get_native_fallback specific operation", "Not found")

        # Test getting all operations
        all_code = get_native_fallback("requests")
        if all_code and "http_get" in all_code and "http_post" in all_code:
            results.add_pass("get_native_fallback all operations")
        else:
            results.add_fail("get_native_fallback all operations", "Missing functions")

        # Test unknown library
        unknown_code = get_native_fallback("unknown-library-xyz")
        if unknown_code is None:
            results.add_pass("get_native_fallback unknown library returns None")
        else:
            results.add_fail("get_native_fallback unknown library", "Should return None")

    except Exception as e:
        results.add_fail("Convenience Function", str(e))


def test_native_fallback_categories():
    """Test fallbacks for different categories"""
    print("\n📋 Testing Fallback Categories...")

    try:
        db_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "data", "fallback_code.db"
        )

        generator = NativeFallbackGenerator(db_path)

        # Test HTTP category
        http_fallback = generator.get_fallback("requests", "request")
        if http_fallback:
            results.add_pass("HTTP category fallback (requests)")
        else:
            results.add_fail("HTTP category fallback", "Not found")

        # Test Data category
        data_fallback = generator.get_fallback("pandas", "dataframe_operations")
        if data_fallback:
            results.add_pass("Data category fallback (pandas)")
        else:
            results.add_fail("Data category fallback", "Not found")

        # Test Datetime category
        dt_fallback = generator.get_fallback("dateutil", "parse_date")
        if dt_fallback:
            results.add_pass("Datetime category fallback (dateutil)")
        else:
            results.add_fail("Datetime category fallback", "Not found")

        # Test Resilience category
        resilience_fallback = generator.get_fallback("tenacity", "retry")
        if resilience_fallback:
            results.add_pass("Resilience category fallback (tenacity)")
        else:
            results.add_fail("Resilience category fallback", "Not found")

        # Test Validation category
        validation_fallback = generator.get_fallback("pydantic", "validate_dict")
        if validation_fallback:
            results.add_pass("Validation category fallback (pydantic)")
        else:
            results.add_fail("Validation category fallback", "Not found")

        # Test Caching category
        caching_fallback = generator.get_fallback("cachetools", "simple_cache")
        if caching_fallback:
            results.add_pass("Caching category fallback (cachetools)")
        else:
            results.add_fail("Caching category fallback", "Not found")

        # Test Template category
        template_fallback = generator.get_fallback("jinja2", "simple_template")
        if template_fallback:
            results.add_pass("Template category fallback (jinja2)")
        else:
            results.add_fail("Template category fallback", "Not found")

        # Test XML category
        xml_fallback = generator.get_fallback("lxml", "parse_xml")
        if xml_fallback:
            results.add_pass("XML category fallback (lxml)")
        else:
            results.add_fail("XML category fallback", "Not found")

        # Test YAML category
        yaml_fallback = generator.get_fallback("pyyaml", "load_yaml")
        if yaml_fallback:
            results.add_pass("YAML category fallback (pyyaml)")
        else:
            results.add_fail("YAML category fallback", "Not found")

        generator.close()
    except Exception as e:
        results.add_fail("Fallback Categories", str(e))


def test_effectiveness_tracking():
    """Test effectiveness tracking mechanism"""
    print("\n📋 Testing Effectiveness Tracking...")

    try:
        db_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "data", "fallback_code.db"
        )

        generator = NativeFallbackGenerator(db_path)

        # Log multiple usages for a specific fallback
        for i in range(5):
            generator.log_fallback_usage(
                library_name="test-lib",
                operation_type="test-op",
                component_name=f"TestComponent{i}",
                success=i < 4  # 4 successes, 1 failure
            )

        # Get effectiveness
        effectiveness = generator.get_effectiveness("test-lib")

        if effectiveness.get("fallbacks"):
            test_fb = next(
                (fb for fb in effectiveness["fallbacks"] if fb["library_name"] == "test-lib"),
                None
            )
            if test_fb:
                if test_fb.get("usage_count", 0) >= 5:
                    results.add_pass("Usage count tracked", f"Count: {test_fb['usage_count']}")
                else:
                    results.add_fail("Usage count tracked", f"Expected >= 5, got {test_fb.get('usage_count', 0)}")

                score = test_fb.get("effectiveness_score", 0)
                if 0.6 <= score <= 1.0:  # Should be around 0.8 (4/5)
                    results.add_pass("Effectiveness score calculated", f"Score: {score:.2f}")
                else:
                    results.add_fail("Effectiveness score calculated", f"Unexpected score: {score}")
            else:
                results.add_fail("Effectiveness data found", "test-lib not in results")
        else:
            results.add_fail("Effectiveness data found", "No fallbacks in results")

        generator.close()
    except Exception as e:
        results.add_fail("Effectiveness Tracking", str(e))


def test_fallback_code_quality():
    """Test that fallback code is valid Python"""
    print("\n📋 Testing Fallback Code Quality...")

    try:
        import ast

        db_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "data", "fallback_code.db"
        )

        generator = NativeFallbackGenerator(db_path)

        # Test that requests fallback code is valid Python
        requests_code = generator.generate_fallback_code("requests")
        try:
            ast.parse(requests_code)
            results.add_pass("Requests fallback code is valid Python")
        except SyntaxError as e:
            results.add_fail("Requests fallback code is valid Python", str(e))

        # Test that pandas fallback code is valid Python
        pandas_code = generator.generate_fallback_code("pandas")
        try:
            ast.parse(pandas_code)
            results.add_pass("Pandas fallback code is valid Python")
        except SyntaxError as e:
            results.add_fail("Pandas fallback code is valid Python", str(e))

        # Test that dateutil fallback code is valid Python
        dateutil_code = generator.generate_fallback_code("dateutil")
        try:
            ast.parse(dateutil_code)
            results.add_pass("Dateutil fallback code is valid Python")
        except SyntaxError as e:
            results.add_fail("Dateutil fallback code is valid Python", str(e))

        generator.close()
    except Exception as e:
        results.add_fail("Fallback Code Quality", str(e))


def main():
    """Run all tests"""
    print("="*80)
    print("PHASE 4: NATIVE PYTHON FALLBACK GENERATION TEST")
    print("="*80)

    # Initialization Tests
    print("\n" + "─"*80)
    print("INITIALIZATION TESTS")
    print("─"*80)
    test_fallback_generator_initialization()

    # Pre-built Fallback Tests
    print("\n" + "─"*80)
    print("PRE-BUILT FALLBACK TESTS")
    print("─"*80)
    test_prebuilt_fallbacks()
    test_get_all_fallbacks_for_library()
    test_generate_fallback_code()

    # Category Tests
    print("\n" + "─"*80)
    print("CATEGORY TESTS")
    print("─"*80)
    test_native_fallback_categories()

    # Usage and Learning Tests
    print("\n" + "─"*80)
    print("USAGE AND LEARNING TESTS")
    print("─"*80)
    test_fallback_usage_logging()
    test_learn_fallback()
    test_effectiveness_tracking()

    # Suggestion Tests
    print("\n" + "─"*80)
    print("SUGGESTION TESTS")
    print("─"*80)
    test_suggest_fallback_for_code()
    test_generate_prompt_addition()

    # Quality Tests
    print("\n" + "─"*80)
    print("CODE QUALITY TESTS")
    print("─"*80)
    test_fallback_code_quality()

    # Utility Tests
    print("\n" + "─"*80)
    print("UTILITY TESTS")
    print("─"*80)
    test_statistics()
    test_convenience_function()

    # Print summary
    success = results.print_summary()

    if success:
        print("\n✅ ALL PHASE 4 TESTS PASSED!")
        print("\nPhase 4 Native Python Fallback Generation is ready.")
        print("Next: Proceed to Phase 5 - Continuous Learning Loop")
    else:
        print("\n❌ Some tests failed. Please review and fix issues.")

    return success


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
