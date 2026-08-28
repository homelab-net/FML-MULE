"""What the node tells its operator.

CONOPS section 67 requires one simplified view answering thirteen questions. A
tired volunteer in the dark should be able to read it and know whether the node
is working, whether it will keep working, and what to do if not.

Two things make this module worth reading carefully.

**`None` is an answer.** Several questions cannot be answered honestly today:
there is no power model, so projected runtime is unknown, and no continuity
mechanism, so nothing knows whether shared data is authoritative. `None` says
"the node cannot say". A number or a `True` in those places would be invented,
and an invented figure in a status view is the kind that gets quoted back as
fact.

**Nothing here is a constant.** Every answer is derived from what the node
observed. An earlier version reported several of these as fixed healthy values,
and the test suite could not tell the difference between that and working code.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from .bearers import Bearer, inter_node_present, missing_required
from .power import PowerAssessment
from .thermal import ThermalAssessment
from .timekeeping import TimeAssessment

#: The states an operator sees, from SAD section 22.
OperatorState = Literal[
    "GREEN", "DEGRADED", "LOW-BANDWIDTH", "NON-AUTHORITATIVE", "EMCON", "FAULT"
]

#: Why shared data is not authoritative, from SAD section 22.
AuthorityReason = Literal[
    "PARTITION",
    "STATE_LAG",
    "HOST_RECOVERY",
    "NO_SAFE_AUTHORITY",
    "UNSYNCHRONIZED",
    "UNKNOWN",
]


@dataclass(frozen=True)
class Observations:
    """Everything the node observed, gathered in one place.

    Plain values only: no radios, no sensors, no clock. Whatever collects these
    deals with hardware; this module only reasons about what was collected,
    which is what makes the reasoning testable on an ordinary laptop.
    """

    booted: bool
    config_error: str | None
    time: TimeAssessment
    enumerated: list[Bearer]
    associated: list[Bearer]
    battery_present: bool
    battery_healthy: bool
    power: PowerAssessment
    thermal: ThermalAssessment
    hosting_shared_services: bool
    emcon: bool
    wan_available: bool


@dataclass(frozen=True)
class NodeStatus:
    """The simplified operator view.

    The thirteen CONOPS section 67 questions, in the order they are asked
    there. Field names track the questions rather than the implementation,
    because the CONOPS list is the acceptance criterion and a reader should be
    able to check them off against it.
    """

    operational: bool  # Is the node operational?
    battery_healthy: bool | None  # Is the battery healthy?
    projected_runtime_minutes: int | None  # What is the projected runtime?
    hosting_shared_services: bool  # Is this node hosting shared services?
    hosting_reduces_runtime: bool | None  # Is hosting reducing runtime?
    tak_available: bool  # Is TAK available?
    shared_data_authoritative: bool | None  # Is shared data authoritative?
    data_stale: bool | None  # Is data stale?
    network_degraded: bool  # Is the network degraded?
    lora_available: bool  # Is LoRa available?
    wan_available: bool  # Is WAN available?
    emcon_active: bool  # Is EMCON active?
    fault: str | None  # Is a fault present?

    # Not a CONOPS question. SAD section 22 supplies these, and they qualify
    # the answers above rather than adding a fourteenth question.
    authority_reason: AuthorityReason | None
    state: OperatorState


def _fault(observed: Observations, missing: list[Bearer]) -> str | None:
    """Describe the most serious thing wrong, or None if nothing is.

    Ordered worst first, and it stops at the first one found. An operator
    handed three simultaneous faults reads none of them; the node names the one
    that has to be fixed before anything else matters.
    """
    if not observed.booted:
        return observed.config_error or "node did not boot"
    if missing:
        return f"RADIO_ABSENT: required bearer(s) {', '.join(missing)}"
    if observed.time.degraded:
        return f"TIME_DEGRADED: {observed.time.reason}"
    if observed.thermal.outside_envelope:
        return (
            "THERMAL_DEGRADED: "
            + ", ".join(observed.thermal.breaches)
            + " outside stated limits"
        )
    return None


def _state(
    observed: Observations, missing: list[Bearer], fault: str | None
) -> OperatorState:
    """Reduce everything to the one word shown on the status view.

    Precedence, decided here because SAD section 22 names the states but not
    their ordering:

    1. A node that cannot serve users is `FAULT`, whatever else is true.
    2. Any other fault is `DEGRADED`.
    3. `EMCON` is a deliberate posture, so it outranks a mere degradation, but
       it never hides a fault: a silent node is a choice, a broken one is not.
    4. Thermal throttling degrades without faulting. The node works, slower.
       This is reported even when the thermal state is UNKNOWN, because the
       hardware states it rather than the node inferring it.
    """
    if not observed.booted or missing:
        return "FAULT"
    if fault is not None:
        return "DEGRADED"
    if observed.emcon:
        return "EMCON"
    if observed.thermal.throttling:
        return "DEGRADED"
    return "GREEN"


def _network_degraded(observed: Observations) -> bool:
    """Say whether the link to other nodes is broken.

    A node with an inter-node radio that will not link is degraded. A node with
    no inter-node radio at all is **not**: it was never meant to mesh, which is
    the ROADMAP v0.0.1 configuration. Reporting that node as permanently
    degraded would make the first milestone's own hardware look broken.
    """
    fitted = inter_node_present(observed.enumerated)
    return bool(fitted) and not any(
        bearer in set(observed.associated) for bearer in fitted
    )


def derive(observed: Observations) -> NodeStatus:
    """Answer the thirteen CONOPS section 67 questions from what was observed."""
    missing = missing_required(observed.enumerated)
    fault = _fault(observed, missing)
    hosting = observed.hosting_shared_services

    return NodeStatus(
        operational=observed.booted,
        # None where no pack is fitted: the question does not apply, which is
        # not the same as a pack in poor health.
        battery_healthy=observed.battery_healthy if observed.battery_present else None,
        # Both answers come from mule/power.py, which returns None with a
        # reason while TBR-PWR-01 leaves it without a measured model. The
        # procedure is written; only the numbers are missing.
        projected_runtime_minutes=observed.power.projected_runtime_minutes,
        hosting_shared_services=hosting,
        hosting_reduces_runtime=observed.power.hosting_reduces_runtime,
        tak_available=hosting,
        # No continuity mechanism exists. TBR-TAK-01, TBR-HA-01.
        shared_data_authoritative=None,
        data_stale=None,
        network_degraded=_network_degraded(observed),
        lora_available="lora" in observed.enumerated and "lora" in observed.associated,
        wan_available=observed.wan_available,
        emcon_active=observed.emcon,
        fault=fault,
        authority_reason=None if hosting else "NO_SAFE_AUTHORITY",
        state=_state(observed, missing, fault),
    )
