"""Narrow interfaces over hardware state.

`AGENTS.md`, the governing code rule:

> Every function that reads or controls radio, power, thermal, or time state
> **shall** sit behind a narrow interface with a fake or recorded-fixture
> implementation.

These Protocol definitions are that contract. They are deliberately small: each
describes what the node needs to *know*, not what a driver can *do*. A wide
interface is one nobody can fake honestly.

**Location note.** A production package now exists, `mule/`, per
`FML-ADR-051`, and these Protocols deliberately did **not** move into it.

They overlap the radio abstraction for the network plane, which
`docs/interfaces/README.md` records as blocked on `TBR-LINUX-01`, `TBR-RF-01`
and `TBR-RF-03`. Promoting them to production would be defining a blocked
interface by relocating a file, which is the same act under a quieter name.

They stay here until either those trades close or a consumer outside the
flat-sat needs them. `mule/timekeeping.py` moved because the decision it makes
is `FML-ADR-042`, which is decided; these describe boundaries that are not.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from mule.bearers import Bearer

# The `Bearer` vocabulary moved to `mule/bearers.py`: it names the node's radio
# functions per FML-ADR-045, which is decided, and production code needs it.
# The Protocols below stayed, for the reason in the location note above.


@runtime_checkable
class RadioState(Protocol):
    """Read-only radio state.

    Narrow means what the node actually reads, not what a driver could report.
    Methods are added when a consumer exists, never in anticipation of one: a
    method nothing calls is surface nobody has had to fake honestly.

    Deliberately excludes anything that transmits or reconfigures. A node's
    status surface reads; it does not command. FML-ADR-028 keeps network and RF
    configuration on the privileged side of the plane boundary, and this
    interface stays on the reading side of it.
    """

    def enumerated(self) -> list[Bearer]:
        """Bearers whose hardware is present and whose driver has attached."""
        ...

    def associated(self, bearer: Bearer) -> bool:
        """Whether the bearer has formed its link: mesh peer, or AP serving."""
        ...


@runtime_checkable
class LoRaPlane(Protocol):
    """Read-only state of the non-IP LoRa plane.

    Separate from `RadioState` on purpose, and the separation is the point.
    `FML-ADR-026` makes LoRa a distinct non-IP plane and states the trap
    outright: do not let it inherit the IP plane's vocabulary.
    `RadioState.associated` means "mesh peer, or AP serving". A LoRa chain does
    neither. Asking it whether it has "associated" is asking an 802.11 question
    of something that is not 802.11, and the answer means nothing.

    What the node actually needs to know about this plane is narrower: whether
    the stack that carries it is answering. `.github/workflows/lora-probe.yml`
    established, at the cost of a run, that changing a node's configuration
    reboots the daemon and that in the container image the re-exec fails and
    the process exits. So a node can have a LoRa radio enumerated and attached
    while nothing at all can carry a message over it.

    That matters more here than it would elsewhere. `FML-ADR-026` makes this
    the degraded-mode lifeline and CONOPS section 50.8 puts it at the bottom of
    the ladder, so it is the bearer whose false "available" is least tolerable:
    it is what an operator falls back to when everything else has gone.

    Deliberately excludes anything that transmits, addresses or reconfigures.
    Addressing on this plane is `TBR-NET-02`, which is open;
    `docs/evidence/TBR-NET-02/2026-08-29-addressing-specification.md` specifies
    it but a trade closes when a named owner accepts evidence, and every owner
    is `TBD-SRR`. Nothing here encodes a member tag, a node number or a
    recipient, because that is the open question and not this interface's.
    """

    def stack_responding(self) -> bool | None:
        """Whether the LoRa stack answers, or None where that cannot be told.

        `None` is not a polite "no". It is the platform saying it cannot
        determine the state: no API endpoint configured, or a socket that
        neither answers nor refuses. A caller deciding whether the lifeline is
        usable must treat that as its own case and not as either answer.
        """
        ...


# Time, power and thermal state are deliberately **not** here. Each lives in
# `mule/`, split into raw readings and an `assess` that decides what they mean:
# `timekeeping.py`, `power.py`, `thermal.py`.
#
# The split is always the same question. Can a sensor state this directly, or
# does somebody have to judge it? Whether a radio has associated is a fact.
# Whether retained time is credible, how long a battery will last, and whether
# a temperature is inside an envelope are judgements, and a judgement a fake
# makes on the node's behalf is a judgement nobody has tested.
#
# `RadioState` is the only interface left here, and the location note above
# says why it stays.
