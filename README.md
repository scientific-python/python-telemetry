# Telemetric

[![Actions Status][actions-badge]][actions-link]
[![Documentation Status][rtd-badge]][rtd-link]

[![PyPI version][pypi-version]][pypi-link]
[![Conda-Forge][conda-badge]][conda-link]
[![PyPI platforms][pypi-platforms]][pypi-link]

[![GitHub Discussion][github-discussions-badge]][github-discussions-link]

<!-- SPHINX-START -->

<!-- prettier-ignore-start -->
[actions-badge]:            https://github.com/scientific-python/telemetric/workflows/CI/badge.svg
[actions-link]:             https://github.com/scientific-python/telemetric/actions
[conda-badge]:              https://img.shields.io/conda/vn/conda-forge/telemetric
[conda-link]:               https://github.com/conda-forge/telemetric-feedstock
[github-discussions-badge]: https://img.shields.io/static/v1?label=Discussions&message=Ask&color=blue&logo=github
[github-discussions-link]:  https://github.com/scientific-python/telemetric/discussions
[pypi-link]:                https://pypi.org/project/telemetric/
[pypi-platforms]:           https://img.shields.io/pypi/pyversions/telemetric
[pypi-version]:             https://img.shields.io/pypi/v/telemetric
[rtd-badge]:                https://readthedocs.org/projects/telemetric/badge/?version=latest
[rtd-link]:                 https://telemetric.readthedocs.io/en/latest/?badge=latest

<!-- prettier-ignore-end -->

This library adds basic telemetry to Python projects that traces the usage and
run time of Python functions within a given scope.

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
from opentelemetry.instrumentation.auto_instrumentation import initialize
from telemetric import install

install([my_project.my_module])
initialize()
start_span_processor("my-project-service")
```

To explicitly add instrumentation to functions you want to trace, use the `span`
decorator:

```python
from telemetric import span, start_span_processor


@span
def foo(bar):
    print(bar)


if __name__ == "__main__":
    start_span_processor("test-service")
    foo(bar="baz")
```

## Start collector

To start a collector that prints each log message to stdout, run
`cd tests/collector` and run

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
