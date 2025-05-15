"""
Copyright (c) 2025 Scientific Python. All rights reserved.

api-tracer: API tracer to gather usage telemetry for Python libraries
"""

from __future__ import annotations

from api_tracer.path_finder import install
from api_tracer.span import span
from api_tracer.statswrapper import stats_deco, stats_deco_auto

from ._version import version as __version__

__all__ = [
    "__version__",
    "install",
    "span",
    "stats_deco",
    "stats_deco_auto",
]
