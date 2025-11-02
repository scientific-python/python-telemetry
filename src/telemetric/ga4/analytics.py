"""Python package analytics client"""

from __future__ import annotations

import logging
import os
import platform
import uuid

import requests  # type: ignore[import-untyped]

_log = logging.getLogger()


class AnalyticsClient:
    """
    Example usage:
    analytics = AnalyticsClient(
        proxy_url="https://your-project.up.railway.app"
    )

    analytics.track_event('package_imported', {
        'package_version': '1.0.0'
    })
    """

    def __init__(self, proxy_url: str) -> None:
        self.proxy_url = proxy_url
        self.client_id = str(uuid.uuid4())
        self.enabled = not self._is_disabled()

    def _is_disabled(self) -> bool:
        return os.environ.get("DO_NOT_TRACK", "").lower() in (
            "1",
            "true",
        ) or os.environ.get("CI", "").lower() in ("1", "true")

    def track_event(
        self, event_name: str, params: dict[str, str] | None = None
    ) -> None:
        if not self.enabled:
            return

        if params is None:
            params = {}

        params.update(
            {
                "python_version": platform.python_version(),
                "os": platform.system(),
            }
        )

        payload = {
            "client_id": self.client_id,
            "event_name": event_name,
            "params": params,
        }

        url = f"{self.proxy_url}/track"
        _log.debug("POST request to: %s", url)
        _log.debug(payload)

        try:  # noqa: SIM105
            requests.post(f"{self.proxy_url}/track", json=payload, timeout=2)
        except (requests.RequestException, OSError):
            pass
