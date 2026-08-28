"""Reading the node's own hardware through the Linux kernel's sysfs interfaces.

Everywhere else in `mule/` is a decision. This module is the other half: the
code that produces the readings those decisions judge. It touches the real
machine, so it is the first thing that will behave differently on hardware than
it does here.

**What is decided.** The node runs a Debian-family userland (`FML-ADR-022`), and
the kernel's thermal framework exposes every thermal zone at
`/sys/class/thermal/thermal_zone<N>/`, with `temp` in **millidegrees Celsius**
and `type` naming the zone. That is kernel ABI, not a property of any particular
board, and it is the same on a Raspberry Pi, an x86 box and every SBC in
between. It needs no trade to close.

**What is not decided, and cannot be here.** Which zone is the processor and
which is the radio. Zone `type` strings are driver-supplied and not
standardised: one board calls its SoC zone `cpu-thermal`, another
`bcm2711_thermal`, another `soc_thermal`. `TBR-HW-01` selects the board, so the
mapping is **configuration**, supplied per board, never compiled in.

**Throttling has no portable answer at all.** Linux exposes no general "am I
thermally throttled" flag. Raspberry Pi has `vcgencmd get_throttled`; other
platforms have cooling-device states, vendor sysfs, or nothing. So the probe is
injected, and a platform with no signal reports `None` rather than `False`.

**Nothing here has run against real hardware.** Its tests build a synthetic
sysfs tree, which is faithful to the documented interface and says nothing about
any board. A capture from a real node belongs in `test/fixtures/` with the node
identifier, capture date and image build recorded, per `docs/evidence/README.md`.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from .thermal import Sensor

#: The kernel reports thermal zone temperatures in thousandths of a degree.
#: Named because a bare 1000 in a temperature conversion reads as a magic
#: number rather than as the unit the ABI actually uses.
MILLIDEGREES_PER_DEGREE = 1000

#: Where the kernel's thermal framework lives. A parameter so tests can point
#: at a synthetic tree, not because it is expected to move.
THERMAL_ROOT = Path("/sys/class/thermal")


@dataclass(frozen=True)
class ZoneMap:
    """Which kernel thermal zone corresponds to which physical sensor.

    Per board, and unknowable in advance. Zone `type` strings come from whatever
    driver registered the zone, and no standard governs them. `TBR-HW-01`
    selects the board; until then this is empty, and an empty map means the node
    reports no temperatures rather than guessing which zone is its processor.

    Matching is on the zone's `type` string, not its number. Zone numbering
    depends on driver probe order and can move between kernel versions, which is
    exactly the kind of thing that works on the bench and fails after an update.
    """

    #: (zone type string, the sensor it is) pairs.
    zones: tuple[tuple[str, Sensor], ...] = ()

    def sensor_for(self, zone_type: str) -> Sensor | None:
        """Return the sensor this zone type is, or None if it is unmapped."""
        for candidate, sensor in self.zones:
            if candidate == zone_type:
                return sensor
        return None


def _read_zone_temperature(zone: Path) -> float | None:
    """Read one zone's temperature in degrees Celsius, or None if it will not.

    A thermal zone can fail to read: the driver may return an error, the file
    may be unreadable, or the value may not parse. None distinguishes "fitted
    and silent" from "not fitted", which `mule/thermal.py` treats differently.
    """
    try:
        raw = (zone / "temp").read_text(encoding="utf-8").strip()
    except OSError:
        return None
    try:
        return int(raw) / MILLIDEGREES_PER_DEGREE
    except ValueError:
        return None


def _read_zone_type(zone: Path) -> str | None:
    """Read one zone's driver-supplied type string."""
    try:
        return (zone / "type").read_text(encoding="utf-8").strip()
    except OSError:
        return None


class SysfsThermalReadings:
    """Thermal readings from the Linux thermal framework.

    Satisfies `mule.thermal.ThermalReadings`. It reads and reports; deciding
    what the numbers mean is `mule.thermal.assess`.
    """

    def __init__(
        self,
        zone_map: ZoneMap,
        *,
        root: Path = THERMAL_ROOT,
        throttling_probe: Callable[[], bool | None] | None = None,
    ) -> None:
        """Compose a reader for one board's zone layout.

        `throttling_probe` is injected because Linux has no portable throttle
        signal. Supplying none means this platform cannot answer, which is
        reported as None rather than as "not throttling".
        """
        self._zone_map = zone_map
        self._root = root
        self._throttling_probe = throttling_probe

    def temperatures_c(self) -> dict[Sensor, float | None]:
        """Every mapped sensor the kernel exposes, with its current reading.

        A sensor absent from the result is one no present zone maps to, which
        means not fitted. A sensor present with None is fitted and did not
        answer.
        """
        # Path.glob returns empty for a missing or non-directory root rather
        # than raising, so there is no error branch here to write. A container
        # with no thermal framework, which is where this was developed, simply
        # yields no zones. Guarding it would be unreachable code that reads
        # like a safety net.
        readings: dict[Sensor, float | None] = {}
        for zone in sorted(self._root.glob("thermal_zone*")):
            zone_type = _read_zone_type(zone)
            if zone_type is None:
                continue
            sensor = self._zone_map.sensor_for(zone_type)
            if sensor is None:
                continue
            readings[sensor] = _read_zone_temperature(zone)
        return readings

    def throttling_reported(self) -> bool | None:
        """Whether the platform says it is throttling, or None if it cannot."""
        if self._throttling_probe is None:
            return None
        return self._throttling_probe()
