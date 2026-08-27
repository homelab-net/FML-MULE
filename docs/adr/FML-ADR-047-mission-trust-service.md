---
id: FML-ADR-047
title: Mission Trust Service is approved thin original software and is not a CA
status: SELECTED
date: 2026-08-25
supersedes: none
superseded-by: none
trades: [TBR-SEC-01, TBR-TIME-01, TBR-TAK-01]
verification: Stage 9
---

# FML-ADR-047 Mission Trust Service is approved thin original software and is not a CA

**Source of rationale:** SAD v0.31 section 16.2. See also sections 16.1, 16.3,
17.3, 27.5.4, 29.5 and CONOPS sections 14, 15 and 69.

New in SAD v0.3.

## Context

Offline signed revocation and policy propagation across MULEs is
subsystem-specific: no upstream project distributes mission authorization state
across a partitioning mesh with no reachback.

CONOPS section 15 accepts that offline operation and instantaneous revocation
across disconnected partitions are incompatible, and requires bounded credential
lifetimes so that a disconnected unrevoked credential eventually fails safe by
expiry.

## Decision

Each MULE **shall** host a lightweight **Mission Trust Service** responsible for
local enforcement and distribution of signed mission authorization state:

- the current mission trust bundle;
- credential-expiry policy;
- signed revocation records;
- signed role and scope policy data where used;
- node revocation data;
- trust-state status for administrators;
- propagation over available approved IP paths.

**The Mission Trust Service shall not become a second certificate authority by
default.** It distributes validated signed state issued by an authorized mission
or enrollment function.

## Status

`SELECTED`, with owner Security / Identity in the MULE-original software
inventory (SAD section 29.5) and the scope limit "not a CA; validates and
distributes signed mission trust state".

## Consequences

- It supplies the local trust and revocation material that the hostapd
  integrated EAP server needs for offline EUD admission (`FML-ADR-038`).
- **LoRa is not required to carry PKI revocation data in v1** (SAD section
  16.3). If later testing shows a compact signed emergency revocation format is
  useful over LoRa, it is added through the ICD and security architecture.
- **The architecture does not claim instantaneous offline revocation.** A
  credential revoked centrally remains valid on a partition that has not learned
  of the revocation, until it expires.
- CONOPS section 69 requires a missing node to be revocable without its
  cooperation, and remaining participants to reject the revoked identity once
  updated authorization information arrives. This service is the propagation
  path.
- A recovered former node cannot rejoin with stale trust; it enters the
  controlled maintenance, rekey and reimage path (SAD section 27.5.4).
- Trust validation depends on credible time (`FML-ADR-042`), so this service
  inherits the `TIME_DEGRADED` fail-closed behaviour.
- **No key material of any kind is committed to this repository**, at any stage.
  See `SECURITY.md` and `services/identity/`.

## Accepted cost

The program accepts writing and sustaining original security-relevant software,
which is the least forgiving category to own. It bounds that by refusing CA
responsibilities and by keeping the service to validation and distribution of
state signed elsewhere.

It accepts a revocation lag it cannot bound, and CONOPS section 15 requires that
limitation be stated in administrator and Team Lead training material rather
than left as an implementation detail.

## Fallback

Expiry-only trust, with no active revocation distribution, relying entirely on
short credential lifetimes. Weaker, and it would push the whole revocation
burden onto credential duration.

## Superseded by

None.

## Verification dependency

Stage 9. Revocation propagation, disconnected revocation lag, node revocation,
mission credential expiry and replacement identity issuance.
