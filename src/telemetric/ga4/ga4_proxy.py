"""
Google Analytics 4 proxy server for forwarding telemetry events
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any

import requests  # type: ignore[import-untyped]
from fastapi import FastAPI, Request, status  # type: ignore[import-not-found]
from fastapi.middleware.cors import CORSMiddleware  # type: ignore[import-not-found]
from fastapi.responses import JSONResponse  # type: ignore[import-not-found]


@dataclass
class GA4Config:
    """Configuration for GA4 Analytics"""

    measurement_id: str | None
    api_secret: str | None

    @classmethod
    def from_environment(cls) -> GA4Config:
        """Load configuration from environment variables"""
        return cls(
            measurement_id=os.environ.get("GA4_MEASUREMENT_ID"),
            api_secret=os.environ.get("GA4_API_SECRET"),
        )

    def is_configured(self) -> bool:
        """Check if all required credentials are present"""
        return bool(self.measurement_id and self.api_secret)

    def get_endpoint_url(self) -> str:
        """Construct the GA4 measurement protocol URL"""
        return (
            f"https://www.google-analytics.com/mp/collect"
            f"?measurement_id={self.measurement_id}&api_secret={self.api_secret}"
        )


def create_app() -> FastAPI:
    """Create and configure the FastAPI application"""
    application = FastAPI(title="GA4 Analytics Proxy")

    application.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["POST"],
        allow_headers=["*"],
    )

    return application


app = create_app()
config = GA4Config.from_environment()


def validate_event_payload(payload: dict[str, Any]) -> tuple[bool, str | None]:
    """
    Validate the incoming event payload

    Returns:
        Tuple of (is_valid, error_message)
    """
    if "event_name" not in payload or not payload["event_name"]:
        return False, "Missing or empty event_name"

    if "client_id" not in payload or not payload["client_id"]:
        return False, "Missing or empty client_id"

    return True, None


def build_ga4_payload(
    client_id: str, event_name: str, params: dict[str, Any]
) -> dict[str, Any]:
    """Construct the GA4 Measurement Protocol payload"""
    return {"client_id": client_id, "events": [{"name": event_name, "params": params}]}


def send_to_ga4(payload: dict[str, Any], endpoint_url: str) -> bool:
    """
    Send event data to Google Analytics 4

    Returns:
        True if successful, False otherwise
    """
    try:
        response = requests.post(endpoint_url, json=payload, timeout=5)
        return bool(response.status_code == 204)
    except requests.RequestException:
        return False


@app.get("/")  # type: ignore[misc]
async def health_check() -> dict[str, str]:
    """Health check endpoint"""
    return {"status": "ok", "service": "GA4 Analytics Proxy"}


@app.get("/debug")  # type: ignore[misc]
async def debug_info() -> dict[str, Any]:
    """Debug endpoint to verify configuration status"""
    measurement_id_preview = (
        f"{config.measurement_id[:5]}..." if config.measurement_id else None
    )

    return {
        "measurement_id_configured": bool(config.measurement_id),
        "api_secret_configured": bool(config.api_secret),
        "measurement_id_preview": measurement_id_preview,
    }


@app.post("/track")  # type: ignore[misc]
async def forward_event(request: Request) -> JSONResponse:
    """
    Receive and forward analytics events to GA4

    Expected request body:
    {
        "client_id": "unique-user-identifier",
        "event_name": "name_of_event",
        "params": {
            "custom_param": "value"
        }
    }
    """
    try:
        payload = await request.json()
    except ValueError:
        return JSONResponse(
            {"status": "error", "message": "Invalid JSON payload"},
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    # Validate the request payload
    is_valid, error_msg = validate_event_payload(payload)
    if not is_valid:
        return JSONResponse(
            {"status": "error", "message": error_msg},
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    # Ensure server is properly configured
    if not config.is_configured():
        return JSONResponse(
            {"status": "error", "message": "Server credentials not configured"},
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    # Extract event data
    client_id = payload["client_id"]
    event_name = payload["event_name"]
    params = payload.get("params", {})

    # Build and send the payload to GA4
    ga4_payload = build_ga4_payload(client_id, event_name, params)
    success = send_to_ga4(ga4_payload, config.get_endpoint_url())

    if success:
        return JSONResponse({"status": "success"}, status_code=status.HTTP_200_OK)

    return JSONResponse(
        {"status": "error", "message": "Failed to forward event to GA4"},
        status_code=status.HTTP_502_BAD_GATEWAY,
    )


if __name__ == "__main__":
    import uvicorn  # type: ignore[import-not-found]

    server_port = int(os.environ.get("PORT", "8000"))
    uvicorn.run(app, host="0.0.0.0", port=server_port)
