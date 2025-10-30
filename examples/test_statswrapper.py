from __future__ import annotations

import time

from telemetric.statswrapper import print_all_stats, stats_deco


@stats_deco(None, b=("a", 3), c=None)
def test_func(a, b=None, c=None):
    time.sleep(a)
    return a, b, c


# Do things with test_func
test_func(1, 3)
test_func(2, 3)

# How many calls (errors, and how often something was odd with the args)
print("counts: ", test_func._get_counts())  # noqa: T201

# Detailed statistics for each parameter.  How often was it passed
# and how often were "a" and 3 passed (or something equal to them,
# I do not consider types right now, although one could)?
print("param stats: ", test_func._get_param_stats())  # noqa: T201

# Timing statistics for the function
print("timing: ", test_func._get_timing())  # noqa: T201

print_all_stats(timing_digits=3)
