---
id: TBR-HA-01
title: Safe automatic service recovery
status: OPEN
owner: TBD
area: HA
critical-path: false
depends-on: [TBR-TAK-01, TBR-COMP-01]
feeds: []
evidence: docs/evidence/TBR-HA-01/
adr: [FML-ADR-029]
---

# TBR-HA-01 Safe automatic service recovery

## Question

Under what conditions may a service be restarted automatically, and what
restart policy avoids turning one failed service into a dead node?

## Why it matters

`FML-ADR-029` puts services under systemd supervision, which makes automatic
restart the default posture. On a resource-constrained node with no operator
present, that default is dangerous in a specific way: a service that fails
because the node is out of memory, restarted immediately, consumes the memory
again. The restart loop then competes with the network plane for CPU, mesh
links flap, and a single service fault becomes total node loss. This is a
common and well-documented failure mode, not a hypothetical.

The opposite failure is a service that stays down after a transient fault,
during an incident, with nobody present to notice.

The service controller is one of the four placeholder components in
`services/`, and it is not to be implemented before this trade closes.

## Options

Axes: restart limits and back-off, whether a failing service is left down after
a threshold, whether the network plane holds a resource reservation that a
restart loop cannot consume, whether recovery escalates to a node reboot, and
how a service that is deliberately down is distinguished from one that failed.

Operator visibility is part of the answer, not separate from it. A node that
has given up on a service must say so somewhere an operator can see, which
connects to the status surface.

## Closure evidence

Committed under `docs/evidence/TBR-HA-01/`:

- Fault injection results for each failure class: service crash, memory
  exhaustion, storage exhaustion, dependency unavailable, and a service that
  starts but does not become healthy.
- Recorded network plane behaviour during each, specifically whether mesh links
  survive.
- Evidence that the restart policy terminates rather than looping indefinitely.
- The state the node reports to an operator after giving up.

## Closure gate

For every injected failure class, the node either recovers the service or
stops trying and reports that it has, and in **all** cases the network plane
retains its mesh links throughout. Recorded, on a node running the full
catalog.

## Dependencies

- **Depends on:** `TBR-TAK-01` (what state a restart must not lose),
  `TBR-COMP-01` (the reservation mechanism).
- **Feeds:** the service controller implementation, which is blocked on this.
- **Requires hardware:** partly. Service fault injection runs on an ordinary
  machine against fakes; the network plane interaction needs radios.
