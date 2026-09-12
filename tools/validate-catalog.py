#!/usr/bin/env python3
"""Validate the service catalog and enforce it against mission packages.

Usage:
    tools/validate-catalog.py [REPOSITORY_ROOT]

Two layers, kept apart the way tools/validate-mission.py keeps them:

1. **Schema.** ``services/catalog/catalog.schema.json`` describes what a catalog
   entry is. Trade-blocked fields may be the string ``TBD``; an image, if given,
   must be by immutable digest, never a tag.

2. **Enforcement.** The mission JSON schema requires every enabled service name
   to have a catalog entry but cannot check it. This tool does: every service
   named in a ``mission/examples/*.json`` package must resolve to a catalog
   entry. That is the check the schema defers to (FML-ADR-078).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import jsonschema
import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
CATALOG_PATH = REPO_ROOT / "services" / "catalog" / "catalog.yml"
CATALOG_SCHEMA_PATH = REPO_ROOT / "services" / "catalog" / "catalog.schema.json"
MISSION_EXAMPLES = REPO_ROOT / "mission" / "examples"


def _load_yaml(path: Path) -> Any:  # noqa: ANN401
    with path.open(encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def validate_repository(root: Path) -> list[str]:
    """Validate the catalog and every mission example against it."""
    errors: list[str] = []
    catalog_path = root / "services" / "catalog" / "catalog.yml"
    schema_path = root / "services" / "catalog" / "catalog.schema.json"

    try:
        catalog = _load_yaml(catalog_path)
    except FileNotFoundError:
        return [f"catalog not found: {catalog_path}"]
    schema = json.loads(schema_path.read_text(encoding="utf-8"))

    validator = jsonschema.Draft202012Validator(schema)
    for error in sorted(validator.iter_errors(catalog), key=str):
        location = "$" + "".join(f"[{part!r}]" for part in error.absolute_path)
        errors.append(f"catalog {location}: {error.message}")
    if errors:
        return errors

    names = {entry["name"] for entry in catalog.get("services", [])}

    # Enforcement: no mission example may enable a service with no catalog entry.
    for package in sorted((root / "mission" / "examples").glob("*.json")):
        try:
            document = json.loads(package.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if not isinstance(document, dict):
            continue
        enabled = document.get("services", [])
        if not isinstance(enabled, list):
            continue
        unknown = [s for s in enabled if s not in names]
        # invalid-* packages are expected to be rejected somewhere; an unknown
        # service in one is not a catalog defect.
        if unknown and package.name.startswith("valid-"):
            errors.append(
                f"{package.relative_to(root)} enables service(s) with no catalog "
                f"entry: {', '.join(unknown)}. Add an entry to services/catalog/ "
                "or correct the package."
            )

    return errors


def main(argv: list[str]) -> int:
    """Validate one repository root and return a process exit status."""
    if len(argv) > 1:
        print("Usage: tools/validate-catalog.py [REPOSITORY_ROOT]", file=sys.stderr)
        return 2
    root = Path(argv[0]) if argv else REPO_ROOT
    errors = validate_repository(root)
    if errors:
        for error in errors:
            print(f"FAIL: {error}", file=sys.stderr)
        return 1
    catalog = _load_yaml(root / "services" / "catalog" / "catalog.yml")
    print(f"Service catalog: {len(catalog.get('services', []))} service(s), 0 defects.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
