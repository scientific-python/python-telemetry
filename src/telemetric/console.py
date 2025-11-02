from __future__ import annotations

import os

from opentelemetry import trace  # type: ignore[import-not-found]
from opentelemetry.sdk.resources import Resource  # type: ignore[import-not-found]
from opentelemetry.sdk.trace import TracerProvider  # type: ignore[import-not-found]
from opentelemetry.sdk.trace.export import (  # type: ignore[import-not-found]
    BatchSpanProcessor,
    ConsoleSpanExporter,
)

__all__ = ["setup_console"]


def setup_console(service_name: str | None = None) -> None:
    if service_name is None:
        attributes_str = os.environ.get("OTEL_RESOURCE_ATTRIBUTES")
        if attributes_str:
            attributes = dict(k.split("=") for k in attributes_str.split(","))
        else:
            attributes = {}
    else:
        attributes = {"service.name": service_name}

    resource = Resource(attributes=attributes)
    trace.set_tracer_provider(TracerProvider(resource=resource))
    console_exporter = ConsoleSpanExporter()

    trace.get_tracer_provider().add_span_processor(BatchSpanProcessor(console_exporter))
