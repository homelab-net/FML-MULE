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
class ThermalState(Protocol):
    """Read-only thermal state."""

    def throttled(self) -> bool:
        """Whether the compute element is currently thermally throttled."""
        ...

    def within_envelope(self) -> bool:
        """Whether all monitored sensors are inside their stated limits.

        What those limits are is TBR-THERM-01. A fake answers from its script;
        a real implementation cannot answer at all until that trade closes.
        """
        ...


# Power state is not here either: `mule/power.py` splits it into raw
# `PowerReadings` and an `assess` that turns them into a runtime estimate,
# for the same reason as time. Deciding how long a node will keep running
# is a judgement, and a fake making it on the node's behalf is untestable.
#
# Time state is deliberately **not** here. It lives in `timekeeping.py`, split
# into raw `TimeReadings` and an `assess` function that decides what they mean.
# The two interfaces above report facts a sensor can state directly; time
# credibility is a judgement, and a judgement a fake makes on the node's behalf
# is a judgement nobody has tested. See `FML-ADR-042`.
