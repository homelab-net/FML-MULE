#!/usr/bin/env python3
"""Validate retained Debian packages against FML-ADR-081 locks.

Usage:
    tools/validate-package-cache.py CACHE LOCK [LOCK ...]
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


def _sha256(path: Path) -> str:
    """Return the lowercase SHA-256 of one package file."""
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def validate(cache: Path, locks: list[Path]) -> list[str]:
    """Return missing or corrupt retained-package defects."""
    errors: list[str] = []
    cache_hashes: set[str] = set()
    if cache.is_dir():
        for path in cache.rglob("*.deb"):
            cache_hashes.add(_sha256(path))
    else:
        errors.append(f"package cache does not exist: {cache}")
    expected: dict[str, str] = {}
    for lock in locks:
        try:
            document = json.loads(lock.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            errors.append(f"cannot read package lock: {lock}: {exc}")
            continue
        packages = document.get("packages") if isinstance(document, dict) else None
        if not isinstance(packages, list):
            errors.append(f"package lock has no package list: {lock}")
            continue
        for package in packages:
            if not isinstance(package, dict):
                errors.append(f"package lock contains a non-object record: {lock}")
                continue
            filename = Path(str(package.get("filename", ""))).name
            checksum = str(package.get("sha256", ""))
            if not filename or not checksum:
                errors.append(
                    f"package lock contains incomplete cache identity: {lock}"
                )
                continue
            previous = expected.setdefault(filename, checksum)
            if previous != checksum:
                errors.append(f"package locks disagree on checksum for {filename}")
    for filename, checksum in sorted(expected.items()):
        if checksum not in cache_hashes:
            errors.append(f"package cache is missing expected SHA-256 for {filename}")
    return errors


def main() -> int:
    """Validate one cache against one or more lock files."""
    parser = argparse.ArgumentParser()
    parser.add_argument("cache", type=Path)
    parser.add_argument("locks", nargs="+", type=Path)
    arguments = parser.parse_args()
    errors = validate(
        arguments.cache.resolve(), [path.resolve() for path in arguments.locks]
    )
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    print("Retained package cache: 0 defects.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
