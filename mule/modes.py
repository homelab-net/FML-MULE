"""Which operating modes the node is in.

CONOPS section 50 names thirteen operating modes. It does not say whether more
than one may hold at a time, and it gives no entry or exit criteria. Both gaps
are raised as `CCR-01`, and this module implements the part of that change
request that adds no binding clause: the thirteen are **nine concurrent axes**,
and a node is on exactly one value of each at all times.

**Concurrent, not exclusive.** Section 51 lets exercise control "force
degradation states", which a mode exclusive of degradation could not do. Section
50.12 requires an EMCON entry *and re-entry* procedure, which is the shape of a
posture over a continuing state. A node low on battery in a congested band is
FIELD-ECONOMY and DEGRADED-IP at once, for two independent reasons.

**Most axes are not decided here.** Only two are derived from observation:
bearer capability and deployment context. A third, the shared TAK service, is
half derived and half blocked. The rest are configuration or authorized action,
and are carried so that "what mode is this node in" has one answer rather than
six callers assembling their own.

**No hysteresis.** `CCR-01` part B would require it, and part B is not approved.
Hysteresis needs the previous value, and building the state machine for it now
would be a mechanism for an unapproved requirement. When part B lands it adds an
argument to this function.

**Location note.** Production code, per `FML-ADR-051`. It reasons about subject
matter `services/status-aggregator/` describes, which `FML-ADR-052` permits on
four conditions: it is a pure function of values passed to it, every name below
is transcribed from CONOPS section 50, it returns `None` where an open trade
would decide, and it defines no interface to hardware or to a peer.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from .bearers import Bearer, inter_node_present
from .power import PowerAssessment

#: Where the node is. It cannot observe this: a bench and a field site look
#: identical from inside. CONOPS section 50.1. Program Owner direction recorded
#: in `CCR-01` makes LAB an environment rather than a deployment context.
Environment = Literal["LAB", "FIELD"]

#: Whether this node is meshed with other MULEs. CONOPS sections 50.2 and 50.3,
#: whose names FIELD-STANDALONE and FIELD-NETWORKED compound this axis with the
#: environment above.
DeploymentContext = Literal["STANDALONE", "NETWORKED"]

#: Whether a shared TAK service is reachable. CONOPS sections 50.4 and 50.5.
SharedTakService = Literal["SERVERLESS-TAK", "SERVER-ENHANCED"]

#: Whether the internet is reachable through the mesh. CONOPS section 50.6.
#: A property of the mesh, not of this node's uplink: section 42 lets any
#: standard MULE hold the authorized gateway role, so a node with no uplink of
#: its own is WAN-ENHANCED when a gateway is reachable.
WanReachability = Literal["NO-WAN", "WAN-ENHANCED"]

#: The graceful-degradation ladder, named in mode terms. CONOPS sections 50.7
#: to 50.9, mapped onto the section 5.5 rungs by `CCR-01`.
BearerCapability = Literal["NOMINAL-IP", "DEGRADED-IP", "LOW-BANDWIDTH", "ISOLATED"]

#: Whether the node is shedding load to preserve energy. CONOPS section 50.10.
EnergyPosture = Literal["NOMINAL-ENERGY", "FIELD-ECONOMY"]

#: Whether the node is prepared for movement or storage. CONOPS section 50.11.
LifecyclePosture = Literal["OPERATIONAL", "TRANSPORT-SECURE"]

#: Whether the node is deliberately reducing its signature. CONOPS section
#: 50.12.
EmissionPosture = Literal["NORMAL-EMISSION", "EMCON-SILENT"]

#: Whether this node's traffic is live or exercise. CONOPS section 50.13.
DataMarking = Literal["LIVE", "EXERCISE"]

#: The bearer whose link places the node on each rung, highest capability
#: first. `CCR-01` maps the CONOPS section 5.5 ladder onto the section 50 axis
#: values; this tuple is that mapping and the only place it is written down.
#:
#: `wifi_ap` is deliberately absent. It serves end user devices rather than
#: carrying traffic between nodes, so it cannot raise the rung. Section 50.9
#: describes ISOLATED as retaining "local EUD and node capability only", which
#: is an access point still serving with no inter-node bearer linked.
CAPABILITY_LADDER: tuple[tuple[Bearer, BearerCapability], ...] = (
    ("wifi_mesh", "NOMINAL-IP"),
    ("halow", "DEGRADED-IP"),
    ("lora", "LOW-BANDWIDTH"),
)


@dataclass(frozen=True)
class ModeInputs:
    """What the caller knows about the node, in plain values.

    No radios, no sensors, no peers. Whatever gathers these deals with
    hardware; this module only reasons about what was gathered, which is what
    lets it run on a laptop with none of it present.
    """

    #: Configuration, not observation. A node cannot tell it is on a bench.
    environment: Environment
    #: Bearers whose hardware is present and whose driver has attached.
    enumerated: tuple[Bearer, ...]
    #: Bearers that have formed their link.
    associated: tuple[Bearer, ...]
    #: Whether this node is running the shared TAK service itself.
    hosting_shared_services: bool
    #: Whether an authorized WAN gateway is reachable through the mesh.
    #: `None` where the node has no way to tell.
    wan_reachable: bool | None
    #: What `mule/power.py` concluded, which is where FIELD-ECONOMY comes from.
    power: PowerAssessment
    #: Authorized action, never automatic. `CCR-01` part B would bind that.
    lifecycle: LifecyclePosture
    emission: EmissionPosture
    data_marking: DataMarking


@dataclass(frozen=True)
class ModeAssessment:
    """The node's value on each of the nine axes.

    `None` on an axis means the node cannot determine it, and never means the
    axis is unremarkable. Those are different answers, and the nominal value of
    every axis is named so they cannot collapse into one another: a node with no
    measured power model is `energy=None`, not `NOMINAL-ENERGY`.
    """

    environment: Environment
    deployment: DeploymentContext
    shared_tak: SharedTakService | None
    wan: WanReachability | None
    bearer_capability: BearerCapability
    energy: EnergyPosture | None
    lifecycle: LifecyclePosture
    emission: EmissionPosture
    data_marking: DataMarking

    #: Why an axis is None, one entry per undetermined axis. An operator asking
    #: "why does it not know?" gets an answer rather than a blank.
    undetermined: tuple[tuple[str, str], ...]

    @property
    def degraded_bearer(self) -> bool:
        """Whether the node is below the top of the capability ladder."""
        return self.bearer_capability != "NOMINAL-IP"


def _bearer_capability(associated: tuple[Bearer, ...]) -> BearerCapability:
    """Place the node on the capability ladder from what has linked.

    The highest-capability bearer that has formed a link sets the rung. This is
    a bound, not a measurement: a linked bearer performing badly belongs lower,
    and detecting that needs link quality and the thresholds TBR-RF-01 and
    TBR-RF-02 will set. Association can never place a node higher than it is,
    which is the direction that matters for a fail-safe reading.
    """
    linked = set(associated)
    for bearer, rung in CAPABILITY_LADDER:
        if bearer in linked:
            return rung
    return "ISOLATED"


def _deployment(inputs: ModeInputs) -> DeploymentContext:
    """Say whether this node is meshed with other nodes.

    Association, not fitment. A node carrying an inter-node radio that has not
    linked is STANDALONE, because it is not networked with anything, and a node
    never fitted with one is STANDALONE for a different reason but the same
    operational fact.
    """
    fitted = inter_node_present(inputs.enumerated)
    linked = set(inputs.associated)
    return "NETWORKED" if any(bearer in linked for bearer in fitted) else "STANDALONE"


def assess(inputs: ModeInputs, *, economy_below_minutes: int | None) -> ModeAssessment:
    """Determine the node's value on each of the nine CONOPS section 50 axes.

    `economy_below_minutes` is the projected runtime below which the node sheds
    load, from CONOPS section 50.10. It has no default and belongs to
    `TBR-PWR-01`: a number here would become a fielded energy policy that nobody
    measured. `None` is the honest state today and leaves the axis undetermined.
    """
    undetermined: list[tuple[str, str]] = []

    # A node knows whether it hosts the service itself. It cannot know whether a
    # peer does: that is the Service Authority Registry, which FML-ADR-049 folds
    # into the status aggregator and TBR-TAK-01 blocks. Reporting SERVERLESS-TAK
    # on a mesh where a peer is hosting would be wrong in the direction that
    # makes an operator stop trusting the display.
    shared_tak: SharedTakService | None
    if inputs.hosting_shared_services:
        shared_tak = "SERVER-ENHANCED"
    else:
        shared_tak = None
        undetermined.append(
            (
                "shared_tak",
                "This node is not hosting, and cannot see whether a peer is. "
                "TBR-TAK-01 and FML-ADR-049 decide that.",
            )
        )

    wan: WanReachability | None
    if inputs.wan_reachable is None:
        wan = None
        undetermined.append(
            ("wan", "Nothing reports whether a WAN gateway is reachable.")
        )
    else:
        wan = "WAN-ENHANCED" if inputs.wan_reachable else "NO-WAN"

    # FIELD-ECONOMY is shedding load to preserve energy, so it needs both how
    # much energy is left and the point below which shedding starts. Either
    # missing leaves the axis undetermined. An unmeasured node must not report
    # itself nominal: that is the claim this repository has made wrongly four
    # times, most recently a thermal fake asserting an envelope nobody had set.
    energy: EnergyPosture | None
    runtime = inputs.power.projected_runtime_minutes
    if runtime is None:
        energy = None
        undetermined.append(
            (
                "energy",
                inputs.power.reason or "No runtime estimate, and no reason given.",
            )
        )
    elif economy_below_minutes is None:
        energy = None
        undetermined.append(
            (
                "energy",
                "No economy threshold. TBR-PWR-01 has not closed, so nothing "
                "says how little runtime is little enough to shed load.",
            )
        )
    else:
        energy = (
            "FIELD-ECONOMY" if runtime < economy_below_minutes else "NOMINAL-ENERGY"
        )

    return ModeAssessment(
        environment=inputs.environment,
        deployment=_deployment(inputs),
        shared_tak=shared_tak,
        wan=wan,
        bearer_capability=_bearer_capability(inputs.associated),
        energy=energy,
        lifecycle=inputs.lifecycle,
        emission=inputs.emission,
        data_marking=inputs.data_marking,
        undetermined=tuple(undetermined),
    )
