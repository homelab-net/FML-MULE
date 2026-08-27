---
id: TBR-RF-01
title: High-rate mesh implementation
status: OPEN
owner: TBD-SRR
area: RF
priority: 10
function-owner: Network + RF
critical-path: false
depends-on: [TBR-RF-03, TBR-LINUX-01]
feeds: [TBR-HW-01]
requires-hardware: yes
evidence: docs/evidence/TBR-RF-01/
adr: [FML-ADR-025, FML-ADR-024]
target-date: TBD-SRR
---

# TBR-RF-01 High-rate mesh implementation

**Source:** SAD v0.31 section 5.1, and the TBR register in SAD section
30.2 (priority 10 of 16).

**Function owner:** Network + RF. **Named owner:** `TBD-SRR`.

SAD section 30.2 records an SRR exit action: the Program Owner assigns one named
individual and one calendar target date to every open TBR. `TBD-SRR` marks the
gap explicitly rather than hiding it behind a functional organization.

## Question

Can high-rate Wi-Fi operate reliably as a second 802.11s/batman interface?

## Why it matters

`FML-ADR-025` prefers exposing the high-rate 802.11s interface as an **additional
batman-adv hard interface**, giving one logical field L2, continued peer
multicast and automatic path selection.

That preference is conditional on chipset and driver stability. If it does not
hold, SAD section 5.3 makes the bearer a routed adjunct and HaLow remains the
baseline MANET fabric.

If both bearers join the same batman-adv mesh, BATMAN-V's metric must
distinguish them sensibly, or traffic will take a fast-but-absent path or a
present-but-slow one.

## Options

1. **Same mechanism, one mesh.** 802.11s plus batman-adv on both bearers, one
   routing domain, metric distinguishes them. Simplest operationally if the
   metric behaves. This is the `FML-ADR-025` preference.
2. **Same mechanism, separate meshes.** Two batman-adv instances with an
   explicit policy for which traffic uses which.
3. **Routed adjunct**, the SAD section 5.3 fallback: bulk file transfer, service
   replication and video over a routed high-rate path, HaLow remaining the MANET
   fabric. Does not change the user-facing service model.
4. **No dedicated high-rate inter-node bearer**, permitted by CONOPS section 81
   if the sub-GHz bearer plus the access point meet the operational need.

## Closure evidence

SAD section 30.2: multi-node mobility and load; recovery; multicast and bulk
transfer.

Measured throughput and latency between nodes at recorded separations and with
recorded antenna configuration. `batctl` output showing the metric each bearer
receives and which path traffic actually took. A path-failover observation with
one bearer removed and traffic continuity recorded.

CONOPS section 40 traffic preference behaviour: video, large files and bulk
synchronization using the high-rate path while critical CoT and PLI stay on a
stable viable path.

Evidence is committed under `docs/evidence/TBR-RF-01/`.

## Closure gate

A selected arrangement carries bidirectional traffic between nodes at a rate
meeting a stated requirement, and routing selects the intended bearer under both
normal and degraded conditions, with all of it recorded.

**Closure gate per SAD section 30.2:** Before PDR / Stage 4.

No TBR closes on document wording alone. It closes only when its listed evidence
exists, the named owner accepts the evidence, and the resulting architecture
decision is entered into the persistent ADR register.

## Dependencies

- **Depends on:** `TBR-RF-03`, `TBR-LINUX-01`
- **Feeds:** `TBR-HW-01`
- **Related decisions:** `FML-ADR-025`, `FML-ADR-024`
- **Validating stage:** Stage 4 (CONOPS section 78)
- **Requires hardware:** Requires at least two nodes with the candidate
  high-rate radio. The prototype
BOM gates that card to one unit until PCIe routing, stack height and kernel
enumeration are verified.
