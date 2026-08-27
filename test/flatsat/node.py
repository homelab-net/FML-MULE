"""A MULE node, composed and run end to end with the hardware layer faked.

This is the flat-sat. It exists to verify the **end user experience** in CONOPS
section 82 — power on, connect, authenticate, authorized services appear, work —
so that what is developed matches how it will be used, and so the end-to-end
flow is free of logic bugs before hardware is scarce and expensive.

**It runs the real artifacts.** Configuration resolution calls
`tools/gen-config.py` itself, not a reimplementation, so a change that breaks
region validation breaks the flat-sat too. A flat-sat that has drifted from the
node is worse than none.

**What is faked** is listed in `README.md` and confined to `fakes.py`: radio,
power, thermal and time state, behind the narrow interfaces in `interfaces.py`.

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
from typing import Any, Literal

from .interfaces import PowerState, RadioState, ThermalState, TimeState

REPO_ROOT = Path(__file__).resolve().parents[2]

#: Operator-visible node states, from SAD section 22.
OperatorState = Literal[
    "GREEN", "DEGRADED", "LOW-BANDWIDTH", "NON-AUTHORITATIVE", "EMCON", "FAULT"
]

#: Reason codes for non-authoritative shared data, from SAD section 22.
AuthorityReason = Literal[
    "PARTITION",
    "STATE_LAG",
    "HOST_RECOVERY",
    "NO_SAFE_AUTHORITY",
    "UNSYNCHRONIZED",
    "UNKNOWN",
]


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


@dataclass
class AdmissionResult:
    """Outcome of an end user device attempting to join."""

    admitted: bool
    reason: str | None


@dataclass
class NodeStatus:
    """The simplified operator view.

    Answers the thirteen questions CONOPS section 67 requires, in order. The
    field names track the questions rather than the implementation, because the
    CONOPS list is the acceptance criterion.
    """

    operational: bool
    battery_healthy: bool | None
    projected_runtime_minutes: int | None
    hosting_shared_services: bool
    hosting_reduces_runtime: bool | None
    tak_available: bool
    shared_data_authoritative: bool | None
    authority_reason: AuthorityReason | None
    data_stale: bool | None
    network_degraded: bool
    lora_available: bool
    wan_available: bool
    emcon_active: bool
    fault: str | None
    state: OperatorState


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
        power: PowerState,
        thermal: ThermalState,
        clock: TimeState,
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
        self._emcon = emcon
        self._wan = wan

        self._booted = False
        self._params: dict[str, Any] | None = None
        self._config_error: str | None = None
        self._services: dict[str, str] = {}
        self._admitted: set[str] = set()

    # --- lifecycle ---------------------------------------------------------

    def power_on(self) -> BootResult:
        """Boot the node: evaluate time, resolve configuration, bring up radios.

        Order matters and follows FML-ADR-042: time credibility is evaluated
        **before** anything trust-sensitive proceeds. A node whose clock is not
        credible still boots and still carries local networking where safe; what
        it refuses is trust validation.
        """
        credibility = self._clock.credibility()
        time_degraded = credibility == "DEGRADED"

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
        enumerated = [str(b) for b in self._radio.enumerated()] if resolved else []

        self._booted = resolved
        if resolved:
            # One stand-in service, matching the ROADMAP v0.0.1 scope: one node,
            # one service, reachable from a client.
            self._services = {"portal.field": "local"}

        return BootResult(
            booted=self._booted,
            time_degraded=time_degraded,
            time_reason=self._clock.reason(),
            config_resolved=resolved,
            config_error=self._config_error,
            radios_enumerated=enumerated,
        )

    # --- admission ---------------------------------------------------------

    def admit(self, device_id: str) -> AdmissionResult:
        """Attempt to admit an end user device.

        **Fails closed on invalid time.** FML-ADR-042: trust validation shall
        not fail open on invalid, implausible or unavailable time. Admission is
        a trust-sensitive operation, so a node in TIME_DEGRADED refuses and
        reports why.

        This is the behaviour most worth having in a flat-sat, because it is
        unwelcome in the field, correct, and easy to regress into failing open.
        """
        if not self._booted:
            return AdmissionResult(False, "node has not booted")

        if self._clock.credibility() == "DEGRADED":
            return AdmissionResult(
                False,
                f"TIME_DEGRADED: {self._clock.reason()}",
            )

        if not self._radio.associated("wifi_ap"):
            return AdmissionResult(False, "EUD access point is not serving")

        self._admitted.add(device_id)
        return AdmissionResult(True, None)

    def resolve_service(self, name: str, device_id: str) -> str | None:
        """Resolve a logical service identity for an admitted device.

        CONOPS section 5.6 and FML-ADR-031: users reach stable logical names,
        not physical hosts. An unadmitted device resolves nothing; network
        admission and application authorization stay separate, and this is the
        former.
        """
        if device_id not in self._admitted:
            return None
        return self._services.get(name)

    # --- status ------------------------------------------------------------

    def status(self) -> NodeStatus:
        """Answer the thirteen CONOPS section 67 questions.

        Several answers are `None`, which is the honest value rather than a
        missing one. Projected runtime has no power model (TBR-PWR-01);
        authority state has no continuity mechanism (TBR-TAK-01, TBR-HA-01).
        A number or a boolean in those fields today would be invented.
        """
        time_degraded = self._clock.credibility() == "DEGRADED"
        enumerated = self._radio.enumerated()

        fault: str | None = None
        if not self._booted:
            fault = self._config_error or "node did not boot"
        elif time_degraded:
            fault = f"TIME_DEGRADED: {self._clock.reason()}"
        elif not self._thermal.within_envelope():
            fault = "THERMAL_DEGRADED: outside stated envelope"

        state: OperatorState = "GREEN"
        if self._emcon:
            state = "EMCON"
        elif fault is not None:
            state = "FAULT" if not self._booted else "DEGRADED"
        elif self._thermal.throttled():
            state = "DEGRADED"

        return NodeStatus(
            operational=self._booted,
            battery_healthy=(
                self._power.battery_healthy() if self._power.battery_present() else None
            ),
            projected_runtime_minutes=self._power.projected_runtime_minutes(),
            # No shared service is hosted: the TAK service plane waits on
            # TBR-TAK-01 and the stand-in is local only.
            hosting_shared_services=False,
            hosting_reduces_runtime=None,
            tak_available=False,
            shared_data_authoritative=None,
            authority_reason="NO_SAFE_AUTHORITY",
            data_stale=None,
            network_degraded=not self._radio.associated("halow"),
            lora_available="lora" in enumerated and self._radio.associated("lora"),
            wan_available=self._wan,
            emcon_active=self._emcon,
            fault=fault,
            state=state,
        )

    @property
    def parameters(self) -> dict[str, Any] | None:
        """The resolved configuration parameters, or None if resolution failed."""
        return self._params
