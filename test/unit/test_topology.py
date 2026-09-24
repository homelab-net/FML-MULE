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


def test_software_path_starts_at_the_repository_root() -> None:
    root = Path(__file__).resolve().parents[2]
    script = (root / "test/topology/cases/tak/integrate.sh").read_text()
    assert '"$here/../../../.."' in script
    assert "exec sudo sh" in script
    assert "--user 0" in script
    assert "services/tak/Containerfile" in script


def test_quadlet_check_reads_generated_service_names() -> None:
    root = Path(__file__).resolve().parents[2]
    script = (root / "test/topology/quadlet-dry-run.sh").read_text()
    assert "QUADLET_UNIT_DIRS" in script
    assert "ots-network.service" in script
    assert "grep -q 'ots.network'" not in script
