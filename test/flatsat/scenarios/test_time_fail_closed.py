"""FML-ADR-042 in the flow: what bad time does to a user trying to connect.

`test_timekeeping.py` checks that the node *decides* correctly. These scenarios
check that the decision is *acted on* at the point where it matters, and that
the refusal reaches the operator rather than appearing as an unexplained
failure to connect.

This is the behaviour most worth having in a flat-sat. It is unwelcome in the
field, it is correct, and it is the easiest thing in the system to regress into
failing open, because failing open makes the symptom disappear.
"""

from __future__ import annotations

import pytest

from ..conftest import EUD, NodeFactory
from ..fakes import FakeClock
from ..timekeeping import TimePolicy

#: One of the services mission/examples/valid-full.json enables.
SERVICE = "example-service-a.example.invalid"

DEGRADING_CLOCKS = [
    FakeClock.restored_from_shutdown,
    FakeClock.dead_backup_cell,
    FakeClock.no_reading,
    FakeClock.stale_before_image,
    FakeClock.implausibly_far_ahead,
    FakeClock.skewed_system_clock,
]
CLOCK_IDS = [
    "no-rtc-restored-from-shutdown",
    "dead-backup-cell",
    "rtc-returns-nothing",
    "retained-time-predates-the-image",
    "retained-time-beyond-the-horizon",
    "system-clock-disagrees-with-rtc",
]


@pytest.mark.parametrize("build_clock", DEGRADING_CLOCKS, ids=CLOCK_IDS)
def test_admission_fails_closed_on_every_untrustworthy_clock(
    build_node: NodeFactory, time_policy: TimePolicy, build_clock: object
) -> None:
    """Trust validation shall not fail open on invalid time. Any invalid time.

    Parametrized over every way the node can lose confidence in its clock, so
    that a new failure mode cannot be added to `assess` and quietly left
    unwired from admission.
    """
    node = build_node(clock=build_clock(time_policy))  # type: ignore[operator]

    boot = node.power_on()
    assert boot.time_degraded
    assert boot.booted, "a degraded clock does not prevent boot; it prevents trust"

    admission = node.admit(EUD)
    assert not admission.admitted
    assert admission.reason is not None
    assert admission.reason.startswith("TIME_DEGRADED")


def test_a_refused_device_reaches_nothing(
    build_node: NodeFactory, time_policy: TimePolicy
) -> None:
    """A refusal has to hold downstream, not only at the admission call."""
    node = build_node(clock=FakeClock.dead_backup_cell(time_policy))
    node.power_on()
    node.admit(EUD)

    assert node.resolve_service(SERVICE, EUD) is None


def test_the_operator_is_told_why(
    build_node: NodeFactory, time_policy: TimePolicy
) -> None:
    """A refusal to validate has to be diagnosable rather than mysterious."""
    node = build_node(clock=FakeClock.dead_backup_cell(time_policy))
    node.power_on()
    status = node.status()

    assert status.state == "DEGRADED"
    assert status.fault is not None
    assert status.fault.startswith("TIME_DEGRADED")
    assert "backup cell" in status.fault


def test_an_already_admitted_device_keeps_its_session(
    build_node: NodeFactory, time_policy: TimePolicy
) -> None:
    """Recorded so it is a decision rather than an accident.

    Losing clock credibility refuses **new** admissions; it does not tear down
    a device already on the network. Network admission and continuous trust are
    different things, and revoking live sessions on a clock fault would take a
    team off the air for a dead coin cell.

    When session revalidation exists this test should be revisited, not
    deleted: it is the record of what the node does today.
    """
    clock = FakeClock.credible(time_policy)
    node = build_node(clock=clock)
    node.power_on()
    assert node.admit(EUD).admitted

    clock.backup_cell = False

    assert node.resolve_service(SERVICE, EUD) == "local"
    assert not node.admit("eud-example-03").admitted


def test_a_clock_that_goes_bad_after_boot_still_refuses(
    build_node: NodeFactory, time_policy: TimePolicy
) -> None:
    """Credibility is judged when it is used, not cached from boot.

    A node that evaluated its clock once at power on would keep admitting
    devices for as long as it stayed up, which is precisely the fail-open this
    ADR exists to prevent.
    """
    clock = FakeClock.credible(time_policy)
    node = build_node(clock=clock)
    node.power_on()
    assert node.admit(EUD).admitted

    clock.backup_cell = False  # the cell fails while the node is running

    assert not node.admit("eud-example-02").admitted
    assert node.status().state == "DEGRADED"
