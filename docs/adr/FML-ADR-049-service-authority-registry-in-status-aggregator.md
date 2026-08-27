---
id: FML-ADR-049
title: Service Authority Registry is a function of the MULE Status Aggregator, not a separate daemon
status: SELECTED
date: 2026-08-25
supersedes: none
superseded-by: none
trades: [TBR-TAK-01, TBR-HA-01]
verification: Stage 5
---

# FML-ADR-049 Service Authority Registry is a function of the MULE Status Aggregator, not a separate daemon

**Source of rationale:** SAD v0.31 section 12. See also sections 11.2, 14.4,
22, 29.5 and 31.

New in SAD v0.31.

## Context

Service discovery and authority-health tracking are needed so that ingress
(`FML-ADR-031`) routes authoritative traffic only to a backend that actually
holds authoritative state. Implementing that as its own daemon would add a sixth
MULE-original component, and SAD section 31 records the risk that such a
registry becomes a hidden single point of failure.

## Decision

Service discovery and authority-health tracking **shall** be functions of the
**MULE Status Aggregator** (`FML-ADR-046`) rather than a separate daemon. The
Status Aggregator therefore contains a **Service Authority Registry** module.

Every eligible S2 service instance **shall** expose machine-readable health and
authority state sufficient to distinguish process alive, service ready,
authoritative, degraded, non-authoritative, and synchronization or state age
where applicable.

**A process that is alive but does not hold authoritative state is not an
acceptable backend for authoritative service traffic.**

The registry **shall**:

1. collect local service health and authority state;
2. receive approved peer service-health and authority records over the field IP
   network;
3. validate the freshness and trust of those records;
4. maintain the local view of eligible and authoritative service hosts;
5. expose a stable local machine interface to HAProxy and service ingress;
6. mark stale or untrusted records unusable for authoritative routing;
7. report disagreement or no-safe-authority conditions to the operator status
   plane.

**The registry shall not elect an authoritative TAK primary by itself.**
Authority is determined by the service-specific continuity mechanism under SAD
section 14. The registry reports and consumes that decision.

## Status

`SELECTED`, owner Platform/SRE.

Original-software accounting: included within `FML-ADR-046`, **not counted as an
additional daemon** (SAD section 12).

Preferred local interface: HTTP/JSON over loopback or a Unix-domain socket, with
an explicit schema and freshness timestamp, and **no general remote
configuration surface**.

## Consequences

- The MULE-original daemon count stays at three plus one conditional, which is a
  controlled architecture metric under governing principle 10.
- Upstream applications expose health through their supported native APIs where
  available; thin adapters normalize that into the registry schema.
- Freshness validation is what turns "the process restarted" into "the process
  is not authoritative", which CONOPS section 28 requires.
- `NO_SAFE_AUTHORITY` becomes an operator-visible condition with a defined field
  action in SAD section 33.6: continue peer ATAK and local PACE, do not treat
  stale shared state as authoritative, contact the recovery authority, and use
  manual coordination if shared-service recovery is unavailable.
- Because it does not elect authority, a registry fault degrades routing
  decisions rather than causing split-brain.

## Accepted cost

The program accepts that the Status Aggregator becomes a larger component with
two distinct responsibilities, in exchange for not adding a daemon. It accepts
that a bug in the registry can make a healthy backend unreachable, and bounds
that by keeping the registry read-mostly with no remote configuration surface.

## Fallback

A standalone registry daemon, if the two responsibilities prove genuinely
separable and the Status Aggregator becomes unwieldy. That would require an ADR
and would add to the original-software count deliberately rather than by drift.

## Superseded by

None.

## Verification dependency

Stage 5. SAD section 30.1 records service discovery and authority ownership as
OPEN until a failover test.
