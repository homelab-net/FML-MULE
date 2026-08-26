"""Tests for the mission configuration package validator.

The mission package schema is validated against both valid and deliberately
invalid example packages. Invalid examples matter as much as valid ones: a
schema that accepts everything passes every valid example and catches nothing.

These tests assert the expectation encoded in each example's filename, so that
a rule which stops catching its counter-example shows up as a regression rather
than as a test that quietly started passing.
"""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from types import ModuleType

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
EXAMPLES_DIR = REPO_ROOT / "mission" / "examples"
VALIDATOR_PATH = REPO_ROOT / "tools" / "validate-mission.py"


def _load_validator() -> ModuleType:
    """Load tools/validate-mission.py as a module.

    The file is a hyphenated executable script rather than an importable
    module name, so it is loaded by path. Keeping it a script matters more
    than keeping it importable: contributors run it directly.
    """
    spec = importlib.util.spec_from_file_location("validate_mission", VALIDATOR_PATH)
    if spec is None or spec.loader is None:  # pragma: no cover - defensive
        message = f"cannot load {VALIDATOR_PATH}"
        raise RuntimeError(message)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


validate_mission = _load_validator()


def _require_jsonschema() -> None:
    """Skip a test that needs the schema layer when jsonschema is absent.

    Skipping beats failing here: a package that could not be checked is not a
    package that passed, and a false pass would be worse than a skip. The
    checks that need no schema still run. CI installs jsonschema, so nothing
    skips there.
    """
    pytest.importorskip("jsonschema", reason="the schema layer needs jsonschema")


def _examples(prefix: str) -> list[Path]:
    return sorted(EXAMPLES_DIR.glob(f"{prefix}*.json"))


def test_examples_exist() -> None:
    """Both kinds of example are present.

    A test suite that silently finds no files passes, which is why this is
    checked first.
    """
    assert _examples("valid-"), "no valid example packages found"
    assert _examples("invalid-"), "no invalid example packages found"


@pytest.mark.parametrize("path", _examples("valid-"), ids=lambda p: p.name)
def test_valid_examples_validate(path: Path) -> None:
    """Every valid example passes both validation layers."""
    _require_jsonschema()
    _require_jsonschema()
    schema = validate_mission.load_schema()
    errors = validate_mission.validate(path, schema)
    assert not errors, f"{path.name} should validate but reported: {errors}"


@pytest.mark.parametrize("path", _examples("invalid-"), ids=lambda p: p.name)
def test_invalid_examples_are_rejected(path: Path) -> None:
    """Every invalid example is rejected by one layer or the other."""
    schema = validate_mission.load_schema()
    errors = validate_mission.validate(path, schema)
    assert errors, (
        f"{path.name} is a counter-example and should have been rejected. "
        f"A counter-example that stops being caught is a regression."
    )


@pytest.mark.parametrize(
    "path", _examples("valid-") + _examples("invalid-"), ids=lambda p: p.name
)
def test_every_example_declares_its_identities_fake(path: Path) -> None:
    """Every committed example carries the mandatory fake-identity header.

    The header is what stops a file being copied out of the examples directory
    and mistaken for a real configuration. See SECURITY.md.
    """
    document = json.loads(path.read_text(encoding="utf-8"))
    assert "_comment" in document, f"{path.name} has no _comment header"
    assert "FAKE" in document["_comment"].upper(), (
        f"{path.name} does not state that its identities are fake"
    )


@pytest.mark.parametrize("path", _examples("invalid-"), ids=lambda p: p.name)
def test_invalid_examples_name_the_rule_they_violate(path: Path) -> None:
    """Every counter-example says what it is a counter-example to.

    Without this, a reader cannot tell a deliberate counter-example from a
    file someone got wrong.
    """
    document = json.loads(path.read_text(encoding="utf-8"))
    assert "_violates" in document, (
        f"{path.name} does not name the rule it violates"
    )
    assert document["_violates"].strip(), f"{path.name} has an empty _violates"


def test_publication_rule_is_enforced_on_examples(tmp_path: Path) -> None:
    """A package under mission/examples/ marked as real is rejected.

    This is a repository rule rather than a schema rule: the schema describes
    packages generally, including real ones, and a schema that forbade real
    packages could not validate the packages the system actually runs.
    """
    _require_jsonschema()
    schema = validate_mission.load_schema()
    real = {
        "_comment": "Test fixture. Identities are FAKE.",
        "schema_version": "0.1",
        "mission": {
            "id": "test-real-flag",
            "name": "Test",
            "example": False,
        },
        "network": {"mesh_id": "test-mesh"},
        "profile": "exercise",
    }
    planted = EXAMPLES_DIR / "zz-test-publication-rule.json"
    planted.write_text(json.dumps(real), encoding="utf-8")
    try:
        errors = validate_mission.validate(planted, schema)
    finally:
        planted.unlink()

    assert any("example" in error for error in errors), (
        "a package under mission/examples/ marked as a real configuration "
        f"must be rejected, but the validator reported: {errors}"
    )


def test_secret_material_is_rejected(tmp_path: Path) -> None:
    """A package containing key material is rejected.

    A backstop behind secret scanning and behind the reviewer, not the control
    itself. See SECURITY.md.
    """
    _require_jsonschema()
    schema = validate_mission.load_schema()
    planted = EXAMPLES_DIR / "zz-test-secret.json"
    planted.write_text(
        json.dumps(
            {
                "_comment": "Test fixture. Identities are FAKE.",
                "schema_version": "0.1",
                "mission": {"id": "t", "name": "T", "example": True},
                "network": {"mesh_id": "t"},
                "profile": "exercise",
                "notes": "-----BEGIN PRIVATE KEY-----not-a-real-key",
            }
        ),
        encoding="utf-8",
    )
    try:
        errors = validate_mission.validate(planted, schema)
    finally:
        planted.unlink()

    assert any("PRIVATE KEY" in error for error in errors), (
        f"key material must be rejected, but the validator reported: {errors}"
    )
