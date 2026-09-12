#!/usr/bin/env python3
"""Check that docs/trades/README.md states each trade the way its record does.

Usage:
    tools/validate-trade-states.py [REPOSITORY_ROOT]

The trade records' frontmatter is the authoritative state. The register page
(``docs/trades/README.md``) is hand-maintained prose, so its status tables drift
from the records when a trade closes and the table is not updated -- which is how
a closed trade gets read as open (GAP-08). This check compares every trade-status
cell in that page's tables against the trade record's ``status`` and fails on any
mismatch, so the drift cannot return silently.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
TRADES_DIR = REPO_ROOT / "docs" / "trades"

_ID_RE = re.compile(r"^id:\s*(TBR-[A-Z]+-[0-9]+)\s*$", re.M)
_STATUS_RE = re.compile(r"^status:\s*([A-Z-]+)\s*$", re.M)
_ROW_ID_RE = re.compile(r"`(TBR-[A-Z]+-[0-9]+)`")


def _frontmatter_states(trades_dir: Path) -> dict[str, str]:
    states: dict[str, str] = {}
    for record in sorted(trades_dir.glob("TBR-*.md")):
        text = record.read_text(encoding="utf-8")
        id_match = _ID_RE.search(text)
        status_match = _STATUS_RE.search(text)
        if id_match and status_match:
            states[id_match.group(1)] = status_match.group(1)
    return states


def validate_repository(root: Path) -> list[str]:
    """Return every trades-page status cell that disagrees with the record."""
    trades_dir = root / "docs" / "trades"
    states = _frontmatter_states(trades_dir)
    if not states:
        return [f"no trade records found under {trades_dir}"]
    statuses = set(states.values())

    errors: list[str] = []
    readme = trades_dir / "README.md"
    for line in readme.read_text(encoding="utf-8").splitlines():
        if not line.lstrip().startswith("|"):
            continue
        id_match = _ROW_ID_RE.search(line)
        if not id_match:
            continue
        trade = id_match.group(1)
        if trade not in states:
            continue
        # The status cell is the first `X` after the id whose X is a real trade
        # status; a priority cell such as `CRITICAL` is not one of these.
        cells = re.findall(r"`([A-Z-]+)`", line)
        stated = next((c for c in cells if c in statuses), None)
        if stated is not None and stated != states[trade]:
            errors.append(
                f"docs/trades/README.md states {trade} as {stated!r}, but its "
                f"record is {states[trade]!r}. Update the table to match the record."
            )
    return errors


def main(argv: list[str]) -> int:
    """Validate one repository root and return a process exit status."""
    if len(argv) > 1:
        usage = "Usage: tools/validate-trade-states.py [REPOSITORY_ROOT]"
        print(usage, file=sys.stderr)
        return 2
    root = Path(argv[0]) if argv else REPO_ROOT
    errors = validate_repository(root)
    if errors:
        for error in errors:
            print(f"FAIL: {error}", file=sys.stderr)
        return 1
    states = _frontmatter_states(root / "docs" / "trades")
    print(f"Trade states: {len(states)} record(s), page matches every stated cell.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
