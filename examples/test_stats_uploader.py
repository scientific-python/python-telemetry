"""Test script for the stats uploader module

This script demonstrates the various features of the StatsUploader class,
including the new enhanced capabilities from the updated AnalyticsClient.

NOTE: This test file demonstrates features from the updated source code.
      If using the installed package, some features may not be available.
"""
# ruff: noqa: T201

from __future__ import annotations

import logging

from telemetric.ga4.stats_uploader import StatsUploader
from telemetric.statswrapper import stats_deco

logging.basicConfig(level=logging.DEBUG)


# Create some test functions with statistics
@stats_deco(None, b=("a", 3), c=None)  # type: ignore[no-untyped-call]
def test_func(a, b=None, c=None):
    """Test function with various parameters"""
    return a, b, c


@stats_deco(x=None, y=(True, False))  # type: ignore[no-untyped-call]
def another_func(x=1, y=True):
    """Another test function with different parameters"""
    if y:
        return x * 2
    return x


@stats_deco()  # type: ignore[no-untyped-call]
def simple_func(value):
    """Simple function for additional testing"""
    return value * 2


# Call the functions to generate some statistics
print("=== Generating Test Statistics ===")
test_func(1, 3)
test_func("hello", "a", "world")
test_func(42)

another_func(5)
another_func(10, False)
another_func(15, True)

# Call simple_func multiple times
simple_func(10)
simple_func(20)
simple_func(30)


# Print current statistics
print("\n=== Current Statistics ===")
print(f"test_func counts: {test_func._get_counts()}")
print(f"test_func param stats: {test_func._get_param_stats()}")
print()
print(f"another_func counts: {another_func._get_counts()}")
print(f"another_func param stats: {another_func._get_param_stats()}")
print()
print(f"simple_func counts: {simple_func._get_counts()}")
print()


# Test 1: Basic usage with default settings
print("=== Test 1: Basic Usage ===")
uploader_basic = StatsUploader(
    proxy_url="https://analytics-proxy-production-665e.up.railway.app"
)
print(f"Analytics client enabled: {uploader_basic.analytics.enabled}")
print(f"Client ID: {uploader_basic.analytics.client_id}")
print(f"Timeout: {getattr(uploader_basic.analytics, 'timeout', 'N/A')}s")
print(f"Max retries: {getattr(uploader_basic.analytics, 'max_retries', 'N/A')}")


# Test 2: Enhanced configuration with retries and custom timeout
print("\n=== Test 2: Enhanced Configuration ===")
try:
    uploader_enhanced = StatsUploader(  # type: ignore[call-arg]
        proxy_url="https://analytics-proxy-production-665e.up.railway.app",
        client_id="test-client-12345",
        timeout=5.0,
        max_retries=2,
    )
    print(f"Custom client ID: {uploader_enhanced.analytics.client_id}")
    print(f"Custom timeout: {getattr(uploader_enhanced.analytics, 'timeout', 'N/A')}s")
    print(
        f"Custom max retries: {getattr(uploader_enhanced.analytics, 'max_retries', 'N/A')}"
    )
except TypeError as e:
    print(f"Enhanced features not available in installed version: {e}")
    print("(Update to the latest version to use these features)")


# Test 3: Upload individual function stats
print("\n=== Test 3: Individual Function Upload ===")
result1 = uploader_basic.upload_function_stats(test_func, package_name="test_package")
print(f"test_func upload result: {result1}")

result2 = uploader_basic.upload_function_stats(
    another_func, package_name="test_package"
)
print(f"another_func upload result: {result2}")

result3 = uploader_basic.upload_function_stats(simple_func, package_name="test_package")
print(f"simple_func upload result: {result3}")


# Test 4: Upload all stats with detailed results
print("\n=== Test 4: Upload All Stats ===")
summary = uploader_basic.upload_all_stats(package_name="test_package")
print("Upload summary:")
print(f"  - Uploaded: {summary['uploaded']}")
print(f"  - Failed: {summary.get('failed', 0)}")
print(f"  - Skipped: {summary['skipped']}")
print(f"  - Total functions: {summary['total_functions']}")
print(f"  - Status: {summary['status']}")


# Test 5: Custom stats upload
print("\n=== Test 5: Custom Stats Upload ===")
custom_result = uploader_basic.upload_custom_stats(
    "custom_metric",
    {
        "metric_name": "test_metric",
        "value": 42,
        "category": "testing",
        "description": "Testing custom metrics",
    },
)
print(f"Custom upload result: {custom_result}")


# Test 6: Context manager usage
print("\n=== Test 6: Context Manager Usage ===")
try:
    with StatsUploader(  # type: ignore[call-arg,attr-defined]
        proxy_url="https://analytics-proxy-production-665e.up.railway.app",
        client_id="context-manager-test",
        max_retries=1,
    ) as uploader_ctx:
        print(
            f"Using context manager with client ID: {uploader_ctx.analytics.client_id}"
        )
        ctx_summary = uploader_ctx.upload_all_stats(package_name="test_package_ctx")
        print(f"Context manager upload status: {ctx_summary['status']}")
    print("Context manager closed")
except (TypeError, AttributeError) as e:
    print(f"Context manager not available in installed version: {e}")
    print("(Update to the latest version to use this feature)")


# Test 7: Disabled telemetry
print("\n=== Test 7: Disabled Telemetry ===")
try:
    uploader_disabled = StatsUploader(  # type: ignore[call-arg]
        proxy_url="https://analytics-proxy-production-665e.up.railway.app",
        enabled=False,
    )
    print(f"Telemetry enabled: {uploader_disabled.analytics.enabled}")
    disabled_result = uploader_disabled.upload_function_stats(test_func)
    print(f"Upload result when disabled: {disabled_result}")
    disabled_summary = uploader_disabled.upload_all_stats()
    print(f"Upload summary when disabled: {disabled_summary}")
except TypeError as e:
    print(f"Explicit disable feature not available in installed version: {e}")
    print("(Can still use DO_NOT_TRACK=1 environment variable)")


print("\n=== All Tests Complete ===")
