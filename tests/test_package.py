from __future__ import annotations

import importlib.metadata

import telemetric as m


def test_version():
    assert importlib.metadata.version("telemetric") == m.__version__
