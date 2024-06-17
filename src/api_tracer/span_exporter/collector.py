import os
import os.path

from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

__all__ = ["start_span_processor"]


def start_span_processor(service_name: str):
    resource = Resource(attributes={
        "service.name": service_name
    })
    trace.set_tracer_provider(TracerProvider(resource=resource))

    agent_host_name = os.environ.get("OTEL_COLLECTOR_HOST", "localhost")
    agent_port = os.environ.get("OTEL_COLLECTOR_PORT", 4317)
    endpoint = f"http://{agent_host_name}:{agent_port}"

    otlp_exporter = OTLPSpanExporter(endpoint=endpoint, insecure=True)

    trace.get_tracer_provider().add_span_processor(
        BatchSpanProcessor(otlp_exporter)
    )
