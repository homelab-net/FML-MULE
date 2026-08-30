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
from datetime import UTC, datetime
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


#: Where the Linux RTC class puts its devices.
RTC_ROOT = Path("/sys/class/rtc")


@dataclass
class SysfsTimeReadings:
    """Time readings from the Linux RTC class and the running clock.

    Satisfies `mule.timekeeping.TimeReadings`. It reads and reports; deciding
    whether retained time can be trusted is `mule.timekeeping.assess`, and
    `FML-ADR-042` is why that split exists.

    **`rtc_backup_cell_ok` always returns `None`, and that is not a stub.** The
    Linux RTC class ABI defines no battery-low attribute. Confirmed on a real
    machine: `/sys/class/rtc/rtc0/` on Debian 13 with `rtc_cmos` exposes
    `date`, `time`, `since_epoch`, `hctosys`, `max_user_freq`, `wakealarm` and
    `name`, and nothing about the cell. `docs/readings.md` records the same
    thing from the ABI.

    That matters more here than anywhere else in this package.
    `FakeClock.dead_backup_cell()` is the scenario `FML-ADR-042` was written
    for and the one the flat-sat exercises hardest, and **a real node cannot
    detect it**. The reading is not missing because nobody wrote it; there is
    nothing to read. A board that exposes a vendor attribute can supply one
    through `backup_cell_probe`, the same way thermal supplies throttling.
    """

    #: Which RTC. TBR-HW-01 selects the board; rtc0 is the class default.
    device: str = "rtc0"
    root: Path = RTC_ROOT
    #: A board-specific way to read cell health, where one exists at all.
    backup_cell_probe: Callable[[], bool | None] | None = None
    #: Whether a trusted upstream has set the clock. `chronyc tracking` is the
    #: source `docs/readings.md` names, and it is a command rather than a
    #: kernel interface, so it is injected rather than shelled out from here.
    #: Absent, this reports False: unable to confirm synchronisation is not the
    #: same as being synchronised, and `assess` treats False as "fall through
    #: to the retained-time checks", which is the fail-closed direction.
    synchronized_probe: Callable[[], bool] | None = None

    def _device_root(self) -> Path:
        return self.root / self.device

    def rtc_present(self) -> bool:
        """Whether a battery-backed real-time clock is fitted and responding."""
        return self._device_root().is_dir()

    def rtc_backup_cell_ok(self) -> bool | None:
        """Backup cell health, or None where the platform cannot report it."""
        if self.backup_cell_probe is None:
            return None
        return self.backup_cell_probe()

    def rtc_time(self) -> datetime | None:
        """Return the RTC's retained time, or None if it gave no reading."""
        # since_epoch rather than parsing date and time separately: one read,
        # no locale, no midnight race between two files.
        try:
            raw = (self._device_root() / "since_epoch").read_text(encoding="utf-8")
        except OSError:
            return None
        try:
            seconds = int(raw.strip())
        except ValueError:
            return None
        # Timezone-aware, always. mule.timekeeping.assess refuses a naive
        # stamp rather than guessing, and the hardware clock is UTC by
        # convention on a node this program controls.
        return datetime.fromtimestamp(seconds, tz=UTC)

    def system_time(self) -> datetime:
        """Return the running system clock, whatever it currently believes."""
        return datetime.now(tz=UTC)

    def synchronized(self) -> bool:
        """Whether time has been set from a source the node trusts."""
        if self.synchronized_probe is None:
            return False
        return self.synchronized_probe()
