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
    assert "_violates" in document, f"{path.name} does not name the rule it violates"
    assert document["_violates"].strip(), f"{path.name} has an empty _violates"


def test_publication_rule_is_enforced_on_examples(tmp_path: Path) -> None:
    """A package under mission/examples/ marked as real is rejected.

    This is a repository rule rather than a schema rule: the schema describes
    packages generally, including real ones, and a schema that forbade real
    packages could not validate the packages the system actually runs.
    """
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


def test_non_mapping_example_returns_schema_errors_without_crashing() -> None:
    """Repository-only checks shall tolerate every JSON value the schema rejects."""
    schema = validate_mission.load_schema()
    planted = EXAMPLES_DIR / "zz-test-array.json"
    planted.write_text("[]", encoding="utf-8")
    try:
        errors = validate_mission.validate(planted, schema)
    finally:
        planted.unlink()

    assert any(error.startswith("schema: $") for error in errors)


def test_wrong_mission_type_returns_schema_errors_without_crashing() -> None:
    """Repository checks shall not dereference a schema-invalid mission value."""
    schema = validate_mission.load_schema()
    document = {"mission": []}

    errors = validate_mission.check_schema(
        document, schema
    ) + validate_mission.check_repository_rules(
        document, EXAMPLES_DIR / "invalid-mission-type.json", "{}"
    )

    assert any(error.startswith("schema: $.mission") for error in errors)


def test_validate_reports_unreadable_package(tmp_path: Path) -> None:
    """A missing package produces a stable diagnostic instead of an exception."""
    errors = validate_mission.validate(
        tmp_path / "missing.json", validate_mission.load_schema()
    )

    assert len(errors) == 1
    assert errors[0].startswith("cannot read package:")


def test_validate_reports_invalid_utf8(tmp_path: Path) -> None:
    """A non-UTF-8 package produces a stable diagnostic instead of an exception."""
    path = tmp_path / "invalid-utf8.json"
    path.write_bytes(b"\xff")

    errors = validate_mission.validate(path, validate_mission.load_schema())

    assert errors == ["not valid UTF-8: byte 0"]


def test_main_reports_unreadable_package(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """The CLI reports an unreadable package without a traceback."""
    path = tmp_path / "package.json"

    assert validate_mission.main([str(path)]) == 1
    captured = capsys.readouterr()
    assert f"FAIL {path}" in captured.out
    assert "cannot read package:" in captured.out
    assert captured.err == "1 failure(s).\n"


def test_main_reports_invalid_utf8(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """The CLI reports invalid UTF-8 without a traceback."""
    path = tmp_path / "package.json"
    path.write_bytes(b"\xff")

    assert validate_mission.main([str(path)]) == 1
    captured = capsys.readouterr()
    assert f"FAIL {path}" in captured.out
    assert "not valid UTF-8: byte 0" in captured.out
    assert captured.err == "1 failure(s).\n"


def test_main_reports_schema_load_failure(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """The CLI maps a controlling-schema failure to a stable exit status."""

    def fail_schema() -> dict[str, object]:
        raise validate_mission.MissionLoadError("test schema failure")

    monkeypatch.setattr(validate_mission, "load_schema", fail_schema)

    assert validate_mission.main([]) == 2
    assert capsys.readouterr().err == "ERROR: test schema failure\n"
