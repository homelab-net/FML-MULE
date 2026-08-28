"""Tests for the Linux thermal reader.

These build a **synthetic sysfs tree**. That is faithful to the kernel's
documented interface - `thermal_zone<N>/temp` in millidegrees Celsius and
`thermal_zone<N>/type` naming the zone - and says nothing whatever about any
board. A capture from real hardware belongs in `test/fixtures/`, and none
exists.

What these do establish: the reader parses the ABI correctly, survives the ways
a zone can fail to answer, and refuses to guess which zone is which.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from mule.sysfs import MILLIDEGREES_PER_DEGREE, SysfsThermalReadings, ZoneMap
from mule.thermal import Sensor, assess

from .conftest import FIXTURE_THERMAL_LIMITS

#: Zone type strings are driver-supplied. These are plausible shapes, chosen to
#: differ from each other; no board is claimed to use them.
CPU_ZONE = "cpu-thermal"
RADIO_ZONE = "wifi-thermal"

FIXTURE_MAP = ZoneMap(zones=((CPU_ZONE, "processor"), (RADIO_ZONE, "radio")))


def build_sysfs(tmp_path: Path, zones: dict[str, str | None]) -> Path:
    """Write a synthetic /sys/class/thermal tree.

    `zones` maps a zone type string to its raw `temp` contents, or None to omit
    the `temp` file entirely, which is how a zone that will not read behaves.
    """
    root = tmp_path / "thermal"
    root.mkdir()
    for index, (zone_type, raw) in enumerate(zones.items()):
        zone = root / f"thermal_zone{index}"
        zone.mkdir()
        (zone / "type").write_text(zone_type, encoding="utf-8")
        if raw is not None:
            (zone / "temp").write_text(raw, encoding="utf-8")
    return root


# --- parsing the ABI ------------------------------------------------------


def test_millidegrees_are_converted_to_degrees(tmp_path: Path) -> None:
    """The kernel reports thousandths. Getting this wrong is off by 1000.

    A node that read 48250 as degrees rather than 48.25 would breach every
    limit instantly and fault a healthy machine.
    """
    root = build_sysfs(tmp_path, {CPU_ZONE: "48250"})

    readings = SysfsThermalReadings(FIXTURE_MAP, root=root).temperatures_c()

    assert readings == {"processor": 48250 / MILLIDEGREES_PER_DEGREE}
    assert readings["processor"] == pytest.approx(48.25)


def test_a_negative_reading_is_read_as_negative(tmp_path: Path) -> None:
    """Cold is a normal field condition, not an error.

    CONOPS section 61 makes cold-weather behaviour first-order. A reader that
    mishandled the sign would be wrong exactly when it matters most.
    """
    root = build_sysfs(tmp_path, {CPU_ZONE: "-15000"})

    readings = SysfsThermalReadings(FIXTURE_MAP, root=root).temperatures_c()

    assert readings["processor"] == pytest.approx(-15.0)


def test_zones_are_matched_by_type_not_by_number(tmp_path: Path) -> None:
    """Zone numbering depends on driver probe order and moves between kernels.

    Matching on the number is the kind of thing that works on the bench and
    fails after a kernel update, which FML-ADR-040 exists to prevent shipping.
    """
    root = build_sysfs(tmp_path, {RADIO_ZONE: "40000", CPU_ZONE: "50000"})

    readings = SysfsThermalReadings(FIXTURE_MAP, root=root).temperatures_c()

    # radio is thermal_zone0 here and processor is thermal_zone1.
    assert readings == {"radio": 40.0, "processor": 50.0}


# --- the ways a zone fails to answer --------------------------------------


def test_a_zone_that_will_not_read_reports_none_not_absence(
    tmp_path: Path,
) -> None:
    """Fitted and silent is not the same as not fitted.

    mule/thermal.py treats them differently, so the reader has to keep them
    apart rather than dropping the sensor.
    """
    root = build_sysfs(tmp_path, {CPU_ZONE: None})

    readings = SysfsThermalReadings(FIXTURE_MAP, root=root).temperatures_c()

    assert readings == {"processor": None}


def test_a_zone_with_no_type_file_is_skipped(tmp_path: Path) -> None:
    """An unnameable zone cannot be mapped, so it is passed over.

    Not every directory under the thermal root is a well-formed zone, and a
    reader that assumed otherwise would fail on the first board that had one.
    """
    root = build_sysfs(tmp_path, {CPU_ZONE: "50000"})
    malformed = root / "thermal_zone9"
    malformed.mkdir()
    (malformed / "temp").write_text("70000", encoding="utf-8")

    readings = SysfsThermalReadings(FIXTURE_MAP, root=root).temperatures_c()

    assert readings == {"processor": 50.0}


def test_an_unreadable_type_file_is_skipped(tmp_path: Path) -> None:
    """A zone whose type cannot be read is one nothing can map."""
    root = build_sysfs(tmp_path, {CPU_ZONE: "50000"})
    unreadable = root / "thermal_zone9"
    unreadable.mkdir()
    (unreadable / "type").mkdir()  # a directory where a file belongs
    (unreadable / "temp").write_text("70000", encoding="utf-8")

    readings = SysfsThermalReadings(FIXTURE_MAP, root=root).temperatures_c()

    assert readings == {"processor": 50.0}


def test_an_unparseable_reading_is_none(tmp_path: Path) -> None:
    root = build_sysfs(tmp_path, {CPU_ZONE: "not a number"})

    readings = SysfsThermalReadings(FIXTURE_MAP, root=root).temperatures_c()

    assert readings == {"processor": None}


def test_a_missing_thermal_root_yields_no_readings(tmp_path: Path) -> None:
    """A kernel with no thermal framework, or a container like this one.

    The node reports nothing and mule/thermal.py calls that UNKNOWN. It does
    not crash, and it does not report an absence of heat.
    """
    readings = SysfsThermalReadings(
        FIXTURE_MAP, root=tmp_path / "does-not-exist"
    ).temperatures_c()

    assert readings == {}


# --- refusing to guess ----------------------------------------------------


def test_an_unmapped_zone_is_ignored_rather_than_guessed(
    tmp_path: Path,
) -> None:
    """No standard governs zone type strings, so an unknown one means nothing.

    Assuming thermal_zone0 is the processor is the tempting shortcut, and it is
    how a node ends up judging its radio against a processor's limits.
    """
    root = build_sysfs(tmp_path, {"some-unknown-zone": "70000"})

    readings = SysfsThermalReadings(FIXTURE_MAP, root=root).temperatures_c()

    assert readings == {}


def test_an_empty_map_reports_nothing_however_many_zones_exist(
    tmp_path: Path,
) -> None:
    """The state today: TBR-HW-01 has not selected a board, so there is no map."""
    root = build_sysfs(tmp_path, {CPU_ZONE: "50000", RADIO_ZONE: "60000"})

    readings = SysfsThermalReadings(ZoneMap(), root=root).temperatures_c()

    assert readings == {}


# --- throttling has no portable answer ------------------------------------


def test_a_platform_with_no_throttle_probe_says_it_cannot_tell(
    tmp_path: Path,
) -> None:
    """Linux exposes no general throttle flag, so None is the honest answer.

    Returning False here would assert the node is not throttling on every board
    that has no way to know.
    """
    reader = SysfsThermalReadings(FIXTURE_MAP, root=build_sysfs(tmp_path, {}))

    assert reader.throttling_reported() is None


@pytest.mark.parametrize("reported", [True, False])
def test_an_injected_probe_is_passed_through(tmp_path: Path, reported: bool) -> None:
    reader = SysfsThermalReadings(
        FIXTURE_MAP,
        root=build_sysfs(tmp_path, {}),
        throttling_probe=lambda: reported,
    )

    assert reader.throttling_reported() is reported


# --- it satisfies the interface the decision consumes ---------------------


def test_the_reader_feeds_the_decision(tmp_path: Path) -> None:
    """End to end across the seam: real reader, real decision, synthetic sysfs.

    This is the join the whole design rests on. The reader produces readings
    with no opinion; assess turns them into a state using limits the reader
    knows nothing about.
    """
    _, critical = FIXTURE_THERMAL_LIMITS.for_sensor("processor")
    root = build_sysfs(
        tmp_path, {CPU_ZONE: str(int((critical + 5) * MILLIDEGREES_PER_DEGREE))}
    )
    reader = SysfsThermalReadings(FIXTURE_MAP, root=root)

    result = assess(reader, FIXTURE_THERMAL_LIMITS)

    assert result.state == "CRITICAL"
    assert result.breaches == ("processor",)
    assert result.throttling is None


def test_the_same_reader_says_unknown_with_no_limits(tmp_path: Path) -> None:
    """Which is the state today, on any board, however well instrumented."""
    root = build_sysfs(tmp_path, {CPU_ZONE: "95000"})
    reader = SysfsThermalReadings(FIXTURE_MAP, root=root)

    assert assess(reader, None).state == "UNKNOWN"


def test_sensor_names_come_from_the_shared_vocabulary() -> None:
    """The map cannot invent a sensor mule/thermal.py does not know."""
    mapped: Sensor = "processor"
    assert FIXTURE_MAP.sensor_for(CPU_ZONE) == mapped
    assert FIXTURE_MAP.sensor_for("unmapped") is None
