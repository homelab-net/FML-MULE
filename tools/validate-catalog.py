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
   named in a ``mission/examples/*.json`` package must resolve uniquely to an
   enabled catalog entry whose loadable Quadlet exists. It also rejects a
   loadable Quadlet with no enabled catalog record. These are the checks the
   schema defers to (FML-ADR-078).
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
QUADLETS_PATH = REPO_ROOT / "services" / "quadlets"


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

    services = catalog.get("services", [])
    names: dict[str, list[dict[str, Any]]] = {}
    references: dict[str, list[dict[str, Any]]] = {}
    units: dict[str, list[dict[str, Any]]] = {}
    quadlets_path = root / "services" / "quadlets"

    # ``uniqueItems`` distinguishes whole objects, not their identity fields.
    # Build the actual lookup tables and require every canonical name, alias and
    # deployment unit to resolve exactly once. FML-ADR-078, GAP-02.
    for entry in services:
        name = entry["name"]
        names.setdefault(name, []).append(entry)
        for reference in [name, *entry["aliases"]]:
            references.setdefault(reference, []).append(entry)
        if entry["unit"] != "TBD":
            units.setdefault(entry["unit"], []).append(entry)

    for name, owners in sorted(names.items()):
        if len(owners) != 1:
            errors.append(f"duplicate catalog service name {name!r}")
    for reference, owners in sorted(references.items()):
        if len(owners) != 1:
            errors.append(f"service reference {reference!r} is ambiguous")

    for entry in services:
        name = entry["name"]
        unit = entry["unit"]
        if entry["enabled"]:
            expected = f"{name}.container"
            if unit == "TBD":
                errors.append(
                    f"enabled service {name!r} has no deployment unit reference"
                )
            elif unit != expected:
                errors.append(
                    f"enabled service {name!r} unit must be {expected!r}, got {unit!r}"
                )
            elif not (quadlets_path / unit).is_file():
                errors.append(
                    f"enabled service {name!r} deployment unit is absent: "
                    f"services/quadlets/{unit}"
                )
        elif unit != "TBD":
            errors.append(
                f"disabled service {name!r} names loadable deployment unit {unit!r}"
            )

    for path in sorted(quadlets_path.glob("*.container")):
        owners = units.get(path.name, [])
        if len(owners) != 1 or not owners[0]["enabled"]:
            errors.append(
                f"loadable Quadlet {path.name!r} has no enabled catalog record"
            )

    # Enforcement: every accepted reference resolves to exactly one enabled
    # record. Invalid mission examples are expected to fail at another layer.
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
        unknown = [s for s in enabled if s not in references]
        # invalid-* packages are expected to be rejected somewhere; an unknown
        # service in one is not a catalog defect.
        if unknown and package.name.startswith("valid-"):
            errors.append(
                f"{package.relative_to(root)} enables service(s) with no catalog "
                f"entry: {', '.join(unknown)}. Add an entry to services/catalog/ "
                "or correct the package."
            )
        if package.name.startswith("valid-"):
            for reference in enabled:
                owners = references.get(reference, [])
                if len(owners) == 1 and not owners[0]["enabled"]:
                    errors.append(
                        f"{package.relative_to(root)} enables disabled service "
                        f"{owners[0]['name']!r} through reference {reference!r}"
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
