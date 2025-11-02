# Copyright (c) 2025 Scientific Python. All rights reserved.
# pylint: disable=import-error,no-name-in-module
from __future__ import annotations

import functools
import inspect
import sys

from ._stats_wrapper import (  # type: ignore[import-not-found]
    _StatsWrapper,
    stats_wrapper,
)

# Keep a list of all wrapped functions (could be per package or so...)
_wrapped: list[_StatsWrapper] = []


def print_all_stats(skip_uncalled: bool = True) -> None:  # noqa: ARG001  # pylint: disable=unused-argument
    print()  # noqa: T201
    print("Statistics for argument usage of wrapped functions")  # noqa: T201
    print("--------------------------------------------------")  # noqa: T201
    sorted_w = sorted(_wrapped, key=lambda x: x._get_counts()[0], reverse=True)  # pylint: disable=protected-access
    for func in sorted_w:
        counts = func._get_counts()  # pylint: disable=protected-access
        if counts[0] == 0:
            continue
        counts = f"{counts[0]},{counts[1]},{counts[2]}"
        stats = func._get_param_stats()  # pylint: disable=protected-access
        argcounts = []
        for name, n_uses, _, _ in stats:
            if name is None:
                argcounts.append(str(n_uses))
            else:
                argcounts.append(f"{name}={n_uses}")

        argcounts_str = ", ".join(argcounts)
        print(f"{func.__module__}.{func.__name__}[{counts}]({argcounts_str})")  # noqa: T201


def stats_deco(*args, **kwargs):  # type: ignore[no-untyped-def]
    """
    Decorate for statistic gathering.  There should be auto mode!

    The usage of this decorator is that you have to describe what to keep
    track of (this doesn't work for *args, **kwargs functions).

    For example::

        @stats_deco(a=None, b=(True, False), c=("default",))
        def func(a, b=False, c="default")
            pass

    Would track how often ``a``, ``b``, and ``c`` were passed. You must pass
    ``None`` or a tuple (and give the name) to track if a parameter was passed.
    The ``(True, False)`` will track how often ``True`` or ``False`` were
    passed, if a user passes something that is not listed in the tuple we
    will still add this call to the total number ``b`` was passed.

    If you wish to distinguish a user passing an argument positionally or
    by keyword argument, duplicate it as in::

        @stats_deco(None, ("a", "b"), pos1=None, pos2=("a", "b"))

    This tracker is meant for a non-large amount of keyword arguments in which
    case it is extremely light-weight.  For a large of keyword arguments
    the performance may deteriorate.

    Parameters
    ----------
    *args : None or tuple
    **kwargs : None or tuple

    Methods
    -------
    _get_counts : tuple of int
        Returns the counts:
        * total function calls
        * number of calls which errored (i.e. wrapped function errored)
        * A counter for invalid args (indicative of some wrapping issues)

    _get_param_stats : tuple of tuples
        Returns a tuple with one entry for each arg and kwarg described above.
        The tuple contains the following:
        * The keyword argument name or None (positional only).
        * The number of times this argument was passed.
        * The parameters we are keeping track of explicitly (or None)
        * The number of times the corresponding parameter was used (or None)
    """

    def deco(func):  # type: ignore[no-untyped-def]
        new_func = stats_wrapper(func, *args, **kwargs)
        functools.update_wrapper(new_func, func)
        _wrapped.append(new_func)
        if hasattr(func, "__code__"):
            new_func.__code__ = func.__code__
        return new_func

    return deco


def stats_deco_auto(func, /, *, track_positional_use: bool = False):  # type: ignore[no-untyped-def]
    """Similar to `stats_deco`, but attempts to use inspect to add
    any arguments and keyword arguments automatically.

    Will keep track of the default value being passed if a parameter has one.

    Parameters
    ----------
    track_positional_use : bool
        If set to ``True`` arguments that are both positional or keyword
        are also tracked as positional only.  That way it is possible to
        find out how if users used the param positionally or by keyword.
    """
    if isinstance(func, _StatsWrapper):
        # Already wrapped, assume the same options were used.
        return func

    try:
        s = inspect.signature(func)
    except ValueError:
        return func

    args: list[tuple[str, ...] | None] = []
    kwargs: dict[str, tuple[str, ...] | None] = {}
    positional_kws = 0
    for param in s.parameters.values():
        # Tracked the default parameter initially, but that doesn't really
        # work reasonably.  If a project had type annotations indicating
        # certain literal values, that might work.
        values = None

        if param.kind == inspect.Parameter.POSITIONAL_ONLY:
            args.append(values)
        elif param.kind == inspect.Parameter.POSITIONAL_OR_KEYWORD:
            if track_positional_use:
                args.append(values)
            else:
                positional_kws += 1
            kwargs[param.name] = values
        elif param.kind == inspect.Parameter.KEYWORD_ONLY:
            # TODO: keyword-only isn't enforced right now.  Mostly fine, but
            #       `*args` would confuse it.
            kwargs[param.name] = values
        else:
            # We simply ignore *args, **kwargs style parameters.  They will
            # end up as "invalid" counts (without an error) if used.
            pass

    new = stats_wrapper(func, *args, **kwargs)
    new._set_npos(len(args) + positional_kws)  # pylint: disable=protected-access

    functools.update_wrapper(new, func)
    if hasattr(func, "__code__"):
        new.__code__ = func.__code__

    _wrapped.append(new)
    return new


def install_in_module_by_name(
    name: str, /, *, track_positional_use: bool = False
) -> None:
    """
    Quick way to wrap module functions via
    `install_in_module_by_name(__name__)`.
    """
    module = sys.modules[name]

    for _name, obj in module.__dict__.items():
        if _name.startswith("_"):
            continue
        if inspect.isroutine(obj):
            wrapper = stats_deco_auto(obj, track_positional_use=track_positional_use)
            setattr(module, _name, wrapper)
