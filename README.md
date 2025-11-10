# Telemetric

[![Actions Status][actions-badge]][actions-link]
[![PyPI version][pypi-version]][pypi-link]

<div align="left">
     <picture>
          <source media="(prefers-color-scheme: dark)" srcset="https://i.imgur.com/lTSgUcA.png" width=100>
          <source media="(prefers-color-scheme: light)" srcset="https://i.imgur.com/tPK9g5Y.png" width=100>
          <img alt="Telemetric" src=".github/images/logo.png">
     </picture>
</div>

<!-- SPHINX-START -->

<!-- prettier-ignore-start -->
[actions-badge]:            https://github.com/scientific-python/telemetric/workflows/CI/badge.svg
[actions-link]:             https://github.com/scientific-python/telemetric/actions
[pypi-link]:                https://pypi.org/project/telemetric/
[pypi-version]:             https://img.shields.io/pypi/v/telemetric

<!-- prettier-ignore-end -->

This library provides lightweight telemetry for Python projects, collecting
statistics on function parameter usage to understand how APIs are being used.

## Installation

```bash
pip install telemetric
```

## Usage

### Automatic Function Wrapping

To automatically track parameter usage statistics for existing Python packages,
use the `install()` function before importing the target modules:

```python
from telemetric import install

# Install telemetry for specific modules
install(["scipy.stats._correlation", "scipy.stats._distn_infrastructure"])

from scipy import stats

# Use functions normally
stats.norm.pdf(x=1, loc=1, scale=0.01)
stats.norm(loc=1, scale=0.02).pdf(1)

# Retrieve statistics for wrapped functions
print("Call counts:", stats.norm.pdf._get_counts())
print("Parameter stats:", stats.norm.pdf._get_param_stats())
print("Timing stats:", stats.norm.pdf._get_timing())
```

The `_get_counts()` method returns a tuple of:

- Total function calls
- Number of calls that raised errors
- Number of calls with invalid arguments (wrapping issues)

The `_get_param_stats()` method returns detailed statistics for each parameter:

- Parameter name (or None for positional-only)
- Number of times the parameter was passed
- Tracked parameter values (if specified)
- Counts for each tracked value (if specified)

The `_get_timing()` method returns a dictionary with timing statistics:

- `'total'`: Total time spent in all calls (seconds)
- `'average'`: Average time per call (seconds)
- `'min'`: Minimum time for a single call (seconds)
- `'max'`: Maximum time for a single call (seconds)

Timing measurements use `time.perf_counter()` for high-resolution timing with
nanosecond-level accuracy on most platforms.

### Manual Function Decoration

For more control, use the `stats_deco_auto` decorator to automatically track all
parameters:

```python
from telemetric import stats_deco_auto


@stats_deco_auto
def my_function(x, y=10, z="default"):
    return x + y


my_function(5)
my_function(5, y=20)
my_function(5, 20, "custom")

print(my_function._get_counts())
print(my_function._get_param_stats())
print(my_function._get_timing())
```

For fine-grained control over which parameter values to track, use `stats_deco`:

```python
from telemetric import stats_deco


@stats_deco(x=None, y=(10, 20, 30), z=("default", "custom"))
def my_function(x, y=10, z="default"):
    return x + y


# The decorator will track:
# - Whether x was passed (any value)
# - How often y was 10, 20, or 30 (and count other values separately)
# - How often z was "default" or "custom" (and count other values separately)
```

### Printing All Statistics

To print a summary of all wrapped functions and their statistics:

```python
from telemetric.statswrapper import print_all_stats

# After your code has run
print_all_stats()

# Control timing precision with scientific notation (default: 6 digits)
print_all_stats(timing_digits=3)  # Display timing with 3 decimal places

# Or disable rounding for full precision
print_all_stats(timing_digits=None)
```

The output includes call counts, parameter usage, and timing statistics in
scientific notation for each wrapped function.

### OpenTelemetry Integration (Legacy)

The library also supports OpenTelemetry-based tracing for distributed systems:

```python
from telemetric import span, start_span_processor


@span
def foo(bar):
    print(bar)


if __name__ == "__main__":
    start_span_processor("test-service")
    foo(bar="baz")
```

## OpenTelemetry Collector Setup (Legacy)

If using the OpenTelemetry integration, you can set up collectors for trace
data:

To start a collector that prints each log message to stdout:

```bash
cd tests/collector
docker run -p 4317:4317 -p 4318:4318 --rm \
  -v $(pwd)/collector-config.yaml:/etc/otelcol/config.yaml \
  otel/opentelemetry-collector
```

To start a Jaeger collector with a dashboard UI:

```bash
docker run --name jaeger \
  -e COLLECTOR_OTLP_ENABLED=true \
  -p 16686:16686 \
  -p 4317:4317 \
  -p 4318:4318 \
  jaegertracing/all-in-one:1.35
```

Access the Jaeger UI at <http://localhost:16686>
