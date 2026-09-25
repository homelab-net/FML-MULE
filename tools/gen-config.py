#!/usr/bin/env python3
"""Resolve node configuration through the packaged MULE runtime.

Usage:
    tools/gen-config.py --region <id-or-path> --mission <path> [--out <dir>]
    tools/gen-config.py --region <id-or-path> --mission <path> --check

FML-ADR-083 puts node-time configuration decisions in ``mule.configuration``.
This builder-side command remains as a compatibility wrapper for operators and
repository checks; it contains no second implementation.
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from mule.configuration import main  # noqa: E402

if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
