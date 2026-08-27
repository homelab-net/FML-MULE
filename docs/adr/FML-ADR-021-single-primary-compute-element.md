---
id: FML-ADR-021
title: Single primary compute / single Debian host with logical plane isolation
status: SELECTED
date: 2026-08-25
supersedes: none
superseded-by: none
trades: [TBR-COMP-01, TBR-PWR-01, TBR-THERM-01, TBR-HW-01, TBR-CARRIER-01]
verification: Stage 1
---

# FML-ADR-021 Single primary compute / single Debian host with logical plane isolation

**Source of rationale:** SAD v0.31 section 2.1. See also sections 1.2, 2.2, 2.3,
10 and 26.

Supersedes the draft-local `AD-001` labels used in SAD v0.1 and v0.2. Those
labels were reused when their meanings changed and are historical only; see SAD
section 0.8.

## Context

The engineering question was not whether OpenWrt can host applications. It was
whether MULE must consume OpenMANET as a complete firmware distribution or may
consume its networking model, configuration knowledge and reusable components.

The critical MANET mechanisms are ordinary Linux components: 802.11s,
`mac80211`/`cfg80211`, `batman-adv`, BATMAN-V, the Morse Micro Linux driver
stack, and standard DHCP, DNS, firewall and routing. OpenWrt provides mature
packaging and UCI integration, but the required mesh behaviour is not
OpenWrt-exclusive.

Four options were assessed in SAD section 2.2: single board with one Debian OS;
single board with an OpenWrt VM; dual board OpenWrt plus Debian; and an
OpenWrt-only monolith.

## Decision

MULE **shall** use one primary general-purpose compute element running one
supported stable Linux operating system.

Network, mission-service, management and security functions **shall** be
separated logically, through Linux process isolation, namespaces, users,
capabilities, cgroups, container boundaries and nftables policy. See
`FML-ADR-030`.

Physical separation into a second general-purpose network computer is not part
of the preferred v1 architecture.

## Status

`SELECTED`.

The dual-board architecture is retained as a **FALLBACK**, not discarded. SAD
section 2.3 lists six triggers that would reinstate it: radio drivers that
cannot coexist with the service host; application workload that degrades routing
despite cgroups; a security finding that shared-kernel isolation is insufficient;
service recovery that cannot occur without unacceptable disruption; power or
thermal evidence favouring a dedicated network processor; or a regulatory
requirement for a separate certified network module.

Any fallback activation is an ADR and a BOM change, not an informal field
variant.

The compute element itself is **not selected**. See `TBR-HW-01`, which is a
convergence decision behind `TBR-COMP-01`, `TBR-PWR-01`, `TBR-THERM-01`,
`TBR-RF-03`, `TBR-TIME-01` and `TBR-SEC-01`.

## Consequences

- One operating system to build, patch, promote and roll back rather than two.
  SAD section 32 records this as the deliberate simplification of v0.1.
- One inter-board Ethernet link and one OS lifecycle removed; reduced idle and
  active power, enclosure volume and internal cabling.
- Radio drivers stay close to the hardware. No VM radio passthrough.
- **One failure domain.** Host, kernel or primary-compute failure removes both
  network and hosted-service capability from that node. SAD section 26 records
  the host/kernel as the primary per-node single point of failure.
- Resource contention between the planes becomes a software problem, addressed
  by reserved CPU and memory priority for critical network functions (SAD
  section 10.4) and sized by `TBR-COMP-01`.
- One concentrated thermal and power load, feeding `TBR-PWR-01` and
  `TBR-THERM-01`.
- Contributors can work against an ordinary Debian-family machine, which is what
  makes the hardware abstraction rule in `AGENTS.md` workable.

## Accepted cost

The program accepts a single point of failure in the compute element, and
accepts that a fault in the mission-service plane can starve the network plane
on the same host.

It also accepts a **weaker, one-directional isolation boundary**: ordinary
application contexts are constrained from changing network and RF state, but the
privileged host network context is not itself contained by those application
namespaces. SAD sections 10.1 and 27 state this explicitly rather than hiding it
behind container terminology.

The v1 mitigation is fleet-level replaceability rather than duplicated internal
compute: a standardized spare MULE, common image and configuration, peer MULE
continuity, field swap, and analog or manual PACE.

## Fallback

The dual-board architecture in SAD section 2.3, reinstated only on one of the
six stated triggers. Because the logical interface model is the same, physical
separation can be implemented without changing EUD-facing services or field
procedures (SAD section 10.5). It is an implementation fallback, not a separate
operational architecture.

## Superseded by

None.

## Verification dependency

Stages 1, 7 and 8. SAD section 30.1 records this finding as OPEN until test.
Stage 1 and Stage 7 must demonstrate that representative service load does not
destabilize the Network Plane (SAD section 10.4).

An independent shared-kernel security reviewer is a named SRR/PDR action (SAD
section 32.1, item 3). A negative finding is an explicit trigger for the
fallback.
