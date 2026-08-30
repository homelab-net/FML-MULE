"""The order a node brings its network plane up in, and what breaks it.

Bring-up ordering is not a style question. `batman-adv` attached to an
interface that is not yet up fails in a way that **looks like a radio fault**,
so a node assembled in the wrong order does not report "wrong order": it
reports something that sends the next person to the antenna.

This module holds the order as data and answers one question about it. It
brings nothing up itself. It names no interface, sets no address and runs no
command, because interface naming is `TBR-LINUX-01`, addressing is
`TBR-NET-01`, and both are open.

**It is not the systemd units.** `docs/ROADMAP-DEV.md` item 1.2 asks for those
too, and they cannot be written without deciding which network management stack
owns link configuration. `os/config/interfaces.conf.template` records that as
undecided. Writing units against `ip` and `batctl` directly is not a way round
it, because that is choosing direct commands over a managed stack, which is the
same decision taken quietly. Whoever writes them opens an ADR first.

Every step name below is transcribed from the bring-up ordering section of
`os/config/interfaces.conf.template`, except `hard_mtu_set`, which comes from
`.github/workflows/mesh-probe.yml`.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Literal, Protocol, runtime_checkable

#: One action in bringing the network plane up.
#:
#: Seven of these are the numbered steps in the bring-up ordering section of
#: os/config/interfaces.conf.template. `hard_mtu_set` is the eighth and comes
#: from the mesh probe rather than the template.
#:
#: The value is 1560 and it is not derived here. batman-adv says it, on every
#: interface add, when the hard interface is too small: "Setting the MTU to
#: 1560 would solve the problem." An earlier version of this comment justified
#: it as a 18-byte header leaving 1500 for the payload, which does not add up
#: and was not where the number came from.
Step = Literal[
    "driver_loaded",
    "link_up",
    "associated",
    "routing_algo_set",
    "hard_mtu_set",
    "mesh_interface_created",
    "mesh_member_added",
    "mesh_interface_up",
    "services_started",
]

#: What must happen before what, as pairs rather than as one sequence.
#:
#: A single ordered list would be easier to read and would state more than is
#: known. Nothing establishes whether the routing algorithm is set before or
#: after the MTU; both are established to come before the add, and a list would
#: have to invent an order between them and would then be enforcing a
#: constraint no evidence supports.
#:
#: Sources, per pair:
#:
#: - The first and the last two are the template's numbered order.
#: - `routing_algo_set` before `mesh_interface_created`, NOT before the first
#:   member is added. `systemd.netdev(5)` on `RoutingAlgorithm=`: "The
#:   algorithm cannot be changed after interface creation." An earlier version
#:   of this file required it only before `mesh_member_added`, which a node can
#:   satisfy while still running the wrong algorithm, because creation comes
#:   first. That is a constraint that permitted the failure it was written for.
#: - `hard_mtu_set` before `mesh_member_added`: the mesh probe. An MTU raised
#:   after the add leaves the mesh fragmenting traffic it should have carried
#:   whole.
#: - `link_up` before `mesh_member_added`: `batman-adv` attached to an
#:   interface that is not yet up fails in a way that looks like a radio fault,
#:   which is the hazard `os/config/interfaces.conf.template` names.
#:
#: `associated` before `mesh_member_added` is deliberately NOT listed, and an
#: earlier version of this file had it. `.github/workflows/mesh-probe.yml` is a
#: counterexample: it attaches `veth` interfaces that associate with nothing,
#: and the mesh forms. `batman-adv` accepts an interface that is up, and
#: association is what makes a WIRELESS member carry rather than what makes the
#: add legal. The evidenced constraint is `link_up`, and stating the stronger
#: one meant enforcing something this repository's own probe violates.
REQUIRED_ORDER: tuple[tuple[Step, Step], ...] = (
    ("driver_loaded", "link_up"),
    ("link_up", "associated"),
    ("link_up", "mesh_member_added"),
    ("routing_algo_set", "mesh_interface_created"),
    ("mesh_interface_created", "mesh_member_added"),
    ("hard_mtu_set", "mesh_member_added"),
    ("mesh_member_added", "mesh_interface_up"),
    ("mesh_interface_up", "services_started"),
)


def violations(performed: Sequence[Step]) -> list[tuple[Step, Step]]:
    """List the ordering rules a bring-up sequence broke, in `REQUIRED_ORDER`.

    `performed` is what the node actually did, in the order it did it.

    A rule is broken when the later step happened and the earlier one either
    happened after it or **did not happen at all**. The second case is the one
    worth stating: adding an interface to the mesh without having set the
    routing algorithm is not a missing step to be tidied up later, it is the
    failure this module exists for, and it produces a mesh that looks up.

    Returns the rules broken rather than a boolean. A caller that only needs to
    know whether the sequence was sound can test the list for emptiness; one
    diagnosing a node needs to know which rule went and cannot recover it from
    a `False`.

    This says nothing about *which* services start, or in what order among
    themselves. `services_started` is one step here. Service policy is
    `FML-ADR-035` and belongs to `services/service-controller/`.
    """
    position = {step: index for index, step in enumerate(performed)}
    broken = []
    for earlier, later in REQUIRED_ORDER:
        if later not in position:
            continue
        if earlier not in position or position[earlier] > position[later]:
            broken.append((earlier, later))
    return broken


#: The MTU batman-adv asks for on a hard interface carrying the mesh.
#:
#: Not derived. The module prints it when the interface is too small: "Setting
#: the MTU to 1560 would solve the problem." See `.github/workflows/mesh-probe.yml`.
BATMAN_HARD_MTU_BYTES = 1560

#: A bring-up invariant that a finished node either holds or does not.
#:
#: Named for the rule rather than for a symptom, because the symptom is the
#: problem: every one of these presents as a radio fault.
Invariant = Literal[
    "routing_algo_not_the_intended_one",
    "bridge_loop_avoidance_enabled_on_the_mesh",
    "hard_mtu_below_batman_minimum",
    "mesh_has_no_members",
]


@runtime_checkable
class MeshReadings(Protocol):
    """Raw readings from a node's mesh, taken after bring-up has finished.

    A `Protocol` and not a dataclass, which is the whole point. Every other
    reading in `mule/` arrives through one -- `ThermalReadings`,
    `PowerReadings`, `TimeReadings` -- and `tools/list-readings.py` walks
    Protocol classes to check that each reading has a row in
    `docs/readings.md`. An earlier version of this file carried the same four
    values as a plain dataclass, so the check could not see them and they were
    added with no statement of where they come from, which is the
    `mule/thermal.py` failure that file exists to prevent.

    **Where these come from is not obvious.** batman-adv has removed its
    `sysfs` interface: on kernel 6.12 a `batadv` device has no `mesh/`
    directory at all. Three of the four are `batctl` over netlink and need that
    package in the image. Only the MTU is a plain kernel read. See
    `docs/readings.md` under "Mesh state".

    Every method returns `T | None`. `None` is the platform saying it cannot
    answer, which is a different thing from an invariant being broken.
    """

    def routing_algo(self) -> str | None:
        """Report the algorithm the mesh interface is actually running."""
        ...

    def bridge_loop_avoidance(self) -> bool | None:
        """Report whether bridge loop avoidance is on, from the mesh interface."""
        ...

    def hard_mtu_bytes(self) -> int | None:
        """Report the MTU of the hard interface carrying the mesh."""
        ...

    def mesh_member_count(self) -> int | None:
        """Report how many interfaces are attached to the mesh."""
        ...


def state_violations(
    observed: MeshReadings, intended_routing_algo: str
) -> list[Invariant]:
    """List the bring-up invariants a finished node is not holding.

    **This cannot verify the order, and it is important to say why rather than
    let a caller assume otherwise.** The order is temporal and the state is a
    snapshot. A node that did things in the wrong order can arrive at a correct
    end state, which is exactly what makes the failure this module exists for
    hard to catch: `mule.bringup.violations` checks a sequence somebody
    recorded, and if nobody recorded one there is nothing to check.

    What this does instead is check the invariants a wrong order **breaks
    detectably**. There are two kinds, and the difference matters:

    - **Leaves a trace.** `batman-adv` fixes the routing algorithm for an
      interface when the interface is added, so setting it afterwards changes
      nothing. A mesh running an algorithm that is not the intended one is
      therefore evidence that the algorithm was set late or never, and it is
      the sharpest thing here because `FML-ADR-053` chose BATMAN-IV
      deliberately and a node quietly running something else has undone that.
    - **Leaves no trace.** An MTU raised after the add ends with the hard
      interface at the right value anyway. This check sees the value, not when
      it was set, so a late MTU passes. That gap is real and is not closed
      here; a recorded sequence is the only thing that closes it.

    `None` for any reading is not a violation. The platform saying it cannot
    answer is a different thing from the platform saying the invariant is
    broken, and treating them alike is how a node with no instrumentation comes
    to look faulty.
    """
    broken: list[Invariant] = []

    algo = observed.routing_algo()
    if algo is not None and algo != intended_routing_algo:
        broken.append("routing_algo_not_the_intended_one")

    # FML-ADR-056 disables bridge loop avoidance on the mesh interface and asks
    # for a loop detector in exchange. Enabled here means the decision is not
    # in force on this node, whatever the configuration says.
    if observed.bridge_loop_avoidance() is True:
        broken.append("bridge_loop_avoidance_enabled_on_the_mesh")

    mtu = observed.hard_mtu_bytes()
    if mtu is not None and mtu < BATMAN_HARD_MTU_BYTES:
        broken.append("hard_mtu_below_batman_minimum")

    # A mesh with nothing attached is the shape a node has when the add failed,
    # which is what attaching to an interface that was not up produces.
    members = observed.mesh_member_count()
    if members is not None and members < 1:
        broken.append("mesh_has_no_members")

    return broken
