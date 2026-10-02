"""Give each upstream EUD connection its own mutable bookkeeping.

FML-ADR-048 / TBR-HA-01: preserve stock TAK fields and routing while fixing
the connection lifecycle defect encountered during prototype recovery tests.
The version-specific anchor fails closed if upstream changes its constructor.
"""

from importlib.metadata import distribution

ANCHOR = (
    "    def __init__(self, request: socket, client_address, server):\n"
    "        super().__init__(request, client_address, server)\n"
)
REPLACEMENT = (
    "    def __init__(self, request: socket, client_address, server):\n"
    "        self.cached_messages = []\n"
    "        self.bound_queues = []\n"
    "        self.group_memberships = []\n"
    "        super().__init__(request, client_address, server)\n"
)


def isolate_handler_state(source: str) -> str:
    """Initialize instance lists before BaseRequestHandler dispatches setup."""
    if source.count(REPLACEMENT) == 1 and ANCHOR not in source:
        return source
    if source.count(ANCHOR) != 1:
        raise ValueError("Unsupported upstream EudHandler constructor")
    return source.replace(ANCHOR, REPLACEMENT, 1)


def main() -> None:
    """Apply the bounded integration fix to the installed upstream package."""
    path = distribution("opentakserver").locate_file(
        "opentakserver/eud_handler/EudHandler.py"
    )
    path.write_text(isolate_handler_state(path.read_text()))


if __name__ == "__main__":
    main()
