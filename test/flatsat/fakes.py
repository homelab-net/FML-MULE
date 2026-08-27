"""Fakes for the hardware interfaces.

Every fake in this file is listed in `test/flatsat/README.md`, and
`tools/validate-docs.sh` fails if one is not. That listing is a rule, not a
courtesy: a reader must be able to see exactly which boundary is simulated, and
an unlisted fake is how "it works on the flat-sat" becomes a permanent excuse.

Each fake is scripted, not modelled. `FakePower` does not simulate a battery
discharge curve, because no measured curve exists and inventing one would put a
plausible number into a test that later gets quoted. It returns what the
scenario told it to return, and nothing else.

**A fake reports; it does not conclude.** `FakeClock` supplies raw readings and
`timekeeping.assess` decides what they mean. A fake that returns a verdict makes
the verdict untestable, because the test then agrees with the fixture rather
than with the code.

**A fake may not describe hardware that cannot exist.** `FakeRadio` rejects a
bearer that is linked without being present. The flat-sat's whole claim is that
passing here means something on hardware, and a fake free to script impossible
states voids it.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta

from .interfaces import Bearer
from .timekeeping import TimePolicy

#: Offsets used to build scripted clock readings. Expressed relative to the
#: image build time because that is the semantic anchor `timekeeping.assess`
#: judges against, not because any of these durations is a measured value.
AFTER_BUILD = timedelta(days=1)
WELL_BEFORE_BUILD = timedelta(days=30)
BEYOND_ANY_HORIZON = timedelta(days=1)


class ImpossibleHardwareState(ValueError):
    """A scenario described hardware that cannot physically exist.

    Raised at construction rather than reported as a test failure, so the
    scenario author is told they wrote an impossible fixture instead of being
    shown a passing run that means nothing.
    """


@dataclass
class FakeRadio:
    """Scripted radio state.

    Simulates: driver attachment, link formation and peer visibility.
    Does not simulate: RF propagation, throughput, desense, multicast scaling,
    or anything else TBR-RF-01, TBR-RF-02 and TBR-RF-03 exist to measure.
    """

    present: list[Bearer] = field(default_factory=lambda: ["halow", "wifi_ap", "lora"])
    linked: list[Bearer] = field(default_factory=lambda: ["halow", "wifi_ap", "lora"])

    def __post_init__(self) -> None:
        """Reject hardware that cannot exist before any scenario runs."""
        absent = set(self.linked) - set(self.present)
        if absent:
            message = (
                f"bearers {sorted(absent)} are linked but not present. A radio "
                "cannot associate before its driver attaches."
            )
            raise ImpossibleHardwareState(message)

    def enumerated(self) -> list[Bearer]:
        """Bearers whose hardware is present and whose driver has attached."""
        return list(self.present)

    def associated(self, bearer: Bearer) -> bool:
        """Whether the bearer has formed its link."""
        return bearer in self.linked


@dataclass
class FakePower:
    """Scripted power state.

    Simulates: pack presence and pack health.
    Does not simulate: consumption, endurance or runtime. `projected_runtime`
    returns None because TBR-PWR-01 has not closed and no measured load model
    exists.
    """

    battery: bool = False
    healthy: bool = True

    def battery_present(self) -> bool:
        """Whether a protected battery assembly is fitted."""
        return self.battery

    def battery_healthy(self) -> bool:
        """Whether the pack reports itself within its operating envelope."""
        return self.battery and self.healthy

    def projected_runtime_minutes(self) -> int | None:
        """Return None always. No power model exists; see TBR-PWR-01."""
        return None


@dataclass
class FakeThermal:
    """Scripted thermal state.

    Simulates: a throttle flag and an in-envelope flag.
    Does not simulate: temperature, heat flow, ambient sensitivity or the
    enclosure. TBR-THERM-01 measures those and needs hardware.
    """

    is_throttled: bool = False
    in_envelope: bool = True

    def throttled(self) -> bool:
        """Whether the compute element is currently thermally throttled."""
        return self.is_throttled

    def within_envelope(self) -> bool:
        """Whether all monitored sensors are inside their stated limits."""
        return self.in_envelope


@dataclass
class FakeClock:
    """Scripted raw time readings.

    Simulates: what the RTC and system clock report, and whether time was set
    from a trusted source.
    Does not simulate: drift, holdover duration or skew accumulation. Those are
    TBR-TIME-01 and are bound by elapsed time on real hardware.

    **It reaches no conclusion.** Whether these readings are credible is
    `timekeeping.assess`'s decision. Every constructor below builds readings
    relative to a policy's image build time, so a scenario states the physical
    situation and the code under test states what it means.
    """

    present: bool
    backup_cell: bool | None
    rtc: datetime | None
    system: datetime
    synced: bool = False

    def rtc_present(self) -> bool:
        """Whether a battery-backed real-time clock is fitted and responding."""
        return self.present

    def rtc_backup_cell_ok(self) -> bool | None:
        """Backup cell health, or None where the platform cannot report it."""
        return self.backup_cell

    def rtc_time(self) -> datetime | None:
        """Return the RTC's retained time, or None if it gave no reading."""
        return self.rtc

    def system_time(self) -> datetime:
        """Return the running system clock, whatever it currently believes."""
        return self.system

    def synchronized(self) -> bool:
        """Whether time has been set from a source the node trusts."""
        return self.synced

    @classmethod
    def credible(cls, policy: TimePolicy) -> FakeClock:
        """Build a healthy RTC reading a time the policy accepts."""
        moment = policy.image_build_time + AFTER_BUILD
        return cls(present=True, backup_cell=True, rtc=moment, system=moment)

    @classmethod
    def dead_backup_cell(cls, policy: TimePolicy) -> FakeClock:
        """Build an RTC whose backup cell has failed."""
        moment = policy.image_build_time + AFTER_BUILD
        return cls(present=True, backup_cell=False, rtc=moment, system=moment)

    @classmethod
    def restored_from_shutdown(cls, policy: TimePolicy) -> FakeClock:
        """Build a node with no RTC whose system time looks entirely plausible.

        SAD section 24.5.1 calls this worse than having no clock, because it
        looks valid. The readings here are deliberately innocuous: only the
        missing RTC distinguishes them, and `assess` must notice.
        """
        return cls(
            present=False,
            backup_cell=None,
            rtc=None,
            system=policy.image_build_time + AFTER_BUILD,
        )

    @classmethod
    def stale_before_image(cls, policy: TimePolicy) -> FakeClock:
        """Build an RTC reading a time earlier than the running image's build."""
        moment = policy.image_build_time - WELL_BEFORE_BUILD
        return cls(present=True, backup_cell=True, rtc=moment, system=moment)

    @classmethod
    def implausibly_far_ahead(cls, policy: TimePolicy) -> FakeClock:
        """Build an RTC reading a time beyond the policy's forward horizon."""
        moment = (
            policy.image_build_time + policy.max_plausible_forward + BEYOND_ANY_HORIZON
        )
        return cls(present=True, backup_cell=True, rtc=moment, system=moment)

    @classmethod
    def no_reading(cls, policy: TimePolicy) -> FakeClock:
        """Build a present RTC that returns nothing when read."""
        return cls(
            present=True,
            backup_cell=True,
            rtc=None,
            system=policy.image_build_time + AFTER_BUILD,
        )

    @classmethod
    def skewed_system_clock(cls, policy: TimePolicy) -> FakeClock:
        """Build a healthy RTC that the system clock disagrees with."""
        moment = policy.image_build_time + AFTER_BUILD
        return cls(
            present=True,
            backup_cell=True,
            rtc=moment,
            system=moment + policy.max_system_rtc_skew + BEYOND_ANY_HORIZON,
        )

    @classmethod
    def synchronized_despite_bad_rtc(cls, policy: TimePolicy) -> FakeClock:
        """Build a node synchronized upstream while its RTC is unusable.

        Proves the ordering in `assess`: a trusted upstream settles the question
        before any retained reading is consulted.
        """
        return cls(
            present=True,
            backup_cell=False,
            rtc=policy.image_build_time - WELL_BEFORE_BUILD,
            system=policy.image_build_time + AFTER_BUILD,
            synced=True,
        )
