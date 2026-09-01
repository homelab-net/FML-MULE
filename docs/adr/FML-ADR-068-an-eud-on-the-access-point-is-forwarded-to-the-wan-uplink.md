---
id: FML-ADR-068
title: An EUD on the access point is forwarded to the WAN uplink
status: SELECTED
date: 2026-09-01
supersedes: none
superseded-by: none
trades: []
verification: TBD
---

# FML-ADR-068 An EUD on the access point is forwarded to the WAN uplink

## Context

The EUD access point (`os/config/hostapd.conf.template`) admits operator phones
and tablets. `os/config/nftables.conf.template` left every forwarding question
about those devices open: its `forward` chain defaults to drop and carries two
`TBD` notes, one for EUD-to-mesh forwarding and one for mesh-to-mesh. Neither
said what happens between an EUD and the node's own WAN uplink.

That gap forced a decision during bench bring-up. An operator on a single phone
who joins the MULE expects the MULE to be their connectivity, not to lose the
internet the moment they associate. A default-drop forward chain makes the
access point a captive island: an EUD reaches services on its own node and
nothing else. On the bench this presented exactly as "I lose WAN when I
connect", because source NAT was in place but the `filter` `forward` chain still
dropped the traffic.

The tension is real and is not resolved by wishing it away. `THREAT_MODEL.md`
records that the MULE **cannot detect or contain a compromised EUD**, and the
WAN uplink is not a dumb internet pipe: it reaches the WAN overlay
(`FML-ADR-039`, Tailscale) and therefore other MULEs and program
infrastructure. Forwarding an untrusted device to that uplink widens what a
compromised EUD can touch.

Three options were genuinely on the table:

- **Local mission services only.** Safest; an EUD never reaches the uplink. But
  it makes the MULE useless as the operator's connectivity, which is a role the
  program expects it to fill.
- **Full passthrough.** The EUD gets general IP connectivity through the MULE's
  uplink, like any home router. Operationally what people expect; carries the
  exposure above.
- **Gated passthrough.** Passthrough allowed but constrained to defined
  destinations or toggled per mission package. More capable, but it needs a
  policy nobody has written and a trade to define it.

The Program Owner decided on 2026-08-31 for full passthrough, accepting the
exposure explicitly rather than deferring the capability.

## Decision

An end user device associated to the EUD access point **shall** be forwarded to
the node's WAN uplink and **shall** receive general IP connectivity through it,
by source NAT at the uplink and an explicit accept of the access-point-to-uplink
path in the node firewall.

This decision governs the path from **this node's own access point** to **this
node's own WAN uplink**: the node-local first step of the WAN-gateway role CONOPS
section 42 gives every MULE. It is consistent with the CONOPS v1 baseline of one
active gateway at a time, and it is deliberately **not** the whole picture:

- **Mesh-wide WAN sharing -- a MULE fanning its uplink out to WAN-less nodes, and
  pooling several nodes' uplinks -- is the intended end state, decided in
  `FML-ADR-069`,** not something this ADR forecloses. An earlier draft of this
  ADR wrongly called the mesh out of scope; it is the target this step builds
  toward. The mechanism (`batman-adv` gateway mode, gateway election, pooling)
  is `TBR-NET-04`, and the `GatewayMode` `TBD` in
  `os/config/networkd.conf.template` is where it lands.
- The rules this ADR adds match on the **access-point interface and the EUD
  prefix** so that mesh-wide egress is enabled deliberately by `FML-ADR-069`,
  never inherited by accident before its mechanism is decided.
- **Whether an EUD is also forwarded onto the `batman-adv` mesh** (distinct from
  the uplink) remains open: the existing `forward`-chain `TBD` and `TBR-TAK-01`.

The passthrough targets the **general WAN uplink** (Starlink, Ethernet, cellular;
CONOPS section 42), and the node **shall not** route EUD traffic into the secure
WAN overlay: CONOPS section 43 and section 744 make the MULE the routing and
security boundary and forbid EUDs reaching the overlay. So the exposure this
creates is to the general internet uplink, not to the overlay and the other MULEs
behind it.

The path **shall** remain subject to the node's emission posture: a mission or
EMCON profile that forbids emission on the WAN bearer suppresses the passthrough
along with every other emitter, because an EUD's uplink traffic makes the node
transmit.

## Status

`SELECTED`. Architecture direction accepted by the Program Owner for the current
package on 2026-08-31.

Demonstrated on the prototype access point as `SIMULATED` only: with the
`forward` policy at drop, source NAT alone did not pass EUD traffic, and adding
the access-point-to-uplink accept plus established-return accept restored it,
verified end to end from the EUD subnet. Nothing here is `HARDWARE-VERIFIED`,
and the production firewall that expresses this is not yet built; see
verification.

## Consequences

- **`os/config/nftables.conf.template` gains a decided rule where it had a
  `TBD`.** The `forward` chain accepts the access-point interface outbound to
  the WAN uplink and accepts established/related return traffic; a `nat`
  `postrouting` masquerade on the uplink is required. The bench showed the
  masquerade is necessary but **not sufficient**: with a default-drop `filter`
  `forward` policy the packet is still dropped, and both pieces must be present.
- **The threat model widens.** A compromised EUD now has a routed path to the
  general WAN uplink, so the blast radius of a bad EUD grows from node-local to
  that uplink. It does **not** gain the secure overlay: CONOPS section 43 keeps
  the MULE the boundary and the rules do not route EUD traffic onto it. This is
  recorded in `THREAT_MODEL.md` under what the design does not defend against;
  it is a consequence of this decision, not a defect to fix.
- **EMCON and QoS become live concerns.** Passthrough must be suppressible by
  the emission profile (`mission/profiles/`), and an EUD saturating the uplink
  can starve mission traffic, which is the peak condition `TBR-COMP-01` must
  measure. Neither the suppression hook nor a rate policy exists yet.
- **Contributor impact is small.** The firewall rule is expressible and
  reviewable on a laptop against the template and the bench; it needs no radio.

## Accepted cost

The program knowingly accepts that an untrusted, possibly compromised EUD has a
routed path to the WAN uplink and, through it, to the overlay that reaches other
MULEs and program infrastructure. This is the specific thing someone will later
argue was a mistake: a device the MULE cannot vet or contain is given reach
beyond its own node.

It is accepted because being the operator's connectivity is a role the MULE is
expected to fill, and because the compensating controls are organisational and
deferred rather than structural: mission-time vetting of who holds an EUD
(`THREAT_MODEL.md` names admission vetting as the primary control), the emission
profile, and a future gating policy. Until that gating exists the exposure is
un-narrowed, and that is the cost.

## Fallback

Reversible, not structural. Removing the forward accept and the uplink
masquerade returns an EUD to node-local services only, which is the "local
mission services only" option above. The recovery costs one firewall change and
breaks no stored state.

The signal to take the fallback: evidence that EUD-originated traffic reached a
sensitive overlay endpoint it had no reason to reach, or that uplink contention
from EUD traffic starved mission traffic under load. Either would argue for
gated passthrough (`TBR-TAK-01` is where that policy belongs) rather than a bare
revert.

## Superseded by

None.

## Verification dependency

`TBD`. The firewall behaviour is exercisable now on the flat-sat and the bench:
a packet sourced from the EUD subnet reaches the internet through the uplink,
and the same packet is dropped when the accept rule is removed, which is the
test that fails without the decision. Hardware confirmation and the EMCON
suppression path belong to `test/stages/stage-06-wan-overlay/`, and the
contention behaviour under load to `TBR-COMP-01`.
