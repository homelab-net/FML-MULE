"""Shared fixtures for the flat-sat.

Everything a scenario needs to compose a node lives here, so that no scenario
carries a literal another scenario has to match by hand.
"""

from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from mule.modes import EmissionPosture
from mule.power import PowerModel
from mule.thermal import ThermalLimits
from mule.timekeeping import TimePolicy

from .fakes import FakeClock, FakeLoRaPlane, FakePower, FakeRadio, FakeThermal
from .node import REPO_ROOT, FlatSatNode

FIXTURE_REGIONS = REPO_ROOT / "test" / "fixtures" / "regions" / "xx-testfixture"
GOOD_PROFILE = FIXTURE_REGIONS / "profile.yml"
MISSION_EXAMPLES = REPO_ROOT / "mission" / "examples"

#: A package that enables two services and names a local domain.
MISSION_WITH_SERVICES = MISSION_EXAMPLES / "valid-full.json"
#: The smallest package the schema accepts. It enables no services and names no
#: domain, which is a valid deployment and a useful negative case.
MISSION_MINIMAL = MISSION_EXAMPLES / "valid-minimal.json"

#: An arbitrary anchor for fixture clock readings. It is not a real build time
#: and nothing is derived from its particular value; every scripted reading is
#: expressed as an offset from it.
FIXTURE_IMAGE_BUILD_TIME = datetime(2026, 1, 1, tzinfo=UTC)

#: Fixture bounds. The real values belong to TBR-TIME-01, which has not closed.
#: These exist so the decision under test has something to judge against, and
#: no node should ever be configured from them.
FIXTURE_MAX_PLAUSIBLE_FORWARD = timedelta(days=3650)
FIXTURE_MAX_SYSTEM_RTC_SKEW = timedelta(minutes=15)

#: A synthetic power model. Every number is invented and none is measured.
#: TBR-PWR-01 owns the real ones, and until it closes and its evidence is
#: accepted, no node is configured from anything like this.
#:
#: The values deliberately do NOT produce the CONOPS section 59 eight-hour
#: planning objective. A fixture that landed on the objective would invite
#: someone to read arithmetic on invented numbers as confirmation of it.
FIXTURE_POWER_MODEL = PowerModel(
    pack_capacity_wh=100.0,
    reserve_fraction=0.25,
    baseline_load_w=12.5,
    hosting_load_w=5.0,
    cold_derating=((0.0, 0.5),),
)

#: Synthetic thermal limits. Every number is invented; TBR-THERM-01 owns the
#: real ones. The battery override exists because SAD section 25.7 measures the
#: pack separately from the processor, and a single envelope across both would
#: be wrong in a way that looks reasonable.
FIXTURE_THERMAL_LIMITS = ThermalLimits(
    warn_above_c=60.0,
    critical_above_c=80.0,
    per_sensor=(("battery", 40.0, 50.0),),
)

#: The device identity used by scenarios that need one. Any string works today,
#: which is itself a finding recorded in test/flatsat/README.md.
EUD = "eud-example-01"


@pytest.fixture
def time_policy() -> TimePolicy:
    """Return the fixture policy every scenario judges clock readings against."""
    return TimePolicy(
        image_build_time=FIXTURE_IMAGE_BUILD_TIME,
        max_plausible_forward=FIXTURE_MAX_PLAUSIBLE_FORWARD,
        max_system_rtc_skew=FIXTURE_MAX_SYSTEM_RTC_SKEW,
    )


NodeFactory = Callable[..., FlatSatNode]


@pytest.fixture
def build_node(time_policy: TimePolicy) -> NodeFactory:
    """Return a factory composing a node from healthy fakes, overridable."""

    def factory(
        *,
        profile: Path = GOOD_PROFILE,
        mission: Path = MISSION_WITH_SERVICES,
        clock: FakeClock | None = None,
        radio: FakeRadio | None = None,
        power: FakePower | None = None,
        thermal: FakeThermal | None = None,
        lora_plane: FakeLoRaPlane | None = None,
        power_model: PowerModel | None = None,
        thermal_limits: ThermalLimits | None = None,
        emission: EmissionPosture = "NORMAL-EMISSION",
        economy_below_minutes: int | None = None,
        wan: bool | None = None,
        peer_reachable: bool | None = None,
    ) -> FlatSatNode:
        return FlatSatNode(
            region_profile=profile,
            mission_package=mission,
            radio=radio if radio is not None else FakeRadio(),
            power=power if power is not None else FakePower(),
            thermal=thermal if thermal is not None else FakeThermal(),
            lora_plane=lora_plane if lora_plane is not None else FakeLoRaPlane(),
            clock=clock if clock is not None else FakeClock.credible(time_policy),
            time_policy=time_policy,
            power_model=power_model,
            thermal_limits=thermal_limits,
            emission=emission,
            economy_below_minutes=economy_below_minutes,
            wan=wan,
            peer_reachable=peer_reachable,
        )

    return factory
