"""Unit tests for the thermal envelope decision.

`mule/thermal.py` is the comparison SAD section 25.7 implies and
`TBR-THERM-01` has not yet supplied numbers for. These exercise it both ways:
with no limits, which is the state of the programme today, and against a
synthetic set, which is the state the day that trade closes.

Every temperature below comes from `FIXTURE_THERMAL_LIMITS` or is chosen
relative to it. None is evidence about any hardware.
"""

from __future__ import annotations

from mule.thermal import assess

from .conftest import FIXTURE_THERMAL_LIMITS
from .fakes import FakeThermal

LIMITS = FIXTURE_THERMAL_LIMITS
COOL = LIMITS.warn_above_c - 10.0
WARM = LIMITS.warn_above_c + 1.0
HOT = LIMITS.critical_above_c + 10.0


# --- what the node can say today ------------------------------------------


def test_with_no_limits_the_state_is_unknown_however_hot_it_is() -> None:
    """Not knowing is not the same as being fine, and not the same as failing.

    A node reading ninety-five degrees with no defined envelope is not inside
    one and is not outside one. It is a node nobody has told what its limits
    are, and UNKNOWN is the only honest word for that.
    """
    result = assess(FakeThermal.at(HOT), None)

    assert result.state == "UNKNOWN"
    assert not result.outside_envelope
    assert result.reason is not None
    assert "TBR-THERM-01" in result.reason


def test_throttling_is_reported_even_when_the_state_is_unknown() -> None:
    """The one thermal fact available without a measured envelope.

    SAD section 25.7 lists throttling among the things measured rather than
    derived, so the hardware states it. Withholding it because the limits are
    unknown would hide the clearest signal the node has.
    """
    result = assess(FakeThermal(is_throttling=True), None)

    assert result.state == "UNKNOWN"
    assert result.throttling


def test_a_node_with_no_reporting_sensors_is_unknown_for_a_different_reason() -> None:
    silent = assess(FakeThermal(sensors={"processor": None}), LIMITS)
    unlimited = assess(FakeThermal.at(COOL), None)

    assert silent.state == unlimited.state == "UNKNOWN"
    assert silent.reason != unlimited.reason
    assert "No sensor reported" in (silent.reason or "")


# --- what it says once TBR-THERM-01 closes --------------------------------


def test_a_cool_node_is_nominal() -> None:
    result = assess(FakeThermal(sensors={"processor": COOL}), LIMITS)

    assert result.state == "NOMINAL"
    assert result.breaches == ()
    assert result.reason is None


def test_a_sensor_over_the_warning_is_warm_but_not_a_breach() -> None:
    result = assess(FakeThermal(sensors={"processor": WARM}), LIMITS)

    assert result.state == "WARM"
    assert not result.outside_envelope
    assert result.breaches == ()


def test_a_sensor_at_its_limit_is_a_breach() -> None:
    """The boundary belongs to the failing side.

    A limit is the temperature at which the envelope ends, not the last one
    inside it. Getting this backwards means a node sitting exactly on its
    critical figure reports itself healthy.
    """
    result = assess(FakeThermal(sensors={"processor": LIMITS.critical_above_c}), LIMITS)

    assert result.state == "CRITICAL"
    assert result.outside_envelope
    assert result.breaches == ("processor",)


def test_per_sensor_limits_apply_where_they_differ() -> None:
    """A battery and a processor do not share an envelope.

    SAD section 25.7 measures them separately, and a single figure across both
    would be wrong in a way that looks entirely reasonable: comfortable for the
    processor and dangerous for the pack.
    """
    _, battery_critical = LIMITS.for_sensor("battery")
    assert battery_critical < LIMITS.critical_above_c

    at_battery_limit = battery_critical + 1.0
    result = assess(
        FakeThermal(
            sensors={"battery": at_battery_limit, "processor": at_battery_limit}
        ),
        LIMITS,
    )

    # The same temperature breaches for one sensor and not the other.
    assert result.breaches == ("battery",)
    assert result.state == "CRITICAL"


def test_breaches_are_ordered_hottest_first() -> None:
    """An operator reads the first one. It should be the worst one."""
    result = assess(
        FakeThermal(sensors={"processor": HOT, "radio": HOT + 20.0}), LIMITS
    )

    assert result.breaches == ("radio", "processor")


def test_the_hottest_sensor_is_reported_whatever_the_state() -> None:
    result = assess(FakeThermal(sensors={"processor": COOL, "radio": WARM}), LIMITS)

    assert result.hottest == ("radio", WARM)


def test_a_sensor_that_did_not_answer_is_not_counted_as_cool() -> None:
    """Absent is not zero. A silent sensor must not lower the hottest reading."""
    result = assess(FakeThermal(sensors={"processor": WARM, "radio": None}), LIMITS)

    assert result.hottest == ("processor", WARM)
    assert result.state == "WARM"
