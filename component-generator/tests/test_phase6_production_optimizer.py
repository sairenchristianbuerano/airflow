"""
Phase 6: Production Optimization Test Suite

Comprehensive tests for the Production Optimizer implementation.
Tests all aspects including:
- LRU Cache functionality
- Rate limiting
- Performance metrics collection
- Health monitoring
- Dashboard data aggregation
"""

import os
import sys
import time
import threading
from typing import Dict, Any

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.production_optimizer import (
    ProductionOptimizer,
    LRUCache,
    RateLimiter,
    PerformanceMetrics,
    HealthMonitor,
    CacheConfig,
    RateLimitConfig,
    AlertThreshold,
    HealthStatus,
    create_production_optimizer
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
        print("PHASE 6 TEST SUMMARY - PRODUCTION OPTIMIZER")
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


# ============================================================================
# Section 1: LRU Cache Tests
# ============================================================================

def test_cache_basic_operations():
    """Test 1.1: Basic cache get/set operations"""
    try:
        cache = LRUCache(CacheConfig(max_size=100, ttl_seconds=60))

        # Test set and get
        cache.set("key1", "value1")
        result = cache.get("key1")

        assert result == "value1", f"Expected 'value1', got '{result}'"

        # Test missing key
        missing = cache.get("nonexistent")
        assert missing is None, "Expected None for missing key"

        results.add_pass("Cache Basic Operations")
    except Exception as e:
        results.add_fail("Cache Basic Operations", str(e))


def test_cache_ttl_expiration():
    """Test 1.2: Cache entries expire after TTL"""
    try:
        cache = LRUCache(CacheConfig(max_size=100, ttl_seconds=1))

        cache.set("key1", "value1")

        # Should exist immediately
        assert cache.get("key1") == "value1"

        # Wait for expiration
        time.sleep(1.5)

        # Should be expired
        result = cache.get("key1")
        assert result is None, "Expected None after TTL expiration"

        results.add_pass("Cache TTL Expiration")
    except Exception as e:
        results.add_fail("Cache TTL Expiration", str(e))


def test_cache_max_size_eviction():
    """Test 1.3: Cache evicts oldest entries when full"""
    try:
        cache = LRUCache(CacheConfig(max_size=3, ttl_seconds=3600))

        # Fill cache
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.set("key3", "value3")

        # Add one more, should evict key1
        cache.set("key4", "value4")

        assert cache.get("key1") is None, "key1 should be evicted"
        assert cache.get("key4") == "value4", "key4 should exist"

        results.add_pass("Cache Max Size Eviction")
    except Exception as e:
        results.add_fail("Cache Max Size Eviction", str(e))


def test_cache_lru_ordering():
    """Test 1.4: Recently accessed items are kept"""
    try:
        cache = LRUCache(CacheConfig(max_size=3, ttl_seconds=3600))

        # Fill cache
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.set("key3", "value3")

        # Access key1 to make it recently used
        cache.get("key1")

        # Add new key, should evict key2 (oldest unused)
        cache.set("key4", "value4")

        assert cache.get("key1") == "value1", "key1 should still exist (recently used)"
        assert cache.get("key2") is None, "key2 should be evicted (LRU)"

        results.add_pass("Cache LRU Ordering")
    except Exception as e:
        results.add_fail("Cache LRU Ordering", str(e))


def test_cache_statistics():
    """Test 1.5: Cache tracks hit/miss statistics"""
    try:
        cache = LRUCache(CacheConfig(max_size=100, ttl_seconds=3600))

        cache.set("key1", "value1")

        # Generate hits
        for _ in range(5):
            cache.get("key1")

        # Generate misses
        for _ in range(3):
            cache.get("nonexistent")

        stats = cache.get_stats()

        assert stats["hits"] == 5, f"Expected 5 hits, got {stats['hits']}"
        assert stats["misses"] == 3, f"Expected 3 misses, got {stats['misses']}"
        assert 0 < stats["hit_rate"] < 1, "Hit rate should be between 0 and 1"

        results.add_pass("Cache Statistics")
    except Exception as e:
        results.add_fail("Cache Statistics", str(e))


def test_cache_clear():
    """Test 1.6: Cache clear removes all entries"""
    try:
        cache = LRUCache(CacheConfig(max_size=100, ttl_seconds=3600))

        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.set("key3", "value3")

        cleared = cache.clear()

        assert cleared == 3, f"Expected 3 cleared, got {cleared}"
        assert cache.get("key1") is None
        assert cache.get("key2") is None
        assert cache.get("key3") is None

        results.add_pass("Cache Clear")
    except Exception as e:
        results.add_fail("Cache Clear", str(e))


def test_cache_thread_safety():
    """Test 1.7: Cache is thread-safe"""
    try:
        cache = LRUCache(CacheConfig(max_size=1000, ttl_seconds=3600))
        errors = []

        def writer():
            for i in range(100):
                cache.set(f"key_{threading.current_thread().name}_{i}", f"value_{i}")

        def reader():
            for i in range(100):
                cache.get(f"key_{threading.current_thread().name}_{i}")

        threads = []
        for i in range(5):
            t = threading.Thread(target=writer, name=f"writer_{i}")
            threads.append(t)
            t = threading.Thread(target=reader, name=f"reader_{i}")
            threads.append(t)

        for t in threads:
            t.start()

        for t in threads:
            t.join()

        # Should not crash
        stats = cache.get_stats()
        assert stats["size"] > 0, "Cache should have entries"

        results.add_pass("Cache Thread Safety")
    except Exception as e:
        results.add_fail("Cache Thread Safety", str(e))


def test_cache_disabled():
    """Test 1.8: Cache can be disabled"""
    try:
        cache = LRUCache(CacheConfig(max_size=100, ttl_seconds=3600, enabled=False))

        cache.set("key1", "value1")
        result = cache.get("key1")

        assert result is None, "Disabled cache should return None"

        stats = cache.get_stats()
        assert stats["enabled"] == False

        results.add_pass("Cache Disabled")
    except Exception as e:
        results.add_fail("Cache Disabled", str(e))


# ============================================================================
# Section 2: Rate Limiter Tests
# ============================================================================

def test_rate_limiter_allows_requests():
    """Test 2.1: Rate limiter allows requests under limit"""
    try:
        limiter = RateLimiter(RateLimitConfig(
            requests_per_minute=10,
            requests_per_hour=100,
            burst_limit=5
        ))

        # Should allow first few requests
        for i in range(3):
            allowed, reason = limiter.acquire()
            assert allowed, f"Request {i} should be allowed"
            limiter.release()

        results.add_pass("Rate Limiter Allows Requests")
    except Exception as e:
        results.add_fail("Rate Limiter Allows Requests", str(e))


def test_rate_limiter_burst_limit():
    """Test 2.2: Rate limiter enforces burst limit"""
    try:
        limiter = RateLimiter(RateLimitConfig(
            requests_per_minute=100,
            requests_per_hour=1000,
            burst_limit=3
        ))

        # Acquire without releasing to hit burst limit
        for i in range(3):
            allowed, _ = limiter.acquire()
            assert allowed, f"Request {i} should be allowed"

        # 4th request should be blocked
        allowed, reason = limiter.acquire()
        assert not allowed, "Should be blocked by burst limit"
        assert "burst" in reason.lower()

        results.add_pass("Rate Limiter Burst Limit")
    except Exception as e:
        results.add_fail("Rate Limiter Burst Limit", str(e))


def test_rate_limiter_minute_limit():
    """Test 2.3: Rate limiter enforces per-minute limit"""
    try:
        limiter = RateLimiter(RateLimitConfig(
            requests_per_minute=5,
            requests_per_hour=1000,
            burst_limit=10
        ))

        # Should allow up to limit
        for i in range(5):
            allowed, _ = limiter.acquire()
            assert allowed
            limiter.release()

        # 6th request should be blocked
        allowed, reason = limiter.acquire()
        assert not allowed, "Should be blocked by minute limit"
        assert "minute" in reason.lower()

        results.add_pass("Rate Limiter Minute Limit")
    except Exception as e:
        results.add_fail("Rate Limiter Minute Limit", str(e))


def test_rate_limiter_statistics():
    """Test 2.4: Rate limiter tracks statistics"""
    try:
        limiter = RateLimiter(RateLimitConfig(
            requests_per_minute=10,
            requests_per_hour=100,
            burst_limit=5
        ))

        # Make some requests
        for _ in range(3):
            limiter.acquire()
            limiter.release()

        stats = limiter.get_stats()

        assert stats["total_requests"] == 3
        assert stats["current_minute_requests"] == 3
        assert "limits" in stats

        results.add_pass("Rate Limiter Statistics")
    except Exception as e:
        results.add_fail("Rate Limiter Statistics", str(e))


def test_rate_limiter_disabled():
    """Test 2.5: Rate limiter can be disabled"""
    try:
        limiter = RateLimiter(RateLimitConfig(
            requests_per_minute=1,
            requests_per_hour=1,
            burst_limit=1,
            enabled=False
        ))

        # Should allow all requests when disabled
        for _ in range(10):
            allowed, _ = limiter.acquire()
            assert allowed, "All requests should be allowed when disabled"

        results.add_pass("Rate Limiter Disabled")
    except Exception as e:
        results.add_fail("Rate Limiter Disabled", str(e))


# ============================================================================
# Section 3: Performance Metrics Tests
# ============================================================================

def test_metrics_recording():
    """Test 3.1: Metrics records generation data"""
    try:
        metrics = PerformanceMetrics()

        metrics.record_generation(
            success=True,
            time_seconds=5.0,
            tokens=1000,
            retries=1,
            cost_usd=0.05
        )

        data = metrics.get_metrics()

        assert data["total_generations"] == 1
        assert data["successful_generations"] == 1
        assert data["failed_generations"] == 0
        assert data["avg_generation_time"] == 5.0
        assert data["avg_tokens"] == 1000

        results.add_pass("Metrics Recording")
    except Exception as e:
        results.add_fail("Metrics Recording", str(e))


def test_metrics_success_rate():
    """Test 3.2: Metrics calculates correct success rate"""
    try:
        metrics = PerformanceMetrics()

        # 8 successes
        for _ in range(8):
            metrics.record_generation(True, 5.0, 1000, 0, 0.05)

        # 2 failures
        for _ in range(2):
            metrics.record_generation(False, 5.0, 1000, 3, 0.05)

        data = metrics.get_metrics()

        assert data["total_generations"] == 10
        assert data["success_rate"] == 0.8  # 80%

        results.add_pass("Metrics Success Rate")
    except Exception as e:
        results.add_fail("Metrics Success Rate", str(e))


def test_metrics_averages():
    """Test 3.3: Metrics calculates correct averages"""
    try:
        metrics = PerformanceMetrics()

        metrics.record_generation(True, 10.0, 1000, 0, 0.10)
        metrics.record_generation(True, 20.0, 2000, 2, 0.20)
        metrics.record_generation(True, 30.0, 3000, 1, 0.30)

        data = metrics.get_metrics()

        assert data["avg_generation_time"] == 20.0  # (10+20+30)/3
        assert data["avg_tokens"] == 2000  # (1000+2000+3000)/3
        assert data["avg_retries"] == 1.0  # (0+2+1)/3
        assert data["total_cost_usd"] == 0.60

        results.add_pass("Metrics Averages")
    except Exception as e:
        results.add_fail("Metrics Averages", str(e))


def test_metrics_throughput():
    """Test 3.4: Metrics calculates throughput"""
    try:
        metrics = PerformanceMetrics()

        # Record some generations
        for _ in range(5):
            metrics.record_generation(True, 5.0, 1000, 0, 0.05)

        data = metrics.get_metrics()

        assert data["uptime_seconds"] > 0
        assert data["generations_per_hour"] >= 0

        results.add_pass("Metrics Throughput")
    except Exception as e:
        results.add_fail("Metrics Throughput", str(e))


# ============================================================================
# Section 4: Health Monitor Tests
# ============================================================================

def test_health_monitor_basic():
    """Test 4.1: Health monitor returns status"""
    try:
        monitor = HealthMonitor()

        health = monitor.check_health()

        assert isinstance(health, HealthStatus)
        assert health.status in ["healthy", "degraded"]
        assert isinstance(health.components, dict)
        assert isinstance(health.alerts, list)
        assert health.last_check != ""

        results.add_pass("Health Monitor Basic")
    except Exception as e:
        results.add_fail("Health Monitor Basic", str(e))


def test_health_monitor_system_resources():
    """Test 4.2: Health monitor checks system resources"""
    try:
        monitor = HealthMonitor()

        health = monitor.check_health()

        assert "memory_percent" in health.metrics
        assert "disk_percent" in health.metrics
        assert "cpu_percent" in health.metrics

        results.add_pass("Health Monitor System Resources")
    except Exception as e:
        results.add_fail("Health Monitor System Resources", str(e))


def test_health_monitor_with_cache():
    """Test 4.3: Health monitor integrates with cache"""
    try:
        cache = LRUCache()
        monitor = HealthMonitor(cache=cache)

        # Generate some cache activity
        cache.set("test", "value")
        cache.get("test")
        cache.get("missing")

        health = monitor.check_health()

        assert "cache" in health.metrics
        assert "hit_rate" in health.metrics["cache"]

        results.add_pass("Health Monitor with Cache")
    except Exception as e:
        results.add_fail("Health Monitor with Cache", str(e))


def test_health_monitor_alerts():
    """Test 4.4: Health monitor generates alerts"""
    try:
        # Set very low thresholds to trigger alerts
        thresholds = AlertThreshold(
            memory_usage_percent=0.1,  # Almost any usage will trigger
            error_rate_percent=0.1
        )

        monitor = HealthMonitor(thresholds=thresholds)
        health = monitor.check_health()

        # Should have at least memory alert
        assert len(health.alerts) > 0, "Expected alerts with low thresholds"

        results.add_pass("Health Monitor Alerts")
    except Exception as e:
        results.add_fail("Health Monitor Alerts", str(e))


def test_health_monitor_dashboard():
    """Test 4.5: Health monitor provides dashboard data"""
    try:
        cache = LRUCache()
        rate_limiter = RateLimiter()
        metrics = PerformanceMetrics()

        monitor = HealthMonitor(
            cache=cache,
            rate_limiter=rate_limiter,
            metrics=metrics
        )

        dashboard = monitor.get_dashboard_data()

        assert "timestamp" in dashboard
        assert "status" in dashboard
        assert "healthy" in dashboard
        assert "system" in dashboard

        results.add_pass("Health Monitor Dashboard")
    except Exception as e:
        results.add_fail("Health Monitor Dashboard", str(e))


# ============================================================================
# Section 5: Production Optimizer Integration Tests
# ============================================================================

def test_optimizer_initialization():
    """Test 5.1: Optimizer initializes correctly"""
    try:
        optimizer = ProductionOptimizer()

        assert optimizer.cache is not None
        assert optimizer.rate_limiter is not None
        assert optimizer.metrics is not None
        assert optimizer.health_monitor is not None

        results.add_pass("Optimizer Initialization")
    except Exception as e:
        results.add_fail("Optimizer Initialization", str(e))


def test_optimizer_cache_key():
    """Test 5.2: Optimizer generates consistent cache keys"""
    try:
        optimizer = ProductionOptimizer()

        key1 = optimizer.cache_key("http", "operator", limit=5)
        key2 = optimizer.cache_key("http", "operator", limit=5)
        key3 = optimizer.cache_key("ml", "operator", limit=5)

        assert key1 == key2, "Same inputs should produce same key"
        assert key1 != key3, "Different inputs should produce different keys"

        results.add_pass("Optimizer Cache Key")
    except Exception as e:
        results.add_fail("Optimizer Cache Key", str(e))


def test_optimizer_cached_patterns():
    """Test 5.3: Optimizer caches pattern retrieval"""
    try:
        optimizer = ProductionOptimizer()

        call_count = 0

        def mock_retrieval(category, component_type, **kwargs):
            nonlocal call_count
            call_count += 1
            return [{"pattern": "test"}]

        # First call should invoke retrieval
        result1 = optimizer.get_cached_patterns(
            "http", "operator", mock_retrieval, limit=5
        )
        assert call_count == 1

        # Second call should use cache
        result2 = optimizer.get_cached_patterns(
            "http", "operator", mock_retrieval, limit=5
        )
        assert call_count == 1, "Should use cached result"

        assert result1 == result2

        results.add_pass("Optimizer Cached Patterns")
    except Exception as e:
        results.add_fail("Optimizer Cached Patterns", str(e))


def test_optimizer_rate_limiting():
    """Test 5.4: Optimizer applies rate limiting"""
    try:
        optimizer = ProductionOptimizer(
            rate_limit_config=RateLimitConfig(
                requests_per_minute=5,
                requests_per_hour=100,
                burst_limit=3
            )
        )

        # Should allow requests
        for _ in range(3):
            allowed, _ = optimizer.check_rate_limit()
            assert allowed
            optimizer.release_rate_limit()

        results.add_pass("Optimizer Rate Limiting")
    except Exception as e:
        results.add_fail("Optimizer Rate Limiting", str(e))


def test_optimizer_metrics_recording():
    """Test 5.5: Optimizer records generation metrics"""
    try:
        optimizer = ProductionOptimizer()

        optimizer.record_generation(
            success=True,
            time_seconds=10.0,
            tokens=2000,
            retries=1,
            cost_usd=0.10
        )

        health = optimizer.get_health()
        assert "performance" in health.metrics

        results.add_pass("Optimizer Metrics Recording")
    except Exception as e:
        results.add_fail("Optimizer Metrics Recording", str(e))


def test_optimizer_get_health():
    """Test 5.6: Optimizer returns health status"""
    try:
        optimizer = ProductionOptimizer()

        health = optimizer.get_health()

        assert isinstance(health, HealthStatus)
        assert health.status in ["healthy", "degraded"]

        results.add_pass("Optimizer Get Health")
    except Exception as e:
        results.add_fail("Optimizer Get Health", str(e))


def test_optimizer_get_dashboard():
    """Test 5.7: Optimizer returns dashboard data"""
    try:
        optimizer = ProductionOptimizer()

        dashboard = optimizer.get_dashboard()

        assert "timestamp" in dashboard
        assert "status" in dashboard
        assert "system" in dashboard

        results.add_pass("Optimizer Get Dashboard")
    except Exception as e:
        results.add_fail("Optimizer Get Dashboard", str(e))


def test_optimizer_cache_invalidation():
    """Test 5.8: Optimizer can invalidate cache"""
    try:
        optimizer = ProductionOptimizer()

        # Add some cache entries
        optimizer.cache.set("key1", "value1")
        optimizer.cache.set("key2", "value2")

        # Invalidate all
        cleared = optimizer.invalidate_cache()

        assert cleared == 2
        assert optimizer.cache.get("key1") is None

        results.add_pass("Optimizer Cache Invalidation")
    except Exception as e:
        results.add_fail("Optimizer Cache Invalidation", str(e))


def test_optimizer_statistics():
    """Test 5.9: Optimizer returns comprehensive statistics"""
    try:
        optimizer = ProductionOptimizer()

        stats = optimizer.get_statistics()

        assert "cache" in stats
        assert "rate_limiter" in stats
        assert "performance" in stats
        assert "health" in stats

        results.add_pass("Optimizer Statistics")
    except Exception as e:
        results.add_fail("Optimizer Statistics", str(e))


def test_create_optimizer_helper():
    """Test 5.10: Helper function creates optimizer correctly"""
    try:
        optimizer = create_production_optimizer(
            cache_max_size=500,
            cache_ttl=1800,
            rate_limit_per_minute=30
        )

        assert optimizer is not None
        assert optimizer.cache.config.max_size == 500
        assert optimizer.cache.config.ttl_seconds == 1800
        assert optimizer.rate_limiter.config.requests_per_minute == 30

        results.add_pass("Create Optimizer Helper")
    except Exception as e:
        results.add_fail("Create Optimizer Helper", str(e))


# ============================================================================
# Section 6: Configuration Tests
# ============================================================================

def test_cache_config_defaults():
    """Test 6.1: Cache config has correct defaults"""
    try:
        config = CacheConfig()

        assert config.max_size == 1000
        assert config.ttl_seconds == 3600
        assert config.cleanup_interval == 300
        assert config.enabled == True

        results.add_pass("Cache Config Defaults")
    except Exception as e:
        results.add_fail("Cache Config Defaults", str(e))


def test_rate_limit_config_defaults():
    """Test 6.2: Rate limit config has correct defaults"""
    try:
        config = RateLimitConfig()

        assert config.requests_per_minute == 60
        assert config.requests_per_hour == 1000
        assert config.burst_limit == 10
        assert config.enabled == True

        results.add_pass("Rate Limit Config Defaults")
    except Exception as e:
        results.add_fail("Rate Limit Config Defaults", str(e))


def test_alert_threshold_defaults():
    """Test 6.3: Alert thresholds have correct defaults"""
    try:
        thresholds = AlertThreshold()

        assert thresholds.error_rate_percent == 10.0
        assert thresholds.avg_response_time_seconds == 30.0
        assert thresholds.cache_hit_rate_percent == 50.0
        assert thresholds.memory_usage_percent == 80.0
        assert thresholds.disk_usage_percent == 90.0

        results.add_pass("Alert Threshold Defaults")
    except Exception as e:
        results.add_fail("Alert Threshold Defaults", str(e))


# ============================================================================
# Main Test Runner
# ============================================================================

def run_all_tests():
    """Run all Phase 6 tests"""
    print("="*80)
    print("PHASE 6: PRODUCTION OPTIMIZER - TEST SUITE")
    print("="*80)
    print()

    # Section 1: LRU Cache
    print("\n--- Section 1: LRU Cache Tests ---")
    test_cache_basic_operations()
    test_cache_ttl_expiration()
    test_cache_max_size_eviction()
    test_cache_lru_ordering()
    test_cache_statistics()
    test_cache_clear()
    test_cache_thread_safety()
    test_cache_disabled()

    # Section 2: Rate Limiter
    print("\n--- Section 2: Rate Limiter Tests ---")
    test_rate_limiter_allows_requests()
    test_rate_limiter_burst_limit()
    test_rate_limiter_minute_limit()
    test_rate_limiter_statistics()
    test_rate_limiter_disabled()

    # Section 3: Performance Metrics
    print("\n--- Section 3: Performance Metrics Tests ---")
    test_metrics_recording()
    test_metrics_success_rate()
    test_metrics_averages()
    test_metrics_throughput()

    # Section 4: Health Monitor
    print("\n--- Section 4: Health Monitor Tests ---")
    test_health_monitor_basic()
    test_health_monitor_system_resources()
    test_health_monitor_with_cache()
    test_health_monitor_alerts()
    test_health_monitor_dashboard()

    # Section 5: Production Optimizer
    print("\n--- Section 5: Production Optimizer Tests ---")
    test_optimizer_initialization()
    test_optimizer_cache_key()
    test_optimizer_cached_patterns()
    test_optimizer_rate_limiting()
    test_optimizer_metrics_recording()
    test_optimizer_get_health()
    test_optimizer_get_dashboard()
    test_optimizer_cache_invalidation()
    test_optimizer_statistics()
    test_create_optimizer_helper()

    # Section 6: Configuration
    print("\n--- Section 6: Configuration Tests ---")
    test_cache_config_defaults()
    test_rate_limit_config_defaults()
    test_alert_threshold_defaults()

    # Print summary
    return results.print_summary()


if __name__ == "__main__":
    import sys
    success = run_all_tests()
    sys.exit(0 if success else 1)
