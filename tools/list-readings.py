#!/usr/bin/env python3
"""List every hardware reading the node takes, from the Protocols in mule/.

Usage: tools/list-readings.py

Prints one method name per line. `tools/validate-docs.sh` uses it to require a
row in `docs/readings.md` for each, so that a decision cannot be written without
someone having asked what the platform can actually provide.

Reads the source with `ast` rather than importing it: this runs inside a
document check, and a check that imports the code it is checking fails for
reasons that have nothing to do with the check.
"""

from __future__ import annotations

import ast
import sys
from pathlib import Path

MULE = Path(__file__).resolve().parent.parent / "mule"


def _is_protocol(node: ast.ClassDef) -> bool:
    """Whether a class declares itself a Protocol."""
    return any(
        getattr(base, "id", getattr(base, "attr", "")) == "Protocol"
        for base in node.bases
    )


def readings() -> list[str]:
    """Every public method of every Protocol under mule/, sorted."""
    found: set[str] = set()
    for source in sorted(MULE.glob("*.py")):
        tree = ast.parse(source.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if not isinstance(node, ast.ClassDef) or not _is_protocol(node):
                continue
            found.update(
                item.name
                for item in node.body
                if isinstance(item, ast.FunctionDef) and not item.name.startswith("_")
            )
    return sorted(found)


def main() -> int:
    """Print the readings, one per line."""
    for name in readings():
        print(name)
    return 0


if __name__ == "__main__":
    sys.exit(main())
