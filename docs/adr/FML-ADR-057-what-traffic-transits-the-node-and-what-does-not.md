---
id: FML-ADR-057
title: What traffic transits the node and what does not
status: SELECTED PRINCIPLE
date: 2026-08-29
supersedes: FML-ADR-055
superseded-by: none
trades: [TBR-NET-02, TBR-ID-01]
verification: TBD
---

# FML-ADR-057 What traffic transits the node and what does not

## Context

`FML-ADR-055` decided that traffic between EUDs associated with the same node
shall transit the node, so that the node could address, filter and apply policy
to it. It was written on the same wrong premise as `FML-ADR-054`: that the EUD
access point is not bridged into the field domain.

It is. SAD section 4.3 bridges local EUD access into the BATMAN domain
precisely so that peer ATAK multicast traverses the mesh and clients need no
MANET routing awareness. Achieving `FML-ADR-055` would mean isolating stations
at the access point, which stops the station-to-station traffic that peer ATAK
depends on. CONOPS section 9.2 makes peer-to-peer ATAK an S1 local mission
service that should remain available even when all external service hosts are
absent, so `FML-ADR-055` would have traded away an S1 capability to gain a
property the architecture never promised.

The motivation behind it was still sound, and the correction is narrower than
withdrawal. `TBR-NET-02` needs to know which traffic the node can act on. The
honest answer is that it depends on where the traffic came from, and the two
cases are cleanly separable.

## Decision

Traffic arriving from the mesh or from the LoRa plane and destined for an EUD
**shall** be treated as transiting the node, because the node forwards it and
therefore may resolve, filter or annotate it.

Traffic between two EUDs associated with the same access point **shall not** be
assumed to transit the node. Design shall not place a requirement on that path.

## Status

`SELECTED PRINCIPLE`.

What is decided is which traffic a node may act on, which is what `TBR-NET-02`
needs in order to be answerable. What is left to that trade and to a later
implementation ADR is what the node then does with the traffic it can act on.

## Consequences

`TBR-NET-02` becomes answerable without requiring station isolation. Every
message arriving from another MULE or over LoRa passes through the node, so
recipient resolution has somewhere to live.

Peer-to-peer ATAK between two people at the same MULE keeps working exactly as
the architecture intends, over the bridge, at layer 2, with no node function in
the path and nothing to fail.

The limit is real and worth stating plainly: **a node cannot enforce policy on
traffic between two EUDs on its own access point.** CONOPS section 9.1 lists
policy enforcement as an S0 core node service, and this decision records that
the service does not extend to that path. CONOPS section 23 already governs it
from the other direction: information on a common peer domain is visible to all
authenticated participants, and role-restricted information shall use an
authenticated service rather than relying on peer distribution behaviour. The
rule and the limit agree.

## Accepted cost

The node has a blind spot on its own access point, and it is the path with the
least supervision and the most traffic. Two EUDs can exchange anything at layer
2 without the node observing it, which means it cannot be filtered, counted, or
audited.

The program accepts this because closing it costs an S1 capability the CONOPS
wants available when everything else is gone, and because CONOPS section 23
already tells operators not to rely on that path for anything restricted. A
blind spot that is written down and covered by a training rule is better than
an S1 service that fails when a node function does.

## Fallback

Isolate stations at the access point and provide peer distribution as a node
function. That is `FML-ADR-055`'s position and it remains available.

The signal to take it is a requirement that cannot be met any other way: an
auditing or filtering obligation over EUD-to-EUD traffic that CONOPS section 23
turns out not to satisfy. Taking it means specifying, building and testing the
peer distribution function first, because without it peer ATAK stops.

## Superseded by

None.

## Verification dependency

`TBD`.

The first half is exercisable against the flat-sat: traffic arriving from a
peer can be shown to reach a resolution point. The second half is a statement
about what is *not* required and is verified by the absence of any design that
depends on it, which is a review obligation rather than a test.
