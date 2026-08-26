---
id: FML-ADR-024
title: 802.11s plus batman-adv and BATMAN-V as the baseline IP MANET
status: SELECTED
date: TBD
supersedes: none
superseded-by: none
trades: [TBR-RF-01, TBR-RF-03, TBR-NET-01, TBR-LINUX-01]
verification: TBD
---

# FML-ADR-024 802.11s plus batman-adv and BATMAN-V as the baseline IP MANET

This is a stub. The **system architecture description is the source of
rationale**; see `docs/architecture/README.md`.

## Context

The range-oriented bearer needs an IP-level mesh that forms without
configuration, tolerates nodes appearing and disappearing, and routes over
links of very unequal quality. Writing a routing protocol was rejected; see
`docs/NON-GOALS.md`.

The candidates were in-kernel mesh with a layer 2 routing daemon, or a layer 3
routing protocol running over point-to-point links.

## Decision

The baseline IP MANET **shall** use IEEE 802.11s for mesh association together
with `batman-adv` in BATMAN-V mode for routing.

## Status

`SELECTED`.

Applies to the range-oriented sub-GHz bearer. Whether the high-throughput
inter-node bearer uses the same mechanism is a separate question, `TBR-RF-01`,
and its relationship to the access point function is `TBR-RF-03` and
`FML-ADR-045`.

The field address prefix is `TBD`: `TBR-NET-01`.

## Consequences

- Routing happens at layer 2, so the mission-service plane sees one flat
  broadcast domain and services that rely on link-local discovery work without
  a discovery proxy.
- `batman-adv` is an out-of-tree-adjacent kernel component in practice, which
  couples this decision to the kernel question in `TBR-LINUX-01` and to the
  compatibility-set rule in `FML-ADR-040`.
- BATMAN-V's throughput-based metric needs a usable throughput estimate from
  the driver. Whether the HaLow driver provides one is `UNVERIFIED` and feeds
  `TBR-LINUX-01`.
- A flat layer 2 domain means broadcast and multicast traffic reaches every
  node over a low-rate bearer. Controlling that is real work and is not solved
  by this decision.
- Peer traffic is visible to all admitted participants. This is stated as a
  condition in `THREAT_MODEL.md`, not a defect.

## Accepted cost

The program accepts kernel coupling, and accepts the broadcast burden of a flat
layer 2 mesh over a bearer whose capacity is `TBD`. It accepts that scaling
behaviour beyond a small node count is unmeasured, and that the number of nodes
at which this arrangement stops working is unknown.

## Fallback

A layer 3 routing protocol over the same radio links is the fallback, at the
cost of link-local service discovery and of the configuration-free property.
Taking it would supersede this ADR.

## Superseded by

None.

## Verification dependency

`TBD`. Requires a mesh-formation and multi-hop traffic stage under
`test/stages/`, with node count, spacing, and offered load recorded. Nothing
has been measured.
