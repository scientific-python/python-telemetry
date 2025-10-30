"""Module for uploading statswrapper statistics to Google Analytics 4"""

from __future__ import annotations

from typing import Any

from telemetric.ga4.analytics import AnalyticsClient
from telemetric.statswrapper import _wrapped


class StatsUploader:
    """
    Uploads statswrapper function usage statistics to Google Analytics 4.

    This class wraps the AnalyticsClient to provide specialized functionality
    for uploading function usage statistics from the statswrapper module.

    Args:
        proxy_url: The URL of the GA4 proxy server
        client_id: Optional unique identifier for this client
        timeout: Request timeout in seconds (default: 2.0)
        max_retries: Maximum number of retry attempts (default: 1)
        enabled: Override automatic telemetry detection

    Example:
        Basic usage:
        >>> uploader = StatsUploader(
        ...     proxy_url="https://your-project.up.railway.app"
        ... )
        >>> result = uploader.upload_all_stats(package_name="mypackage")
        >>> print(f"Uploaded {result['uploaded']} functions")

        With retry logic:
        >>> uploader = StatsUploader(
        ...     proxy_url="https://your-project.up.railway.app",
        ...     max_retries=2,
        ...     timeout=5.0
        ... )
        >>> uploader.upload_all_stats()

        Using as context manager:
        >>> with StatsUploader(proxy_url="...") as uploader:
        ...     uploader.upload_all_stats()
    """

    def __init__(
        self,
        proxy_url: str,
        client_id: str | None = None,
        timeout: float = 2.0,
        max_retries: int = 1,
        enabled: bool | None = None,
    ) -> None:
        """
        Initialize the stats uploader.

        Args:
            proxy_url: The URL of the GA4 proxy server
            client_id: Optional unique identifier for this client
            timeout: Request timeout in seconds (default: 2.0)
            max_retries: Maximum number of retry attempts (default: 1)
            enabled: Override automatic telemetry detection
        """
        self.analytics = AnalyticsClient(
            proxy_url=proxy_url,
            client_id=client_id,
            timeout=timeout,
            max_retries=max_retries,
            enabled=enabled,
        )

    def upload_function_stats(
        self, wrapped_func: Any, package_name: str | None = None
    ) -> bool:
        """
        Upload statistics for a single wrapped function to GA4.

        Args:
            wrapped_func: A statswrapper-wrapped function
            package_name: Optional package name to include in the event

        Returns:
            True if the event was sent successfully, False if telemetry is
            disabled or the request failed
        """
        # Get function counts: (total_calls, error_calls, invalid_args)
        counts = wrapped_func._get_counts()  # pylint: disable=protected-access
        total_calls, error_calls, invalid_args = counts

        # Skip functions that haven't been called
        if total_calls == 0:
            return False

        # Get parameter statistics
        param_stats = wrapped_func._get_param_stats()  # pylint: disable=protected-access

        # Build event parameters
        event_params: dict[str, Any] = {
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
        param_data: dict[str, Any] = {}
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

        # Send to GA4 and return the result
        return self.analytics.track_event("function_usage_stats", event_params)

    def upload_all_stats(
        self, package_name: str | None = None, skip_uncalled: bool = True
    ) -> dict[str, Any]:
        """
        Upload statistics for all wrapped functions to GA4.

        This method uploads individual function stats and then a summary event.
        It uses the analytics client's tracking capabilities to handle retries
        and error handling automatically.

        Args:
            package_name: Optional package name to include in events
            skip_uncalled: Whether to skip functions that haven't been called

        Returns:
            Dictionary containing upload results:
            - uploaded: Number of functions successfully uploaded
            - failed: Number of functions that failed to upload
            - skipped: Number of functions skipped (not called)
            - total_functions: Total number of wrapped functions
            - status: Overall status ('disabled', 'completed', or 'partial')

        Example:
            >>> uploader = StatsUploader(proxy_url="https://analytics.example.com")
            >>> result = uploader.upload_all_stats(package_name="mylib")
            >>> print(f"{result['uploaded']}/{result['total_functions']} uploaded")
        """
        if not self.analytics.enabled:
            return {
                "uploaded": 0,
                "failed": 0,
                "skipped": 0,
                "total_functions": len(_wrapped),
                "status": "disabled",
            }

        uploaded = 0
        failed = 0
        skipped = 0

        for wrapped_func in _wrapped:
            counts = wrapped_func._get_counts()  # pylint: disable=protected-access
            total_calls = counts[0]

            if skip_uncalled and total_calls == 0:
                skipped += 1
                continue

            # Track success/failure of each upload
            success = self.upload_function_stats(wrapped_func, package_name)
            if success:
                uploaded += 1
            else:
                failed += 1

        # Upload summary statistics
        summary_params: dict[str, Any] = {
            "total_wrapped_functions": len(_wrapped),
            "functions_called": sum(
                1
                for f in _wrapped
                if f._get_counts()[0] > 0  # pylint: disable=protected-access
            ),
            "total_function_calls": sum(
                f._get_counts()[0]
                for f in _wrapped  # pylint: disable=protected-access
            ),
            "total_errors": sum(
                f._get_counts()[1]
                for f in _wrapped  # pylint: disable=protected-access
            ),
        }

        if package_name:
            summary_params["package_name"] = package_name

        summary_sent = self.analytics.track_event(
            "package_usage_summary", summary_params
        )

        # Determine overall status
        status = "completed" if failed == 0 else "partial"
        if not summary_sent:
            status = "partial"

        return {
            "uploaded": uploaded,
            "failed": failed,
            "skipped": skipped,
            "total_functions": len(_wrapped),
            "status": status,
        }

    def upload_custom_stats(self, event_name: str, stats_data: dict[str, Any]) -> bool:
        """
        Upload custom statistics data to GA4.

        This is a convenience method for sending custom analytics events
        that don't fit the standard function usage format.

        Args:
            event_name: Name of the GA4 event
            stats_data: Dictionary of statistics to upload

        Returns:
            True if the event was sent successfully, False if telemetry is
            disabled or the request failed

        Example:
            >>> uploader = StatsUploader(proxy_url="https://analytics.example.com")
            >>> uploader.upload_custom_stats('custom_metric', {
            ...     'metric_value': 42,
            ...     'metric_type': 'performance'
            ... })
            True
        """
        return self.analytics.track_event(event_name, stats_data)

    def __enter__(self) -> StatsUploader:
        """Context manager entry."""
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Context manager exit."""
        # Delegate to analytics client
        self.analytics.__exit__(exc_type, exc_val, exc_tb)
