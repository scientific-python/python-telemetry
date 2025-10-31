"""Module for uploading statswrapper statistics to Google Analytics 4"""

from __future__ import annotations

from typing import Any, Dict, Optional

from telemetric.ga4.analytics import AnalyticsClient
from telemetric.statswrapper import _wrapped


class StatsUploader:
    """
    Uploads statswrapper function usage statistics to Google Analytics 4.

    Example usage:
    uploader = StatsUploader(proxy_url="https://your-project.up.railway.app")
    uploader.upload_all_stats()
    """

    def __init__(self, proxy_url: str):
        """
        Initialize the stats uploader.

        Args:
            proxy_url: The URL of the GA4 proxy server
        """
        self.analytics = AnalyticsClient(proxy_url)

    def upload_function_stats(
        self, wrapped_func, package_name: Optional[str] = None
    ) -> bool:
        """
        Upload statistics for a single wrapped function to GA4.

        Args:
            wrapped_func: A statswrapper-wrapped function
            package_name: Optional package name to include in the event

        Returns:
            bool: True if upload was attempted (regardless of success), False if disabled
        """
        if not self.analytics.enabled:
            return False

        # Get function counts: (total_calls, error_calls, invalid_args)
        counts = wrapped_func._get_counts()
        total_calls, error_calls, invalid_args = counts

        # Skip functions that haven't been called
        if total_calls == 0:
            return True

        # Get parameter statistics
        param_stats = wrapped_func._get_param_stats()

        # Build event parameters
        event_params = {
            "function_name": f"{wrapped_func.__module__}.{wrapped_func.__name__}",
            "total_calls": total_calls,
            "error_calls": error_calls,
            "invalid_args": invalid_args,
            "success_rate": round((total_calls - error_calls) / total_calls, 3)
            if total_calls > 0
            else 0,
        }

        if package_name:
            event_params["package_name"] = package_name

        # Add parameter usage statistics
        param_data = {}
        for name, n_uses, known_params, param_counts in param_stats:
            if name is None:
                # Positional argument
                param_key = "pos_arg_uses"
                param_data[param_key] = n_uses
            else:
                # Named argument
                param_key = f"arg_{name}_uses"
                param_data[param_key] = n_uses

                # Add specific parameter value counts if available
                if known_params is not None and param_counts is not None:
                    for i, param_val in enumerate(known_params):
                        if i < len(param_counts):
                            count_key = f"arg_{name}_{param_val}_count"
                            param_data[count_key] = param_counts[i]

        # Merge parameter data into event params (limit to reasonable size)
        if len(param_data) <= 20:  # GA4 has parameter limits
            event_params.update(param_data)
        else:
            # If too many parameters, just include summary
            event_params["total_params_tracked"] = len(param_data)

        # Send to GA4
        self.analytics.track_event("function_usage_stats", event_params)
        return True

    def upload_all_stats(
        self, package_name: Optional[str] = None, skip_uncalled: bool = True
    ) -> Dict[str, Any]:
        """
        Upload statistics for all wrapped functions to GA4.

        Args:
            package_name: Optional package name to include in events
            skip_uncalled: Whether to skip functions that haven't been called

        Returns:
            dict: Summary of upload results
        """
        if not self.analytics.enabled:
            return {
                "uploaded": 0,
                "skipped": 0,
                "total_functions": len(_wrapped),
                "status": "disabled",
            }

        uploaded = 0
        skipped = 0

        for wrapped_func in _wrapped:
            counts = wrapped_func._get_counts()
            total_calls = counts[0]

            if skip_uncalled and total_calls == 0:
                skipped += 1
                continue

            self.upload_function_stats(wrapped_func, package_name)
            uploaded += 1

        # Upload summary statistics
        summary_params = {
            "total_wrapped_functions": len(_wrapped),
            "functions_called": sum(1 for f in _wrapped if f._get_counts()[0] > 0),
            "total_function_calls": sum(f._get_counts()[0] for f in _wrapped),
            "total_errors": sum(f._get_counts()[1] for f in _wrapped),
        }

        if package_name:
            summary_params["package_name"] = package_name

        self.analytics.track_event("package_usage_summary", summary_params)

        return {
            "uploaded": uploaded,
            "skipped": skipped,
            "total_functions": len(_wrapped),
            "status": "completed",
        }

    def upload_custom_stats(self, event_name: str, stats_data: Dict[str, Any]) -> bool:
        """
        Upload custom statistics data to GA4.

        Args:
            event_name: Name of the GA4 event
            stats_data: Dictionary of statistics to upload

        Returns:
            bool: True if upload was attempted, False if disabled
        """
        if not self.analytics.enabled:
            return False

        self.analytics.track_event(event_name, stats_data)
        return True
