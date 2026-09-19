"""Tests for `mule.recipients`.

Two rules from `FML-ADR-070` and the `TBR-NET-02` addressing specification: a
composed LoRa message plus its identity fields must fit the 231-byte usable
payload, and an unresolved recipient must fail closed -- never broadcast to every
EUD (CONOPS section 23). The budget thresholds here are illustrative caller
policy, not `TBR-RF-01`/wire-measured values; the point is the rules.
"""

from __future__ import annotations

from mule.recipients import (
    LoraPayloadBudget,
    decide_delivery,
    fits_payload,
    usable_body_bytes,
)

# Illustrative: 231 usable (FML-ADR-070), 6 bytes of framing overhead (a stand-in
# for the measurable protobuf field cost, supplied rather than invented in code).
BUDGET = LoraPayloadBudget(usable_bytes=231, framing_overhead_bytes=6)

SENDER = "RIDGE6"  # 6 bytes
RECIPIENT = "BASE"  # 4 bytes; identity = 10, framing = 6, so body budget = 215


# --- payload budget ---------------------------------------------------------


def test_usable_body_bytes_after_identity_and_framing() -> None:
    assert usable_body_bytes(SENDER, RECIPIENT, BUDGET) == 215


def test_body_exactly_at_budget_fits() -> None:
    assert fits_payload("x" * 215, SENDER, RECIPIENT, BUDGET) is True


def test_body_one_over_budget_is_refused() -> None:
    assert fits_payload("x" * 216, SENDER, RECIPIENT, BUDGET) is False


def test_recipient_user_tag_shrinks_the_body_budget() -> None:
    # A longer recipient tag consumes more of the 231 bytes, leaving less for body.
    short = usable_body_bytes(SENDER, "BASE", BUDGET)
    long = usable_body_bytes(SENDER, "LONG-CALLSIGN", BUDGET)
    assert long < short


def test_body_budget_is_signed_when_identity_alone_exceeds_it() -> None:
    tiny = LoraPayloadBudget(usable_bytes=8, framing_overhead_bytes=6)
    # 8 - 10 - 6 = -8: the identity fields alone blow the budget.
    assert usable_body_bytes(SENDER, RECIPIENT, tiny) < 0
    # So not even an empty body fits.
    assert fits_payload("", SENDER, RECIPIENT, tiny) is False


# --- fail-closed delivery ---------------------------------------------------


def test_deliver_when_the_recipient_resolves() -> None:
    decision = decide_delivery("BASE", {"BASE": "eud-7"}, None)
    assert decision.delivery == "DELIVER"
    assert decision.target == "eud-7"
    assert decision.reason is None


def test_refuse_when_unresolved_and_no_default() -> None:
    decision = decide_delivery("GHOST", {}, None)
    assert decision.delivery == "REFUSE"
    assert decision.target is None


def test_redirect_to_default_when_unresolved() -> None:
    decision = decide_delivery("GHOST", {}, "TOC")
    assert decision.delivery == "REDIRECT"
    assert decision.target == "TOC"


def test_unresolved_never_delivers_to_everyone() -> None:
    # The whole point of the rule: no unresolved path becomes a broadcast.
    for default in (None, "TOC"):
        decision = decide_delivery("NOBODY", {"BASE": "eud-7"}, default)
        assert decision.delivery != "DELIVER"
