"""A real `RadioState` reader over `iw` and `batctl`.

`interfaces.py` defines the boundary and `fakes.py` scripts it; this is the
implementation that reads the actual machine. It is built the same way
`mule.sysfs.SysfsThermalReadings` is: an injected per-board map, empty until
`TBR-HW-01` selects a board, and an injected command runner so a test feeds
fixtures and a node runs the real binaries. Nothing here shells out directly and
nothing here is board-specific; both are injected.

**Why this is in the flat-sat and not `mule/`.** The `RadioState` interface is
blocked on `TBR-LINUX-01`, `TBR-RF-01` and `TBR-RF-03` and stays here by the
decision `interfaces.py` records. A reader beside the Protocol is not the
promotion that note prohibits -- it does not relocate the interface into
production -- so it can be built now. It moves to `mule/` with the Protocol when
those trades close.

**`None` is the whole discipline.** Every method returns `None` where the node
cannot tell: a bearer that maps to no interface, or a command that could not
run. `False` and `[]` are real readings from a command that ran. `radio_parse`
keeps that line at the text boundary and this reader keeps it at the semantic
one.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from mule.bearers import Bearer

from . import radio_parse

#: Runs a command and returns its stdout, or `None` if it could not run.
#: A test supplies a lookup over fixtures; a node supplies a subprocess call
#: that returns `None` on a non-zero exit or a missing binary.
CommandRunner = Callable[[list[str]], str | None]


@dataclass
class CommandRadio:
    """`RadioState` read from `iw` and `batctl` through an injected runner.

    `interface_map` is per board -- interface name to the `Bearer` it carries,
    for example `{"wlan0": "halow", "wlan1": "wifi_ap"}` -- and is **empty until
    `TBR-HW-01`**, exactly as `SysfsThermalReadings` takes an empty zone map. An
    empty map is not a fault; it is a node that does not yet know which radio is
    which, and every method then reports `None` or `[]` honestly rather than
    guessing.
    """

    interface_map: dict[str, Bearer]
    run: CommandRunner

    def _interface_for(self, bearer: Bearer) -> str | None:
        for interface, mapped in self.interface_map.items():
            if mapped == bearer:
                return interface
        return None

    def enumerated(self) -> list[Bearer] | None:
        """Bearers whose interface is present, per `iw dev`.

        `None` if `iw dev` could not run. Otherwise the mapped bearers whose
        interface `iw` lists as present -- an empty list where none is, which is
        a real reading and not the same as `None`. An interface `iw` shows that
        maps to no bearer is not a bearer and is not enumerated.
        """
        parsed = radio_parse.interfaces(self.run(["iw", "dev"]))
        if parsed is None:
            return None
        present = {name for name, _type in parsed}
        return [
            bearer
            for interface, bearer in self.interface_map.items()
            if interface in present
        ]

    def associated(self, bearer: Bearer) -> bool | None:
        """Whether the bearer's interface has at least one station.

        A station is a mesh peer or an associated AP client; `iw station dump`
        reports both. So this answers "has this bearer formed a link to another
        node", which for a mesh point is a peer and for an AP is a served client.
        An AP that is up and beaconing with no client reads `False`: it is
        serving, but it has not formed a link, which is what the caller asks.

        `None` where the node cannot tell: the bearer maps to no interface, or
        `iw` could not run. `False` where the interface is present and has no
        station, which is a real reading.
        """
        interface = self._interface_for(bearer)
        if interface is None:
            return None
        count = radio_parse.station_count(
            self.run(["iw", "dev", interface, "station", "dump"])
        )
        if count is None:
            return None
        return count > 0
