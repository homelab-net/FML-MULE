---
id: TBR-NET-01
title: Field address prefix
status: OPEN
owner: TBD
area: NET
critical-path: false
depends-on: []
feeds: []
evidence: docs/evidence/TBR-NET-01/
adr: [FML-ADR-024]
---

# TBR-NET-01 Field address prefix

## Question

What address prefix and allocation scheme does the field network use, such that
independently built deployments do not collide when they meet?

## Why it matters

Small, and it will bite. Two volunteer groups that built nodes independently
from this repository, arriving at the same incident, must be able to
interoperate or at least coexist. If both used the same hardcoded prefix with
overlapping host allocations, they cannot.

The scenario is not hypothetical for a repository published for other makers to
build from: the more successful this program is, the more likely two
independently built deployments meet.

Ancillary questions that belong here: whether addressing is IPv6, IPv4 or both;
whether addresses are derived from node identity or allocated; how an EUD on
the access point is addressed relative to the mesh; and what DNS names exist in
`services/ingress/`.

## Options

Axes: address family, whether a prefix is fixed for all deployments or
per-deployment and set in the mission package, whether host addresses are
derived from a node identifier or allocated by a service, and whether a
deployment identifier is embedded in the prefix so that two deployments differ
by construction.

Deriving addresses from node identity has an obvious interaction with
`THREAT_MODEL.md`: an address that encodes a durable identifier is a durable
identifier visible to anyone observing traffic.

## Closure evidence

Committed under `docs/evidence/TBR-NET-01/`:

- A written scheme, including the address family, the prefix source, and the
  host allocation rule.
- Demonstrated behaviour when two deployments configured independently form a
  mesh: whether they interoperate, coexist, or conflict, and what an operator
  sees.
- Confirmation that the scheme is expressible in the mission configuration
  package schema, and validated by `mission/schema/`.
- Analysis of what the address discloses, referred to `THREAT_MODEL.md`.

## Closure gate

The scheme is documented, two independently configured deployments are
demonstrated not to collide, and the mission package schema validates a
deployment's addressing configuration.

## Dependencies

- **Depends on:** none.
- **Feeds:** `os/config/` interface and DHCP templates, `services/ingress/`,
  and the mission package schema.
- **Requires hardware:** **no.** The scheme can be designed and the collision
  case exercised with virtual interfaces on an ordinary machine. Another good
  candidate for a contributor without a node.
