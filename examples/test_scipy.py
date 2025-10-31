# from opentelemetry.instrumentation.auto_instrumentation import initialize
from __future__ import annotations

from telemetric import install

# from telemetric.console import setup_console

install(["scipy.stats._correlation", "scipy.stats._distn_infrastructure"])
# initialize()
# setup_console()

from scipy import stats  # noqa: E402

stats.norm.pdf(x=1, loc=1, scale=0.01)
stats.norm(loc=1, scale=0.02).pdf(1)
stats.chatterjeexi([1, 2, 3, 4], [1.1, 2.2, 3.3, 4.4])

# X = stats.Normal()
# Y = stats.exp((X + 1)*0.01)
# from scipy import test
# test()

# How many calls (errors, and how often something was odd with the args)
print("counts: ", stats.norm.pdf._get_counts())

# Detailed statistics for each parameter.  How often was it passed
# and how often were "a" and 3 passed (or something equal to them,
# I do not consider types right now, although one could)?
print("param stats: ", stats.norm.pdf._get_param_stats())
