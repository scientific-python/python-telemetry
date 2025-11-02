"""
Google Analytics proxy server
"""

from __future__ import annotations

import os

import requests  # type: ignore[import-untyped]
from fastapi import FastAPI, Request  # type: ignore[import-not-found]
from fastapi.middleware.cors import CORSMiddleware  # type: ignore[import-not-found]
from fastapi.responses import JSONResponse  # type: ignore[import-not-found]

app = FastAPI()

# Allow requests from anywhere (your Python package)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["POST"],
    allow_headers=["*"],
)

# Get credentials from environment variables
GA4_MEASUREMENT_ID = os.environ.get("GA4_MEASUREMENT_ID")
GA4_API_SECRET = os.environ.get("GA4_API_SECRET")


@app.get("/debug")
async def debug():  # type: ignore[no-untyped-def]
    """Debug endpoint to check if env vars are loaded"""
    return {
        "GA4_MEASUREMENT_ID_set": bool(GA4_MEASUREMENT_ID),
        "GA4_API_SECRET_set": bool(GA4_API_SECRET),
        "GA4_MEASUREMENT_ID_value": GA4_MEASUREMENT_ID[:5] + "..."
        if GA4_MEASUREMENT_ID
        else None,
    }


@app.get("/")
async def root():  # type: ignore[no-untyped-def]
    """Health check endpoint"""
    return {"status": "ok", "service": "GA4 Analytics Proxy"}


@app.post("/track")  # type: ignore[misc]
async def track_event(request: Request):  # type: ignore[no-untyped-def]
    """
    Proxy endpoint that forwards events to GA4

    Expected payload:
    {
        "client_id": "unique-user-id",
        "event_name": "event_name",
        "params": {
            "param1": "value1",
            "param2": "value2"
        }
    }
    """
    try:
        data = await request.json()

        # Validate required fields
        event_name = data.get("event_name")
        params = data.get("params", {})
        client_id = data.get("client_id")

        if not event_name or not client_id:
            return JSONResponse(
                {"status": "error", "message": "Missing event_name or client_id"},
                status_code=400,
            )

        # Check if credentials are configured
        if not GA4_MEASUREMENT_ID or not GA4_API_SECRET:
            return JSONResponse(
                {"status": "error", "message": "Server not configured"}, status_code=500
            )

        # Build GA4 payload
        ga4_payload = {
            "client_id": client_id,
            "events": [{"name": event_name, "params": params}],
        }

        # Forward to GA4
        response = requests.post(
            f"https://www.google-analytics.com/mp/collect?measurement_id={GA4_MEASUREMENT_ID}&api_secret={GA4_API_SECRET}",
            json=ga4_payload,
            timeout=5,
        )

        if response.status_code == 204:
            return JSONResponse({"status": "success"})
        return JSONResponse(
            {"status": "error", "message": "GA4 request failed"}, status_code=502
        )

    except Exception as e:
        return JSONResponse({"status": "error", "message": str(e)}, status_code=500)


if __name__ == "__main__":
    import uvicorn  # type: ignore[import-not-found]

    port = int(os.environ.get("PORT", "8000"))
    uvicorn.run(app, host="0.0.0.0", port=port)
