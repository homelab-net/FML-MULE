"""The static topology check, including the mutations that must fail."""

from __future__ import annotations

import importlib.util
from pathlib import Path
from types import ModuleType


def _load() -> ModuleType:
    path = Path(__file__).resolve().parents[2] / "test" / "topology" / "validate.py"
    spec = importlib.util.spec_from_file_location("topology_validate", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_tak_topology_holds_and_mutations_fail() -> None:
    validator = _load()
    assert validator.main() == 0
