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

#: Whether retained local time can be trusted for credential validation.
#: FML-ADR-042: trust validation never fails open on invalid time.
TimeCredibility = Literal["CREDIBLE", "DEGRADED"]


@runtime_checkable
class RadioState(Protocol):
    """Read-only radio state.

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

    def peer_count(self, bearer: Bearer) -> int:
        """Peers currently visible on the bearer. Zero for the access point."""
        ...


@runtime_checkable
class PowerState(Protocol):
    """Read-only power and battery state."""

    def on_external_power(self) -> bool:
        """Whether an approved external source is supplying the node."""
        ...

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


@runtime_checkable
class TimeState(Protocol):
    """Retained local time, and whether it can be trusted.

    FML-ADR-042 makes this security-bearing rather than a convenience:
    certificate validity, credential expiry and revocation freshness all depend
    on it, and a node that restores a plausible-looking time from its last
    shutdown is worse than one with no clock, because it looks valid.
    """

    def credibility(self) -> TimeCredibility:
        """Whether retained time is plausible enough for trust validation."""
        ...

    def reason(self) -> str | None:
        """Why time is not credible, for the operator. None when credible.

        FML-ADR-042 requires the node to report this, so that a refusal to
        validate is diagnosable rather than mysterious.
        """
        ...
