"""
Copyright (c) 2025 Scientific Python. All rights reserved.

telemetric: API tracer to gather usage telemetry for Python libraries
"""

from __future__ import annotations

from telemetric.path_finder import install
from telemetric.span import span
from telemetric.statswrapper import stats_deco, stats_deco_auto

from ._version import version as __version__

__all__ = [
    "__version__",
    "install",
    "span",
    "stats_deco",
    "stats_deco_auto",
]
