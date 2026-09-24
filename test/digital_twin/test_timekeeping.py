"""Unit tests for the time credibility decision.

`timekeeping.assess` is production code, so these are unit tests rather than
scenarios and they move with the module when a production package exists.

They matter more than their size suggests. Before this module existed the fake
returned the verdict directly, so the fail-closed tests asserted that a fixture
agreed with itself. Every case below feeds raw readings and checks what the
code concludes, which is the only arrangement in which FML-ADR-042 can fail a
test.
"""

from __future__ import annotations

from datetime import timedelta

import pytest

from mule.timekeeping import TimePolicy, assess

from .conftest import FIXTURE_IMAGE_BUILD_TIME
from .fakes import AFTER_BUILD, FakeClock


def test_a_healthy_clock_is_credible(time_policy: TimePolicy) -> None:
    result = assess(FakeClock.credible(time_policy), time_policy)

    assert result.credibility == "CREDIBLE"
    assert result.reason is None
    assert not result.degraded


def test_a_trusted_upstream_settles_it_before_the_rtc_is_consulted(
    time_policy: TimePolicy,
) -> None:
    """Ordering matters: a synchronized node is credible despite a dead RTC.

    If the RTC checks ran first, a node that had just synchronized from a
    trusted source would refuse to validate anything, which is fail-closed in
    the wrong place and would be discovered in the field.
    """
    result = assess(FakeClock.synchronized_despite_bad_rtc(time_policy), time_policy)

    assert result.credibility == "CREDIBLE"


@pytest.mark.parametrize(
    ("build", "fragment"),
    [
        (FakeClock.restored_from_shutdown, "No retained time source"),
        (FakeClock.dead_backup_cell, "backup cell depleted"),
        (FakeClock.no_reading, "returned no reading"),
        (FakeClock.stale_before_image, "precedes the running"),
        (FakeClock.implausibly_far_ahead, "further ahead"),
        (FakeClock.skewed_system_clock, "disagree by"),
    ],
    ids=[
        "no-rtc-restored-from-shutdown",
        "dead-backup-cell",
        "rtc-returns-nothing",
        "retained-time-predates-the-image",
        "retained-time-beyond-the-horizon",
        "system-clock-disagrees-with-rtc",
    ],
)
def test_every_untrustworthy_reading_is_refused_with_a_reason(
    time_policy: TimePolicy, build: object, fragment: str
) -> None:
    """Six distinct ways to have bad time, six distinct refusals.

    FML-ADR-042 requires a refusal to be diagnosable. A single generic message
    would satisfy the fail-closed behaviour and leave an operator with a node
    that will not authenticate anyone and will not say why.
    """
    result = assess(build(time_policy), time_policy)  # type: ignore[operator]

    assert result.degraded
    assert result.reason is not None
    assert fragment in result.reason


def test_a_plausible_looking_stale_clock_is_still_refused(
    time_policy: TimePolicy,
) -> None:
    """SAD section 24.5.1: this state is worse than having no clock.

    Nothing about the reading looks wrong. It is a well-formed timestamp from a
    present, healthy RTC whose backup cell reports fine. Only the comparison
    against the running image's build time catches it.
    """
    clock = FakeClock.stale_before_image(time_policy)

    assert clock.rtc_present()
    assert clock.rtc_backup_cell_ok() is True
    assert clock.rtc_time() is not None
    assert assess(clock, time_policy).degraded


def test_unknown_backup_cell_health_is_not_by_itself_a_refusal(
    time_policy: TimePolicy,
) -> None:
    """None means the platform cannot report cell health, not that it failed.

    Refusing on it would make every board without cell telemetry permanently
    unable to validate credentials. The plausibility checks still apply.
    """
    clock = FakeClock.credible(time_policy)
    clock.backup_cell = None

    assert not assess(clock, time_policy).degraded


def test_a_reading_exactly_at_the_build_time_is_accepted(
    time_policy: TimePolicy,
) -> None:
    """The boundary belongs to the accepting side.

    A node that booted the instant its image was built is implausible but not
    impossible, and an off-by-one here refuses a legitimate clock.
    """
    clock = FakeClock.credible(time_policy)
    clock.rtc = FIXTURE_IMAGE_BUILD_TIME
    clock.system = FIXTURE_IMAGE_BUILD_TIME

    assert not assess(clock, time_policy).degraded


def test_a_timestamp_without_a_timezone_fails_closed(
    time_policy: TimePolicy,
) -> None:
    """A crash is not a refusal.

    Comparing a naive datetime with an aware one raises TypeError. In trust
    validation that is an exception where a decision belongs: the node would
    stop, and whether it stopped safely would depend on the caller. This is the
    difference between failing closed and merely failing.
    """
    clock = FakeClock.credible(time_policy)
    clock.rtc = clock.rtc.replace(tzinfo=None) if clock.rtc else None

    result = assess(clock, time_policy)

    assert result.degraded
    assert result.reason is not None
    assert "timezone" in result.reason


def test_the_horizon_is_taken_from_the_policy_not_from_a_constant(
    time_policy: TimePolicy,
) -> None:
    """A reading credible under one policy is refused under a stricter one.

    TBR-TIME-01 sets the real bounds. If `assess` carried its own constant, the
    trade would close and nothing would change.
    """
    clock = FakeClock.credible(time_policy)
    assert not assess(clock, time_policy).degraded

    stricter = TimePolicy(
        image_build_time=time_policy.image_build_time,
        max_plausible_forward=AFTER_BUILD - timedelta(seconds=1),
        max_system_rtc_skew=time_policy.max_system_rtc_skew,
    )

    assert assess(clock, stricter).degraded
