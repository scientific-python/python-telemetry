from __future__ import annotations

import importlib.metadata

import api_tracer as m


def test_version():
    assert importlib.metadata.version("api_tracer") == m.__version__
