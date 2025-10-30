from __future__ import annotations

from collections.abc import Sequence
from functools import wraps

from opentelemetry import trace  # type: ignore[import-not-found]

ALLOWED_TYPES = [bool, str, bytes, int, float]

__all__ = ["span"]


def _get_func_name(func):  # type: ignore[no-untyped-def]
    return f"{func.__module__}.{func.__qualname__}"


def _serialize(arg):  # type: ignore[no-untyped-def]
    for _type in ALLOWED_TYPES:
        if isinstance(arg, _type):
            return arg
        if isinstance(arg, Sequence) and len(arg) > 0 and isinstance(arg[0], _type):
            return arg
    return str(arg)


def span(func):  # type: ignore[no-untyped-def]
    # Creates a tracer from the global tracer provider
    tracer = trace.get_tracer(__name__)
    func_name = _get_func_name(func)  # type: ignore[no-untyped-call]

    @wraps(func)
    def span_wrapper(*args, **kwargs):  # type: ignore[no-untyped-def]
        with tracer.start_as_current_span(func_name) as current_span:
            current_span.set_attribute("num_args", len(args))
            current_span.set_attribute("num_kwargs", len(kwargs))
            for n, arg in enumerate(args):
                current_span.set_attribute(f"args.{n}", _serialize(arg))  # type: ignore[no-untyped-call]
            for k, v in kwargs.items():
                current_span.set_attribute(f"kwargs.{k}", v)
            current_span.set_status(trace.StatusCode.OK)
            return func(*args, **kwargs)

    return span_wrapper
