"""Test script for the stats uploader module"""

from __future__ import annotations

import logging

from telemetric.ga4.stats_uploader import StatsUploader
from telemetric.statswrapper import stats_deco

logging.basicConfig(level=logging.DEBUG)


# Create some test functions with statistics
@stats_deco(None, b=("a", 3), c=None)
def test_func(a, b=None, c=None):
    return a, b, c


@stats_deco(x=None, y=(True, False))
def another_func(x=1, y=True):
    if y:
        return x * 2
    return x


# Call the functions to generate some statistics
test_func(1, 3)
test_func("hello", "a", "world")
test_func(42)

another_func(5)
another_func(10, False)
another_func(15, True)


# Print current statistics
print("=== Current Statistics ===")  # noqa: T201
print("test_func counts:", test_func._get_counts())  # noqa: T201
print("test_func param stats:", test_func._get_param_stats())  # noqa: T201
print()  # noqa: T201
print("another_func counts:", another_func._get_counts())  # noqa: T201
print("another_func param stats:", another_func._get_param_stats())  # noqa: T201
print()  # noqa: T201


# Test the stats uploader (this will try to upload to GA4)
print("=== Testing Stats Uploader ===")  # noqa: T201

# Use a dummy proxy URL for testing (won't actually send data unless configured)
uploader = StatsUploader(
    proxy_url="https://analytics-proxy-production-665e.up.railway.app"
)

print("Analytics client enabled:", uploader.analytics.enabled)  # noqa: T201

# Test uploading individual function stats
print("Uploading test_func stats...")  # noqa: T201
result1 = uploader.upload_function_stats(test_func, package_name="test_package")
print("Upload result:", result1)  # noqa: T201

print("Uploading another_func stats...")  # noqa: T201
result2 = uploader.upload_function_stats(another_func, package_name="test_package")
print("Upload result:", result2)  # noqa: T201

# Test uploading all stats
print("\nUploading all stats...")  # noqa: T201
summary = uploader.upload_all_stats(package_name="test_package")
print("Upload summary:", summary)  # noqa: T201

# Test custom stats upload
print("\nUploading custom stats...")  # noqa: T201
custom_result = uploader.upload_custom_stats(
    "custom_metric", {"metric_name": "test_metric", "value": 42, "category": "testing"}
)
print("Custom upload result:", custom_result)  # noqa: T201
