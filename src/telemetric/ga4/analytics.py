"""
Google Analytics 4 client for tracking events via a proxy server.

This module provides a client for sending analytics events to Google Analytics 4
through a proxy server. It includes features like automatic environment detection,
retry logic, and optional async support.
"""

from __future__ import annotations

import logging
import os
import platform
import uuid
from typing import Any

import requests  # type: ignore[import-untyped]

_log = logging.getLogger(__name__)


class AnalyticsClient:
    """
    Client for tracking analytics events through a GA4 proxy server.

    The client automatically includes system information (Python version, OS)
    with each event and respects DO_NOT_TRACK and CI environment variables.

    Args:
        proxy_url: Base URL of the GA4 proxy server
        client_id: Optional unique identifier for this client. If not provided,
            a random UUID will be generated
        timeout: Request timeout in seconds (default: 2)
        max_retries: Maximum number of retry attempts for failed requests (default: 0)
        enabled: Override automatic telemetry detection. If None, respects
            DO_NOT_TRACK and CI environment variables

    Example:
        Basic usage:
        >>> analytics = AnalyticsClient(
        ...     proxy_url="https://your-project.up.railway.app"
        ... )
        >>> analytics.track_event('package_imported', {
        ...     'package_version': '1.0.0',
        ...     'feature': 'auth'
        ... })

        With custom client ID:
        >>> analytics = AnalyticsClient(
        ...     proxy_url="https://analytics.example.com",
        ...     client_id="user-12345"
        ... )
        >>> analytics.track_event('feature_used', {'feature_name': 'export'})

        Force enable/disable:
        >>> analytics = AnalyticsClient(
        ...     proxy_url="https://analytics.example.com",
        ...     enabled=False  # Explicitly disable tracking
        ... )
    """

    def __init__(
        self,
        proxy_url: str,
        client_id: str | None = None,
        timeout: float = 2.0,
        max_retries: int = 0,
        enabled: bool | None = None,
    ) -> None:
        """Initialize the analytics client."""
        self.proxy_url = proxy_url.rstrip("/")
        self.client_id = client_id or str(uuid.uuid4())
        self.timeout = timeout
        self.max_retries = max(0, max_retries)
        self.enabled = enabled if enabled is not None else not self._is_disabled()

        _log.debug(
            "AnalyticsClient initialized: enabled=%s, client_id=%s, proxy_url=%s",
            self.enabled,
            self.client_id,
            self.proxy_url,
        )

    def _is_disabled(self) -> bool:
        """
        Check if telemetry should be disabled based on environment variables.

        Returns:
            True if telemetry is disabled via DO_NOT_TRACK or CI environment variables
        """
        do_not_track = os.environ.get("DO_NOT_TRACK", "").lower() in ("1", "true")
        is_ci = os.environ.get("CI", "").lower() in ("1", "true")
        return do_not_track or is_ci

    def _get_system_info(self) -> dict[str, str]:
        """
        Get system information to include with events.

        Returns:
            Dictionary containing Python version and OS information
        """
        return {
            "python_version": platform.python_version(),
            "os": platform.system(),
            "platform": platform.platform(),
        }

    def _build_payload(
        self, event_name: str, params: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """
        Build the event payload for the proxy server.

        Args:
            event_name: Name of the event to track
            params: Optional event parameters

        Returns:
            Complete payload dictionary ready to send
        """
        merged_params = params.copy() if params else {}
        merged_params.update(self._get_system_info())

        return {
            "client_id": self.client_id,
            "event_name": event_name,
            "params": merged_params,
        }

    def _send_request(self, payload: dict[str, Any]) -> bool:
        """
        Send the event payload to the proxy server with retry logic.

        Args:
            payload: Event payload to send

        Returns:
            True if the request was successful, False otherwise
        """
        url = f"{self.proxy_url}/track"

        for attempt in range(self.max_retries + 1):
            try:
                response = requests.post(url, json=payload, timeout=self.timeout)

                if response.status_code == 200:
                    _log.debug("Event sent successfully: %s", payload.get("event_name"))
                    return True

                _log.warning(
                    "Failed to send event (status %d): %s",
                    response.status_code,
                    payload.get("event_name"),
                )

                # Don't retry client errors (4xx)
                if 400 <= response.status_code < 500:
                    return False

            except requests.Timeout:
                _log.debug(
                    "Request timeout (attempt %d/%d): %s",
                    attempt + 1,
                    self.max_retries + 1,
                    url,
                )
            except requests.RequestException as e:
                _log.debug(
                    "Request failed (attempt %d/%d): %s - %s",
                    attempt + 1,
                    self.max_retries + 1,
                    url,
                    str(e),
                )
            except OSError as e:
                _log.debug(
                    "Network error (attempt %d/%d): %s",
                    attempt + 1,
                    self.max_retries + 1,
                    str(e),
                )

        return False

    def track_event(
        self, event_name: str, params: dict[str, Any] | None = None
    ) -> bool:
        """
        Track an analytics event.

        The event will be sent to the proxy server along with automatic system
        information. If telemetry is disabled, this method returns immediately
        without sending anything.

        Args:
            event_name: Name of the event to track (e.g., 'package_imported')
            params: Optional dictionary of event parameters

        Returns:
            True if the event was sent successfully, False if telemetry is disabled
            or the request failed

        Example:
            >>> client = AnalyticsClient(proxy_url="https://analytics.example.com")
            >>> client.track_event('user_action', {
            ...     'action': 'button_click',
            ...     'page': 'dashboard'
            ... })
            True
        """
        if not self.enabled:
            _log.debug("Telemetry disabled, skipping event: %s", event_name)
            return False

        payload = self._build_payload(event_name, params)

        _log.debug("Tracking event: %s with params: %s", event_name, params)

        return self._send_request(payload)

    def track_events_batch(
        self, events: list[tuple[str, dict[str, Any] | None]]
    ) -> dict[str, bool]:
        """
        Track multiple events in sequence.

        Note: Events are sent sequentially, not as a batch request. Each event
        is tracked independently.

        Args:
            events: List of (event_name, params) tuples

        Returns:
            Dictionary mapping event names to success status

        Example:
            >>> client = AnalyticsClient(proxy_url="https://analytics.example.com")
            >>> events = [
            ...     ('feature_a_used', {'count': 5}),
            ...     ('feature_b_used', {'count': 3}),
            ... ]
            >>> results = client.track_events_batch(events)
            >>> results
            {'feature_a_used': True, 'feature_b_used': True}
        """
        results: dict[str, bool] = {}

        for event_name, params in events:
            success = self.track_event(event_name, params)
            results[event_name] = success

        return results

    def __enter__(self) -> AnalyticsClient:
        """Context manager entry."""
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Context manager exit."""
        # Could add cleanup logic here if needed
