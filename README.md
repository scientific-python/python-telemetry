# API Tracer

This library adds basic telemetry to Python projects that traces the usage and run time of Python functions within a given scope.

## Installation

Prerequisites:

```
pip install opentelemetry-distro
pip install opentelemetry-exporter-otlp
opentelemetry-bootstrap --action=install
```

## Usage

To track usage of one or more existing Python projects, run:

```python
from api_tracer import install, start_span_processor

install(
  [
    my_project.my_module
  ]
)
start_span_processor('my-project-service')
```

To explicitly add instrumentation to functions you want to trace, use the `span` decorator:

```python
from api_tracer import span, start_span_processor


@span
def foo(bar):
    print(bar)

if __name__ == "__main__":
    start_span_processor("test-service")
    foo(bar="baz")
```

## Start collector

To start a collector that prints each log message to stdout, run `cd tests/collector` and run

```bash
docker run -p 4317:4317 -p 4318:4318 --rm -v $(pwd)/collector-config.yaml:/etc/otelcol/config.yaml otel/opentelemetry-collector
```

To start a Jaeger collector that starts a basic dashboard, run:

```bash
docker run --name jaeger \
  -e COLLECTOR_OTLP_ENABLED=true \
  -p 16686:16686 \
  -p 4317:4317 \
  -p 4318:4318 \
  jaegertracing/all-in-one:1.35
```
