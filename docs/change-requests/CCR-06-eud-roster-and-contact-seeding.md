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

The grounding this follows established that `GeoChat.to` carries the recipient's
**id** (a DM's recipient id, a room's name), not uniformly a callsign, and that the
callsign-to-id binding lives in the contact list. `mule/recipients.py.decide_delivery`
already resolves a recipient key against a roster and **fails closed** on the
unresolved -- so the missing piece is *where the roster comes from and how it is
kept current*.

This request holds that the proposal is **two decisions with two owners**, and that
they must be decided separately because they have very different cost.

## Part A -- the addressing roster (callsign -> device), cheap and recommended

A static mapping from a member callsign to a delivery device (an EUD UID, or a mesh
node for an EUD behind the gateway). This is what makes "DM the callsign, not the
radio" work, and it has near-zero emission cost -- it is configuration, not a
transmission.

Owner to choose the **source of truth**:

1. A **mission-package roster field** (none exists today; `TBR-NET-02` named and
   declined it). Simple, static, per-deployment.
2. **`FML-ADR-047` Mission Trust Service** issuing signed enrollment/role state --
   the closest existing mechanism; it already distributes signed role and scope
   policy from an authorized mission or enrollment function.
3. A **gateway-maintained registry** for mesh EUDs that never connect to OTS (the
   `FML-ADR-048` gateway holds callsign<->node), fed by (1) or (2).

Constraints to carry into whichever is chosen:

- **Callsign uniqueness.** LoRa has no per-deployment boundary by default, so two
  deployments' identical callsigns collide and misdeliver
  (`docs/evidence/TBR-NET-02/2026-08-30-the-eud-code-must-be-unique-to-everyone-who-can-hear-it.md`).
  Uniqueness is enforced where the roster is issued (enrollment).
- **Fail closed.** An unresolved callsign must not broadcast; it redirects to a
  configured default (marked redirected) or refuses -- already `recipients.py`.

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
