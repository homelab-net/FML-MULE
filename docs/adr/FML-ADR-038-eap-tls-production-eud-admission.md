---
id: FML-ADR-038
title: EAP-TLS is the production EUD admission target
status: SELECTED TARGET
date: 2026-08-25
supersedes: none
superseded-by: none
trades: [TBR-SEC-01, TBR-TIME-01, TBR-RF-03]
verification: Stage 9
---

# FML-ADR-038 EAP-TLS is the production EUD admission target

**Source of rationale:** SAD v0.31 sections 17.1-17.3. See also sections 16.2,
28, 29 and CONOPS section 13.

Carries forward draft `AD-019`; see SAD section 0.8.

## Context

CONOPS section 13 states that knowledge of a shared WLAN password **shall not**
be sufficient authorization for the production field environment, that each
authorized EUD **shall** use an individually identifiable, revocable and
time-bounded credential, and that MAC addresses **shall not** be trusted as
primary proof of identity.

## Decision

The production target for EUD WLAN admission **shall** be certificate-based
802.1X/EAP-TLS.

The preferred initial production implementation uses the **hostapd integrated
EAP server** for local EAP-TLS validation, so EUD admission does not depend on a
central RADIUS server. The Mission Trust Service (`FML-ADR-047`) supplies the
local trust and revocation material.

FreeRADIUS remains an **approved alternate** if Stage 9 demonstrates a need for
richer AAA, accounting or roaming semantics that hostapd cannot provide cleanly.

## Status

`SELECTED TARGET`.

It is a target rather than a plain selection because it has not been
demonstrated on the selected hardware and because a prototype path is explicitly
permitted:

**Per-device PPSK may be used during prototype development** when EAP-TLS would
delay RF and network characterization. Prototype PPSK **shall not** be treated
as the final authorization architecture (SAD section 17.2).

## Consequences

- Per-device identity, no shared fleet password, offline CA validation,
  revocation and expiry support, and compatibility with the mission-scoped PKI
  model.
- Local validation means admission survives loss of WAN, which CONOPS section
  5.4 requires.
- **Network admission never substitutes for application authorization** (SAD
  section 17.3, CONOPS section 13). An admitted device is not an authorized
  user.
- Certificate validation depends on credible time; see `FML-ADR-042` and
  `TBR-TIME-01`. A node in `TIME_DEGRADED` may restrict trust-sensitive
  enrollment.
- EUD client compatibility with EAP-TLS provisioning is an operational burden on
  the Communications and Identity Management function.

## Accepted cost

The program accepts the provisioning burden of per-device certificates on
volunteer-owned EUDs, and accepts that prototype work may run on PPSK for a
period, with the risk that the prototype posture is mistaken for the production
one. The status vocabulary exists partly to prevent that.

## Fallback

FreeRADIUS as the approved alternate, for richer AAA needs. Falling back to
shared-password admission in production would violate CONOPS section 13 and
requires a CONOPS change request.

## Superseded by

None.

## Verification dependency

Stage 9, with Stage 1 for association. SAD section 20.4 includes EAP-TLS
admission in the hardware-in-the-loop release suite where enabled.
