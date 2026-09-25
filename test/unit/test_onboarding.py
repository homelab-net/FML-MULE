"""Unit tests for the temporary onboarding access-network decision."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from mule.onboarding import OnboardingState, decide, parse_expiry
from mule.timekeeping import TimeAssessment

ACTIVE_AT = datetime(2026, 1, 2, tzinfo=UTC)
EXPIRES_AT = datetime(2026, 1, 3, tzinfo=UTC)
CREDENTIAL_REF = "example-onboarding-reference-not-material"


def test_active_window_broadcasts_only_the_quarantined_network() -> None:
    decision = decide(
        booted=True,
        time=TimeAssessment("CREDIBLE", None),
        now=ACTIVE_AT,
        expires_at=EXPIRES_AT,
        credential_ref=CREDENTIAL_REF,
    )

    assert decision.state is OnboardingState.QUARANTINED
    assert decision.broadcast_ssid
    assert decision.accepting_associations
    assert decision.client_isolated
    assert decision.enrollment_only
    assert decision.reason is None


def test_mission_expiry_parses_as_an_aware_utc_instant() -> None:
    assert parse_expiry("2026-01-03T00:00:00Z") == EXPIRES_AT


@pytest.mark.parametrize("value", [None, 7, "not-a-time", "2026-01-03T00:00:00"])
def test_unusable_mission_expiry_fails_closed_at_the_parser(value: object) -> None:
    assert parse_expiry(value) is None


@pytest.mark.parametrize(
    ("booted", "time", "now", "expires_at", "credential_ref", "reason"),
    [
        (
            False,
            TimeAssessment("CREDIBLE", None),
            ACTIVE_AT,
            EXPIRES_AT,
            CREDENTIAL_REF,
            "node has not booted",
        ),
        (
            True,
            TimeAssessment("DEGRADED", "fixture clock is not credible"),
            ACTIVE_AT,
            EXPIRES_AT,
            CREDENTIAL_REF,
            "TIME_DEGRADED",
        ),
        (
            True,
            TimeAssessment("CREDIBLE", None),
            ACTIVE_AT.replace(tzinfo=None),
            EXPIRES_AT,
            CREDENTIAL_REF,
            "timezone",
        ),
        (
            True,
            TimeAssessment("CREDIBLE", None),
            EXPIRES_AT,
            EXPIRES_AT,
            CREDENTIAL_REF,
            "expired",
        ),
        (
            True,
            TimeAssessment("CREDIBLE", None),
            ACTIVE_AT,
            EXPIRES_AT,
            None,
            "credential reference",
        ),
        (
            True,
            TimeAssessment("CREDIBLE", None),
            ACTIVE_AT,
            None,
            CREDENTIAL_REF,
            "unavailable",
        ),
        (
            True,
            TimeAssessment("CREDIBLE", None),
            None,
            EXPIRES_AT,
            CREDENTIAL_REF,
            "unavailable",
        ),
    ],
    ids=[
        "not-booted",
        "time-degraded",
        "naive-time",
        "expiry-boundary",
        "missing-credential-reference",
        "missing-expiry",
        "missing-current-time",
    ],
)
def test_every_uncertain_or_inactive_state_hides_and_closes(
    booted: bool,
    time: TimeAssessment,
    now: datetime | None,
    expires_at: datetime | None,
    credential_ref: str | None,
    reason: str,
) -> None:
    decision = decide(
        booted=booted,
        time=time,
        now=now,
        expires_at=expires_at,
        credential_ref=credential_ref,
    )

    assert decision.state is OnboardingState.CLOSED
    assert not decision.broadcast_ssid
    assert not decision.accepting_associations
    assert decision.client_isolated
    assert decision.enrollment_only
    assert decision.reason is not None
    assert reason in decision.reason
