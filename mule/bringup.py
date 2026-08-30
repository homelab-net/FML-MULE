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
from typing import Literal

#: One action in bringing the network plane up.
#:
#: Seven of these are the numbered steps in the bring-up ordering section of
#: os/config/interfaces.conf.template. `hard_mtu_set` is the eighth and comes
#: from the mesh probe rather than the template: batman-adv adds 18 bytes of
#: header, so a hard interface carrying the mesh needs an MTU of 1560 to leave
#: 1500 for the payload, and it has to be set before the add rather than after.
Step = Literal[
    "driver_loaded",
    "link_up",
    "associated",
    "routing_algo_set",
    "hard_mtu_set",
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
#: - The first three and the last two are the template's numbered order.
#: - `routing_algo_set` before `mesh_member_added`: the mesh probe sets the
#:   algorithm before any interface joins. batman-adv fixes the algorithm for
#:   an interface at the moment it is added, so setting it afterwards changes
#:   nothing and reads as though it had.
#: - `hard_mtu_set` before `mesh_member_added`: same probe. An MTU raised after
#:   the add leaves the mesh fragmenting traffic it should have carried whole.
#:
#: `link_up` before `mesh_member_added` is deliberately NOT listed. It follows
#: from `link_up` before `associated` before `mesh_member_added`, and a second
#: rule saying the same thing makes both easier to ignore.
REQUIRED_ORDER: tuple[tuple[Step, Step], ...] = (
    ("driver_loaded", "link_up"),
    ("link_up", "associated"),
    ("associated", "mesh_member_added"),
    ("routing_algo_set", "mesh_member_added"),
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
