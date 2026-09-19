"""Addressing a message to an EUD recipient over the LoRa bearer.

`TBR-NET-02` decided *how* a node addresses the EUDs behind it, and `FML-ADR-070`
fixed the encoding: identity rides in upstream's own fields -- the sender in
`Contact.callsign`, the recipient in `GeoChat.to` -- on a Meshtastic payload whose
usable size is 231 bytes, with no custom member index. Two rules follow from that
and are what this module enforces:

    Because the usable payload is 231 bytes and a callsign now shares it with the
    message, composed messages shall be constrained by an artificial character
    limit ... so a message plus its identity fields fits the usable payload.
    (`FML-ADR-070`)

    A node that cannot resolve the intended member shall not deliver to every EUD.
    ... deliver to a configured default and mark it redirected, or do not deliver.
    Both branches fail closed relative to broadcasting.
    (`docs/evidence/TBR-NET-02/2026-08-29-addressing-specification.md`, CONOPS 23)

These are pure functions of values a caller passes in (`FML-ADR-052`): they read
nothing, hold no state, and invent no numbers. Two things `TBR-NET-02` deliberately
left for later are **not** done here and are passed in rather than derived:

- The **roster** (callsign/member -> device) is a `Mapping` argument. The mission
  package has no roster field today; adding one is a schema change `TBR-NET-02`
  named and declined, and `TBR-ID-01` later governs the identity half. Until then
  the caller supplies whatever mapping exists (empty is fine, and fails closed).
- Parsing `GeoChat.to` into a `recipient_key` is upstream's job, not this module's;
  its exact contents were not established when `FML-ADR-070` was written.

It lives in `mule/` because it is a decision the node makes while running
(`FML-ADR-051`); the blocked `services/gateways/` component names it per
`FML-ADR-052`.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True)
class LoraPayloadBudget:
    """The byte budget a composed LoRa message must fit within.

    `usable_bytes` is transcribed from `FML-ADR-070`: the Meshtastic payload's
    usable size is **231**, "not the 233 the protobuf advertises". The framing
    overhead a callsign and recipient tag cost on the wire is measurable, not
    named by any controlling document, so it is caller policy with **no default** --
    the discipline `mule.capability.CapabilityPolicy` uses for its thresholds.
    """

    usable_bytes: int
    framing_overhead_bytes: int


def usable_body_bytes(
    sender_callsign: str, recipient_tag: str, budget: LoraPayloadBudget
) -> int:
    """Bytes left for the message body after the identity fields and framing.

    The recipient's user-tag and the sender callsign share the 231-byte payload
    (`FML-ADR-070`), so both are subtracted here. The result is **signed**: a
    negative value means the identity fields alone already exceed the budget, so
    not even an empty body fits -- do not clamp it, the sign carries that fact.
    """
    identity_bytes = len(sender_callsign.encode()) + len(recipient_tag.encode())
    return budget.usable_bytes - identity_bytes - budget.framing_overhead_bytes


def fits_payload(
    body: str, sender_callsign: str, recipient_tag: str, budget: LoraPayloadBudget
) -> bool:
    """Whether body plus identity fields fits the usable payload.

    The addressing specification makes this a hard rule: the writer "shall refuse
    a payload over 231 bytes rather than hand it to a sender that accepts and
    discards it." A body over the remaining budget does not fit.
    """
    return len(body.encode()) <= usable_body_bytes(
        sender_callsign, recipient_tag, budget
    )


#: The delivery decision for a message whose recipient may or may not resolve.
#: Transcribed from the addressing specification's two fail-closed branches plus
#: the resolved case; there is deliberately no "broadcast" member (CONOPS 23).
Delivery = Literal["DELIVER", "REDIRECT", "REFUSE"]


@dataclass(frozen=True)
class DeliveryDecision:
    """Where a message goes, with a diagnosable reason.

    `target` is the resolved device for `DELIVER`, the default recipient for
    `REDIRECT`, and `None` for `REFUSE`. `reason` is `None` for the clean
    `DELIVER` case, the same shape `mule.addressing.OverlapAssessment` uses.
    """

    delivery: Delivery
    target: str | None
    reason: str | None


def decide_delivery(
    recipient_key: str, roster: Mapping[str, str], default_recipient: str | None
) -> DeliveryDecision:
    """Decide delivery for a named recipient, failing closed on the unresolved.

    `recipient_key` is whatever a future upstream step parsed from `GeoChat.to`
    (not decided here). `roster` maps a recipient key to a device; the mission
    package carries no roster yet (`TBR-NET-02`/`TBR-ID-01`), so an empty mapping
    is expected and simply fails closed. A resolved key delivers; an unresolved
    key redirects to a configured default (marked redirected) or refuses. It
    **never** delivers to everyone -- that is the CONOPS section 23 rule this
    exists to hold.
    """
    target = roster.get(recipient_key)
    if target is not None:
        return DeliveryDecision("DELIVER", target, None)
    if default_recipient is not None:
        return DeliveryDecision(
            "REDIRECT",
            default_recipient,
            f"recipient {recipient_key!r} unresolved; redirected to the default",
        )
    return DeliveryDecision(
        "REFUSE",
        None,
        f"recipient {recipient_key!r} unresolved and no default; not delivered",
    )
