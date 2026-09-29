---
id: FML-ADR-087
title: The EUD addressing roster is signed enrollment state carried by the Mission Trust Service
status: SELECTED
date: 2026-09-29
supersedes: none
superseded-by: none
trades: []
verification: TBD
---

# FML-ADR-087 The EUD addressing roster is signed enrollment state carried by the Mission Trust Service

## Context

`CCR-06` (ACCEPTED, 2026-09-29) decided that an operator addresses a person by
callsign and the message reaches that person, which needs an addressing roster:
`callsign -> key -> delivery device`, where `key` is what a client places in
`<__chat id>` (a UID by convention, pending the owed live-client capture) and the
delivery device is what `mule/recipients.py.decide_delivery` resolves. `CCR-06`
asked the Program Owner to pick the roster's source of truth, and the Owner chose
the Mission Trust Service.

That choice needs its own record. `FML-ADR-047` decides that each MULE hosts a
Mission Trust Service for **local enforcement and distribution of signed mission
authorization state** -- including "signed role and scope policy data where used" --
and that the MTS "distributes validated signed state issued by an authorized mission
or enrollment function" and "shall not become a second certificate authority by
default." `FML-ADR-047` does not, on its own, name a `callsign -> key -> device`
roster or assign its issuance. Folding the roster into `FML-ADR-047` by reading would
silently widen an immutable `SELECTED` decision. So the assignment is recorded here as
a distinct decision that builds on `FML-ADR-047`'s mechanism without editing it.

## Decision

The EUD addressing roster **shall** be treated as **signed enrollment/role state**:
issued by an authorized mission or enrollment function and **distributed by the
`FML-ADR-047` Mission Trust Service** over its existing signed-state distribution
mechanism. The MTS **distributes** the roster; it **shall not** issue it (consistent
with `FML-ADR-047`'s "not a certificate authority; distributes validated signed state
issued by an authorized function").

The roster **shall not** be a new mission-package field (`TBR-NET-02` named and
declined one), and it **shall not** be, initially, a gateway-maintained registry; a
gateway registry for mesh-only EUDs that never reach the MTS, if later needed
(`FML-ADR-048`), is **fed from** this signed state rather than being an independent
source of truth.

This decision assigns a responsibility to the enrollment -> MTS path. It does **not**
edit `FML-ADR-047`, and it decides nothing about the roster's on-the-wire schema, its
signing, or its refresh cadence -- those are implementation detail for the enrollment
function and the MTS, and stay `TBD` until built.

## Status

`SELECTED`. Accepted by the Program Owner (Cameron Zobrist) on 2026-09-29 through the
`CCR-06` decision, which selected the Mission Trust Service as the roster source. It
builds on `FML-ADR-047` and supersedes nothing.

## Consequences

- The roster gets an authoritative owner without widening `FML-ADR-047`: the MTS
  distributes it, the enrollment function issues it, and `mule/recipients.py` consumes
  the resolved mapping it produces.
- It reuses a decided distribution path (signed state over approved IP paths), so no
  new transport or schema field is introduced for addressing.
- The `services/mission-trust/` component stays blocked; this names the roster as one
  of the signed states it will carry, it does not unblock or build it.
- Threat model: the roster is per-person identity data. Distributing it as signed
  state keeps it inside the same trust envelope as role and scope policy, rather than
  inventing a second, less-controlled channel. Presence self-publish -- a separate,
  transmitting behaviour -- is deliberately **not** in this decision; `CCR-06` routed
  it to `TBR-EMCON-01`.

## Accepted cost

The roster now depends on the Mission Trust Service, which is itself unbuilt and
blocked. A deployment cannot have a live roster before the MTS exists, so until then
`mule/recipients.py` runs on whatever mapping a caller supplies (empty is fine, and
fails closed). The program accepts that coupling because the alternative -- a
standalone roster source -- would duplicate the signed-state distribution the MTS
already owns.

## Fallback

If binding the roster to the MTS proves impractical before the MTS is built, the
fallback is the mission-package roster field `CCR-06`/`TBR-NET-02` described: a static,
per-deployment field, less current but decided and simple. Taking it would be a new
ADR superseding this one, not a silent change. The signal to take it is the MTS
slipping far enough that a static roster is needed for a demonstration first.

## Superseded by

None.

## Verification dependency

`TBD`. The roster's end-to-end behaviour is verified when the Mission Trust Service and
the enrollment function exist and `mule/recipients.py` resolves a real MTS-distributed
roster; `FML-ADR-047`'s own verification owns the MTS side. The `callsign -> key`
binding additionally depends on the owed live-client `<__chat id>` capture
(`docs/evidence/TBR-NET-02/2026-09-28-real-geochat-encoding-through-ots.md`).
