from collections.abc import Sequence
from contextlib import wraps

from opentelemetry import trace

ALLOWED_TYPES = [bool, str, bytes, int, float]

__all__ = ["span"]


def _get_func_name(func):
    return f"{func.__module__}.{func.__qualname__}"


def _serialize(arg):
    for _type in ALLOWED_TYPES:
        if isinstance(arg, _type):
            return arg
        if isinstance(arg, Sequence) and len(arg) > 0:
            if isinstance(arg[0], _type):
                return arg
    return str(arg)


def span(func):
    # Creates a tracer from the global tracer provider
    tracer = trace.get_tracer(__name__)
    func_name = _get_func_name(func)
    
    @wraps(func)
    def span_wrapper(*args, **kwargs):
        with tracer.start_as_current_span(func_name) as span:
            span.set_attribute("num_args", len(args))
            span.set_attribute("num_kwargs", len(kwargs))
            print(args)
            print(kwargs)
            for n, arg in enumerate(args):
                span.set_attribute(f"args.{n}", _serialize(arg))
            for k, v in kwargs.items():
                span.set_attribute(f"kwargs.{k}", v)
            return func(*args, **kwargs)

    return span_wrapper
