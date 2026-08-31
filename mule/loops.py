"""Whether the node is in a bridging loop, and how it can tell.

`FML-ADR-056` disables `batman-adv`'s bridge loop avoidance and asks for a
detector in exchange. Its words, and the reason this module exists:

    `batman-adv` already exposes what is needed: a client address appearing in
    the translation table under more than one originator, or the node's own
    bridge address arriving from the mesh, are both loop signatures readable
    with `batctl`. That detector does not exist and is named here so it is not
    forgotten.

It exists now. This module decides; it reads nothing and commands nothing.

**A signature is not a diagnosis.** Both conditions have innocent explanations,
and the docstrings say which. What they mean is "look", and the alternative
`FML-ADR-056` names is an operator inferring a loop from a dead mesh.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Literal, Protocol, runtime_checkable

#: A loop signature, named for the observation rather than the conclusion.
#: Neither name says "loop", because neither observation proves one.
Signature = Literal[
    "client_under_more_than_one_originator",
    "own_address_announced_by_a_peer",
]


@runtime_checkable
class TranslationReadings(Protocol):
    """What the node can read about who is reachable where.

    `batman-adv` removed its `sysfs` interface, so both of these come from
    `batctl` over netlink and need that package in the image. See
    `docs/readings.md` under "Translation table".
    """

    def global_translation_entries(self) -> tuple[tuple[str, str], ...] | None:
        """Report (client, originator) pairs, or None if they cannot be read."""
        ...

    def own_addresses(self) -> tuple[str, ...] | None:
        """Report every address belonging to this node, or None if unknown.

        Every one, not just the bridge. `FML-ADR-056` names "the node's own
        bridge address arriving from the mesh", and a loop reproduced on the
        bench put the mesh hard interface's address into the table **first**,
        with the bridge address following. Watching only the bridge detects the
        same loop later. See
        `docs/evidence/TBR-NET-01/2026-08-30-loop-detected-on-the-bench.md`.
        """
        ...


def loop_signatures(observed: TranslationReadings) -> list[Signature]:
    """List the loop signatures present, in the order `Signature` declares them.

    Returns signatures rather than a boolean for the same reason
    `mule.bringup.violations` does: an operator diagnosing a node needs to know
    which observation fired, and cannot recover it from a `True`.

    A reading of `None` yields no signature. The platform being unable to
    answer is not the platform reporting a loop, and treating them alike would
    make a node with no `batctl` look like a node with a broken network.
    """
    found: list[Signature] = []

    entries = observed.global_translation_entries()
    if entries is None:
        return found

    # A client announced by more than one originator means two nodes both claim
    # to reach it, which is what a bridged loop looks like from the outside.
    #
    # INNOCENT EXPLANATION: a device that roamed between two access points and
    # whose old entry has not yet expired. That is why this is a signature and
    # not a fault, and why a caller should look rather than act.
    seen: dict[str, set[str]] = {}
    for client, originator in entries:
        seen.setdefault(client, set()).add(originator)
    if any(len(originators) > 1 for originators in seen.values()):
        found.append("client_under_more_than_one_originator")

    # Any of this node's own addresses arriving from the mesh means a frame
    # left and came back, which is the loop FML-ADR-056 accepts the risk of.
    # Nothing legitimate announces this node's own address to this node.
    mine = observed.own_addresses()
    if mine and _announced_by_a_peer(entries, mine):
        found.append("own_address_announced_by_a_peer")

    return found


def _announced_by_a_peer(
    entries: Sequence[tuple[str, str]], own: Sequence[str]
) -> bool:
    """Whether any originator claims to reach an address this node owns."""
    # Case-insensitive: batctl and ip both print lower case, but a caller
    # assembling these from elsewhere may not, and a missed match here is a
    # loop nobody sees.
    wanted = {address.lower() for address in own}
    return any(client.lower() in wanted for client, _ in entries)
