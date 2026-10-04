---
id: TBR-NET-05
title: How does a node assign the EUD access-point subnet and DHCP
status: OPEN
owner: Cameron Zobrist
area: NET
priority: 99
function-owner: Network
critical-path: false
depends-on: []
feeds: [GAP-09E, GAP-09H]
requires-hardware: no
evidence: docs/evidence/TBR-NET-05/
adr: [FML-ADR-063, FML-ADR-059]
target-date: TBD-SRR
---

# TBR-NET-05 How does a node assign the EUD access-point subnet and DHCP

## Question

What IPv4 subnet, DHCP range, and lease does a node hand to the phones on its
EUD access point, and how is that scoped so two nodes do not collide?

## Why it matters

This is an unowned gap surfaced 2026-09-26 while sequencing v0.0.1 (GAP-09H gap
register, item G6). It is easily assumed closed and is not:

- `TBR-NET-01` is `CLOSED` but decided only the per-deployment **mesh field
  prefix** (`FML-ADR-063`); it does not define the AP subnet.
- `TBR-NET-02` is `CLOSED` but decided **recipient/identity** addressing (which
  message is for which EUD), not IP address assignment.

So nothing decides the EUD AP subnet or its DHCP. Waiting on it:

- **GAP-09E** cannot render `dnsmasq`'s `dhcp-range` for the AP; the AP-only
  parameter document has no AP subnet to derive from (`mule-v001` fields no mesh,
  so the mesh prefix does not apply).
- **GAP-09H** (the v0.0.1 operator procedure) can only set the AP subnet by hand
  for the cold-start drill; it cannot be hands-free from the image.
- **Ingress reach-by-name** (`FML-ADR-031`, roadmap 4.4) needs a stable AP
  address for the reverse proxy's frontend and for `dnsmasq` to resolve the
  service name onto.

## Options

- **A per-deployment AP subnet carried in the mission package**, mirroring the
  `FML-ADR-063` field-prefix pattern (generated, not a program-wide constant, so
  two independently built deployments meeting at an incident do not collide).
  Right if the collision and OPSEC arguments that drove `FML-ADR-063` apply
  equally to the AP subnet -- which they appear to.
- **A fixed AP subnet compiled into the node** (e.g. a documented RFC1918 range).
  Simplest to render, but reintroduces the program-wide-constant collision risk
  `FML-ADR-063` rejected for the mesh; right only if AP subnets never meet.
- **Derive the AP subnet from the field prefix.** Rejected shape: an AP-only node
  fields no mesh, so it has no field prefix to derive from.
- **Defer for v0.0.1**: set the AP subnet by hand in the drill and decide later.
  Acceptable only as an explicit, recorded v0.0.1 deferral, not a silent gap.

## Closure evidence

A written addressing decision under `docs/evidence/TBR-NET-05/`: the AP subnet
form (fixed vs per-deployment), the DHCP range and lease, where the value lives
(mission package vs region profile vs constant), the collision argument against
two nodes at one incident, and the fail-closed behavior when the value is absent.
An ADR records the choice. No hardware is required; it is a design decision.

## Closure gate

The named owner accepts how the EUD AP subnet and DHCP are assigned, and an ADR
records it in the register. The Stage 1 / GAP-09I demonstrations are not this
gate. Until the choice is recorded this trade stays `OPEN`.

## Dependencies

- **Depends on:** none.
- **Feeds:** GAP-09E (AP config rendering), GAP-09H (operator procedure), the
  `FML-ADR-031` ingress reach-by-name path.
- **Related decisions:** `FML-ADR-063` (mesh field prefix -- the pattern, not the
  AP subnet), `FML-ADR-059` (systemd-networkd owns links/addressing).
- **Validating stage:** Stage 1 (the v0.0.1 AP), then hardware acceptance.
- **Requires hardware:** no. It is a design decision, workable without a node.

## Frontmatter notes

`owner` is `TBD-SRR`: assigning a named owner and target date is a Program Owner
act (SAD section 30.2), left explicit rather than presumed. `function-owner` is
Network. `priority` is a placeholder pending the owner's register position.
