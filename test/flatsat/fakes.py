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

from mule.bearers import Bearer
from mule.thermal import Sensor
from mule.timekeeping import TimePolicy

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
class FakeLoRaPlane:
    """Scripted state of the non-IP LoRa plane.

    Simulates: whether the LoRa stack answers, including the case where the
    platform cannot tell. That third case is the one worth having a fake for.
    The probe found the daemon exits when its configuration changes, so
    "radio present, nothing carrying" is a real state and not a hypothetical.

    Does not simulate: airtime, duty cycle, range, collisions, or anything a
    message crossing this plane would actually encounter. It carries no
    messages at all. `.github/workflows/lora-probe.yml` passes a real message
    between two meshtasticd instances, and even that runs over UDP on a Docker
    bridge, which is a perfect wire.

    Nothing here addresses a recipient. That is `TBR-NET-02` and it is open.
    """

    #: True answering, False not answering, None the platform cannot tell.
    responding: bool | None = True

    def stack_responding(self) -> bool | None:
        """Whether the LoRa stack answers, or None where that cannot be told."""
        return self.responding


@dataclass
class FakeMeshState:
    """Scripted readings from a node's mesh after bring-up.

    Simulates: what a finished node reports about its mesh, including the case
    where the platform cannot answer.

    Does not simulate: bring-up itself, or the order it happened in. That is
    the point of the interface it fakes. A snapshot cannot show an order, and
    `mule.bringup.state_violations` says which invariants a wrong order leaves
    detectable and which leave no trace at all.

    Defaults describe a node that came up correctly, so a scenario asserting a
    fault has to say which one.
    """

    algo: str | None = "BATMAN_IV"
    bla: bool | None = False
    mtu_bytes: int | None = 1560
    members: int | None = 1

    def routing_algo(self) -> str | None:
        """Report the algorithm the mesh interface is actually running."""
        return self.algo

    def bridge_loop_avoidance(self) -> bool | None:
        """Report whether bridge loop avoidance is on."""
        return self.bla

    def hard_mtu_bytes(self) -> int | None:
        """Report the MTU of the hard interface carrying the mesh."""
        return self.mtu_bytes

    def mesh_member_count(self) -> int | None:
        """Report how many interfaces are attached to the mesh."""
        return self.members


@dataclass
class FakePower:
    """Scripted raw power readings.

    Simulates: pack presence, pack health, reported charge, pack temperature.
    Does not simulate: discharge behaviour, capacity fade, load. There is no
    measured curve to model and inventing one would put a plausible number into
    a test that later gets quoted. TBR-PWR-01 measures those.

    **It reaches no conclusion.** How long the node will keep running is
    `mule.power.assess`'s decision, made from these readings and a measured
    model that does not exist yet.

    `charge` and `temperature_c` default to None: a pack that cannot report its
    own charge, and one that is not temperature-instrumented, are configurations
    the program has to handle rather than assume away.
    """

    pack: bool = False
    healthy: bool = True
    charge: float | None = None
    temperature_c: float | None = None

    def pack_present(self) -> bool:
        """Whether a protected battery assembly is fitted."""
        return self.pack

    def pack_healthy(self) -> bool:
        """Whether the pack reports itself within its operating envelope."""
        return self.pack and self.healthy

    def state_of_charge_fraction(self) -> float | None:
        """Fraction of capacity remaining, or None where nothing reports it."""
        return self.charge

    def pack_temperature_c(self) -> float | None:
        """Pack temperature, or None where it is not instrumented."""
        return self.temperature_c


@dataclass
class FakeThermal:
    """Scripted raw thermal readings.

    Simulates: what each fitted sensor reports, and whether the compute element
    says it is throttling.
    Does not simulate: heat flow, ambient sensitivity, solar load, or the
    enclosure. TBR-THERM-01 measures those and needs hardware.

    **It reaches no conclusion.** Whether a temperature is inside an envelope is
    `mule.thermal.assess`'s decision, made against limits that do not exist yet.
    An earlier version returned `within_envelope=True` by default, so a node
    with no defined envelope asserted it was inside one.

    The default is an empty sensor set: a node reports the sensors it has, and
    which sensors a build carries is TBR-HW-01 and TBR-THERM-01.
    """

    sensors: dict[Sensor, float | None] = field(default_factory=dict)
    is_throttling: bool | None = None

    def temperatures_c(self) -> dict[Sensor, float | None]:
        """Each fitted sensor's reading, or None where it did not report."""
        return dict(self.sensors)

    def throttling_reported(self) -> bool | None:
        """Whether the compute element reports that it is throttling.

        None by default: a scenario that did not script this has not said the
        node is running unthrottled, and the fake must not say it either.
        """
        return self.is_throttling

    @classmethod
    def at(cls, temperature_c: float, **kwargs: object) -> FakeThermal:
        """Build a node whose every SAD section 25.7 sensor reads the same.

        A convenience for scenarios about one temperature. Real nodes do not
        have a single temperature, which is why the general form takes a
        mapping.
        """
        sensors: dict[Sensor, float | None] = {
            "processor": temperature_c,
            "radio": temperature_c,
            "battery": temperature_c,
            "enclosure": temperature_c,
            "ambient": temperature_c,
        }
        return cls(sensors=sensors, **kwargs)  # type: ignore[arg-type]


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
