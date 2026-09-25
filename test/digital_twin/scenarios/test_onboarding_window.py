"""The onboarding BSS is discoverable only inside its approved time window."""

from __future__ import annotations

from datetime import timedelta

from mule.onboarding import OnboardingState
from mule.timekeeping import TimePolicy

from ..conftest import NodeFactory
from ..fakes import FakeClock


def test_active_onboarding_is_broadcast_but_quarantined(
    build_node: NodeFactory,
) -> None:
    node = build_node()
    node.power_on()

    decision = node.onboarding()

    assert decision.state is OnboardingState.QUARANTINED
    assert decision.broadcast_ssid
    assert decision.client_isolated
    assert decision.enrollment_only


def test_expired_onboarding_is_hidden_and_refuses_new_associations(
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
    assert not decision.broadcast_ssid
    assert not decision.accepting_associations


def test_untrusted_time_hides_and_closes_an_unexpired_window(
    build_node: NodeFactory,
    time_policy: TimePolicy,
) -> None:
    node = build_node(clock=FakeClock.dead_backup_cell(time_policy))
    node.power_on()

    decision = node.onboarding()

    assert decision.state is OnboardingState.CLOSED
    assert not decision.broadcast_ssid
    assert not decision.accepting_associations
    assert decision.reason is not None
    assert decision.reason.startswith("TIME_DEGRADED")
