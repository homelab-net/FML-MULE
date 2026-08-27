---
id: FML-ADR-036
title: Smallstep step-ca is preferred initial PKI
status: PREFERRED
date: 2026-08-25
supersedes: none
superseded-by: none
trades: [TBR-TIME-01, TBR-SEC-01, TBR-ID-01]
verification: Stage 9
---

# FML-ADR-036 Smallstep step-ca is preferred initial PKI

**Source of rationale:** SAD v0.31 section 16.1. See also sections 16.2-16.4,
17.3 and CONOPS section 14.

Carries forward draft `AD-017`; see SAD section 0.8.

## Context

CONOPS section 14 establishes bounded mission trust: an offline organizational
root, a mission or enrollment authority, and mission-scoped identities with a
defined validity window. The organizational root **shall not** be required to be
present on any MULE.

## Decision

**Smallstep `step-ca`** is the preferred initial open-source PKI implementation
for the offline organizational root, mission intermediates, service
certificates, device certificates and short-lived mission credentials.

The root signing key **shall** remain offline.

A mission or enrollment authority **may** be delegated without placing the
organizational root key on field nodes.

## Status

`PREFERRED`, not `SELECTED`.

The trust model is what binds; the implementation is replaceable. CONOPS section
14 and `FML-ADR-047` are expressed independently of the CA product.

## Consequences

- Short-lived mission credentials are the primary revocation mechanism, because
  CONOPS section 15 accepts that instantaneous offline revocation across
  partitions is impossible and requires credentials that fail safe by expiry.
- Certificate validity depends on credible time, which is why `FML-ADR-042`
  requires trust validation never to fail open on invalid time, and why
  `TBR-TIME-01` must supply the skew tolerance.
- Field recovery or enrollment authority is delegated only as necessary (CONOPS
  section 14), and CONOPS section 17.3 requires that authority to issue or
  delegate identities be more constrained than normal network administration.
- The Mission Trust Service (`FML-ADR-047`) distributes signed state issued by
  this authority. It is **not** a second CA.
- Whether a common browser-service identity provider is needed beyond
  application-native RBAC is a separate open question, `TBR-ID-01`.

## Accepted cost

The program accepts operating a PKI with volunteer administrators, and the
associated risk that credential issuance and review become the least-staffed
function. CONOPS section 7.6 requires a standing Communications and Identity
Management function that exists and is staffed before fielding; `MAINTAINERS.md`
currently records that role as `VACANT`.

## Fallback

Another open-source CA, or an externally operated issuance process, without
changing the trust model. Would supersede this ADR.

## Superseded by

None.

## Verification dependency

Stage 9. Mission credential expiry, revocation propagation, disconnected
revocation lag, node revocation and replacement identity issuance.
