"""Fakes for the hardware interfaces.

Every fake in this file is listed in `test/flatsat/README.md`. That listing is a
rule, not a courtesy: a reader must be able to see exactly which boundary is
simulated, and an unlisted fake is how "it works on the flat-sat" becomes a
permanent excuse.

Each fake is scripted, not modelled. `FakePower` does not simulate a battery
discharge curve, because no measured curve exists and inventing one would put a
plausible number into a test that later gets quoted. It returns what the
scenario told it to return, and nothing else.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .interfaces import Bearer, TimeCredibility


@dataclass
class FakeRadio:
    """Scripted radio state.

    Simulates: driver attachment, link formation and peer visibility.
    Does not simulate: RF propagation, throughput, desense, multicast scaling,
    or anything else TBR-RF-01, TBR-RF-02 and TBR-RF-03 exist to measure.
    """

    present: list[Bearer] = field(default_factory=lambda: ["halow", "wifi_ap", "lora"])
    linked: list[Bearer] = field(default_factory=lambda: ["halow", "wifi_ap", "lora"])
    peers: dict[Bearer, int] = field(default_factory=dict)

    def enumerated(self) -> list[Bearer]:
        """Bearers whose hardware is present and whose driver has attached."""
        return list(self.present)

    def associated(self, bearer: Bearer) -> bool:
        """Whether the bearer has formed its link."""
        return bearer in self.linked

    def peer_count(self, bearer: Bearer) -> int:
        """Peers currently visible on the bearer."""
        return self.peers.get(bearer, 0)


@dataclass
class FakePower:
    """Scripted power state.

    Simulates: external power presence, pack presence, pack health.
    Does not simulate: consumption, endurance or runtime. `projected_runtime`
    returns None because TBR-PWR-01 has not closed and no measured load model
    exists.
    """

    external: bool = True
    battery: bool = False
    healthy: bool = True

    def on_external_power(self) -> bool:
        """Whether an approved external source is supplying the node."""
        return self.external

    def battery_present(self) -> bool:
        """Whether a protected battery assembly is fitted."""
        return self.battery

    def battery_healthy(self) -> bool:
        """Whether the pack reports itself within its operating envelope."""
        return self.battery and self.healthy

    def projected_runtime_minutes(self) -> int | None:
        """Return None always. No power model exists; see TBR-PWR-01."""
        return None


@dataclass
class FakeThermal:
    """Scripted thermal state.

    Simulates: a throttle flag and an in-envelope flag.
    Does not simulate: temperature, heat flow, ambient sensitivity or the
    enclosure. TBR-THERM-01 measures those and needs hardware.
    """

    is_throttled: bool = False
    in_envelope: bool = True

    def throttled(self) -> bool:
        """Whether the compute element is currently thermally throttled."""
        return self.is_throttled

    def within_envelope(self) -> bool:
        """Whether all monitored sensors are inside their stated limits."""
        return self.in_envelope


@dataclass
class FakeClock:
    """Scripted retained local time.

    Simulates: whether retained time is credible, and why not when it is not.
    Does not simulate: drift, holdover duration or skew. Those are TBR-TIME-01
    and are bound by elapsed time on real hardware.

    The default is credible. `dead_backup_cell()` produces the case
    FML-ADR-042 was written for: an RTC whose backup cell has failed, where the
    node must refuse to validate rather than accept credentials it cannot check.
    """

    is_credible: bool = True
    why_not: str | None = None

    def credibility(self) -> TimeCredibility:
        """Whether retained time is plausible enough for trust validation."""
        return "CREDIBLE" if self.is_credible else "DEGRADED"

    def reason(self) -> str | None:
        """Why time is not credible, for the operator."""
        return None if self.is_credible else self.why_not

    @classmethod
    def dead_backup_cell(cls) -> FakeClock:
        """Build a node whose RTC backup cell has failed."""
        return cls(
            is_credible=False,
            why_not=(
                "RTC backup cell depleted; retained time implausible. "
                "Trust validation is refused rather than failing open. "
                "Replace the backup cell and re-establish time."
            ),
        )

    @classmethod
    def restored_from_shutdown(cls) -> FakeClock:
        """Build a node with no RTC that restored a plausible-looking time.

        SAD section 24.5.1 calls this out as worse than having no clock,
        because it looks valid. The node must still refuse.
        """
        return cls(
            is_credible=False,
            why_not=(
                "No retained time source; system time restored from last "
                "shutdown and cannot be trusted. A plausible-looking time is "
                "not a credible one."
            ),
        )
