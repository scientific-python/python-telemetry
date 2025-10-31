from __future__ import annotations

import os

from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter

__all__ = ["setup_console"]


def setup_console(service_name: str | None = None):
    if service_name is None:
        attributes = os.environ.get("OTEL_RESOURCE_ATTRIBUTES")
        attributes = dict(k.split("=") for k in attributes.split(","))
    else:
        attributes = {"service.name": service_name}

    resource = Resource(attributes=attributes)
    trace.set_tracer_provider(TracerProvider(resource=resource))
    console_exporter = ConsoleSpanExporter()

    trace.get_tracer_provider().add_span_processor(BatchSpanProcessor(console_exporter))
