"""Tests for service-catalog uniqueness and deployment-unit integrity."""

from __future__ import annotations

import importlib.util
import json
import shutil
import sys
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
CATALOG_PATH = Path("services/catalog/catalog.yml")
SCHEMA_PATH = Path("services/catalog/catalog.schema.json")
VALIDATOR_PATH = REPO_ROOT / "tools/validate-catalog.py"


def _load_validator() -> ModuleType:
    """Import the hyphenated validation script as a test module."""
    spec = importlib.util.spec_from_file_location("validate_catalog", VALIDATOR_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def validator() -> ModuleType:
    """Return the catalog validator module."""
    return _load_validator()


@pytest.fixture
def repository(tmp_path: Path) -> Path:
    """Copy the catalog inputs and create an empty Quadlet directory."""
    for relative in (CATALOG_PATH, SCHEMA_PATH):
        destination = tmp_path / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(REPO_ROOT / relative, destination)
    (tmp_path / "mission" / "examples").mkdir(parents=True)
    (tmp_path / "services" / "quadlets").mkdir(parents=True)
    return tmp_path


def _catalog(repository: Path) -> dict[str, Any]:
    """Load the disposable catalog."""
    document = yaml.safe_load((repository / CATALOG_PATH).read_text(encoding="utf-8"))
    assert isinstance(document, dict)
    return document


def _write_catalog(repository: Path, document: dict[str, Any]) -> None:
    """Write one mutated catalog fixture."""
    (repository / CATALOG_PATH).write_text(
        yaml.safe_dump(document, sort_keys=False), encoding="utf-8"
    )


def _enable(entry: dict[str, Any]) -> None:
    """Make a copied catalog record deployable in a disposable fixture."""
    entry["enabled"] = True
    entry["unit"] = f"{entry['name']}.container"


def _write_mission(repository: Path, services: list[str]) -> None:
    """Write the subset of a valid mission document used by this validator."""
    path = repository / "mission" / "examples" / "valid-catalog.json"
    path.write_text(json.dumps({"services": services}), encoding="utf-8")


def test_repository_catalog_is_valid(validator: ModuleType) -> None:
    """The committed catalog satisfies its schema and unit-integrity rules."""
    assert validator.validate_repository(REPO_ROOT) == []


def test_duplicate_service_names_are_rejected(
    repository: Path, validator: ModuleType
) -> None:
    """Unique YAML objects may not hide a duplicated canonical service name."""
    document = _catalog(repository)
    duplicate = dict(document["services"][0])
    duplicate["purpose"] = "A different record with the same identity."
    document["services"].append(duplicate)
    _write_catalog(repository, document)

    assert any(
        "duplicate catalog service name 'opentakserver'" in error
        for error in validator.validate_repository(repository)
    )


def test_ambiguous_alias_is_rejected(repository: Path, validator: ModuleType) -> None:
    """An alias cannot name two records or collide with another canonical name."""
    document = _catalog(repository)
    document["services"][0]["aliases"] = ["maps"]
    document["services"][1]["aliases"] = ["maps"]
    _write_catalog(repository, document)

    assert any(
        "service reference 'maps' is ambiguous" in error
        for error in validator.validate_repository(repository)
    )


def test_disabled_service_cannot_be_enabled_by_mission(
    repository: Path, validator: ModuleType
) -> None:
    """A retained contract is not a deployable service until explicitly enabled."""
    _write_mission(repository, ["martin"])

    assert any(
        "enables disabled service 'martin'" in error
        for error in validator.validate_repository(repository)
    )


def test_enabled_service_requires_existing_named_quadlet(
    repository: Path, validator: ModuleType
) -> None:
    """An enabled entry cannot point at a missing or differently named unit."""
    document = _catalog(repository)
    _enable(document["services"][1])
    _write_catalog(repository, document)
    _write_mission(repository, ["martin"])

    assert any(
        "enabled service 'martin' deployment unit is absent" in error
        for error in validator.validate_repository(repository)
    )


def test_unregistered_loadable_quadlet_is_rejected(
    repository: Path, validator: ModuleType
) -> None:
    """A loadable unit cannot bypass the catalog by merely appearing on disk."""
    (repository / "services" / "quadlets" / "rogue.container").touch()

    assert any(
        "loadable Quadlet 'rogue.container' has no enabled catalog record" in error
        for error in validator.validate_repository(repository)
    )


def test_enabled_alias_resolves_uniquely(
    repository: Path, validator: ModuleType
) -> None:
    """One alias may resolve to one enabled record with its real unit present."""
    document = _catalog(repository)
    martin = document["services"][1]
    _enable(martin)
    martin["aliases"] = ["maps"]
    _write_catalog(repository, document)
    (repository / "services" / "quadlets" / "martin.container").touch()
    _write_mission(repository, ["maps"])

    assert validator.validate_repository(repository) == []
