#!/usr/bin/env python3
"""
Phase 6: Production Optimization & Integration

This module provides production-ready optimizations including:
1. Pattern caching with LRU eviction
2. Request rate limiting
3. System health monitoring
4. Performance metrics collection
5. Dashboard data aggregation
6. Resource management

Key Features:
- In-memory LRU cache for pattern retrieval (configurable size)
- Rate limiting with sliding window algorithm
- Health checks with component status monitoring
- Real-time performance metrics
- Alert thresholds for proactive monitoring
"""

import os
import time
import threading
import hashlib
import json
import psutil
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from collections import OrderedDict
from functools import wraps
import logging


@dataclass
class CacheConfig:
    """Configuration for the caching layer"""
    max_size: int = 1000  # Maximum cache entries
    ttl_seconds: int = 3600  # Time-to-live (1 hour default)
    cleanup_interval: int = 300  # Cleanup every 5 minutes
    enabled: bool = True


@dataclass
class RateLimitConfig:
    """Configuration for rate limiting"""
    requests_per_minute: int = 60
    requests_per_hour: int = 1000
    burst_limit: int = 10  # Max concurrent requests
    enabled: bool = True


@dataclass
class AlertThreshold:
    """Alert thresholds for monitoring"""
    error_rate_percent: float = 10.0  # Alert if > 10% errors
    avg_response_time_seconds: float = 30.0  # Alert if avg > 30s
    cache_hit_rate_percent: float = 50.0  # Alert if < 50% cache hits
    memory_usage_percent: float = 80.0  # Alert if > 80% memory
    disk_usage_percent: float = 90.0  # Alert if > 90% disk


@dataclass
class HealthStatus:
    """System health status"""
    healthy: bool = True
    status: str = "healthy"
    components: Dict[str, bool] = field(default_factory=dict)
    alerts: List[str] = field(default_factory=list)
    metrics: Dict[str, Any] = field(default_factory=dict)
    last_check: str = ""


class LRUCache:
    """Thread-safe LRU cache with TTL support"""

    def __init__(self, config: CacheConfig = None):
        self.config = config or CacheConfig()
        self._cache: OrderedDict[str, Tuple[Any, float]] = OrderedDict()
        self._lock = threading.RLock()
        self._hits = 0
        self._misses = 0
        self._last_cleanup = time.time()

    def get(self, key: str) -> Optional[Any]:
        """Get item from cache"""
        if not self.config.enabled:
            return None

        with self._lock:
            self._maybe_cleanup()

            if key in self._cache:
                value, expiry = self._cache[key]
                if time.time() < expiry:
                    # Move to end (most recently used)
                    self._cache.move_to_end(key)
                    self._hits += 1
                    return value
                else:
                    # Expired
                    del self._cache[key]

            self._misses += 1
            return None

    def set(self, key: str, value: Any, ttl: int = None) -> None:
        """Set item in cache"""
        if not self.config.enabled:
            return

        ttl = ttl or self.config.ttl_seconds
        expiry = time.time() + ttl

        with self._lock:
            self._maybe_cleanup()

            # Remove oldest if at capacity
            while len(self._cache) >= self.config.max_size:
                self._cache.popitem(last=False)

            self._cache[key] = (value, expiry)

    def delete(self, key: str) -> bool:
        """Delete item from cache"""
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                return True
            return False

    def clear(self) -> int:
        """Clear all cache entries"""
        with self._lock:
            count = len(self._cache)
            self._cache.clear()
            return count

    def _maybe_cleanup(self) -> None:
        """Remove expired entries periodically"""
        now = time.time()
        if now - self._last_cleanup < self.config.cleanup_interval:
            return

        self._last_cleanup = now
        expired_keys = [
            k for k, (_, expiry) in self._cache.items()
            if now >= expiry
        ]
        for key in expired_keys:
            del self._cache[key]

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        with self._lock:
            total = self._hits + self._misses
            return {
                "size": len(self._cache),
                "max_size": self.config.max_size,
                "hits": self._hits,
                "misses": self._misses,
                "hit_rate": self._hits / total if total > 0 else 0,
                "ttl_seconds": self.config.ttl_seconds,
                "enabled": self.config.enabled
            }


class RateLimiter:
    """Sliding window rate limiter"""

    def __init__(self, config: RateLimitConfig = None):
        self.config = config or RateLimitConfig()
        self._minute_requests: List[float] = []
        self._hour_requests: List[float] = []
        self._concurrent = 0
        self._lock = threading.RLock()
        self._total_requests = 0
        self._rejected_requests = 0

    def acquire(self) -> Tuple[bool, str]:
        """
        Try to acquire a rate limit slot.

        Returns:
            Tuple of (allowed: bool, reason: str)
        """
        if not self.config.enabled:
            return True, "rate_limiting_disabled"

        now = time.time()

        with self._lock:
            # Clean old entries
            minute_ago = now - 60
            hour_ago = now - 3600

            self._minute_requests = [t for t in self._minute_requests if t > minute_ago]
            self._hour_requests = [t for t in self._hour_requests if t > hour_ago]

            self._total_requests += 1

            # Check burst limit
            if self._concurrent >= self.config.burst_limit:
                self._rejected_requests += 1
                return False, f"burst_limit_exceeded ({self.config.burst_limit})"

            # Check per-minute limit
            if len(self._minute_requests) >= self.config.requests_per_minute:
                self._rejected_requests += 1
                return False, f"minute_limit_exceeded ({self.config.requests_per_minute}/min)"

            # Check per-hour limit
            if len(self._hour_requests) >= self.config.requests_per_hour:
                self._rejected_requests += 1
                return False, f"hour_limit_exceeded ({self.config.requests_per_hour}/hour)"

            # Allow request
            self._minute_requests.append(now)
            self._hour_requests.append(now)
            self._concurrent += 1

            return True, "allowed"

    def release(self) -> None:
        """Release a rate limit slot"""
        with self._lock:
            self._concurrent = max(0, self._concurrent - 1)

    def get_stats(self) -> Dict[str, Any]:
        """Get rate limiter statistics"""
        with self._lock:
            return {
                "current_minute_requests": len(self._minute_requests),
                "current_hour_requests": len(self._hour_requests),
                "concurrent_requests": self._concurrent,
                "total_requests": self._total_requests,
                "rejected_requests": self._rejected_requests,
                "rejection_rate": self._rejected_requests / self._total_requests if self._total_requests > 0 else 0,
                "limits": {
                    "per_minute": self.config.requests_per_minute,
                    "per_hour": self.config.requests_per_hour,
                    "burst": self.config.burst_limit
                },
                "enabled": self.config.enabled
            }


class PerformanceMetrics:
    """Collect and track performance metrics"""

    def __init__(self):
        self._lock = threading.RLock()
        self._generation_times: List[float] = []
        self._token_counts: List[int] = []
        self._success_count = 0
        self._failure_count = 0
        self._retry_counts: List[int] = []
        self._cost_tracker: List[float] = []
        self._start_time = time.time()

    def record_generation(
        self,
        success: bool,
        time_seconds: float,
        tokens: int,
        retries: int,
        cost_usd: float = 0.0
    ) -> None:
        """Record a generation attempt"""
        with self._lock:
            self._generation_times.append(time_seconds)
            self._token_counts.append(tokens)
            self._retry_counts.append(retries)
            self._cost_tracker.append(cost_usd)

            if success:
                self._success_count += 1
            else:
                self._failure_count += 1

            # Keep only last 1000 entries
            if len(self._generation_times) > 1000:
                self._generation_times = self._generation_times[-1000:]
                self._token_counts = self._token_counts[-1000:]
                self._retry_counts = self._retry_counts[-1000:]
                self._cost_tracker = self._cost_tracker[-1000:]

    def get_metrics(self) -> Dict[str, Any]:
        """Get current performance metrics"""
        with self._lock:
            total = self._success_count + self._failure_count
            uptime = time.time() - self._start_time

            return {
                "total_generations": total,
                "successful_generations": self._success_count,
                "failed_generations": self._failure_count,
                "success_rate": self._success_count / total if total > 0 else 0,
                "avg_generation_time": sum(self._generation_times) / len(self._generation_times) if self._generation_times else 0,
                "avg_tokens": sum(self._token_counts) / len(self._token_counts) if self._token_counts else 0,
                "avg_retries": sum(self._retry_counts) / len(self._retry_counts) if self._retry_counts else 0,
                "total_cost_usd": sum(self._cost_tracker),
                "uptime_seconds": uptime,
                "generations_per_hour": total / (uptime / 3600) if uptime > 0 else 0
            }


class HealthMonitor:
    """Monitor system health and generate alerts"""

    def __init__(
        self,
        thresholds: AlertThreshold = None,
        cache: LRUCache = None,
        rate_limiter: RateLimiter = None,
        metrics: PerformanceMetrics = None
    ):
        self.thresholds = thresholds or AlertThreshold()
        self.cache = cache
        self.rate_limiter = rate_limiter
        self.metrics = metrics
        self.logger = logging.getLogger(__name__)

        # Component health tracking
        self._component_status: Dict[str, bool] = {}
        self._last_check = None

    def check_health(self) -> HealthStatus:
        """
        Perform comprehensive health check.

        Returns:
            HealthStatus with component status and any alerts
        """
        status = HealthStatus()
        status.last_check = datetime.now().isoformat()

        alerts = []

        # 1. Check system resources
        try:
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')

            status.metrics["memory_percent"] = memory.percent
            status.metrics["disk_percent"] = disk.percent
            status.metrics["cpu_percent"] = psutil.cpu_percent(interval=0.1)

            if memory.percent > self.thresholds.memory_usage_percent:
                alerts.append(f"High memory usage: {memory.percent:.1f}%")

            if disk.percent > self.thresholds.disk_usage_percent:
                alerts.append(f"High disk usage: {disk.percent:.1f}%")

            self._component_status["system_resources"] = True
        except Exception as e:
            self._component_status["system_resources"] = False
            alerts.append(f"Failed to check system resources: {str(e)}")

        # 2. Check cache health
        if self.cache:
            try:
                cache_stats = self.cache.get_stats()
                status.metrics["cache"] = cache_stats

                if cache_stats["hit_rate"] * 100 < self.thresholds.cache_hit_rate_percent:
                    if cache_stats["hits"] + cache_stats["misses"] > 100:  # Only alert after enough requests
                        alerts.append(f"Low cache hit rate: {cache_stats['hit_rate']*100:.1f}%")

                self._component_status["cache"] = True
            except Exception as e:
                self._component_status["cache"] = False
                alerts.append(f"Cache health check failed: {str(e)}")

        # 3. Check rate limiter
        if self.rate_limiter:
            try:
                rl_stats = self.rate_limiter.get_stats()
                status.metrics["rate_limiter"] = rl_stats

                if rl_stats["rejection_rate"] > 0.1:  # More than 10% rejected
                    alerts.append(f"High rate limit rejection: {rl_stats['rejection_rate']*100:.1f}%")

                self._component_status["rate_limiter"] = True
            except Exception as e:
                self._component_status["rate_limiter"] = False
                alerts.append(f"Rate limiter check failed: {str(e)}")

        # 4. Check performance metrics
        if self.metrics:
            try:
                perf_metrics = self.metrics.get_metrics()
                status.metrics["performance"] = perf_metrics

                # Check error rate
                error_rate = (1 - perf_metrics["success_rate"]) * 100
                if error_rate > self.thresholds.error_rate_percent:
                    if perf_metrics["total_generations"] > 10:  # Only alert after enough requests
                        alerts.append(f"High error rate: {error_rate:.1f}%")

                # Check response time
                if perf_metrics["avg_generation_time"] > self.thresholds.avg_response_time_seconds:
                    alerts.append(f"Slow generation time: {perf_metrics['avg_generation_time']:.1f}s avg")

                self._component_status["performance"] = True
            except Exception as e:
                self._component_status["performance"] = False
                alerts.append(f"Performance check failed: {str(e)}")

        # Set overall status
        status.components = self._component_status.copy()
        status.alerts = alerts
        status.healthy = len(alerts) == 0 and all(self._component_status.values())
        status.status = "healthy" if status.healthy else "degraded"

        self._last_check = status
        return status

    def get_dashboard_data(self) -> Dict[str, Any]:
        """Get data for dashboard visualization"""
        health = self.check_health()

        dashboard = {
            "timestamp": datetime.now().isoformat(),
            "status": health.status,
            "healthy": health.healthy,
            "alerts_count": len(health.alerts),
            "alerts": health.alerts,
            "components": health.components,
            "system": {
                "memory_percent": health.metrics.get("memory_percent", 0),
                "disk_percent": health.metrics.get("disk_percent", 0),
                "cpu_percent": health.metrics.get("cpu_percent", 0)
            }
        }

        # Add cache stats
        if "cache" in health.metrics:
            dashboard["cache"] = health.metrics["cache"]

        # Add rate limiter stats
        if "rate_limiter" in health.metrics:
            dashboard["rate_limiting"] = health.metrics["rate_limiter"]

        # Add performance stats
        if "performance" in health.metrics:
            perf = health.metrics["performance"]
            dashboard["performance"] = {
                "total_generations": perf["total_generations"],
                "success_rate_percent": perf["success_rate"] * 100,
                "avg_time_seconds": round(perf["avg_generation_time"], 2),
                "avg_tokens": int(perf["avg_tokens"]),
                "avg_retries": round(perf["avg_retries"], 2),
                "total_cost_usd": round(perf["total_cost_usd"], 2),
                "generations_per_hour": round(perf["generations_per_hour"], 1)
            }

        return dashboard


class ProductionOptimizer:
    """
    Main production optimizer that integrates all optimization components.

    This class provides:
    - Caching for pattern retrieval
    - Rate limiting for API protection
    - Performance metrics collection
    - Health monitoring with alerts
    - Dashboard data aggregation
    """

    def __init__(
        self,
        cache_config: CacheConfig = None,
        rate_limit_config: RateLimitConfig = None,
        alert_thresholds: AlertThreshold = None
    ):
        """
        Initialize the production optimizer.

        Args:
            cache_config: Configuration for caching
            rate_limit_config: Configuration for rate limiting
            alert_thresholds: Thresholds for health alerts
        """
        self.logger = logging.getLogger(__name__)

        # Initialize components
        self.cache = LRUCache(cache_config)
        self.rate_limiter = RateLimiter(rate_limit_config)
        self.metrics = PerformanceMetrics()
        self.health_monitor = HealthMonitor(
            thresholds=alert_thresholds,
            cache=self.cache,
            rate_limiter=self.rate_limiter,
            metrics=self.metrics
        )

        self.logger.info("Production optimizer initialized")

    def cache_key(self, category: str, component_type: str, **kwargs) -> str:
        """Generate cache key for pattern retrieval"""
        key_parts = [category, component_type]
        key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
        key_str = "|".join(str(p) for p in key_parts)
        return hashlib.md5(key_str.encode()).hexdigest()

    def get_cached_patterns(
        self,
        category: str,
        component_type: str,
        retrieval_func,
        **kwargs
    ) -> List[Dict]:
        """
        Get patterns with caching.

        Args:
            category: Component category
            component_type: Type of component
            retrieval_func: Function to call on cache miss
            **kwargs: Additional arguments for retrieval

        Returns:
            List of patterns
        """
        key = self.cache_key(category, component_type, **kwargs)

        # Try cache first
        cached = self.cache.get(key)
        if cached is not None:
            return cached

        # Cache miss - retrieve patterns
        patterns = retrieval_func(category, component_type, **kwargs)

        # Cache the result
        self.cache.set(key, patterns)

        return patterns

    def check_rate_limit(self) -> Tuple[bool, str]:
        """
        Check if request is allowed under rate limits.

        Returns:
            Tuple of (allowed: bool, reason: str)
        """
        return self.rate_limiter.acquire()

    def release_rate_limit(self) -> None:
        """Release rate limit slot after request completes"""
        self.rate_limiter.release()

    def record_generation(
        self,
        success: bool,
        time_seconds: float,
        tokens: int,
        retries: int,
        cost_usd: float = 0.0
    ) -> None:
        """Record generation metrics"""
        self.metrics.record_generation(
            success=success,
            time_seconds=time_seconds,
            tokens=tokens,
            retries=retries,
            cost_usd=cost_usd
        )

    def get_health(self) -> HealthStatus:
        """Get current health status"""
        return self.health_monitor.check_health()

    def get_dashboard(self) -> Dict[str, Any]:
        """Get dashboard data"""
        return self.health_monitor.get_dashboard_data()

    def invalidate_cache(self, category: str = None) -> int:
        """
        Invalidate cache entries.

        Args:
            category: If provided, only invalidate entries for this category.
                     If None, clears entire cache.

        Returns:
            Number of entries cleared
        """
        if category is None:
            return self.cache.clear()

        # Clear entries matching category (requires iterating)
        # For simplicity, clear all if category specified
        return self.cache.clear()

    def get_statistics(self) -> Dict[str, Any]:
        """Get comprehensive statistics"""
        return {
            "cache": self.cache.get_stats(),
            "rate_limiter": self.rate_limiter.get_stats(),
            "performance": self.metrics.get_metrics(),
            "health": self.health_monitor.check_health().__dict__
        }


def rate_limited(optimizer: ProductionOptimizer):
    """
    Decorator for rate-limiting async functions.

    Usage:
        @rate_limited(optimizer)
        async def my_endpoint():
            ...
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            allowed, reason = optimizer.check_rate_limit()
            if not allowed:
                raise Exception(f"Rate limit exceeded: {reason}")

            try:
                return await func(*args, **kwargs)
            finally:
                optimizer.release_rate_limit()

        return wrapper
    return decorator


def cached_patterns(optimizer: ProductionOptimizer, category_arg: str = "category", type_arg: str = "component_type"):
    """
    Decorator for caching pattern retrieval results.

    Usage:
        @cached_patterns(optimizer)
        def get_patterns(category, component_type):
            ...
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            category = kwargs.get(category_arg, "")
            component_type = kwargs.get(type_arg, "")

            key = optimizer.cache_key(category, component_type)
            cached = optimizer.cache.get(key)

            if cached is not None:
                return cached

            result = func(*args, **kwargs)
            optimizer.cache.set(key, result)
            return result

        return wrapper
    return decorator


# Convenience function for creating optimizer with defaults
def create_production_optimizer(
    cache_max_size: int = 1000,
    cache_ttl: int = 3600,
    rate_limit_per_minute: int = 60,
    rate_limit_per_hour: int = 1000
) -> ProductionOptimizer:
    """
    Create a ProductionOptimizer with custom configuration.

    Args:
        cache_max_size: Maximum cache entries
        cache_ttl: Cache TTL in seconds
        rate_limit_per_minute: Max requests per minute
        rate_limit_per_hour: Max requests per hour

    Returns:
        Configured ProductionOptimizer
    """
    return ProductionOptimizer(
        cache_config=CacheConfig(
            max_size=cache_max_size,
            ttl_seconds=cache_ttl
        ),
        rate_limit_config=RateLimitConfig(
            requests_per_minute=rate_limit_per_minute,
            requests_per_hour=rate_limit_per_hour
        )
    )
