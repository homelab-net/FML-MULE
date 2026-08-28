#!/usr/bin/env python3
"""List every hardware reading the node takes, from the Protocols in mule/.

Usage: tools/list-readings.py

Prints one reading per line as `name<TAB>verdict`, where verdict is `ok` or
`needs-unit`. `tools/validate-docs.sh` uses it to require a row in
`docs/readings.md` for each, so that a decision cannot be written without
someone having asked what the platform can actually provide, and to require that
a numeric reading carries its unit in its name.

WHY UNITS BELONG IN THE NAME

Linux reports the same physical quantity in different units in different
subsystems. The thermal framework uses millidegrees Celsius; the power supply
class uses tenths of a degree; battery charge is a percent where the decision
wants a fraction. Each conversion is a place to be wrong by a factor of ten,
a hundred, or a thousand, and each error produces a plausible-looking number.

A method called `state_of_charge` gives a reader nowhere to notice it must
divide. `state_of_charge_fraction` does.

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


#: Suffixes that state a unit. A numeric reading whose name ends in none of
#: these is one whose unit lives only in a docstring, where a reader converting
#: it will not see it.
UNIT_SUFFIXES = (
    "_c",
    "_count",
    "_dbm",
    "_fraction",
    "_hz",
    "_minutes",
    "_percent",
    "_seconds",
    "_w",
    "_wh",
)

#: Annotations that carry a magnitude, and so need a unit. A bool, a string or
#: a datetime does not: there is nothing to convert.
NUMERIC_HINTS = ("int", "float")


def _is_numeric(returns: ast.expr | None) -> bool:
    """Whether a return annotation carries a magnitude."""
    if returns is None:
        return False
    text = ast.unparse(returns)
    return any(hint in text for hint in NUMERIC_HINTS)


def readings() -> list[tuple[str, str]]:
    """Every public Protocol method under mule/, with its unit verdict."""
    found: dict[str, str] = {}
    for source in sorted(MULE.glob("*.py")):
        tree = ast.parse(source.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if not isinstance(node, ast.ClassDef) or not _is_protocol(node):
                continue
            for item in node.body:
                if not isinstance(item, ast.FunctionDef):
                    continue
                if item.name.startswith("_"):
                    continue
                needs_unit = _is_numeric(item.returns) and not item.name.endswith(
                    UNIT_SUFFIXES
                )
                found[item.name] = "needs-unit" if needs_unit else "ok"
    return sorted(found.items())


def main() -> int:
    """Print each reading and its unit verdict, one per line."""
    for name, verdict in readings():
        print(f"{name}\t{verdict}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
