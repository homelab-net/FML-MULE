---
id: TBR-NET-04
title: How does the mesh elect and pool WAN gateways across multiple uplinks
status: OPEN
owner: TBD-SRR
area: NET
priority: 99
function-owner: TBD
critical-path: false
depends-on: []
feeds: []
requires-hardware: partly
evidence: docs/evidence/TBR-NET-04/
adr: [FML-ADR-069]
target-date: TBD-SRR
---

# TBR-NET-04 How does the mesh elect and pool WAN gateways across multiple uplinks

## Question

When several MULEs on one mesh each hold a WAN uplink, how does the mesh decide
which node's uplink carries a given WAN-less node's traffic, and whether the
uplinks are pooled for capacity or held as failover?

## Why it matters

`FML-ADR-069` decides that WAN is a mesh-wide capability and that available
uplinks should be pooled, but names no mechanism. Until this closes,
`os/config/networkd.conf.template` cannot decide `GatewayMode`, the roadmap item
for mesh WAN sharing cannot leave its target state, and the v1 baseline stays at
one active gateway (CONOPS section 42). `FML-ADR-068` (EUD-to-uplink on one node)
is built on the assumption that this generalization is coming and must not be
contradicted by it.

## Options

- **`batman-adv` gateway mode, single active.** One node announces itself as the
  gateway; others run in client mode and route their default through it. Simplest,
  matches the CONOPS v1 baseline, and gives failover if election is automatic.
  Right answer if pooling turns out not to be worth the complexity, or if
  gateway-election churn across partitions proves hard to bound.
- **`batman-adv` gateway mode, multiple active with client selection.** Several
  nodes announce; each client selects a gateway by advertised class or by
  routing metric. Approaches pooling by spreading clients across uplinks. Right
  answer if the class advertisement is stable enough to prevent flapping.
- **Policy routing above batman-adv.** Gateways announced by batman, but uplink
  selection and any load-sharing done by an explicit routing policy per node.
  More control and more moving parts. Right answer only if the batman-native
  mechanisms cannot express the pooling the program wants.
- **Do nothing beyond v1.** Stay at one active gateway indefinitely. Right answer
  if the resilience gain from pooling never justifies the election and fairness
  problems it introduces.

Every option must preserve the CONOPS section 43 boundary: the uplink-owning node
stays the security boundary, and EUD traffic does not enter the secure overlay
through the shared path.

## Closure evidence

A multi-node exercise -- on `mac80211_hwsim` for the routing logic, and on real
radios for the parts `hwsim` cannot speak to -- recording, with at least two
uplink-holding nodes and at least one WAN-less node: which gateway each client
selects, the reachability and throughput a WAN-less node obtains through a peer's
uplink, the behaviour when a gateway node leaves and rejoins, and the default-route
state on both sides of an induced partition. Committed under
`docs/evidence/TBR-NET-04/`.

## Closure gate

A named owner accepts that a WAN-less node obtains WAN reachability through a
peer's uplink; that when the serving gateway leaves, a WAN-less node either fails
over to another available uplink or degrades to no-WAN without losing local
services (CONOPS section 41); and that no configuration in the exercise routes EUD
traffic into the secure overlay (CONOPS section 43). Whether pooling is
multi-active or failover-only is a comparison the owner records against the
resilience and contention observed, not a threshold fixed here.

## Dependencies

- **Depends on:** `TBR-NET-01` (the addressing and prefix scheme the routing acts
  on), `TBR-LINUX-01` (interface naming and driver behaviour).
- **Feeds:** `FML-ADR-069`, and the `GatewayMode` decision in
  `os/config/networkd.conf.template`.
- **Related decisions:** `FML-ADR-069`, `FML-ADR-068`, `FML-ADR-039` (the WAN
  overlay), `FML-ADR-053` (BATMAN-IV, whose gateway-mode behaviour applies).
- **Validating stage:** `test/stages/stage-06-wan-overlay/`.
- **Requires hardware:** `partly`. The routing and election logic is exercisable
  on `mac80211_hwsim`; real uplink behaviour and RF are not.

## Frontmatter notes

`priority` is a placeholder SAD section 30.2 register position pending SRR triage.
`owner` is `TBD-SRR`: assigning a named individual and a target date is an SRR exit
action, and the marker records the gap rather than hiding it.
