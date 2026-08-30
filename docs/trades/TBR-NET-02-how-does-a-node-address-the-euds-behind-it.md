---
id: TBR-NET-02
title: How does a node address the EUDs behind it
status: OPEN
owner: Cameron Zobrist
area: NET
priority: 99
function-owner: Network
critical-path: false
depends-on: []
feeds: [TBR-ID-01]
requires-hardware: no
evidence: docs/evidence/TBR-NET-02/
adr: [FML-ADR-057, FML-ADR-056, FML-ADR-026, FML-ADR-048]
target-date: TBD-SRR
---

# TBR-NET-02 How does a node address the EUDs behind it

## Question

When several EUDs share one MULE, how does the node decide which of them a
given message, packet or mesh frame is for?

## Why it matters

CONOPS section 6 baselines four to eight authenticated EUD users per MULE, and
section 5.3 has a Team Lead and a Unit Member sharing one physical node. The
shared case is the normal case, not the exception.

Three things are waiting on this.

**The LoRa plane cannot express a recipient at all.** `FML-ADR-026` makes
Meshtastic a separate non-IP plane and CONOPS section 50.8 makes it the bearer
that carries selected essential traffic when IP is gone. Meshtastic addresses a
**node**, and its `Data` submessage carries `source` and `dest` as node
numbers. A MULE has one LoRa chain by CONOPS section 36, so it is one node, and
several users behind it collapse to one address. Person to person messaging
over the lifeline bearer is currently not expressible, and nothing records that
it is a known gap rather than an oversight.

**The interface for the LoRa plane cannot be designed.** `docs/ROADMAP-DEV.md`
item 1.1 step 2 is a narrow interface with a fake, and its shape depends
entirely on whether a node is one identity or a gateway fronting several. That
work is blocked on this answer, and building it first would produce an
interface that has to be replaced.

**There are three identity namespaces and nothing maps between them.** ATAK
carries a CoT UID and callsign. Browser services will carry whatever
`TBR-ID-01` decides, with `FML-ADR-037` preferring application-native RBAC.
Meshtastic carries a node number. The degradation ladder in CONOPS section 5.5
deliberately moves traffic between planes as capability is lost, so the absence
of a mapping is felt exactly when things are going badly.

**The IP plane is not the problem, and an earlier draft of this trade said it
was.** SAD section 4.3 bridges local EUD access into the BATMAN domain, so
every EUD behind every MULE sits in one flat layer 2 domain with its own MAC
and address. `EUD-A1` reaching `EUD-B3` two MULEs away is a layer 2 path that
`batman-adv` forwards, with ARP resolving across the mesh. Delivery to a
particular device is already solved there and needs nothing from this trade.

What this trade owes the IP plane is narrower: **which user** a device belongs
to, for policy and for gateway-mediated traffic. That is identity, not routing.

**The cliff is at the plane boundary.** On IP each EUD is individually
addressable. On LoRa only the MULE is, because `Data.dest` names a node and a
MULE has one LoRa chain. CONOPS section 50.8 `LOW-BANDWIDTH` is where an
operator crosses from one to the other, and **nothing in this repository
records that person-to-person addressing is lost at that step.** Someone who
can send to one teammate at 09:00 cannot at 09:05, and no document says so.
Recording that, in terms an operator meets rather than a protocol field, is
part of this trade's output whichever option is selected.

`mule/admission.py` records the floor this sits on: there is no identity,
credential or enrollment anywhere in this repository yet. That is `TBR-ID-01`.
This trade is not that question. It asks how addressing is **structured**, so
that the answer survives `TBR-ID-01` closing rather than being rebuilt by it.

## Options

**A. Defer. Deliver to every EUD behind the node.** Costs nothing now and is
what happens today by default. It is the right answer if per-recipient delivery
turns out never to be needed, which would require that all traffic is
team-wide by nature. Against it: CONOPS section 23 already distinguishes
role-restricted information, and on the LoRa plane every duplicated delivery is
airtime on the bearer with the least of it.

**B. One node-local EUD handle, with a pluggable binding source.** Define a
single handle namespace on the node. Each plane maps its native identifier onto
it. The handle is bound from access point association today and from an
authenticated identity once `TBR-ID-01` closes; the addressing layer does not
change when the binding source does. Right if the program wants to build
before authentication exists without rework. Against it: a handle bound only to
association is a claim about a MAC address, and must be labelled as such rather
than trusted.

**C. Per-plane addressing with pairwise translation, no common handle.** Let
each plane keep its own identifier and translate only where a specific path
needs it. Right if the planes rarely cross-reference and pairwise translation
is cheaper than maintaining a namespace. Against it: the number of mappings
grows with the number of planes, and the degradation ladder makes crossing
planes normal rather than rare.

**D. Move identity to the edge: one Meshtastic radio per EUD.** An ATAK
Meshtastic plugin with a radio per device removes the shared-node case on the
LoRa plane entirely, giving one identity per person and restoring direct
messaging. Right if per-EUD radios are affordable and the section 9.1
obligation can be met another way. Against it: CONOPS section 36 mandates a
LoRa chain in the MULE and that would need re-justifying; and section 9.1 makes
degraded-communications control an S0 node service, which a node cannot perform
on a plane it is not on. Nothing in this repository currently mentions plugins
at all.

## Closure evidence

A written addressing specification, committed under `docs/evidence/TBR-NET-02/`,
containing all four of:

1. **A mapping table** from each of the three namespaces (CoT UID and callsign,
   browser-service identity, Meshtastic node number) onto whatever addressing
   structure is selected, with the direction of resolution stated for each.
2. **A worked trace per plane**, one message end to end: an inbound CoT message
   naming a recipient, and an inbound Meshtastic packet, each followed from
   arrival at the node to delivery at one named EUD, with the resolution step
   shown at each hop.
3. **A statement of what an operator loses at the plane boundary**, written for
   the operator rather than the protocol: what addressing exists on IP, what
   exists on LoRa, and what stops working at CONOPS section 50.8.
4. **The LoRa tag encoding and its cost in bytes**, stated against
   `DATA_PAYLOAD_LEN`, which is 233 bytes in the Meshtastic protobuf. A tag
   whose cost is not stated is not a design.
5. **The unresolved-recipient rule**, stating what the node does when it cannot
   determine the intended EUD.

The first four may be produced by analysis on rig R0 or R1. The fifth is a
decision and needs no rig.

## Closure gate

A named owner accepts the specification when it satisfies all five items above
and, in addition, states explicitly **what changes when `TBR-ID-01` closes and
what does not**. That last condition is the point of running this trade before
that one, and a specification that cannot answer it has not separated
addressing from authentication.

The unresolved-recipient rule shall fail closed: a node that cannot resolve a
recipient shall not deliver to every EUD as a fallback. This is stated as a
gate rather than left to the analysis because delivering to everyone is the
natural implementation, it looks like helpfulness, and CONOPS section 23 makes
it wrong. The same reasoning as `FML-ADR-042` for time.

## Dependencies

- **Depends on:** none. `TBR-ID-01` is not a prerequisite, deliberately: this
  trade exists to structure addressing so that authentication can be added to
  it rather than redesign it.
- **Feeds:** `TBR-ID-01`, and `docs/ROADMAP-DEV.md` item 1.1 step 2, which
  cannot be shaped until this is answered.
- **Related decisions:** `FML-ADR-057` states which traffic the node may act on
  and which it may not, which is what bounds every option here. `FML-ADR-056`
  keeps the field domain flat and bridged, which is why the IP half of this
  trade is identity rather than routing. `FML-ADR-026` makes LoRa a
  separate non-IP plane. `FML-ADR-048` fixes the gateway translation order.
  `FML-ADR-037` prefers application-native RBAC. `FML-ADR-042` is the
  fail-closed precedent the closure gate follows.
- **Validating stage:** stage 1 for the local node path, stage 3 for LoRa
  continuity.
- **Requires hardware:** `no`. Every part of this can be answered on an
  ordinary machine, which is why it is in `ITEP-C01`.

## Frontmatter notes

`priority` is 99 because this trade postdates the SAD section 30.2 register and
therefore has no position in it. `critical-path` is `false` on the same
grounds: the SAD marks the critical path and does not know about this trade.
Neither field should be read as a judgement that the question is unimportant;
`docs/ROADMAP-DEV.md` item 1.1 is blocked on it.
