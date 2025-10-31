from __future__ import annotations

from opentelemetry.instrumentation.auto_instrumentation import initialize

from telemetric import install
from telemetric.console import setup_console

install(["scipy.stats._correlation", "scipy.stats._distn_infrastructure"])
initialize()
setup_console()
