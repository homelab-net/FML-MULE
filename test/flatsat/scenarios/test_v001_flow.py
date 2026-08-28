"""The v0.0.1 flow: power on, connect, reach a service.

This is the flat-sat's first target, and it is deliberately the same flow as the
`ROADMAP.md` v0.0.1 acceptance criterion: one node, one service, reachable from
a client.

**What this file does not cover, and must not be read as covering.** CONOPS
section 82 runs power on -> connect -> **authenticate** -> **authorized services
appear** -> **operate**. There is no authentication, no authorization and no
request/response here, because the node has none: see the "Not covered" section
of `test/flatsat/README.md`, which names each gap and the trade blocking it.
What is covered is power on, configuration resolution, bearer bring-up, and
whether the services a mission package enables are the services a device can
resolve.

A pass yields `SIMULATED`. It says nothing about RF, power, thermal, timing
under load, or driver behaviour.
"""

from __future__ import annotations

from ..conftest import EUD, FIXTURE_REGIONS, MISSION_MINIMAL, NodeFactory
from ..fakes import FakeRadio
from ..node import REPO_ROOT

#: The services `mission/examples/valid-full.json` enables, under the local
#: domain that same package names. Written here as the expected *result* of
#: reading the package, not as configuration: if the package changes, this
#: assertion is meant to fail.
EXPECTED_SERVICES = {
    "example-service-a.example.invalid",
    "example-service-b.example.invalid",
}


# --- the happy path ------------------------------------------------------


def test_power_on_resolves_configuration_and_brings_up_radios(
    build_node: NodeFactory,
) -> None:
    radio = FakeRadio()
    boot = build_node(radio=radio).power_on()

    assert boot.booted
    assert boot.config_resolved
    assert boot.config_error is None
    assert not boot.time_degraded
    # The bearers that came up are the bearers the hardware had, asserted
    # against the fake rather than against a list repeated from it.
    assert set(boot.radios_enumerated) == set(radio.present)


def test_resolved_parameters_come_from_the_region_profile(
    build_node: NodeFactory,
) -> None:
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


def test_the_node_serves_what_the_mission_package_enables(
    build_node: NodeFactory,
) -> None:
    """Services are deployment data, not a list compiled into the node.

    The node is asked for names it could only know by reading the package, and
    the package is the one artifact a deployment actually edits.
    """
    node = build_node()
    node.power_on()
    node.admit(EUD)

    for name in EXPECTED_SERVICES:
        assert node.resolve_service(name, EUD) == "local"


def test_a_package_that_enables_no_services_yields_none(
    build_node: NodeFactory,
) -> None:
    """The minimal package is a valid deployment with no mission services.

    A node that invented a default service here would be serving something
    nobody asked for, which is the failure this asserts against.
    """
    node = build_node(mission=MISSION_MINIMAL)
    node.power_on()
    node.admit(EUD)

    for name in EXPECTED_SERVICES:
        assert node.resolve_service(name, EUD) is None
    assert node.resolve_service("portal.field", EUD) is None


def test_an_access_point_only_node_is_healthy(build_node: NodeFactory) -> None:
    """The actual v0.0.1 configuration: no HaLow, no mesh, no LoRa.

    A node with no inter-node bearer is not a degraded mesh node; it is a node
    that was never meant to mesh. Reporting it as degraded forever would make
    the milestone's own hardware look broken.
    """
    node = build_node(radio=FakeRadio(present=["wifi_ap"], linked=["wifi_ap"]))
    node.power_on()
    status = node.status()

    assert status.state == "GREEN"
    assert status.fault is None
    assert not status.network_degraded
    assert not status.lora_available


def test_status_answers_the_thirteen_conops_questions(
    build_node: NodeFactory,
) -> None:
    """CONOPS section 67: one screen, thirteen questions, no jargon.

    All thirteen are asserted. Several answers are `None`, which is the honest
    value rather than a missing one: projected runtime has no power model
    (TBR-PWR-01), and authority state has no continuity mechanism (TBR-TAK-01,
    TBR-HA-01).
    """
    node = build_node()
    node.power_on()
    status = node.status()

    assert status.operational  # 1
    assert status.battery_healthy is None  # 2, no pack fitted
    assert status.projected_runtime_minutes is None  # 3
    assert not status.hosting_shared_services  # 4
    assert status.hosting_reduces_runtime is None  # 5
    assert not status.tak_available  # 6
    assert status.shared_data_authoritative is None  # 7
    assert status.data_stale is None  # 8
    assert not status.network_degraded  # 9
    assert status.lora_available  # 10
    assert not status.wan_available  # 11
    assert not status.emcon_active  # 12
    assert status.fault is None  # 13

    assert status.state == "GREEN"
    assert status.authority_reason == "NO_SAFE_AUTHORITY"


# --- configuration refusal gates transmission ----------------------------


def test_unresolvable_region_stops_the_node_before_any_radio_comes_up(
    build_node: NodeFactory,
) -> None:
    """No region profile in `regions/` is resolvable, and that is correct.

    A node that cannot resolve a lawful channel does not transmit. The failure
    names the trade that will supply the missing value, so the reader knows who
    to ask rather than being invited to guess.
    """
    boot = build_node(
        profile=REPO_ROOT / "regions" / "us-915" / "profile.yml"
    ).power_on()

    assert not boot.booted
    assert not boot.config_resolved
    assert boot.radios_enumerated == []
    assert boot.config_error is not None
    assert "TBD" in boot.config_error
    assert "TBR-RF-02" in boot.config_error


def test_out_of_band_profile_is_rejected_rather_than_generated(
    build_node: NodeFactory,
) -> None:
    """A generated channel outside the permitted band is a regulatory problem."""
    boot = build_node(profile=FIXTURE_REGIONS / "profile-out-of-band.yml").power_on()

    assert not boot.booted
    assert boot.config_error is not None
    assert "outside the permitted band" in boot.config_error
    assert boot.radios_enumerated == []


def test_amateur_enabled_profile_is_rejected(build_node: NodeFactory) -> None:
    """Amateur integration is off by default in every region and stays off."""
    boot = build_node(
        profile=FIXTURE_REGIONS / "profile-amateur-enabled.yml"
    ).power_on()

    assert not boot.booted
    assert boot.config_error is not None
    assert "amateur" in boot.config_error


def test_emcon_is_reported_even_when_everything_else_is_healthy(
    build_node: NodeFactory,
) -> None:
    node = build_node(emission="EMCON-SILENT")
    node.power_on()
    status = node.status()

    assert status.emcon_active
    assert status.state == "EMCON"
