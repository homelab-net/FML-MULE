"""Tests for the canonical runtime mission-package loader."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from mule.mission import (
    MissionLoadError,
    MissionValidationError,
    ValidationIssue,
    load_mission,
    load_schema,
    validate_document,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
VALID_MISSION = REPO_ROOT / "mission" / "examples" / "valid-full.json"


def test_valid_mission_loads_through_the_canonical_schema() -> None:
    """The public loader returns the validated mapping."""
    loaded = load_mission(VALID_MISSION)

    assert loaded["mission"]["id"] == "example-full"


def test_public_loader_does_not_accept_a_schema_override() -> None:
    """Callers cannot replace the declared runtime schema with a permissive one."""
    with pytest.raises(TypeError, match="unexpected keyword argument 'schema'"):
        load_mission(VALID_MISSION, schema={})  # type: ignore[call-arg]


def test_schema_errors_include_stable_object_and_array_paths() -> None:
    mission = json.loads(VALID_MISSION.read_text(encoding="utf-8"))
    mission["network"]["unknown"] = True
    mission["services"].append(7)

    issues = validate_document(mission, load_schema())

    assert [issue.path for issue in issues] == ["$.network", "$.services[0]"]
    assert all(issue.message for issue in issues)
    assert issues[0].render().startswith("$.network: ")


def test_invalid_package_raises_with_structured_issues(tmp_path: Path) -> None:
    mission = json.loads(VALID_MISSION.read_text(encoding="utf-8"))
    mission["mission"]["unknown"] = True
    path = tmp_path / "invalid.json"
    path.write_text(json.dumps(mission), encoding="utf-8")

    with pytest.raises(MissionValidationError) as excinfo:
        load_mission(path)

    assert excinfo.value.source == path
    assert excinfo.value.issues[0].path == "$.mission"
    assert "unknown" in str(excinfo.value)


def test_malformed_json_is_a_root_path_validation_error(tmp_path: Path) -> None:
    path = tmp_path / "malformed.json"
    path.write_text('{"mission":', encoding="utf-8")

    with pytest.raises(MissionValidationError) as excinfo:
        load_mission(path)

    assert excinfo.value.issues == (
        ValidationIssue("$", "invalid JSON at line 1, column 12: Expecting value"),
    )


def test_invalid_utf8_is_a_root_path_validation_error(tmp_path: Path) -> None:
    path = tmp_path / "invalid-utf8.json"
    path.write_bytes(b"\xff")

    with pytest.raises(MissionValidationError) as excinfo:
        load_mission(path)

    assert excinfo.value.issues == (ValidationIssue("$", "invalid UTF-8 at byte 0"),)


def test_invalid_utf8_schema_is_a_load_error(tmp_path: Path) -> None:
    path = tmp_path / "invalid-utf8-schema.json"
    path.write_bytes(b"\xff")

    with pytest.raises(MissionLoadError, match="cannot be loaded"):
        load_schema(path)


def test_missing_package_is_a_load_error(tmp_path: Path) -> None:
    missing = tmp_path / "missing.json"

    with pytest.raises(MissionLoadError, match="not found or unreadable"):
        load_mission(missing)


@pytest.mark.parametrize(
    ("contents", "fragment"),
    [
        ("{", "cannot be loaded"),
        ("[]", "not a JSON object"),
        ('{"type": 42}', "schema is invalid"),
    ],
    ids=["malformed", "non-object", "invalid-schema"],
)
def test_bad_schema_is_refused(tmp_path: Path, contents: str, fragment: str) -> None:
    path = tmp_path / "schema.json"
    path.write_text(contents, encoding="utf-8")

    with pytest.raises(MissionLoadError, match=fragment):
        load_schema(path)


def test_missing_schema_is_refused(tmp_path: Path) -> None:
    with pytest.raises(MissionLoadError, match="cannot be loaded"):
        load_schema(tmp_path / "missing-schema.json")
