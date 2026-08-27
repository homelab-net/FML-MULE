"""The v0.0.1 flow: power on, connect, authenticate, reach a service.

This is the flat-sat's first target, and it is deliberately the same flow as the
`ROADMAP.md` v0.0.1 acceptance criterion: one node, one service, reachable from
a client. Verifying it here means the end-to-end logic is exercised before
hardware is scarce and expensive, not after.

The flow under test is CONOPS section 82:

    power on -> connect -> authenticate -> authorized services appear -> work

Everything below runs against the fakes in `fakes.py` and the synthetic region
fixture in `test/fixtures/regions/`. A pass yields `SIMULATED`. It says the
software is correct and the user flow is coherent. It says nothing whatsoever
about RF, power, thermal, timing under load, or driver behaviour.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from ..fakes import FakeClock, FakePower, FakeRadio, FakeThermal
from ..node import REPO_ROOT, FlatSatNode

FIXTURE_REGIONS = REPO_ROOT / "test" / "fixtures" / "regions" / "xx-testfixture"
GOOD_PROFILE = FIXTURE_REGIONS / "profile.yml"
MISSION = REPO_ROOT / "mission" / "examples" / "valid-minimal.json"

EUD = "eud-example-01"


def build_node(
    *,
    profile: Path = GOOD_PROFILE,
    clock: FakeClock | None = None,
    radio: FakeRadio | None = None,
    power: FakePower | None = None,
    thermal: FakeThermal | None = None,
    emcon: bool = False,
) -> FlatSatNode:
    """Compose a node with the default healthy fakes, overriding as asked."""
    return FlatSatNode(
        region_profile=profile,
        mission_package=MISSION,
        radio=radio or FakeRadio(),
        power=power or FakePower(),
        thermal=thermal or FakeThermal(),
        clock=clock or FakeClock(),
        emcon=emcon,
    )


# --- the happy path ------------------------------------------------------


def test_power_on_resolves_configuration_and_brings_up_radios() -> None:
    node = build_node()

    boot = node.power_on()

    assert boot.booted
    assert boot.config_resolved
    assert boot.config_error is None
    assert not boot.time_degraded
    assert set(boot.radios_enumerated) == {"halow", "wifi_ap", "lora"}


def test_resolved_parameters_come_from_the_region_profile() -> None:
    """Region is a parameter, not a constant.

    The node holds no channel of its own. Every value below is traceable to the
    profile it was generated from, which is the property that lets one image
    serve several regions.
    """
    node = build_node()
    node.power_on()

    params = node.parameters
    assert params is not None
    assert params["region"]["id"] == "xx-testfixture"
    assert params["halow"]["channel"] == 905000000
    assert params["wifi"]["ap_channel"] == 36
    assert params["amateur"]["enabled"] is False


def test_end_user_device_is_admitted_and_reaches_the_service() -> None:
    """CONOPS section 82, end to end.

    An operator powers the node on, a device associates and is admitted, and the
    service the user was told about resolves and answers.
    """
    node = build_node()
    node.power_on()

    admission = node.admit(EUD)
    assert admission.admitted
    assert admission.reason is None

    assert node.resolve_service("portal.field", EUD) == "local"


def test_status_answers_the_thirteen_conops_questions() -> None:
    """CONOPS section 67: one screen, thirteen questions, no jargon.

    Several answers are `None`. That is the honest value, not a missing one:
    projected runtime has no power model (TBR-PWR-01), and authority state has
    no continuity mechanism (TBR-TAK-01, TBR-HA-01). The assertions below hold
    the tool to answering `None` rather than inventing a number a reader would
    quote later.
    """
    node = build_node()
    node.power_on()
    status = node.status()

    assert status.operational
    assert status.state == "GREEN"
    assert status.fault is None
    assert not status.network_degraded
    assert status.lora_available
    assert not status.wan_available
    assert not status.emcon_active

    # Unanswerable today, and answered as such.
    assert status.projected_runtime_minutes is None
    assert status.hosting_reduces_runtime is None
    assert status.shared_data_authoritative is None
    assert status.data_stale is None

    # Nothing shared is hosted: the TAK service plane waits on TBR-TAK-01.
    assert not status.hosting_shared_services
    assert not status.tak_available
    assert status.authority_reason == "NO_SAFE_AUTHORITY"


# --- fail closed on time -------------------------------------------------


@pytest.mark.parametrize(
    ("clock", "expected_fragment"),
    [
        (FakeClock.dead_backup_cell(), "RTC backup cell depleted"),
        (FakeClock.restored_from_shutdown(), "restored from last shutdown"),
    ],
    ids=["dead-backup-cell", "restored-from-shutdown"],
)
def test_admission_fails_closed_when_time_is_not_credible(
    clock: FakeClock, expected_fragment: str
) -> None:
    """FML-ADR-042: trust validation shall not fail open on invalid time.

    This is the behaviour most worth having in a flat-sat. It is unwelcome in
    the field, it is correct, and it is the easiest thing in the system to
    regress into failing open, because failing open makes the symptom disappear.
    """
    node = build_node(clock=clock)

    boot = node.power_on()
    assert boot.time_degraded
    assert boot.booted, "a degraded clock does not prevent boot; it prevents trust"

    admission = node.admit(EUD)
    assert not admission.admitted
    assert admission.reason is not None
    assert admission.reason.startswith("TIME_DEGRADED")
    assert expected_fragment in admission.reason


def test_refused_device_reaches_nothing() -> None:
    """A refusal has to hold downstream, not only at the admission call."""
    node = build_node(clock=FakeClock.dead_backup_cell())
    node.power_on()
    node.admit(EUD)

    assert node.resolve_service("portal.field", EUD) is None


def test_degraded_time_is_visible_to_the_operator() -> None:
    """A refusal to validate has to be diagnosable rather than mysterious."""
    node = build_node(clock=FakeClock.dead_backup_cell())
    node.power_on()
    status = node.status()

    assert status.state == "DEGRADED"
    assert status.fault is not None
    assert status.fault.startswith("TIME_DEGRADED")


# --- configuration refusal gates transmission ----------------------------


def test_unresolvable_region_stops_the_node_before_any_radio_comes_up() -> None:
    """No region profile in `regions/` is resolvable, and that is correct.

    A node that cannot resolve a lawful channel does not transmit. The failure
    names the trade that will supply the missing value, so the reader knows who
    to ask rather than being invited to guess.
    """
    node = build_node(profile=REPO_ROOT / "regions" / "us-915" / "profile.yml")

    boot = node.power_on()

    assert not boot.booted
    assert not boot.config_resolved
    assert boot.radios_enumerated == []
    assert boot.config_error is not None
    assert "TBD" in boot.config_error
    assert "TBR-RF-02" in boot.config_error


def test_out_of_band_profile_is_rejected_rather_than_generated() -> None:
    """A generated channel outside the permitted band is a regulatory problem.

    The fixture puts the HaLow channel outside the band the same fixture
    permits. The tool rejects it; the node does not come up.
    """
    node = build_node(profile=FIXTURE_REGIONS / "profile-out-of-band.yml")

    boot = node.power_on()

    assert not boot.booted
    assert boot.config_error is not None
    assert "outside the permitted band" in boot.config_error
    assert boot.radios_enumerated == []


def test_amateur_enabled_profile_is_rejected() -> None:
    """Amateur integration is off by default in every region and stays off here."""
    node = build_node(profile=FIXTURE_REGIONS / "profile-amateur-enabled.yml")

    boot = node.power_on()

    assert not boot.booted
    assert boot.config_error is not None
    assert "amateur" in boot.config_error


def test_no_node_boots_without_a_radio_serving_the_access_point() -> None:
    """Association is not admission, but there is no admission without it."""
    node = build_node(radio=FakeRadio(linked=["halow", "lora"]))
    node.power_on()

    admission = node.admit(EUD)

    assert not admission.admitted
    assert admission.reason == "EUD access point is not serving"


def test_emcon_is_reported_even_when_everything_else_is_healthy() -> None:
    node = build_node(emcon=True)
    node.power_on()
    status = node.status()

    assert status.emcon_active
    assert status.state == "EMCON"
