"""Helper library for the NetAuto CLI tool.

Submodules load on first use so ``python netauto.py --demo`` does not import
Netmiko, PyYAML, or python-dotenv.
"""
from __future__ import annotations

from typing import Any

__all__ = [
    "config_loader",
    "connection",
    "demo",
    "logging_setup",
    "operations",
    "utils",
]


def __getattr__(name: str) -> Any:
    """Import a public submodule the first time it is accessed."""
    if name in __all__:
        import importlib

        module = importlib.import_module(f"{__name__}.{name}")
        globals()[name] = module
        return module
    raise AttributeError(f"module {__name__!r} has no attribute {name}")
