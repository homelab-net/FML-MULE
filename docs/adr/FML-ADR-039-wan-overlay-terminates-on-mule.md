---
id: FML-ADR-039
title: WAN overlay terminates on MULE infrastructure, never directly on EUDs
status: SELECTED
date: 2026-08-25
supersedes: none
superseded-by: none
trades: []
verification: Stage 6
---

# FML-ADR-039 WAN overlay terminates on MULE infrastructure, never directly on EUDs

**Source of rationale:** SAD v0.31 section 18. See also section 27 and CONOPS
sections 12, 43, 44 and 68.

Carries forward draft `AD-020`; see SAD section 0.8.

## Context

CONOPS section 12 requires that EUDs not join the Tailscale or equivalent WAN
overlay directly, and that the MULE be the routing, authentication and security
boundary between EUDs and remote field services.

## Decision

Only MULE infrastructure **shall** participate in Tailscale or an equivalent WAN
overlay. **EUDs shall not join the tailnet.**

Overlay policy **shall** remain deny-by-default and restrict MULE nodes to
approved field-service destinations. Tailscale Grants are the preferred current
policy model.

Tailscale device tags and grants represent **infrastructure and service
identity**. They **shall not** represent Team Alpha, Team Bravo, Team Lead or
any other operational mission role.

## Status

`SELECTED`.

CONOPS section 43 adds that infrastructure access control and mission
authorization remain separate, and that overlay authentication alone **shall
not** grant service or data authorization.

## Consequences

- The MULE remains the single WAN security and routing boundary, so EUD policy
  is enforced in one reviewable place.
- CONOPS section 68 requires that WAN reachability **shall not** grant access to
  unrelated home, private, administrative or cyber-range infrastructure. SAD
  section 27 states that no external RF or WAN path provides unrestricted shell,
  home or private, Vaultwarden, or management access.
- Cross-site peer multicast is not assumed to stretch transparently through the
  overlay. Remote ATAK communication uses the TAK service or another approved
  routed application service (CONOPS section 44).
- Tailscale is **entirely optional** to baseline operation. Its loss does not
  remove local mesh, peer ATAK, local services or LoRa (SAD section 18.3).
- Any standard MULE is technically capable of assuming an authorized local
  WAN-gateway role (CONOPS section 42). One active gateway at a time is the
  initial baseline; competing automatic multi-gateway operation is out of scope
  per CONOPS section 81.

## Accepted cost

The program accepts that remote users cannot reach field services without a MULE
in the path, and that the overlay identity model cannot be reused to express
operational roles, requiring role and scope to be carried separately in signed
mission policy.

## Fallback

None that preserves the boundary. Admitting EUDs to the overlay would violate
CONOPS section 12 and requires a CONOPS change request.

## Superseded by

None.

## Verification dependency

Stage 6. Local WAN gateway, secure overlay, remote field services, EUD isolation
from the overlay, unauthorized Homelab access denial, and WAN loss with local
continuity.
