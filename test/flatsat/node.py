"""A MULE node, composed and run end to end with the hardware layer faked.

This is the flat-sat's node. Its job is **assembly, not judgement**: it reads
the fakes, hands plain values to the decision modules in `mule/`, and reports
what they said. Every rule it appears to apply lives somewhere else.

That split is `FML-ADR-051`, and it is what lets the same decisions run on a
real node with real drivers behind the same interfaces. If you are looking for
what the node *decides*, this is the wrong file. Read:

- `mule/timekeeping.py` - can the clock be trusted?
- `mule/admission.py` - may this device join?
- `mule/services.py` - what does this node offer, and by what name?
- `mule/status.py` - what do we tell the operator?
- `mule/bearers.py` - which radios matter?

**It runs the real artifacts.** Configuration resolution calls
`tools/gen-config.py` itself, not a reimplementation.

**What is faked** is listed in `README.md` and confined to `fakes.py`: radio,
power and thermal state behind the interfaces in `interfaces.py`, and raw clock
readings behind `mule.timekeeping.TimeReadings`.

**What is not simulated, and cannot be:** RF propagation, throughput, mesh
scaling, coexistence, power draw, endurance, thermal behaviour, driver
attachment, or timing under load. A passing scenario yields `SIMULATED` and
never supports a claim about any of those.
"""

from __future__ import annotations

import importlib.util
from dataclasses import dataclass
from pathlib import Path
from types import ModuleType
from typing import Any

from mule import power, services, status, thermal
from mule.admission import AdmissionDecision, decide
from mule.bearers import Bearer
from mule.power import PowerModel, PowerReadings
from mule.status import NodeStatus, Observations
from mule.thermal import ThermalLimits, ThermalReadings
from mule.timekeeping import TimeAssessment, TimePolicy, TimeReadings, assess

from .interfaces import RadioState

REPO_ROOT = Path(__file__).resolve().parents[2]

#: Where the flat-sat's stand-in services are said to run. The real service
#: plane waits on trades that have not closed; see `README.md`.
STAND_IN_LOCATION = "local"


def _load_gen_config() -> ModuleType:
    """Load `tools/gen-config.py` as a module.

    Loaded by path because the file is a hyphenated executable script.
    Importing the real tool rather than reimplementing it is what keeps the
    flat-sat from drifting: if region validation changes, this changes with it.
    """
    path = REPO_ROOT / "tools" / "gen-config.py"
    spec = importlib.util.spec_from_file_location("gen_config", path)
    if spec is None or spec.loader is None:  # pragma: no cover - defensive
        message = f"cannot load {path}"
        raise RuntimeError(message)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


gen_config = _load_gen_config()


@dataclass
class BootResult:
    """Outcome of powering the node on."""

    booted: bool
    time_degraded: bool
    time_reason: str | None
    config_resolved: bool
    config_error: str | None
    radios_enumerated: list[str]


#: The flat-sat reports admission using the decision type itself, so a scenario
#: reads the same shape the node produced.
AdmissionResult = AdmissionDecision


class FlatSatNode:
    """A node running against fakes.

    The service plane is represented by a stand-in, not by the real services.
    Three of the four MULE-original components are approved but blocked on
    trades, and `AGENTS.md` forbids implementing them to make a scenario pass.
    The flat-sat exercises their **interfaces** with stand-ins, which is what a
    flat-sat is for: bringing up the bus while the payload does not exist.
    """

    def __init__(
        self,
        region_profile: Path,
        mission_package: Path,
        radio: RadioState,
        power: PowerReadings,
        thermal: ThermalReadings,
        clock: TimeReadings,
        time_policy: TimePolicy,
        power_model: PowerModel | None = None,
        thermal_limits: ThermalLimits | None = None,
        *,
        emcon: bool = False,
        wan: bool = False,
    ) -> None:
        """Compose a node from a region profile, a mission package and fakes."""
        self._region_profile = region_profile
        self._mission_package = mission_package
        self._radio = radio
        self._power = power
        self._thermal = thermal
        self._clock = clock
        self._time_policy = time_policy
        # None while TBR-PWR-01 is open. See mule/power.py.
        self._power_model = power_model
        # None while TBR-THERM-01 is open. See mule/thermal.py.
        self._thermal_limits = thermal_limits
        self._emcon = emcon
        self._wan = wan

        self._booted = False
        self._params: dict[str, Any] | None = None
        self._config_error: str | None = None
        self._services: dict[str, str] = {}
        self._shared_services: dict[str, str] = {}
        self._admitted: set[str] = set()

    # --- reading the hardware ----------------------------------------------

    def _assess_time(self) -> TimeAssessment:
        """Judge retained time now, rather than trusting a cached verdict.

        A clock can lose credibility while the node is running, and a cached
        CREDIBLE is exactly the stale answer FML-ADR-042 warns about.
        """
        return assess(self._clock, self._time_policy)

    def _enumerated(self) -> list[Bearer]:
        """Bearers the platform found."""
        return list(self._radio.enumerated())

    def _associated(self) -> list[Bearer]:
        """Bearers that have formed their link."""
        return [b for b in self._enumerated() if self._radio.associated(b)]

    # --- lifecycle ---------------------------------------------------------

    def power_on(self) -> BootResult:
        """Boot the node: evaluate time, resolve configuration, bring up radios.

        Order matters and follows FML-ADR-042: time credibility is evaluated
        **before** anything trust-sensitive proceeds. A node whose clock is not
        credible still boots and still carries local networking where safe; what
        it refuses is trust validation.
        """
        assessment = self._assess_time()

        self._config_error = None
        self._services = {}
        self._shared_services = {}
        self._admitted = set()

        try:
            self._params = gen_config.generate(
                str(self._region_profile), self._mission_package, None
            )
            resolved = True
        except gen_config.ConfigError as exc:
            self._params = None
            self._config_error = str(exc)
            resolved = False

        # Configuration resolution gates radio bring-up. A node that cannot
        # resolve a lawful channel does not transmit: os/config/README.md makes
        # a generated channel outside the permitted set a regulatory problem,
        # not a bug, and the same logic applies to having no channel at all.
        enumerated = [str(b) for b in self._enumerated()] if resolved else []

        self._booted = resolved
        if resolved and self._params is not None:
            self._services = {
                name: STAND_IN_LOCATION
                for name in services.identities(
                    self._params["mission"]["services"],
                    self._params["network"]["local_domain"],
                )
            }

        return BootResult(
            booted=self._booted,
            time_degraded=assessment.degraded,
            time_reason=assessment.reason,
            config_resolved=resolved,
            config_error=self._config_error,
            radios_enumerated=enumerated,
        )

    # --- admission ---------------------------------------------------------

    def admit(self, device_id: str) -> AdmissionDecision:
        """Ask `mule.admission` whether this device may join, and record it.

        The decision is not made here. This gathers what the decision needs and
        keeps the set of admitted devices, which is state rather than judgement.
        """
        decision = decide(
            booted=self._booted,
            time=self._assess_time(),
            associated=self._associated() if self._booted else [],
        )
        if decision.admitted:
            self._admitted.add(device_id)
        return decision

    def resolve_service(self, name: str, device_id: str) -> str | None:
        """Resolve a logical service identity for an admitted device.

        An unadmitted device resolves nothing. Network admission and
        application authorization stay separate, and this is the former; there
        is no authorization anywhere yet, which `README.md` records as a gap.
        """
        if device_id not in self._admitted:
            return None
        return self._services.get(name)

    # --- status ------------------------------------------------------------

    def status(self) -> NodeStatus:
        """Gather what the node observed and let `mule.status` interpret it."""
        return status.derive(
            Observations(
                booted=self._booted,
                config_error=self._config_error,
                time=self._assess_time(),
                enumerated=self._enumerated(),
                associated=self._associated(),
                battery_present=self._power.pack_present(),
                battery_healthy=self._power.pack_healthy(),
                power=power.assess(
                    self._power,
                    self._power_model,
                    hosting_shared_services=bool(self._shared_services),
                ),
                thermal=thermal.assess(self._thermal, self._thermal_limits),
                # No shared service is hosted: the TAK service plane waits on
                # TBR-TAK-01 and the stand-in is local only.
                hosting_shared_services=bool(self._shared_services),
                emcon=self._emcon,
                wan_available=self._wan,
            )
        )

    def thermal_state(self) -> str:
        """Return what `mule.thermal` concluded, for scenarios needing the detail.

        `NodeStatus` deliberately does not carry this: CONOPS section 67 asks
        thirteen questions and none of them is "what is the thermal state".
        It reaches the operator as a fault or as nothing.
        """
        return thermal.assess(self._thermal, self._thermal_limits).state

    @property
    def parameters(self) -> dict[str, Any] | None:
        """The resolved configuration parameters, or None if resolution failed."""
        return self._params
