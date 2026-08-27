"""Narrow interfaces over hardware state.

`AGENTS.md`, the governing code rule:

> Every function that reads or controls radio, power, thermal, or time state
> **shall** sit behind a narrow interface with a fake or recorded-fixture
> implementation.

These Protocol definitions are that contract. They are deliberately small: each
describes what the node needs to *know*, not what a driver can *do*. A wide
interface is one nobody can fake honestly.

**Location note.** These belong to production code, not to tests. They live
under `test/flatsat/` today because no production package exists yet — the first
functional code in this repository is the image and configuration pipeline, and
the service plane waits on trades that have not closed. When a production
package exists, these Protocols move to it unchanged and the fakes in
`fakes.py` implement them from here. Their location reflects that ordering, not
a judgement that they are test-only.
"""

from __future__ import annotations

from typing import Literal, Protocol, runtime_checkable

#: Bearers the node may carry. Four radio functions per FML-ADR-045, of which
#: the EUD access point and the high-rate inter-node mesh are separate logical
#: functions whether or not they share a physical radio.
Bearer = Literal["halow", "wifi_mesh", "wifi_ap", "lora"]


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
class PowerState(Protocol):
    """Read-only power and battery state."""

    def battery_present(self) -> bool:
        """Whether a protected battery assembly is fitted."""
        ...

    def battery_healthy(self) -> bool:
        """Whether the pack reports itself within its operating envelope."""
        ...

    def projected_runtime_minutes(self) -> int | None:
        """Projected runtime, or None where no power model exists.

        None is the correct answer today. TBR-PWR-01 has not closed, there is no
        measured load model, and a number here would be invented. CONOPS
        section 67 asks the operator-facing question; the honest answer until
        that trade closes is that the node cannot say.
        """
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


# Time state is deliberately **not** here. It lives in `timekeeping.py`, split
# into raw `TimeReadings` and an `assess` function that decides what they mean.
# The other three interfaces above report facts a sensor can state directly; time
# credibility is a judgement, and a judgement a fake makes on the node's behalf
# is a judgement nobody has tested. See `FML-ADR-042`.
