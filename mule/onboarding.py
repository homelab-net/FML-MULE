"""Decide whether the temporary onboarding access network is available.

The onboarding BSS is not the operational EUD network. It exists only to let
an unadmitted EUD reach enrollment, so every associated station remains
isolated and the only permitted destination is the enrollment endpoint.

`FML-ADR-084` makes discovery a time-bounded mission decision. The SSID is
broadcast while the mission-supplied onboarding credential is valid. At its
expiry, or whenever the node cannot establish credible time, new associations
are refused and the SSID is hidden. Hiding is not treated as a security
control; credential invalidation and the quarantine boundary are.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

from .timekeeping import TimeAssessment


class OnboardingState(StrEnum):
    """The only two access states the onboarding BSS may expose."""

    CLOSED = "CLOSED"
    QUARANTINED = "QUARANTINED"


@dataclass(frozen=True)
class OnboardingDecision:
    """How the onboarding BSS shall behave and why."""

    state: OnboardingState
    broadcast_ssid: bool
    accepting_associations: bool
    client_isolated: bool
    enrollment_only: bool
    reason: str | None


def parse_expiry(value: object) -> datetime | None:
    """Parse the mission's UTC RFC 3339 expiry, or return None on doubt."""
    if not isinstance(value, str):
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    return parsed if parsed.tzinfo is not None else None


def _closed(reason: str) -> OnboardingDecision:
    """Return the fail-closed onboarding posture."""
    return OnboardingDecision(
        state=OnboardingState.CLOSED,
        broadcast_ssid=False,
        accepting_associations=False,
        client_isolated=True,
        enrollment_only=True,
        reason=reason,
    )


def decide(
    *,
    booted: bool,
    time: TimeAssessment,
    now: datetime | None,
    expires_at: datetime | None,
    credential_ref: str | None,
) -> OnboardingDecision:
    """Decide whether onboarding is active, failing closed on every doubt."""
    if not booted:
        return _closed("node has not booted")

    if time.degraded:
        return _closed(f"TIME_DEGRADED: {time.reason}")

    if not credential_ref:
        return _closed("mission supplies no onboarding credential reference")

    if now is None or expires_at is None:
        return _closed("onboarding time or expiry is unavailable")

    if now.tzinfo is None or expires_at.tzinfo is None:
        return _closed("onboarding timestamps require a timezone")

    if now >= expires_at:
        return _closed("onboarding credential expired")

    return OnboardingDecision(
        state=OnboardingState.QUARANTINED,
        broadcast_ssid=True,
        accepting_associations=True,
        client_isolated=True,
        enrollment_only=True,
        reason=None,
    )
