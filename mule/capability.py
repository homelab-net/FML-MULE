"""What a link to a peer can carry: video, voice, text, or nothing.

`FML-ADR-080` names the per-peer capability tiers as the per-link view of the
CONOPS section 50 ladder, and fixes the discipline this function follows:

    The passive derivation shall only rule a tier out or report it as a
    ceiling; it shall not assert that a tier is achievable end to end.

So this reports the highest tier the passive signals do not rule out -- a
ceiling, not a promise. Item 1.9's paced active probe is what would confirm a
tier is actually reachable end to end; this function never does.

It is a pure function of values a caller passes in (`FML-ADR-052`): batman-adv
transmit quality, the `iw` PHY-rate ceiling, the bearer, and the hop count. It
reads nothing -- the radio reader stays in the software digital twin pending
`TBR-LINUX-01`/`TBR-RF-01`/`TBR-RF-03` -- and it invents no thresholds: the cut
points are `TBR-RF-01`'s, handed in as `CapabilityPolicy` with no compiled-in
defaults, the readings-versus-policy split `mule.timekeeping.assess` uses. It
lives in `mule/` because it is a decision the node makes while running
(`FML-ADR-051`).

`UNKNOWN` is not `NONE`: a link with no readable signal has not been shown to be
down, and `FML-ADR-080` (through `FML-ADR-052`) requires "cannot tell" to say so
rather than fall to a definite answer.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from .bearers import Bearer

#: The per-peer capability tiers of `FML-ADR-080`: `VIDEO` is the per-link
#: `NOMINAL-IP`, `VOICE` the `DEGRADED-IP`, `TEXT` the `LOW-BANDWIDTH`, `NONE`
#: the `ISOLATED`. `UNKNOWN` is the "cannot tell" member `FML-ADR-052` requires.
Tier = Literal["VIDEO", "VOICE", "TEXT", "NONE", "UNKNOWN"]

#: Capability order, most restrictive first, for taking the lowest ceiling.
#: `NONE` and `UNKNOWN` are decided before this is used, so they are not in it.
_ORDER: tuple[Tier, ...] = ("TEXT", "VOICE", "VIDEO")


@dataclass(frozen=True)
class CapabilityPolicy:
    """The thresholds that map a passive signal to a tier ceiling.

    Every value is `TBR-RF-01`'s to set on measured hardware; `FML-ADR-080`
    keeps them out of this module and out of the ADR. There are no defaults on
    purpose -- a caller that has not chosen thresholds has not earned a tier, the
    reason `mule.timekeeping.TimePolicy` has none either.
    """

    #: PHY-rate ceiling (Mb/s) at or above which VIDEO / VOICE are not ruled out.
    video_min_mbps: float
    voice_min_mbps: float
    #: batman-adv TQ (0-255) at or above which VIDEO / VOICE are not ruled out.
    video_min_tq: int
    voice_min_tq: int
    #: TQ at or below which the link is unusable -- a per-link `ISOLATED`.
    unreachable_at_or_below_tq: int
    #: Hop count at or below which VIDEO / VOICE are not ruled out.
    video_max_hops: int
    voice_max_hops: int


def _ceiling_from_mbps(mbps: float, policy: CapabilityPolicy) -> Tier:
    if mbps >= policy.video_min_mbps:
        return "VIDEO"
    if mbps >= policy.voice_min_mbps:
        return "VOICE"
    return "TEXT"


def _ceiling_from_tq(tq: int, policy: CapabilityPolicy) -> Tier:
    if tq >= policy.video_min_tq:
        return "VIDEO"
    if tq >= policy.voice_min_tq:
        return "VOICE"
    return "TEXT"


def _ceiling_from_hops(hops: int, policy: CapabilityPolicy) -> Tier:
    if hops <= policy.video_max_hops:
        return "VIDEO"
    if hops <= policy.voice_max_hops:
        return "VOICE"
    return "TEXT"


def capability_tier(
    bearer: Bearer | None,
    bitrate_mbps: float | None,
    tq: int | None,
    hops: int | None,
    policy: CapabilityPolicy,
) -> Tier:
    """Report the highest tier the passive signals do not rule out.

    A ceiling, never a promise (`FML-ADR-080`). Each present signal contributes a
    ceiling and the most restrictive one wins. `NONE` comes only from a measured
    TQ at or below the unreachable floor; `UNKNOWN` when no signal rules anything
    out -- never inferred silently as `NONE`.
    """
    # LoRa is a text-only, non-IP plane; no IP-side signal raises it above TEXT
    # (`FML-ADR-026`, the TEXT rung of `FML-ADR-080`).
    if bearer == "lora":
        return "TEXT"

    # A measured TQ at or below the floor is a link shown to be unusable: the
    # per-link `ISOLATED` of `FML-ADR-080`. Only a measured value says this; a
    # missing TQ is "cannot tell", handled below, not `NONE`.
    if tq is not None and tq <= policy.unreachable_at_or_below_tq:
        return "NONE"

    ceilings: list[Tier] = []
    if tq is not None:
        ceilings.append(_ceiling_from_tq(tq, policy))
    # The PHY-rate ceiling is an upper bound, not a goodput (`FML-ADR-053`).
    if bitrate_mbps is not None:
        ceilings.append(_ceiling_from_mbps(bitrate_mbps, policy))
    if hops is not None:
        ceilings.append(_ceiling_from_hops(hops, policy))

    if not ceilings:
        return "UNKNOWN"
    return min(ceilings, key=_ORDER.index)
