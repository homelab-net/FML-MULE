# CCR-06 EUD roster and contact seeding

**Type:** CONOPS change request
**Status:** `OPEN` -- proposed; awaiting the Program Owner's decision.
**Target version:** CONOPS (increment TBD on acceptance)
**Raised by:** the 2026-09-28 Owner question, following the GeoChat-encoding
grounding (`docs/evidence/TBR-NET-02/2026-09-28-real-geochat-encoding-through-ots.md`).
**Decision:** no ADR proposed here. The mechanism questions route to existing
owners: `FML-ADR-047` (Mission Trust Service) and a mission-package field for the
roster; `TBR-EMCON-01` for presence. This request selects nothing.

## Statement

An operator should be able to address a message to a **person by callsign** and
have it delivered to that person, rather than messaging a **mesh radio** and not
knowing whether -- or to whom -- it was delivered. The Owner proposes that **every
EUD enlist and publish itself as a callsign-addressed contact at enrollment**, so
the contact list / roster is pre-seeded.

The grounding this follows established that the encoder copies the client's `<__chat
id>` into `GeoChat.to` verbatim (in-run a DM's id, a room's name), substituting no
callsign of its own; what a live client places in `<__chat id>` -- a UID by
convention -- is owed a capture, and the callsign-to-id binding lives in the contact
list. `mule/recipients.py.decide_delivery`
already resolves a recipient key against a roster and **fails closed** on the
unresolved -- so the missing piece is *where the roster comes from and how it is
kept current*.

This request holds that the proposal is **two decisions with two owners**, and that
they must be decided separately because they have very different cost.

## Part A -- the addressing bindings (callsign -> key -> device), cheap and recommended

The grounding
(`docs/evidence/TBR-NET-02/2026-09-28-real-geochat-encoding-through-ots.md`) showed a
DM's `GeoChat.to` carries the client's `<__chat id>` (an **id**/UID by ATAK
convention), not the recipient callsign (which is absent from the wire). One caveat
that scopes this decision: the run injected the id, so it proved the encoder's copy,
not that a *live* client places the UID there -- a live-client DM is owed before the
`callsign -> UID` binding is assumed exact. So "DM the callsign, not the radio" needs
**two distinct bindings**, not one -- and conflating them into a single
`callsign -> device` map would leave a normal DM unresolved:

1. **Client contact seeding: `callsign -> key`.** So an operator picks a person by
   callsign and the client addresses that person on the wire by the id it places in
   `<__chat id>` (a UID by convention, pending the owed capture). This is the
   "publish as a contact" half the Owner is asking for.
2. **Node/gateway delivery resolution: `recipient_key -> delivery device`** (an EUD, or
   a mesh node for an EUD behind the gateway). This is `mule/recipients.py`'s roster,
   keyed by the `recipient_key` parsed from `<__chat id>` in `GeoChat.to` -- a UID by
   convention, but the key's shape stays conditional until the owed live-client capture
   (if a client writes a callsign there, the roster keys by that) -- `decide_delivery`
   does an exact `roster.get(recipient_key)`. This
   is the **direct-message** path only: a **room** `GeoChat.to` names a group, so room
   delivery is separate **group fan-out**, not this single-device map -- room-name
   scope is analyzed on its own (see uniqueness below), not routed through
   `decide_delivery`.

Both are configuration with near-zero emission cost. Owner to choose the **source of
truth** for these bindings:

1. A **mission-package roster field** (none exists today; `TBR-NET-02` named and
   declined it). Simple, static, per-deployment.
2. **`FML-ADR-047` Mission Trust Service** issuing signed enrollment/role state --
   the closest existing mechanism; it already distributes signed role and scope
   policy from an authorized mission or enrollment function.
3. A **gateway-maintained registry** for mesh EUDs that never connect to OTS (the
   `FML-ADR-048` gateway holds the recipient-key<->node), fed by (1) or (2).

Constraints to carry into whichever is chosen:

- **Uniqueness is a wire-identifier and room-name concern, not a callsign one.** The
  wire carries whatever the client places in `<__chat id>` for a DM (a UID by
  convention, pending the owed capture) or the room name for a room, so that
  identifier -- whatever it turns out to be -- must be unambiguous to every node that
  can hear it. The `the-eud-code-must-be-unique-to-everyone-who-can-hear-it` evidence
  is about the *retired one-byte index* -- an **invisible** cross-deployment collision
  -- and explicitly contrasts that with duplicate callsign **strings**, which are
  operator-visible. Do not carry that citation into a global callsign-uniqueness rule;
  analyze the **wire identifier** and **room-name** scope separately. (A duplicate
  callsign is a resolvable UX/contact-list issue, not the invisible-misdelivery
  failure.)
- **Fail closed.** An unresolved `recipient_key` must not broadcast; it redirects to
  a configured default (marked redirected) or refuses -- already `recipients.py`.

## Part B -- presence self-publish at enrollment, which carries a conflict to raise

"Publish itself as a contact" can mean two things, and only the second is costly:
seeding a **static roster** (Part A) versus **broadcasting live presence** (periodic
situational-awareness, potentially over LoRa) so the EUD shows as an online contact.

Live presence self-publish conflicts with controlling text and must be decided with
that constraint attached, not assumed:

- **CONOPS v1.2 section 11 (SHALL):** *service activation shall not create externally
  observable behavior that directly and unnecessarily reveals privileged-user login,
  leadership presence, or command structure.* Auto-publishing every EUD's presence,
  and per-person identity on the wire, touches leadership-presence / command-structure
  disclosure directly.
- **`THREAT_MODEL.md` / `mission/profiles/README.md`:** presence is detectable
  whenever anything transmits; an EMCON profile cannot make a transmitting node
  undiscoverable. Auto-presence is a transmission class **`TBR-EMCON-01`** must be
  able to suppress.

**Recommendation:** decide the **roster (Part A)** now -- it delivers the operator
benefit at negligible cost -- and route **presence self-publish (Part B)** to
`TBR-EMCON-01` under the section 11 constraint, so a posture can require it off. Do
not bundle presence into the addressing decision.

## The decision this request asks for

1. Accept that the **addressing roster** is worth adding, and pick its source
   (Part A option 1/2/3).
2. Confirm **presence self-publish** is decided separately under `TBR-EMCON-01` +
   CONOPS section 11, not as part of addressing.
3. On acceptance, the roster's mechanism (schema field and/or MTS issuance) and any
   CONOPS clause are drafted; nothing is built here.

Acceptance would not enlarge `v0.0.1` or change `mule/` beyond what a roster source
later requires. `TBR-NET-02` stays CLOSED; `FML-ADR-070` is unchanged (its
`GeoChat.to`-contents item is now established, above).
