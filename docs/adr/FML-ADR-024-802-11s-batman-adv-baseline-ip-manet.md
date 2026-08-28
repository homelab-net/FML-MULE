---
id: FML-ADR-024
title: IEEE 802.11s + batman-adv/BATMAN-V as baseline IP MANET
status: SUPERSEDED
date: 2026-08-25
supersedes: none
superseded-by: FML-ADR-053
trades: [TBR-RF-01, TBR-RF-03, TBR-NET-01, TBR-LINUX-01]
verification: Stage 2
---

# FML-ADR-024 IEEE 802.11s + batman-adv/BATMAN-V as baseline IP MANET

**Source of rationale:** SAD v0.31 section 4.1. See also sections 4.2, 4.3, 5.1,
28 and 29.

Carries forward the v0.1/v0.2 `AD-004` decision; see SAD section 0.8.

## Context

The range-oriented bearer needs an IP-level mesh that forms without
configuration, tolerates nodes appearing and disappearing, and routes over links
of unequal quality. Writing a routing protocol is excluded by CONOPS section 81.

## Decision

The primary IP MANET **shall** use IEEE 802.11s for mesh association together
with `batman-adv` in BATMAN-V mode.

This follows the current OpenMANET model and preserves peer ATAK multicast
behaviour without requiring application-layer routing awareness.

## Status

`SELECTED`.

The field L2 domain retains the OpenMANET flat field domain concept, with
`10.41.0.0/16` as the preferred initial field prefix because it does not
conflict with the parent Homelab `10.77.0.0/16` home prefix or `10.78.0.0/16`
rack prefix. Exact reservations become ICD-controlled values, and the prefix
choice itself is `TBR-NET-01`.

Whether the high-throughput bearer joins the same batman-adv mesh is
`TBR-RF-01`; its relationship to the EUD access point is `TBR-RF-03` and
`FML-ADR-045`.

## Consequences

- Routing happens at layer 2, so the mission-service plane sees one flat
  broadcast domain and services relying on link-local discovery work without a
  discovery proxy.
- Local EUD access is bridged into the field BATMAN domain so peer ATAK
  multicast traverses the mesh and a team retains local connectivity if the mesh
  fragments (SAD section 4.3).
- **Ordinary EUD broadcast is not free.** Because EUD access is bridged in,
  Stage 2 must measure not only CoT and PLI traffic but ordinary broadcast,
  multicast, ARP, mDNS and discovery load at representative client and hop
  counts. SAD section 4.3 states the architecture does not assume normal phone
  broadcast behaviour is free on a constrained multi-hop mesh.
- `batman-adv` couples this decision to the kernel question in `TBR-LINUX-01`
  and to the compatibility-set rule in `FML-ADR-040`.
- BATMAN-V's throughput-based metric needs a usable throughput estimate from the
  driver. Whether the HaLow driver provides one is **UNVERIFIED** and is part of
  `TBR-LINUX-01`. If it does not, path selection may be effectively arbitrary,
  which would undermine this decision.
- Peer traffic is visible to all admitted participants on the domain. CONOPS
  section 23 makes that an explicit rule, not a defect.

## Accepted cost

The program accepts kernel coupling, and the broadcast burden of a flat layer 2
mesh over a bearer whose capacity is `TBD`. It accepts that scaling behaviour
beyond a small node count is unmeasured: CONOPS section 22 states that
bench-scale peer TAK performance is not assumed to extend to a large field
network, and Stage 2 determines usable network size and hop-count limits.

## Fallback

A layer 3 routing protocol over the same radio links, at the cost of link-local
service discovery and the configuration-free property. Taking it would supersede
this ADR.

SAD section 5.3 provides a narrower fallback for the high-rate bearer only: if
its hardware cannot provide stable 802.11s, it becomes a routed adjunct while
HaLow remains the baseline MANET fabric.

## Superseded by

`FML-ADR-053`, which keeps everything here except the routing algorithm.

The first time the program ran `batman-adv`, the stock module reported
`Routing algorithm 'BATMAN_V' is not supported`: it is a kernel build option the
distribution leaves off. The consequence recorded above, that BATMAN-V needs a
driver throughput estimate that may not exist, made the kernel work a certain
cost for an uncertain benefit. `FML-ADR-053` baselines on BATMAN-IV and states
what evidence would bring BATMAN-V back.

## Verification dependency

Stage 2, with Stage 4 for the high-rate bearer. Requires mesh formation and
multi-hop traffic with node count, spacing and offered load recorded, plus the
EUD broadcast measurement above. Nothing has been measured.
