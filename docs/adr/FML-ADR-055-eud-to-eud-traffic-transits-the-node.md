---
id: FML-ADR-055
title: EUD to EUD traffic transits the node
status: SELECTED PRINCIPLE
date: 2026-08-29
supersedes: none
superseded-by: none
trades: [TBR-NET-02, TBR-ID-01, TBR-RF-03]
verification: TBD
---

# FML-ADR-055 EUD to EUD traffic transits the node

## Context

CONOPS section 6 baselines four to eight authenticated EUD users per MULE, and
section 5.3 has a Team Lead and a Unit Member sharing one physical MULE with
different approved capabilities. So the normal case is several devices behind
one node, not one.

Nothing in this repository says whether those devices reach each other through
the node or directly across the access point. `os/config/hostapd.conf.template`
carries the question as `ap_isolate=TBD`, and that single line decides far more
than it appears to.

A node cannot address, filter, log or apply policy to traffic it never sees. If
the access point forwards frames directly between associated devices, then
every scheme for delivering a message to a particular EUD is inoperative, not
because it is badly designed but because the traffic never reaches the
component that would implement it. `TBR-NET-02` cannot be answered under one
setting of this line and is ordinary engineering under the other.

Two CONOPS requirements bear directly. Section 9.1 makes **policy enforcement**
and **degraded-communications control** S0 core node services, which shall
remain active whenever the node is operational; a node that cannot observe
inter-device traffic cannot enforce policy on it. Section 23 requires that
role-restricted information use an authenticated service rather than relying on
peer distribution behaviour, which presupposes that a service is in the path.

Against that sits a real cost, and it is the reason this ADR does not simply
set the flag. Section 9.2 makes **peer-to-peer ATAK** an S1 local mission
service that should remain available even when all external service hosts are
absent. Peer ATAK between two devices on one access point is exactly the
traffic that isolation stops. Whether a given driver and hostapd configuration
suppresses the multicast that peer ATAK depends on is a property of the
selected radio and driver, and **it has not been measured here**. `TBR-RF-03`
and `TBR-LINUX-01` own the hardware half.

## Decision

Traffic between EUDs associated with the same node **shall** transit the node.

The design **shall not** depend on the access point forwarding frames directly
between associated devices.

## Status

`SELECTED PRINCIPLE`.

What is decided is the principle: the node is in the path, and any addressing,
policy or delivery decision may assume it. What is deliberately left to a later
implementation ADR is how that is achieved and what it costs to preserve S1
peer-to-peer ATAK through it.

Specifically left open: the exact `ap_isolate` value and any equivalent driver
setting; whether preserving peer ATAK requires the node to relay or reflect the
traffic, or whether a local service supplants the peer path; and the
measurement of what isolation does to peer ATAK on the selected radio. That
measurement needs a wireless stack, which hosted CI does not have; see
`docs/dev-machine.md`.

## Consequences

`TBR-NET-02` becomes answerable. Every option in it assumes the node can see
the traffic, and this is what makes that assumption legitimate rather than
hopeful.

The S0 obligations in section 9.1 become dischargeable. Policy enforcement and
degraded-communications control over inter-device traffic are possible only if
that traffic is observable.

Work is created rather than avoided. S1 peer-to-peer ATAK now depends on a node
function rather than on the radio doing it for free. That function has to be
specified, built and tested, and until it exists this principle and section 9.2
are in tension. The tension is recorded here rather than resolved, because
resolving it requires a measurement nobody can take yet.

A contributor without hardware can act on this. The principle constrains
software design immediately and the hardware question is separable.

## Accepted cost

**A new single point of failure inside the node, on a capability the CONOPS
wants available when everything else is absent.** Today, two EUDs on one access
point can exchange peer ATAK traffic even if most of the node's software is
broken, because the radio does it. After this decision they cannot: if the
relaying or serving function fails, peer ATAK between co-located team members
fails with it, and section 9.2 wants that capability available precisely when
external hosts are gone.

The program accepts it because the alternative is worse in a way that is harder
to see. An access point that forwards device to device silently makes every
addressing, filtering and audit requirement unimplementable, and it does so
without any error, log line or failed test. A capability that depends on a node
function at least fails visibly and can be tested. This one cannot be tested at
all under the other setting, because there is nothing in the path to test.

There is also an airtime cost on the wireless side: traffic that crossed once
between devices now crosses twice, device to node and node to device. On the
EUD access point that is affordable. It would not be on the sub-GHz bearer, and
this decision does not extend there.

## Fallback

Permit direct forwarding and abandon node-mediated addressing on the IP plane.
That is a real fallback and it is cheap to take: one setting, no structural
change.

What it costs is `TBR-NET-02` on the IP plane entirely, and the section 9.1 S0
obligations over inter-device traffic. The LoRa plane is unaffected either way,
because the node is the only thing with a radio there.

The signal to take it is a measurement showing that preserving S1 peer-to-peer
ATAK through the node costs more than the addressing is worth on the selected
hardware. That measurement is named in the status section and does not exist.

## Superseded by

None.

## Verification dependency

`TBD`, pending `TBR-RF-03` and `TBR-LINUX-01` for the hardware half.

The software half is testable earlier. A node that assumes it is in the path
can be exercised against the flat-sat, and 802.11s and access point behaviour
become testable on a machine with a wireless stack, which hosted CI does not
provide. CONOPS section 78 stage 1 is the first stage that could carry it.
