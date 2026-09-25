"""The rendered AP config reflects the real onboarding posture across the window.

`FML-ADR-084` requires the digital twin to exercise active, expired and
time-degraded onboarding windows. Here the onboarding decision is produced by the
node's real `decide()` against a `FakeClock` -- never a hand-built decision (the
"fake answers the question" failure) -- and fed to `mule.rendering`, so the test
proves the render tracks the decision, not that a fixture agrees with itself.

The renderable surface is the decided one (GAP-09E slice): the operational radio
block is always present; the onboarding BSS appears only while the window is
active. Credentials, DHCP and multi-BSS topology stay gated and unrendered.
"""

from __future__ import annotations

import json
from datetime import timedelta

from mule import rendering as r
from mule.onboarding import OnboardingState
from mule.timekeeping import TimePolicy

from ..conftest import MISSION_WITH_SERVICES, NodeFactory
from ..fakes import FakeClock

_INTERFACES = {"eud_ap": "wlan0", "onboarding_ap": "wlan0_1"}


def _resolved_from_mission() -> dict:
    """Build a resolved doc for the render from the twin mission + US region."""
    mission = json.loads(MISSION_WITH_SERVICES.read_text(encoding="utf-8"))
    network = mission["network"]
    return {
        "region": {"id": "xx", "regulator": "None", "country_code": "US"},
        "network": {
            "ap_ssid": network["ap_ssid"],
            "onboarding": network["onboarding"],
        },
        "wifi": {
            "ap_channel": 149,
            "permitted_bands": ["2.4GHz", "5GHz"],
            "dfs_required": False,
            "ap_max_eirp_dbm": 36,
        },
    }


def test_active_window_renders_the_broadcast_onboarding_bss(
    build_node: NodeFactory,
) -> None:
    node = build_node()
    node.power_on()

    decision = node.onboarding()
    assert decision.state is OnboardingState.QUARANTINED  # real clock, active window

    out = r.render_hostapd(_resolved_from_mission(), _INTERFACES, decision)

    # Operational block is always present.
    assert "interface=wlan0" in out
    assert "country_code=US" in out
    assert "hw_mode=a" in out
    # Onboarding BSS offered, broadcasting, isolated.
    assert "bss=wlan0_1" in out
    assert "ignore_broadcast_ssid=0" in out
    assert "ap_isolate=1" in out


def test_expired_window_renders_no_onboarding_bss(
    build_node: NodeFactory,
    time_policy: TimePolicy,
) -> None:
    clock = FakeClock.credible(time_policy)
    node = build_node(clock=clock)
    node.power_on()
    clock.system += timedelta(days=2)
    assert clock.rtc is not None
    clock.rtc += timedelta(days=2)

    decision = node.onboarding()
    assert decision.state is OnboardingState.CLOSED

    out = r.render_hostapd(_resolved_from_mission(), _INTERFACES, decision)

    assert "bss=" not in out  # fail-closed: the BSS is not offered
    assert "CLOSED" in out
    # The operational AP is unaffected by the onboarding window.
    assert "interface=wlan0" in out


def test_time_degraded_renders_no_onboarding_bss(
    build_node: NodeFactory,
    time_policy: TimePolicy,
) -> None:
    node = build_node(clock=FakeClock.dead_backup_cell(time_policy))
    node.power_on()

    decision = node.onboarding()
    assert decision.state is OnboardingState.CLOSED

    out = r.render_hostapd(_resolved_from_mission(), _INTERFACES, decision)

    assert "bss=" not in out
    assert "interface=wlan0" in out
