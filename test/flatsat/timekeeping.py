"""Decide whether retained local time can be trusted.

`FML-ADR-042`: trust validation shall not fail open on invalid, implausible or
unavailable time. Certificate validity, credential expiry and revocation
freshness all depend on the clock, and SAD section 24.5.1 warns that a node
which restores a plausible-looking time from its last shutdown is **worse** than
one with no clock, because it looks valid.

That warning is the whole reason this module exists. Judging credibility is a
**decision**, and a decision a fake makes on the node's behalf is a decision
nobody has tested. Here the platform supplies raw readings and this code decides
what they mean, so a fake can stimulate the decision but never stand in for it.

**Location note.** This is production code. It lives under `test/flatsat/`
because no production package exists yet, for the reason given in
`interfaces.py`, and moves there unchanged.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Literal, Protocol, runtime_checkable

#: Whether retained local time is trustworthy enough for trust validation.
TimeCredibility = Literal["CREDIBLE", "DEGRADED"]


@runtime_checkable
class TimeReadings(Protocol):
    """Raw readings from the platform's time sources.

    Every method reports what a sensor says. None of them decides what it
    means; that is `assess`. Keeping the split explicit is what makes the
    fail-closed behaviour testable rather than asserted.
    """

    def rtc_present(self) -> bool:
        """Whether a battery-backed real-time clock is fitted and responding."""
        ...

    def rtc_backup_cell_ok(self) -> bool | None:
        """Backup cell health, or None where the platform cannot report it."""
        ...

    def rtc_time(self) -> datetime | None:
        """Return the RTC's retained time, or None if it gave no reading."""
        ...

    def system_time(self) -> datetime:
        """Return the running system clock, whatever it currently believes."""
        ...

    def synchronized(self) -> bool:
        """Whether time has been set from a source the node trusts."""
        ...


@dataclass(frozen=True)
class TimePolicy:
    """The bounds `assess` judges a reading against.

    No field has a default, deliberately. Every value here belongs to
    `TBR-TIME-01`, which has not closed, so there is no defensible default to
    offer and the caller is made to supply one rather than inherit an invented
    number. The flat-sat supplies fixture values; a node will supply measured
    ones once the trade closes.
    """

    #: Build time of the running image. A fact about the artifact, not a policy
    #: choice: nothing the image reads can legitimately predate the image.
    image_build_time: datetime

    #: How far past the build time a retained reading may sit before it is
    #: treated as implausible rather than merely old. `TBR-TIME-01`.
    max_plausible_forward: timedelta

    #: How far the system clock and the RTC may disagree before neither is
    #: trusted. `TBR-TIME-01`.
    max_system_rtc_skew: timedelta


@dataclass(frozen=True)
class TimeAssessment:
    """What `assess` concluded, and why."""

    credibility: TimeCredibility
    reason: str | None

    @property
    def degraded(self) -> bool:
        """Whether trust validation must refuse rather than proceed."""
        return self.credibility == "DEGRADED"


def _degraded(reason: str) -> TimeAssessment:
    """Build a refusal carrying an operator-readable cause."""
    return TimeAssessment("DEGRADED", reason)


def assess(readings: TimeReadings, policy: TimePolicy) -> TimeAssessment:
    """Judge retained time against the policy, failing closed on any doubt.

    The rules are ordered so that the cheapest certainty comes first and the
    plausibility tests run only on a reading that exists. Each returns its own
    reason, because `FML-ADR-042` requires a refusal to be diagnosable rather
    than mysterious.
    """
    # A source the node trusts has set the clock. Nothing retained matters.
    if readings.synchronized():
        return TimeAssessment("CREDIBLE", None)

    if not readings.rtc_present():
        return _degraded(
            "No retained time source. System time was restored from the last "
            "shutdown and cannot be trusted. A plausible-looking time is not a "
            "credible one."
        )

    # None means the platform cannot report cell health. That is not the same
    # as a depleted cell, and it is not by itself a reason to refuse, so the
    # plausibility tests below still get their say.
    if readings.rtc_backup_cell_ok() is False:
        return _degraded(
            "RTC backup cell depleted; retained time is implausible. Trust "
            "validation is refused rather than failing open. Replace the "
            "backup cell and re-establish time."
        )

    retained = readings.rtc_time()
    if retained is None:
        return _degraded(
            "RTC is present but returned no reading. Time is unavailable, and "
            "unavailable time fails closed."
        )

    # A naive datetime cannot be compared with an aware one: Python raises
    # TypeError. In trust-validation code that is a crash where a refusal
    # belongs, so the mismatch is caught and refused. FML-ADR-042 says never
    # fail open on unavailable time, and a time nobody can compare is
    # unavailable for this purpose.
    stamps = (retained, readings.system_time(), policy.image_build_time)
    if any(stamp.tzinfo is None for stamp in stamps):
        return _degraded(
            "A timestamp carries no timezone, so retained time, system time "
            "and the image build time cannot be compared. An uncomparable "
            "clock fails closed."
        )

    # The detection SAD section 24.5.1 asks for. A clock cannot legitimately
    # read earlier than the build time of the software reading it, so a
    # plausible-looking but stale value is caught here rather than believed.
    if retained < policy.image_build_time:
        return _degraded(
            f"Retained time {retained.isoformat()} precedes the running "
            f"image's build time {policy.image_build_time.isoformat()}. The "
            "clock cannot predate the software reading it."
        )

    horizon = policy.image_build_time + policy.max_plausible_forward
    if retained > horizon:
        return _degraded(
            f"Retained time {retained.isoformat()} is further ahead of the "
            f"image build time than {policy.max_plausible_forward} allows."
        )

    skew = abs(readings.system_time() - retained)
    if skew > policy.max_system_rtc_skew:
        return _degraded(
            f"System clock and retained time disagree by {skew}, which exceeds "
            f"{policy.max_system_rtc_skew}. Neither is trusted."
        )

    return TimeAssessment("CREDIBLE", None)
