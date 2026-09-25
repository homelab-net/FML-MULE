#!/usr/bin/env python3
"""Add the installed FML-ADR-083 Python distribution to a CycloneDX SBOM.

Usage:
    tools/add-runtime-sbom.py --root PATH --sbom PATH

``debsbom`` inventories the governed Debian package closure. The MULE runtime
is built from this repository and installed by pip, so it needs one explicit
component derived from the completed root rather than from build intent.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from email.parser import Parser
from pathlib import Path
from typing import Any

RUNTIME_NAME = "fml-mule"
RUNTIME_VERSION = "0.0.1"
RUNTIME_PURL = f"pkg:pypi/{RUNTIME_NAME}@{RUNTIME_VERSION}"


class RuntimeSbomError(Exception):
    """The installed runtime cannot be represented without guessing."""


def _installed_metadata(root: Path) -> Path:
    """Return the one installed runtime METADATA file."""
    candidates = sorted(
        path
        for pattern in (
            "usr/lib/python*/dist-packages/fml_mule-*.dist-info/METADATA",
            "usr/lib/python*/site-packages/fml_mule-*.dist-info/METADATA",
        )
        for path in root.glob(pattern)
    )
    if len(candidates) != 1:
        raise RuntimeSbomError(
            "target shall contain exactly one fml-mule distribution metadata file"
        )
    metadata = candidates[0]
    record = Parser().parsestr(metadata.read_text(encoding="utf-8"), headersonly=True)
    if record.get("Name") != RUNTIME_NAME or record.get("Version") != RUNTIME_VERSION:
        raise RuntimeSbomError(
            "installed MULE distribution identity does not match FML-ADR-083"
        )
    return metadata


def installed_digest(root: Path) -> str:
    """Hash the installed runtime code, metadata, schema, and native unit."""
    metadata = _installed_metadata(root)
    package = metadata.parent.parent / "mule"
    required = [
        metadata,
        root / "usr/share/fml-mule/mission-package.schema.json",
        root / "usr/lib/systemd/system/mule-runtime.service",
    ]
    sources = sorted(package.rglob("*.py")) if package.is_dir() else []
    files = [*sources, *required]
    if not sources or any(not path.is_file() for path in required):
        raise RuntimeSbomError("installed MULE distribution is incomplete")
    digest = hashlib.sha256()
    for path in sorted(files):
        relative = path.relative_to(root).as_posix().encode()
        digest.update(relative)
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def add_component(root: Path, sbom_path: Path) -> None:
    """Append one source-built runtime component to the completed SBOM."""
    try:
        document: Any = json.loads(sbom_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise RuntimeSbomError(f"cannot read CycloneDX SBOM: {exc}") from exc
    if not isinstance(document, dict) or not isinstance(
        document.get("components"), list
    ):
        raise RuntimeSbomError("CycloneDX SBOM shall contain a components list")
    components = document["components"]
    if any(
        isinstance(component, dict) and component.get("purl") == RUNTIME_PURL
        for component in components
    ):
        raise RuntimeSbomError("CycloneDX SBOM already contains fml-mule")
    components.append(
        {
            "type": "application",
            "bom-ref": RUNTIME_PURL,
            "name": RUNTIME_NAME,
            "version": RUNTIME_VERSION,
            "purl": RUNTIME_PURL,
            "hashes": [{"alg": "SHA-256", "content": installed_digest(root)}],
            "licenses": [{"license": {"id": "Apache-2.0"}}],
            "properties": [{"name": "fml:governing-decision", "value": "FML-ADR-083"}],
        }
    )
    sbom_path.write_text(json.dumps(document, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    """Add the runtime component or print one stable error."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", required=True, type=Path)
    parser.add_argument("--sbom", required=True, type=Path)
    arguments = parser.parse_args()
    try:
        add_component(arguments.root.resolve(), arguments.sbom.resolve())
    except RuntimeSbomError as exc:
        print(f"ERROR: {exc}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
