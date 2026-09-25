"""Report whether this container's listener accepts a connection.

Quadlet runs this as ``HealthCmd``. The address is the container hostname
on the internal network. It is not a loopback dependency.
"""

from __future__ import annotations

import socket
import sys


def main(argv: list[str]) -> int:
    """Exit 0 when ``argv[1]`` accepts a TCP connection."""
    port = int(argv[1])
    with socket.create_connection((socket.gethostname(), port), 2):
        return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
