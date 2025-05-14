from opentelemetry.instrumentation.auto_instrumentation import initialize

from api_tracer import install
from api_tracer.console import setup_console

install(["scipy.stats._correlation", "scipy.stats._distn_infrastructure"])
initialize()
setup_console()
