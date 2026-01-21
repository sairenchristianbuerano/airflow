#!/bin/bash
# Comprehensive Phase 1 Test Suite
# Tests all component-generator functionality

BASE_URL="http://localhost:8095/api/airflow/component-generator"
TOTAL=0
PASSED=0
FAILED=0

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo "================================================================================"
echo "PHASE 1 COMPREHENSIVE TEST SUITE"
echo "Testing Airflow Component Generator Service"
echo "================================================================================"
echo ""

# Test function
run_test() {
    local test_name="$1"
    local test_command="$2"

    TOTAL=$((TOTAL + 1))

    if eval "$test_command" > /dev/null 2>&1; then
        echo -e "${GREEN}✅ PASS${NC}: $test_name"
        PASSED=$((PASSED + 1))
        return 0
    else
        echo -e "${RED}❌ FAIL${NC}: $test_name"
        FAILED=$((FAILED + 1))
        return 1
    fi
}

# Test 1: Health endpoint
echo "Running tests..."
echo ""

run_test "Health Endpoint" \
    "curl -s -f $BASE_URL/health | grep -q 'healthy'"

# Test 2: Sample operator generation
run_test "Sample Operator Generation" \
    "curl -s -f -X POST $BASE_URL/generate/sample -H 'Content-Type: application/json' --max-time 120 | grep -q 'code'"

# Test 3: Analytics metrics
run_test "Analytics Metrics" \
    "curl -s -f $BASE_URL/analytics/metrics | grep -q 'total_generations'"

# Test 4: Analytics insights
run_test "Analytics Insights" \
    "curl -s -f $BASE_URL/analytics/insights | grep -q 'category_insights'"

# Test 5: Analytics trends
run_test "Analytics Trends" \
    "curl -s -f '$BASE_URL/analytics/trends?days=7' | grep -q 'daily_stats'"

# Test 6: Analytics errors
run_test "Analytics Errors" \
    "curl -s -f $BASE_URL/analytics/errors | grep -q 'total_tracked_errors'"

# Test 7: Custom operator generation
CUSTOM_SPEC='{"spec":"name: TestOp\\ndisplay_name: Test\\ndescription: Test\\ncategory: test\\ncomponent_type: operator\\nbase_class: BaseOperator"}'
run_test "Custom Operator Generation" \
    "curl -s -f -X POST $BASE_URL/generate -H 'Content-Type: application/json' -d '$CUSTOM_SPEC' --max-time 120 | grep -q 'TestOp'"

# Test 8: Sensor generation
SENSOR_SPEC='{"spec":"name: TestSensor\\ndisplay_name: Test\\ndescription: Test\\ncategory: test\\ncomponent_type: sensor\\nbase_class: BaseSensor"}'
run_test "Sensor Generation" \
    "curl -s -f -X POST $BASE_URL/generate -H 'Content-Type: application/json' -d '$SENSOR_SPEC' --max-time 120 | grep -q 'poke'"

# Test 9: Feasibility assessment
ASSESS_SPEC='{"spec":"name: SimpleOp\\ndescription: Test\\ncategory: test\\ncomponent_type: operator"}'
run_test "Feasibility Assessment" \
    "curl -s -f -X POST $BASE_URL/assess -H 'Content-Type: application/json' -d '$ASSESS_SPEC' | grep -q 'feasible'"

# Print summary
echo ""
echo "================================================================================"
echo "TEST SUMMARY"
echo "================================================================================"
echo "Total Tests: $TOTAL"
echo -e "Passed: ${GREEN}$PASSED ✅${NC}"
echo -e "Failed: ${RED}$FAILED ❌${NC}"

SUCCESS_RATE=$(( PASSED * 100 / TOTAL ))
echo "Success Rate: $SUCCESS_RATE%"
echo "================================================================================"

if [ $FAILED -eq 0 ]; then
    echo ""
    echo -e "${GREEN}✅ All tests passed! Phase 1 is 100% SOLID!${NC}"
    echo "Ready to proceed to Phase 2: Component Index Service with ChromaDB RAG"
    exit 0
else
    echo ""
    echo -e "${RED}❌ Some tests failed. Please review and fix issues before Phase 2.${NC}"
    exit 1
fi
