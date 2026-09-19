#!/usr/bin/env python3
"""Validate a built FML-ADR-081 filesystem and its CycloneDX SBOM.

Usage:
    tools/validate-image-root.py --root PATH --lock PATH --sbom PATH \
        --write-exceptions PATH
"""

from __future__ import annotations

import argparse
import json
import re
from email.parser import Parser
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, unquote

SPDX_TOKEN = re.compile(r"\s*(\(|\)|AND\b|OR\b|WITH\b|[A-Za-z0-9][A-Za-z0-9.+-]*)")


def _read_json(path: Path, label: str, errors: list[str]) -> dict[str, Any]:
    """Read one JSON object or append a stable diagnostic."""
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        errors.append(f"cannot read {label}: {path}: {exc}")
        return {}
    if not isinstance(value, dict):
        errors.append(f"{label} shall be a JSON object")
        return {}
    return value


def _installed(root: Path, errors: list[str]) -> dict[str, tuple[str, str]]:
    """Read installed package name, version, and architecture from dpkg status."""
    status = root / "var/lib/dpkg/status"
    try:
        content = status.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        errors.append(f"cannot read target dpkg status: {status}: {exc}")
        return {}
    installed: dict[str, tuple[str, str]] = {}
    for block in content.split("\n\n"):
        if not block.strip():
            continue
        record = Parser().parsestr(block, headersonly=True)
        if record.get("Status") != "install ok installed":
            continue
        name = record.get("Package")
        version = record.get("Version")
        architecture = record.get("Architecture")
        if not name or not version or not architecture:
            errors.append("installed dpkg record has an incomplete identity")
            continue
        installed[name] = (version, architecture)
    if not installed:
        errors.append("target dpkg status contains no installed packages")
    return installed


def _purl_identity(purl: object) -> tuple[str, str, str] | None:
    """Return name, version, and architecture from one Debian package URL."""
    if not isinstance(purl, str) or not purl.startswith("pkg:deb/debian/"):
        return None
    identity = purl.removeprefix("pkg:deb/debian/")
    if "@" not in identity:
        return None
    name, version_query = identity.split("@", maxsplit=1)
    version, _, query = version_query.partition("?")
    architecture = parse_qs(query).get("arch", [""])[0]
    return unquote(name), unquote(version), unquote(architecture)


def _sbom_components(
    document: dict[str, Any], errors: list[str]
) -> dict[tuple[str, str, str], dict[str, Any]]:
    """Index Debian components from one CycloneDX document."""
    if document.get("bomFormat") != "CycloneDX":
        errors.append("SBOM bomFormat shall be CycloneDX")
    if document.get("specVersion") != "1.6":
        errors.append("SBOM specVersion shall be 1.6")
    raw_components = document.get("components")
    if not isinstance(raw_components, list):
        errors.append("SBOM components shall be a list")
        return {}
    components: dict[tuple[str, str, str], dict[str, Any]] = {}
    for component in raw_components:
        if not isinstance(component, dict):
            continue
        identity = _purl_identity(component.get("purl"))
        if identity is not None:
            components[identity] = component
    return components


def _valid_spdx_expression(value: object) -> bool:
    """Recognize the SPDX expression grammar used by CycloneDX choices."""
    if not isinstance(value, str) or not value.strip():
        return False
    tokens: list[str] = []
    position = 0
    while position < len(value):
        match = SPDX_TOKEN.match(value, position)
        if match is None:
            return False
        tokens.append(match.group(1))
        position = match.end()

    index = 0

    def parse_primary() -> bool:
        nonlocal index
        if index >= len(tokens):
            return False
        if tokens[index] == "(":
            index += 1
            if not parse_or() or index >= len(tokens) or tokens[index] != ")":
                return False
            index += 1
            return True
        if tokens[index] in {"AND", "OR", "WITH", ")"}:
            return False
        index += 1
        if index < len(tokens) and tokens[index] == "WITH":
            index += 1
            if index >= len(tokens) or tokens[index] in {
                "AND",
                "OR",
                "WITH",
                "(",
                ")",
            }:
                return False
            index += 1
        return True

    def parse_and() -> bool:
        nonlocal index
        if not parse_primary():
            return False
        while index < len(tokens) and tokens[index] == "AND":
            index += 1
            if not parse_primary():
                return False
        return True

    def parse_or() -> bool:
        nonlocal index
        if not parse_and():
            return False
        while index < len(tokens) and tokens[index] == "OR":
            index += 1
            if not parse_and():
                return False
        return True

    return parse_or() and index == len(tokens)


def _has_spdx_choice(licenses: object) -> bool:
    """Return whether CycloneDX licenses contain normalized SPDX data."""
    if not isinstance(licenses, list):
        return False
    for choice in licenses:
        if not isinstance(choice, dict):
            continue
        if _valid_spdx_expression(choice.get("expression")):
            return True
        license_value = choice.get("license")
        if isinstance(license_value, dict) and _valid_spdx_expression(
            license_value.get("id")
        ):
            return True
    return False


def validate(
    root: Path,
    lock_path: Path,
    sbom_path: Path,
) -> tuple[list[str], list[dict[str, str]]]:
    """Return built-root defects and normalized-licence exceptions."""
    errors: list[str] = []
    lock = _read_json(lock_path, "target lock", errors)
    sbom = _read_json(sbom_path, "CycloneDX SBOM", errors)
    packages = lock.get("packages")
    if not isinstance(packages, list):
        errors.append("target lock packages shall be a list")
        packages = []
    expected = {
        str(package.get("name")): (
            str(package.get("version")),
            str(package.get("architecture")),
        )
        for package in packages
        if isinstance(package, dict)
    }
    installed = _installed(root, errors)
    if installed != expected:
        missing = sorted(set(expected) - set(installed))
        extra = sorted(set(installed) - set(expected))
        changed = sorted(
            name
            for name in set(expected) & set(installed)
            if expected[name] != installed[name]
        )
        errors.append(
            "installed package set differs from target lock: "
            f"missing={missing}, extra={extra}, changed={changed}"
        )
    for prohibited in ("apt", "debsbom"):
        if prohibited in installed:
            errors.append(f"target contains prohibited package {prohibited}")
    if (root / "usr/bin/apt").exists() or (root / "usr/bin/apt-get").exists():
        errors.append("target contains an apt executable")
    source_files = [root / "etc/apt/sources.list"]
    source_directory = root / "etc/apt/sources.list.d"
    if source_directory.exists():
        source_files.extend(
            path for path in source_directory.rglob("*") if path.is_file()
        )
    if any(path.is_file() for path in source_files):
        errors.append("target contains an APT repository file")

    components = _sbom_components(sbom, errors)
    source_names = {
        str(package.get("source")) for package in packages if isinstance(package, dict)
    }
    source_components = {
        name for name, _version, architecture in components if architecture == "source"
    }
    missing_sources = sorted(source_names - source_components)
    if missing_sources:
        errors.append(f"SBOM lacks source-package components: {missing_sources}")

    exceptions: list[dict[str, str]] = []
    for name, (version, architecture) in sorted(expected.items()):
        copyright_file = root / f"usr/share/doc/{name}/copyright"
        if not copyright_file.is_file():
            errors.append(f"target package lacks Debian copyright file: {name}")
        component = components.get((name, version, architecture))
        if component is None:
            errors.append(f"SBOM lacks target binary package: {name}={version}")
            continue
        if not _has_spdx_choice(component.get("licenses")):
            exceptions.append(
                {
                    "name": name,
                    "version": version,
                    "reason": "no SPDX-normalized declared licence",
                }
            )
    return errors, exceptions


def main() -> int:
    """Validate one completed root and write its licence exception report."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", required=True, type=Path)
    parser.add_argument("--lock", required=True, type=Path)
    parser.add_argument("--sbom", required=True, type=Path)
    parser.add_argument("--write-exceptions", required=True, type=Path)
    arguments = parser.parse_args()
    errors, exceptions = validate(
        arguments.root.resolve(),
        arguments.lock.resolve(),
        arguments.sbom.resolve(),
    )
    report = {
        "schema_version": "1.0",
        "governing_decision": "FML-ADR-081",
        "exceptions": exceptions,
    }
    arguments.write_exceptions.write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8"
    )
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    print(f"Built image root: 0 defects; {len(exceptions)} licence exception(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
