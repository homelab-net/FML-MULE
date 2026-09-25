#!/usr/bin/env python3
"""Validate a built FML-ADR-081 filesystem and its CycloneDX SBOM.

Usage:
    tools/validate-image-root.py --root PATH --lock PATH --sbom PATH \
        --write-exceptions PATH
"""

from __future__ import annotations

import argparse
import hashlib
import json
from email.parser import Parser
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, unquote

from license_expression import ExpressionError, get_spdx_licensing

SPDX_LICENSING = get_spdx_licensing()
RUNTIME_NAME = "fml-mule"  # FML-ADR-083
RUNTIME_VERSION = "0.0.1"  # FML-ADR-083
RUNTIME_PURL = f"pkg:pypi/{RUNTIME_NAME}@{RUNTIME_VERSION}"


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


def _runtime_digest(root: Path, errors: list[str]) -> str | None:
    """Hash the one complete installed FML-ADR-083 runtime distribution."""
    metadata_paths = sorted(
        path
        for pattern in (
            "usr/lib/python*/dist-packages/fml_mule-*.dist-info/METADATA",
            "usr/lib/python*/site-packages/fml_mule-*.dist-info/METADATA",
        )
        for path in root.glob(pattern)
    )
    if len(metadata_paths) != 1:
        errors.append(
            "target shall contain exactly one fml-mule distribution metadata file"
        )
        return None
    metadata = metadata_paths[0]
    record = Parser().parsestr(metadata.read_text(encoding="utf-8"), headersonly=True)
    if record.get("Name") != RUNTIME_NAME or record.get("Version") != RUNTIME_VERSION:
        errors.append("installed MULE distribution identity does not match FML-ADR-083")
        return None
    package = metadata.parent.parent / "mule"
    required = [
        metadata,
        root / "usr/share/fml-mule/mission-package.schema.json",
        root / "usr/lib/systemd/system/mule-runtime.service",
    ]
    sources = sorted(package.rglob("*.py")) if package.is_dir() else []
    files = [*sources, *required]
    if not sources or any(not path.is_file() for path in required):
        errors.append("installed MULE distribution is incomplete")
        return None
    digest = hashlib.sha256()
    for path in sorted(files):
        digest.update(path.relative_to(root).as_posix().encode())
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def _validate_runtime_component(
    root: Path, document: dict[str, Any], errors: list[str]
) -> None:
    """Require the source-built runtime beside the Debian SBOM components."""
    digest = _runtime_digest(root, errors)
    raw_components = document.get("components")
    if not isinstance(raw_components, list):
        return
    matches = [
        component
        for component in raw_components
        if isinstance(component, dict) and component.get("purl") == RUNTIME_PURL
    ]
    if len(matches) != 1:
        errors.append("SBOM shall contain fml-mule exactly once")
        return
    component = matches[0]
    expected_hashes = [{"alg": "SHA-256", "content": digest}]
    if (
        component.get("type") != "application"
        or component.get("name") != RUNTIME_NAME
        or component.get("version") != RUNTIME_VERSION
        or component.get("hashes") != expected_hashes
        or component.get("licenses") != [{"license": {"id": "Apache-2.0"}}]
        or component.get("properties")
        != [{"name": "fml:governing-decision", "value": "FML-ADR-083"}]
    ):
        errors.append("SBOM fml-mule component does not match the installed runtime")


def _valid_spdx_expression(value: object) -> bool:
    """Recognize only expressions composed of registered SPDX symbols."""
    if not isinstance(value, str) or not value.strip():
        return False
    try:
        SPDX_LICENSING.parse(value, validate=True, strict=True)
    except ExpressionError:
        return False
    return True


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
    _validate_runtime_component(root, sbom, errors)
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
