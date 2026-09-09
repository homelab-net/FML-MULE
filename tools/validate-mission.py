#!/usr/bin/env python3
"""Validate mission configuration packages.

Usage:
    tools/validate-mission.py [PATH ...]

With no arguments, validates every package in ``mission/examples/``.

Validation has two layers, deliberately kept apart:

1. **Schema.** ``mission/schema/mission-package.schema.json`` describes what a
   mission package is. It describes packages generally, including real ones.

2. **Repository rules.** Constraints that apply to packages *committed to this
   repository* rather than to packages as such. The publication rule is the
   important one: nothing under ``mission/examples/`` may be a real
   configuration.

Keeping the layers apart matters. A schema that forbade real packages outright
would be a schema that could not validate the packages the system actually
runs, which would make it useless for its main job.

Files named ``invalid-*.json`` are expected to fail. Files named ``valid-*.json``
are expected to pass. That expectation is itself checked, so a rule which stops
catching its counter-example shows up as a regression rather than as a test
that quietly started passing.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    # Direct execution starts with tools/ on sys.path. FML-ADR-051 keeps shared
    # runtime decisions in the importable mule/ package.
    sys.path.insert(0, str(REPO_ROOT))

from mule.mission import MissionLoadError, validate_document  # noqa: E402
from mule.mission import load_schema as load_runtime_schema  # noqa: E402

SCHEMA_PATH = REPO_ROOT / "mission" / "schema" / "mission-package.schema.json"
EXAMPLES_DIR = REPO_ROOT / "mission" / "examples"

# Strings that look like committed key or credential material. This is a
# backstop behind secret scanning and behind the reviewer, not the control
# itself. See SECURITY.md.
SECRET_PATTERNS = [
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    re.compile(r"-----BEGIN CERTIFICATE-----"),
    re.compile(r"\bssh-(rsa|ed25519|dss)\s+AAAA"),
]

# Field names that must never carry a value in a committed package.
FORBIDDEN_FIELDS = {"passphrase", "password", "secret", "private_key", "token"}


def load_schema() -> dict[str, object]:
    """Read the mission package schema."""
    return load_runtime_schema(SCHEMA_PATH)


def check_schema(document: object, schema: dict[str, object]) -> list[str]:
    """Validate a document against the JSON Schema.

    Returns a list of error messages, empty when the document is valid.
    """
    return [
        f"schema: {issue.render()}" for issue in validate_document(document, schema)
    ]


def check_repository_rules(document: object, path: Path, raw: str) -> list[str]:
    """Apply the rules that govern packages committed to this repository.

    Returns a list of error messages, empty when the document is acceptable.
    """
    errors: list[str] = []

    # The publication rule. Nothing under mission/examples/ may be a real
    # configuration. See SECURITY.md.
    try:
        in_examples = path.resolve().is_relative_to(EXAMPLES_DIR)
    except AttributeError:  # Python < 3.9 has no is_relative_to
        in_examples = str(EXAMPLES_DIR) in str(path.resolve())

    if in_examples and isinstance(document, dict):
        mission = document.get("mission", {})
        if isinstance(mission, dict) and mission.get("example") is not True:
            errors.append(
                "repository rule: a package under mission/examples/ must set "
                "mission.example to true. A real configuration belongs in "
                "mission/local/, which is git-ignored, and is never committed. "
                "See SECURITY.md."
            )

        if "_comment" not in document:
            errors.append(
                "repository rule: every committed example must carry a "
                '"_comment" header stating that its identities are fake. See '
                "mission/examples/README.md."
            )

    for pattern in SECRET_PATTERNS:
        if pattern.search(raw):
            errors.append(
                f"repository rule: file contains material matching "
                f"{pattern.pattern!r}. No key, certificate or credential is "
                f"ever committed. See SECURITY.md."
            )

    for field in _walk_keys(document):
        if field.lower() in FORBIDDEN_FIELDS:
            errors.append(
                f"repository rule: field {field!r} must not appear in a "
                f"committed package. See SECURITY.md."
            )

    return errors


def _walk_keys(node: object) -> list[str]:
    """Collect every mapping key in a nested structure."""
    keys: list[str] = []
    if isinstance(node, dict):
        for key, value in node.items():
            keys.append(key)
            keys.extend(_walk_keys(value))
    elif isinstance(node, list):
        for item in node:
            keys.extend(_walk_keys(item))
    return keys


def validate(path: Path, schema: dict[str, object]) -> list[str]:
    """Validate one package. Returns a list of error messages."""
    try:
        raw = path.read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:
        return [f"not valid UTF-8: byte {exc.start}"]
    except OSError as exc:
        return [f"cannot read package: {path}: {exc}"]

    try:
        document = json.loads(raw)
    except json.JSONDecodeError as exc:
        return [f"not valid JSON: {exc}"]

    return check_schema(document, schema) + check_repository_rules(document, path, raw)


def expected_valid(path: Path) -> bool | None:
    """Whether this file is expected to pass, by naming convention.

    Returns True, False, or None where the name carries no expectation.
    """
    name = path.name
    if name.startswith("invalid-"):
        return False
    if name.startswith("valid-"):
        return True
    return None


def main(argv: list[str]) -> int:
    """Validate the packages named on the command line, or every example."""
    try:
        schema = load_schema()
    except MissionLoadError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    if argv:
        paths = [Path(arg) for arg in argv]
    else:
        paths = sorted(EXAMPLES_DIR.glob("*.json"))

    if not paths:
        print("No packages to validate.")
        return 0

    failures = 0
    for path in paths:
        errors = validate(path, schema)
        expectation = expected_valid(path)

        if expectation is None:
            if errors:
                failures += 1
                print(f"FAIL {path}")
                for error in errors:
                    print(f"       {error}")
            else:
                print(f"OK   {path}")
            continue

        if expectation and errors:
            failures += 1
            print(f"FAIL {path}: expected to validate, but did not")
            for error in errors:
                print(f"       {error}")
        elif not expectation and not errors:
            failures += 1
            print(
                f"FAIL {path}: expected to be REJECTED, but validated. "
                f"A counter-example that stops being caught is a regression."
            )
        else:
            verdict = "valid" if expectation else "correctly rejected"
            print(f"OK   {path} ({verdict})")

    print()
    if failures:
        print(f"{failures} failure(s).", file=sys.stderr)
        return 1
    print(f"All {len(paths)} package(s) behaved as expected.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
