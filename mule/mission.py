"""Load and validate mission packages against the canonical JSON schema.

Mission-package shape is a runtime contract. Repository publication rules for
committed examples remain in ``tools/validate-mission.py`` because they do not
apply to real packages loaded by a node.
"""

from __future__ import annotations

import json
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any, cast

from jsonschema import Draft202012Validator
from jsonschema.exceptions import SchemaError

# FML-ADR-051: runtime decision logic is importable outside the test tree.
REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_SCHEMA_PATH = REPO_ROOT / "mission" / "schema" / "mission-package.schema.json"


class MissionLoadError(Exception):
    """A mission package or its controlling schema could not be loaded."""


@dataclass(frozen=True)
class ValidationIssue:
    """One stable, path-addressed mission schema violation."""

    path: str
    message: str

    def render(self) -> str:
        """Render the issue for a CLI or log."""
        return f"{self.path}: {self.message}"


class MissionValidationError(MissionLoadError):
    """A readable mission package does not satisfy the mission schema."""

    def __init__(self, source: Path, issues: Sequence[ValidationIssue]) -> None:
        """Retain structured issues while providing an actionable message."""
        self.source = source
        self.issues = tuple(issues)
        detail = "\n".join(f"  {issue.render()}" for issue in self.issues)
        super().__init__(
            f"mission package {source} failed schema validation:\n{detail}"
        )


def _json_path(parts: Sequence[str | int]) -> str:
    """Return a deterministic JSON path for a jsonschema error path."""
    rendered = "$"
    for part in parts:
        rendered += f"[{part}]" if isinstance(part, int) else f".{part}"
    return rendered


def load_schema(path: str | Path = DEFAULT_SCHEMA_PATH) -> dict[str, Any]:
    """Load and check the declared Draft 2020-12 mission schema."""
    resolved = Path(path)
    try:
        document = json.loads(resolved.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise MissionLoadError(
            f"mission schema cannot be loaded: {resolved}: {exc}"
        ) from exc
    if not isinstance(document, dict):
        raise MissionLoadError(f"mission schema is not a JSON object: {resolved}")
    try:
        Draft202012Validator.check_schema(document)
    except SchemaError as exc:
        raise MissionLoadError(
            f"mission schema is invalid: {resolved}: {exc.message}"
        ) from exc
    return document


def validate_document(
    document: object, schema: dict[str, Any]
) -> tuple[ValidationIssue, ...]:
    """Return every mission-schema violation in deterministic order."""
    errors = sorted(
        Draft202012Validator(schema).iter_errors(document),
        key=lambda error: (_json_path(tuple(error.absolute_path)), error.message),
    )
    return tuple(
        ValidationIssue(_json_path(tuple(error.absolute_path)), error.message)
        for error in errors
    )


def load_mission(path: str | Path) -> dict[str, Any]:
    """Load one mission package and reject it unless it satisfies the schema."""
    resolved = Path(path)
    try:
        document = json.loads(resolved.read_text(encoding="utf-8"))
    except OSError as exc:
        raise MissionLoadError(
            f"mission package not found or unreadable: {resolved}: {exc}"
        ) from exc
    except UnicodeDecodeError as exc:
        issue = ValidationIssue("$", f"invalid UTF-8 at byte {exc.start}")
        raise MissionValidationError(resolved, (issue,)) from exc
    except json.JSONDecodeError as exc:
        issue = ValidationIssue(
            "$", f"invalid JSON at line {exc.lineno}, column {exc.colno}: {exc.msg}"
        )
        raise MissionValidationError(resolved, (issue,)) from exc

    issues = validate_document(document, load_schema())
    if issues:
        raise MissionValidationError(resolved, issues)

    return cast(dict[str, Any], document)
