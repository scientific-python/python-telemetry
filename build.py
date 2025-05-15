from __future__ import annotations

from hatchling.builders.hooks.plugin.interface import BuildHookInterface
from setuptools import Extension
from setuptools.command.build_ext import build_ext


class CustomBuildHook(BuildHookInterface):
    def initialize(self, version, build_data):
        build_data['ext_modules'] = [
            Extension(
                "api_tracer._stats_wrapper",
                ["src/api_tracer/_stats_wrapper.c"],
            ),
        ]
        build_data['cmdclass'] = {"build_ext": build_ext} 
