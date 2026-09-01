---
id: FML-ADR-069
title: A MULE shares its WAN uplink across the mesh and available uplinks are pooled
status: SELECTED TARGET
date: 2026-09-01
supersedes: none
superseded-by: none
trades: [TBR-NET-04]
verification: TBD
---

# FML-ADR-069 A MULE shares its WAN uplink across the mesh and available uplinks are pooled

## Context

The CONOPS already names this as the intended architecture, and an earlier draft
of `FML-ADR-068` wrongly treated the mesh as out of scope. This ADR records the
end state so nothing downstream mistakes the node-local first step for the whole
picture.

- **CONOPS section 41 (WAN independence)** makes WAN optional: losing it must not
  remove local EUD access, the local mesh, peer ATAK, local services, or the
  LoRa plane.
- **CONOPS section 42 (local WAN gateway)** says any standard MULE *shall* be
  capable of an authorized WAN-gateway role, over Starlink, Ethernet, cellular,
  or another approved path. It also says the **initial baseline may use one
  active gateway at a time, and automatic competing multi-gateway operation is
  not required for v1** -- which is exactly the statement that pooling multiple
  uplinks is the end state, deferred past v1, not a rejected idea.
- **CONOPS section 5** (the abstraction at section 410) says a user should not
  need to know which node owns the WAN gateway, which only holds if the gateway
  is a property of the mesh rather than of one node an EUD happens to sit on.
- **CONOPS section 43 (WAN overlay)** makes the MULE the routing and security
  boundary and forbids EUDs joining the overlay directly.

The tension that makes this a decision rather than a note: a WAN-less MULE in the
mesh should still reach reachback services through a peer that has an uplink, and
where several MULEs each hold an uplink -- Starlink on one, cellular on another
-- a single active gateway is both a single point of failure and wasted
capacity. Doing nothing islands every WAN-less node from reachback and pins the
whole mesh's egress to one radio.

What is known: `batman-adv` provides a gateway-mode mechanism for exactly this
shape of problem. What is not: how gateways are elected, whether more than one is
active at once, and whether multiple uplinks are load-shared or kept as
failover. That is `TBR-NET-04`, and this ADR is taken with it open.

## Decision

A MULE holding an authorized WAN uplink **shall** be able to provide WAN
reachability to WAN-less nodes across the mesh, so that WAN is a capability of
the mesh and not of the single node an operator's EUD is associated with.

Where more than one node holds an uplink, the mesh **should** pool the available
uplinks for resilience and capacity rather than depend on one gateway.

The node that owns an uplink **shall** remain the routing and security boundary
for traffic entering the secure WAN overlay (CONOPS section 43), and EUD traffic
**shall not** enter that overlay by way of this sharing (CONOPS section 744).

This is the end-state target. The v1 baseline may operate one active gateway at a
time, per CONOPS section 42; this ADR does not require pooling to exist in v1, it
requires the architecture not to foreclose it.

## Status

`SELECTED TARGET`. An objective the design is driven toward, named by CONOPS
section 42 and not yet demonstrated achievable. Nothing here is built or
measured; the enabling mechanism and its verification are `TBR-NET-04`.

`FML-ADR-068` is the node-local first step of this target -- an EUD reaching the
uplink of its own node -- and is consistent with the v1 single-gateway baseline.
This ADR does not supersede it; it is the mesh-wide generalization 068 pointed
to.

## Consequences

- **`batman-adv` gateway mode becomes a live configuration question.**
  `os/config/networkd.conf.template` lists `GatewayMode` among the `[BatmanAdvanced]`
  settings it does not yet decide; this ADR and `TBR-NET-04` are what will decide
  it. Gateway announcement, client-mode selection, and default-route handling on
  a node with no local uplink all follow.
- **The threat model widens beyond one node.** A device several hops away can
  reach an uplink, and the overlay boundary of CONOPS section 43 must hold across
  the mesh, not only at the node an EUD sits on. `THREAT_MODEL.md` records this.
- **Gateway selection in a partitionable mesh is genuinely hard.** A partition
  may end up with no gateway, or with two that were both valid before the split.
  Default-route churn as partitions form and heal is a failure mode the trade
  must address, and it is why the mesh, not a static route, has to own this.
- **Capacity and fairness become real.** Pooling several uplinks raises
  load-sharing versus failover, and a single EUD or node saturating a shared
  uplink is the contention `TBR-COMP-01` must measure.

## Accepted cost

The program accepts that making WAN a mesh-wide capability gives a compromised
node or EUD several hops away a path toward an uplink, where a node-local design
would not. The containment is the per-node overlay boundary (CONOPS section 43)
and admission vetting, both of which must now hold mesh-wide, and the pooling and
election logic that would make this safe and resilient is unbuilt. The program is
choosing the harder, more capable architecture over the simpler islanded one, and
`TBR-NET-04` is where that choice is paid for in engineering.

## Fallback

The v1 single-active-gateway baseline (CONOPS section 42) is both the fallback and
the starting point. If pooling proves unwise or unmanageable, the program stays at
one active gateway per mesh at a time, which still satisfies WAN independence and
the gateway role. The signal to stay there: gateway-election instability across
partitions, or an inability to bound the contention a shared uplink creates. Not
structural.

## Superseded by

None.

## Verification dependency

`TBD`, defined by `TBR-NET-04`. The gateway-sharing behaviour -- a WAN-less node
reaching the internet through a peer, and continuity when the gateway node leaves
-- belongs to `test/stages/stage-06-wan-overlay/` and
`test/stages/stage-12-nomad-integration/`, and the pooling contention to
`TBR-COMP-01`.
