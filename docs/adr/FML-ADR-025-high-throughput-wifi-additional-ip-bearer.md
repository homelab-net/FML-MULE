---
id: FML-ADR-025
title: High-throughput conventional Wi-Fi as an additional IP bearer
status: SELECTED
date: 2026-08-25
supersedes: none
superseded-by: none
trades: [TBR-RF-01, TBR-RF-03]
verification: Stage 4
---

# FML-ADR-025 High-throughput conventional Wi-Fi as an additional IP bearer

**Source of rationale:** SAD v0.31 section 5.1. See also sections 5.2, 5.3, 25.4
and CONOPS section 33.

Carries forward the v0.1/v0.2 `AD-005` decision; see SAD section 0.8.

## Context

CONOPS section 33 requires the ability to exploit a higher-throughput IP path
when propagation and mission conditions support it, for video, large file
transfer, map packages, mission synchronization, service replication and
high-rate local collaboration. It explicitly does not mandate a specific Wi-Fi
product.

## Decision

The high-throughput conventional Wi-Fi bearer **shall** be a second IP bearer
managed by the host Network Plane.

The preferred architecture is to expose the high-rate 802.11s interface as an
**additional batman-adv hard interface** when chipset and driver stability
support it.

Packet-level striping of a single flow is **not** required. CONOPS section 39
requires best-path selection and failover, not multipath.

## Status

`SELECTED`.

The band is not selected. CONOPS section 33 requires that the high-throughput
bearer band be chosen **before** RF coexistence analysis completes, so its
harmonic and intermodulation relationships with the sub-GHz chains can be
evaluated as part of coexistence work. See `TBR-RF-02`.

Whether this function shares a physical radio with the EUD access point is
`TBR-RF-03`; see `FML-ADR-045`.

## Consequences

- One logical field L2 domain, continued peer multicast, automatic path
  selection, and no application-level route awareness required.
- BATMAN-V must distinguish the two bearers sensibly or traffic will take a
  fast-but-absent path or a present-but-slow one. Unmeasured.
- Adds a radio, its power, its heat and its antenna feeds to the planning
  envelope. SAD section 25.4.1 assumes up to 2x2 MIMO for this function in the
  six-feed mechanical planning envelope.
- Traffic preference (CONOPS section 40) directs video, large files and bulk
  synchronization here, and mission-critical CoT and PLI to whichever stable
  viable IP path exists.

## Accepted cost

The program accepts an additional radio in the planning baseline, with its
power, thermal, antenna and carrier-board cost, before concurrency evidence
exists. SAD section 5.2 states this is deliberate: it avoids underestimating
power, antenna count, RF coexistence and carrier I/O during early trades.

## Fallback

SAD section 5.3: if the selected high-rate hardware cannot provide stable
802.11s, the bearer is implemented as a **routed adjunct** for bulk transfer,
replication and video, with HaLow remaining the baseline MANET fabric. This
fallback does not change the user-facing service model and does not supersede
this ADR.

CONOPS section 81 also permits the program to conclude that no dedicated
high-rate inter-node bearer is needed, which would supersede this decision.

## Superseded by

None.

## Verification dependency

Stage 4, with Stage 1 for concurrency. `TBR-RF-01` validates high-rate 802.11s
chipset and driver behaviour before PDR. Nothing has been measured.
