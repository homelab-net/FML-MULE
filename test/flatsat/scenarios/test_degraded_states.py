"""Scenarios where the node is not healthy.

Every scenario in `test_v001_flow.py` builds a working node, and a suite that
only ever sees a working node cannot tell correct reporting from a status
surface that answers "fine" to everything. Mutation testing showed exactly
that: hardcoding battery, network, LoRa and thermal to healthy values passed
the whole suite. These scenarios are the other half.

The operator questions in CONOPS section 67 are only worth asking if a bad
answer is reachable. Each test below makes one of them answer badly.
"""

from __future__ import annotations

import pytest

from mule.timekeeping import TimePolicy

from ..conftest import EUD, NodeFactory
from ..fakes import (
    FakeClock,
    FakePower,
    FakeRadio,
    FakeThermal,
    ImpossibleHardwareState,
)
from ..node import REPO_ROOT, REQUIRED_BEARERS

UNRESOLVABLE_REGION = REPO_ROOT / "regions" / "us-915" / "profile.yml"

#: One of the services mission/examples/valid-full.json enables, under the
#: local domain that package names.
SERVICE = "example-service-a.example.invalid"


# --- thermal -------------------------------------------------------------


def test_a_sensor_outside_its_envelope_raises_a_fault(
    build_node: NodeFactory,
) -> None:
    node = build_node(thermal=FakeThermal(in_envelope=False))
    node.power_on()
    status = node.status()

    assert status.fault is not None
    assert status.fault.startswith("THERMAL_DEGRADED")
    assert status.state == "DEGRADED"


def test_thermal_throttling_degrades_the_node_without_a_fault(
    build_node: NodeFactory,
) -> None:
    """Throttling is not a fault: the node is working, just more slowly.

    Reporting it as GREEN would hide the most common cause of a node that is
    up but inexplicably slow.
    """
    node = build_node(thermal=FakeThermal(is_throttled=True))
    node.power_on()
    status = node.status()

    assert status.fault is None
    assert status.state == "DEGRADED"


# --- power ---------------------------------------------------------------


@pytest.mark.parametrize(
    ("power", "expected"),
    [
        (FakePower(battery=False), None),
        (FakePower(battery=True, healthy=True), True),
        (FakePower(battery=True, healthy=False), False),
    ],
    ids=["no-pack-fitted", "pack-healthy", "pack-unhealthy"],
)
def test_battery_health_reports_all_three_answers(
    build_node: NodeFactory, power: FakePower, expected: bool | None
) -> None:
    """None, True and False are three different answers, not two.

    None means no pack is fitted and the question does not apply. Collapsing it
    into False would report a healthy mains-powered node as having a bad
    battery.
    """
    node = build_node(power=power)
    node.power_on()

    assert node.status().battery_healthy is expected


def test_projected_runtime_stays_unanswerable(build_node: NodeFactory) -> None:
    """TBR-PWR-01 has not closed, so there is no number to give."""
    node = build_node(power=FakePower(battery=True, healthy=True))
    node.power_on()

    assert node.status().projected_runtime_minutes is None


# --- radio ---------------------------------------------------------------


def test_an_inter_node_bearer_that_will_not_link_degrades_the_network(
    build_node: NodeFactory,
) -> None:
    node = build_node(radio=FakeRadio(present=["halow", "wifi_ap"], linked=["wifi_ap"]))
    node.power_on()

    assert node.status().network_degraded


@pytest.mark.parametrize(
    ("radio", "expected"),
    [
        (FakeRadio(present=["wifi_ap"], linked=["wifi_ap"]), False),
        (FakeRadio(present=["wifi_ap", "lora"], linked=["wifi_ap"]), False),
        (FakeRadio(present=["wifi_ap", "lora"], linked=["wifi_ap", "lora"]), True),
    ],
    ids=["not-fitted", "fitted-not-linked", "fitted-and-linked"],
)
def test_lora_availability_tracks_the_radio(
    build_node: NodeFactory, radio: FakeRadio, expected: bool
) -> None:
    """Track the radio, because LoRa is the degraded-plane bearer.

    Claiming it when it is not fitted is being wrong at the worst moment.
    """
    node = build_node(radio=radio)
    node.power_on()

    assert node.status().lora_available is expected


def test_a_node_with_no_access_point_is_faulted_not_green(
    build_node: NodeFactory,
) -> None:
    """CONOPS section 82 puts "Connect approved EUD" before everything else.

    With no access point there is no user-facing node, whatever else is
    healthy, and a node reporting GREEN in that state is lying to its operator.
    """
    radio = FakeRadio(present=["halow"], linked=["halow"])
    node = build_node(radio=radio)
    node.power_on()
    status = node.status()

    assert not set(REQUIRED_BEARERS) & set(radio.present)

    assert status.state == "FAULT"
    assert status.fault is not None
    assert status.fault.startswith("RADIO_ABSENT")


def test_admission_refused_when_a_required_bearer_is_not_serving(
    build_node: NodeFactory,
) -> None:
    node = build_node(radio=FakeRadio(present=["wifi_ap", "halow"], linked=["halow"]))
    node.power_on()

    admission = node.admit(EUD)

    assert not admission.admitted
    assert admission.reason is not None
    for bearer in REQUIRED_BEARERS:
        assert bearer in admission.reason


# --- boot failure --------------------------------------------------------


def test_a_node_that_never_powered_on_admits_nobody(
    build_node: NodeFactory,
) -> None:
    """Admission before boot is a fail-open waiting to happen."""
    admission = build_node().admit(EUD)

    assert not admission.admitted
    assert admission.reason == "node has not booted"


def test_a_node_whose_configuration_failed_admits_nobody(
    build_node: NodeFactory,
) -> None:
    node = build_node(profile=UNRESOLVABLE_REGION)
    node.power_on()

    assert not node.admit(EUD).admitted
    assert node.status().state == "FAULT"
    assert node.status().operational is False


def test_power_on_clears_the_previous_run(build_node: NodeFactory) -> None:
    """A reboot is a reboot: admissions from the last run do not survive it.

    A device that was admitted before a restart must be admitted again
    afterwards. Carrying the set across would mean a node came back up already
    trusting whoever was connected when it went down, which is a fail-open that
    only shows up after a power cycle in the field.
    """
    node = build_node()
    node.power_on()
    node.admit(EUD)
    assert node.resolve_service(SERVICE, EUD) == "local"

    node.power_on()

    assert node.resolve_service(SERVICE, EUD) is None


# --- the fakes may not lie ------------------------------------------------


def test_a_radio_cannot_be_linked_without_being_present() -> None:
    """The fake refuses to describe hardware that cannot exist.

    Without this, a scenario can pass against a node state no hardware can
    produce, which voids the flat-sat's only real claim.
    """
    with pytest.raises(ImpossibleHardwareState):
        FakeRadio(present=["wifi_ap"], linked=["wifi_ap", "halow"])


def test_a_scripted_failure_reports_the_reading_not_a_verdict(
    time_policy: TimePolicy,
) -> None:
    """A fake supplies readings; `timekeeping.assess` decides what they mean.

    `test_integrity.py` guards the absence of a verdict method. This checks the
    other half: the scripted failure really is a physical state, so the
    scenarios above are exercising the decision rather than selecting it.
    """
    assert FakeClock.dead_backup_cell(time_policy).rtc_backup_cell_ok() is False
