---
id: FML-ADR-031
title: Stable local DNS + HAProxy/TCP ingress for logical service identities
status: SELECTED
date: 2026-08-25
supersedes: none
superseded-by: none
trades: [TBR-NET-01, TBR-TAK-01]
verification: Stage 5
---

# FML-ADR-031 Stable local DNS + HAProxy/TCP ingress for logical service identities

**Source of rationale:** SAD v0.31 section 11. See also sections 12, 14.3 and
CONOPS sections 5.6 and 25.

Supersedes draft `AD-011`; see SAD section 0.8.

## Context

CONOPS section 25 requires EUDs to reference a stable logical TAK service
identity rather than a physical host, and requires that moving the service
between eligible hosts not require ordinary users to change ATAK server
settings.

The logical service identities are `tak.field`, `chat.field`, `files.field` and
`portal.field`.

## Decision

The MULE host **shall** provide stable local service ingress using local DNS and
a lightweight TCP/HTTP proxy layer.

**HAProxy** is the preferred initial open-source proxy, because it supports both
TCP and HTTP forwarding, has mature health checks, and runs under a dedicated
unprivileged service identity.

For TAK and other end-to-end protected protocols, **TCP passthrough is preferred
where possible**. Each eligible backend **may** hold its own private key and a
certificate valid for the same logical service identity.

The architecture **shall not** require copying one service private key to every
node.

## Status

`SELECTED`.

The backend selection is fed by the Service Authority Registry
(`FML-ADR-049`), which exposes a stable local machine interface to the ingress
layer. A process that is alive but does not hold authoritative state is not an
acceptable backend for authoritative service traffic (SAD section 12).

## Consequences

- EUD DNS and server settings do not change when a service moves.
- TCP passthrough preserves end-to-end TLS to the backend, so the proxy is not a
  decryption point.
- Per-backend keys mean a captured node does not yield the whole fleet's service
  identity, which matters because CONOPS section 69 treats capture as expected.
- Rootless containers cannot bind privileged ports without explicit handling, so
  ingress is a single decided concern rather than a per-service setting.
- TLS that a browser accepts, on a node with no internet, no public DNS and no
  reachable CA, is genuinely unsolved. See `services/ingress/README.md`; it
  interacts with `FML-ADR-036`, `TBR-SEC-01` and `FML-ADR-042`.
- Two independently built deployments must not collide on the local domain. The
  domain comes from the mission package; see `TBR-NET-01`.

## Accepted cost

The program accepts an additional hop in the local service path and the
operational cost of managing per-backend certificates for one logical identity,
in exchange for failover that does not require touching an operator's phone.

## Fallback

Direct service addressing with EUD reconfiguration on failover. That would
violate CONOPS section 25 and requires a CONOPS change request, not an
architecture decision.

## Superseded by

None.

## Verification dependency

Stage 5. SAD section 30.1 records stable service identity versus host movement
as OPEN until a failover test.
