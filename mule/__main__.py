"""Run the bounded MULE configuration renderer."""

from __future__ import annotations

import sys

from mule.configuration import main

if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
