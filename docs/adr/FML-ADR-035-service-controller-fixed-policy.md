---
id: FML-ADR-035
title: MULE service controller is a fixed-policy lifecycle layer, not a cluster scheduler
status: SELECTED
date: 2026-08-25
supersedes: none
superseded-by: none
trades: [TBR-HA-01, TBR-TAK-01, TBR-COMP-01]
verification: Stage 1
---

# FML-ADR-035 MULE service controller is a fixed-policy lifecycle layer, not a cluster scheduler

**Source of rationale:** SAD v0.31 section 15. See also sections 29.5 and CONOPS
sections 5.8, 9.4 and 10.

Carries forward draft `AD-016`; see SAD section 0.8.

## Context

MULE needs to translate mission profile, authenticated user demand, role and
scope, battery, thermal state, network state and shared-host availability into
systemd service targets. CONOPS section 81 excludes Kubernetes-scale
orchestration.

## Decision

The service controller **shall not** be a general cluster scheduler.

It **shall** start and stop a fixed approved service catalog, apply grace
timers, apply minimum-residency timers, prevent oscillation, and report current
service state.

It **shall not** replace systemd or Podman health management.

## Status

`SELECTED`, and listed in the MULE-original software inventory (SAD section
29.5) with owner Platform/Systems and the scope limit "starts/stops approved
systemd targets only; not a cluster scheduler".

Custom code is accepted here because this is MULE-specific policy glue, not a
replacement for a mature orchestration platform (governing principle 10).

**Restart policy is not decided by this ADR.** `TBR-HA-01` is open.

## Consequences

- CONOPS section 5.8 requires damping, persistence, minimum-residency or
  threshold logic sufficient to prevent oscillation, and forbids moving services
  merely because another host looks marginally better. This controller is where
  that lives.
- CONOPS section 10 requires that service activation not tie team capability to
  a single EUD remaining connected, and that grace periods absorb roaming and
  sleep states.
- CONOPS section 11 requires that activation not create externally observable
  behaviour revealing privileged-user login or leadership presence. Stable
  hosting behaviour is preferred over demand-driven activation for privileged
  services.
- S3 services are the first class stopped under constrained battery, thermal,
  bandwidth or compute conditions (CONOPS section 9.4).
- Because the controller commands systemd rather than supervising processes
  itself, its failure does not take services down with it.

## Accepted cost

The program accepts writing and sustaining original software. It bounds that
cost by the scope limit above and by the requirement in SAD section 29.5 that
any new MULE-original daemon carry an ADR or explicit TBR status, a named owner,
an interface contract, a reason no OSS project can do the job, a unit and health
test, a resource budget and a sustainment owner.

## Fallback

Fixed systemd targets with no dynamic policy, activated by mission profile only.
Less capable, and it would push the battery, thermal and role logic into an
operator procedure instead.

## Superseded by

None.

## Verification dependency

Stage 1, with Stage 7 for the resource-constrained shedding behaviour.
`TBR-HA-01` must close before the restart and recovery half is implemented: the
failure mode it guards against is a restart loop competing with the routing
daemon until mesh links flap.
