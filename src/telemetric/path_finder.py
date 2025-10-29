from __future__ import annotations

import inspect
import sys
from importlib.abc import MetaPathFinder
from importlib.machinery import SourceFileLoader
from importlib.util import spec_from_loader

from telemetric.statswrapper import stats_deco_auto

__all__ = ["install"]


class TelemetryMetaFinder(MetaPathFinder):
    def __init__(self, module_names, *args, **kwargs):
        """MetaPathFinder implementation that overrides a spec loader
        of type SourceFileLoader with a TelemetrySpanLoader.

        Args:
            module_names (List[str]): Module names to include.
        """
        self._module_names = module_names
        super().__init__(*args, **kwargs)

    def find_spec(self, fullname, path, target=None):
        if any(name in fullname for name in self._module_names):
            for finder in sys.meta_path:
                if finder != self:
                    spec = finder.find_spec(fullname, path, target)
                    if spec is not None:
                        if isinstance(spec.loader, SourceFileLoader):
                            return spec_from_loader(
                                name=spec.name,
                                loader=TelemetrySpanSourceFileLoader(spec.name, spec.origin),
                                origin=spec.origin,
                            )
                        return spec

        return None


class TelemetrySpanSourceFileLoader(SourceFileLoader):
    def exec_module(self, module):
        super().exec_module(module)
        functions = inspect.getmembers(module, predicate=inspect.isfunction)
        classes = inspect.getmembers(module, predicate=inspect.isclass)

        # Add telemetry to functions
        for name, _function in functions:
            _module = inspect.getmodule(_function)
            if module == _module:
                setattr(_module, name, stats_deco_auto(_function))

        # Add telemetry to methods
        for _, _class in classes:
            for name, method in inspect.getmembers(_class, predicate=inspect.isfunction):
                if inspect.getmodule(_class) == module and not name.startswith("_"):
                        setattr(_class, name, stats_deco_auto(method))


def install(module_names: list[str]):
    """Inserts the finder into the import machinery"""
    sys.meta_path.insert(0, TelemetryMetaFinder(module_names))
