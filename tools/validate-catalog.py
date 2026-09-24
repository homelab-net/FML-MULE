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
   enabled catalog entry whose loadable files exist. It also rejects a
   loadable container that is not one enabled service's ``.container`` and
   not a member of one enabled bundle. A bundle member is not a second
   catalog service. These are the checks the schema defers to (FML-ADR-078).
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


def _claimed_containers(entry: dict[str, Any]) -> set[str]:
    """Container files one capability claims, as root or as bundle members.

    A simple capability claims its ``.container``. A bundle claims each member
    container, not the target and not the network. Callers use this for
    enabled records only. A disabled contract is not allowed to have the
    loadable files.
    """
    claimed: set[str] = set()
    unit = str(entry["unit"])
    if unit.endswith(".container"):
        claimed.add(unit)
    for member in entry.get("bundle", []):
        name = str(member)
        if name.endswith(".container"):
            claimed.add(name)
    return claimed


def _disk_name(logical: str, enabled: bool) -> str:
    """On-disk filename for a deployment name.

    A disabled capability keeps the same root and bundle names the enabled
    contract will use. The ``.disabled`` suffix is what keeps systemd from
    loading them, not a second name.
    """
    return logical if enabled else f"{logical}.disabled"


def _check_deployment(
    entry: dict[str, Any], quadlets_path: Path, errors: list[str]
) -> list[str]:
    """Check one capability's root and, if it has one, its bundle."""
    name = entry["name"]
    unit = entry["unit"]
    enabled = entry["enabled"]
    bundle = entry.get("bundle", [])
    owned: list[str] = []
    if bundle and not str(unit).endswith(".target"):
        errors.append(f"bundled service {name!r} unit must be a .target, got {unit!r}")
    if enabled and not bundle and unit != f"{name}.container":
        if unit == "TBD":
            errors.append(f"enabled service {name!r} has no deployment unit reference")
        else:
            errors.append(
                f"enabled service {name!r} unit must be {name}.container, got {unit!r}"
            )
    if not enabled and not bundle and unit != "TBD":
        errors.append(
            f"disabled service {name!r} names loadable deployment unit {unit!r}"
        )
    logicals: list[str] = []
    if unit != "TBD":
        logicals.append(unit)
    logicals.extend(bundle)
    for logical in logicals:
        disk = _disk_name(logical, enabled)
        owned.append(disk)
        if not (quadlets_path / disk).is_file():
            errors.append(
                f"service {name!r} deployment file is absent: services/quadlets/{disk}"
            )
        if enabled and (quadlets_path / f"{logical}.disabled").is_file():
            errors.append(
                f"enabled service {name!r} still has disabled text {logical}.disabled"
            )
        if not enabled and (quadlets_path / logical).is_file():
            errors.append(
                f"disabled service {name!r} names loadable deployment unit {logical!r}"
            )
    return owned


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
    quadlets_path = root / "services" / "quadlets"

    # ``uniqueItems`` distinguishes whole objects, not their identity fields.
    # Build the actual lookup tables and require every canonical name, alias and
    # deployment unit to resolve exactly once. FML-ADR-078, GAP-02.
    for entry in services:
        name = entry["name"]
        names.setdefault(name, []).append(entry)
        for reference in [name, *entry["aliases"]]:
            references.setdefault(reference, []).append(entry)

    for name, owners in sorted(names.items()):
        if len(owners) != 1:
            errors.append(f"duplicate catalog service name {name!r}")
    for reference, owners in sorted(references.items()):
        if len(owners) != 1:
            errors.append(f"service reference {reference!r} is ambiguous")

    owned_disk: set[str] = set()
    for entry in services:
        owned_disk.update(_check_deployment(entry, quadlets_path, errors))

    container_owners: dict[str, list[dict[str, Any]]] = {}
    for entry in services:
        if not entry["enabled"]:
            continue
        for container in _claimed_containers(entry):
            container_owners.setdefault(container, []).append(entry)

    for path in sorted(quadlets_path.glob("*.container")):
        owners = container_owners.get(path.name, [])
        if len(owners) != 1:
            errors.append(
                f"loadable Quadlet {path.name!r} has no enabled catalog record"
            )

    bundle_owners: dict[str, list[str]] = {}
    catalog_names = set(names)
    for entry in services:
        owner = entry["name"]
        for member in entry.get("bundle", []):
            bundle_owners.setdefault(member, []).append(owner)
            stem = member.split(".", 1)[0]
            if stem in catalog_names and stem != owner:
                errors.append(
                    f"bundle member {member!r} collides with catalog service {stem!r}"
                )
    for member, member_owners in sorted(bundle_owners.items()):
        if len(member_owners) != 1:
            errors.append(f"bundle member {member!r} is owned by {member_owners}")

    internal_suffixes = (
        ".container",
        ".container.disabled",
        ".network",
        ".network.disabled",
        ".target",
        ".target.disabled",
    )
    if quadlets_path.is_dir():
        for path in sorted(quadlets_path.iterdir()):
            if not path.is_file() or path.name == "example.container.disabled":
                continue
            if path.name.endswith(internal_suffixes) and path.name not in owned_disk:
                errors.append(f"internal unit {path.name!r} is not in a catalog bundle")

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
