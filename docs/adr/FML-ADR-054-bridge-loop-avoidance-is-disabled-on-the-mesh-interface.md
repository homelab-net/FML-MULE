---
id: FML-ADR-054
title: Bridge loop avoidance is disabled on the mesh interface
status: SUPERSEDED
date: 2026-08-28
supersedes: none
superseded-by: FML-ADR-056
trades: [TBR-RF-01]
verification: TBD
---

# FML-ADR-054 Bridge loop avoidance is disabled on the mesh interface

## Context

A three-node batman-adv mesh in `.github/workflows/mesh-probe.yml` took about
thirty-one seconds after interface attach before any node could reach any other
node. Every table read correctly throughout: originators converged in about
four seconds, the translation tables carried each peer's client address with
the right originator, and batman-adv's own protocol traffic crossed every link
the whole time.

Six runs were spent on the wrong layer before the delay was located, and the
measurement is worth stating because the shape of it is what identified the
cause. node1 emits an ARP request for its peer at 1.07s and repeats it about
once a second. node2's `bat0` does not see the first one until 31.463s, and
answers it 34 microseconds later. The requesting node's neighbour entry goes
`REACHABLE` 1.1ms after that, the first echo request leaves 7 microseconds
later, and the reply is back 27 microseconds after that.

So nothing was slow. One frame was held, and everything downstream of it
followed within two milliseconds of its release.

Reading back the settings actually in force on the running mesh named the only
candidate. The attach path set two of them and left every other one at whatever
the module compiled in:

    aggregation              enabled
    bridge_loop_avoidance    enabled
    distributed_arp_table    disabled
    fragmentation            enabled
    multicast_mode           disabled
    network_coding           disabled
    orig_interval            1000

Bridge loop avoidance is the only one of those that withholds client traffic on
purpose. It exists so that two mesh nodes bridged to a common wired LAN do not
form a forwarding loop, and it holds client frames until its claim mechanism has
settled.

That was measured rather than assumed, one variable, a fresh mesh per value,
both legs of the same run:

    bridge_loop_avoidance    first reply, one hop    first reply, two hops
    enabled                  31.5s                   31.5s
    disabled                  2.150s                  4.391s

With it disabled the first echo request on the wire carries sequence 1. With it
enabled the first one to reach the interface at all carries sequence 101, the
hundred before it having been refused by the requesting node's own neighbour
layer, which reported `Destination Host Unreachable` and backed off.

Nothing chose this setting. It has been in force by default since the mesh was
first brought up, and `os/config/batman-adv.conf.template` carried it as `TBD`.

One further fact shapes this decision, recorded from the program owner after
the measurement and before this ADR was accepted: **several MULE nodes are
likely to share one LAN during configuration, during over-the-air update, and
in a tactical operations centre.** That is the exact topology bridge loop
avoidance exists for, so the protection being given up is not one this program
was never going to need. What makes disabling it safe is narrower than
"nothing is bridged today": it is that the mesh interface is not a member of a
bridge carrying that shared segment, which is a separate decision, and one this
repository had not written down anywhere.

## Decision

Bridge loop avoidance shall be disabled on the mesh interface.

## Status

`SELECTED`.

The evidence is `SIMULATED`. It was taken over a veth pair, which is a perfect
wire, and says nothing about behaviour on a real bearer. What it does establish
is a mechanism rather than a number: a mesh with this setting enabled and
nothing bridged to it withholds client frames for tens of seconds while
reporting itself healthy, and a mesh without it does not. That mechanism does
not depend on the link layer.

## Consequences

A node that joins the mesh becomes usable in about two seconds rather than
about thirty. That is the difference between an operator who plugs in and works
and an operator who plugs in, sees nothing, and starts diagnosing a radio.

It also removes a failure mode that presents as an RF problem and is not one.
Every table reads correct while nothing passes, which is the hardest kind of
fault to diagnose in a car park with no laptop.

The loop protection is genuinely given up, and the condition under which it
matters is a planned operating condition rather than a hypothetical.
`FML-ADR-045` keeps the EUD access point a
separate logical radio function and `os/config/batman-adv.conf.template` records
that the access point does not join the mesh, so today nothing bridges `bat0` to
anything and there is no loop to avoid. The moment anything does bridge `bat0`
to another interface, whether an access point bridge, a wired uplink or a second
mesh interface on a common segment, this decision becomes unsafe and shall be
revisited before that bridge is built.

## Accepted cost

Two or more MULE nodes bridging the mesh interface onto one shared segment form
a forwarding loop that batman-adv no longer breaks, and on a low-rate bearer a
broadcast storm takes the mesh down rather than slowing it. Worse, it presents
as a radio fault: this is the same shape as the defect this ADR came from,
where every table read correct while nothing passed.

An earlier draft of this section called that a foreseeable field mistake. That
was wrong, and it is corrected here rather than softened. The program owner
states that several nodes sharing one LAN is expected during configuration,
during over-the-air update, and in a tactical operations centre. It is a normal
operating condition, and calling it a mistake would have understated it to
exactly the reader who most needs the warning.

What the program accepts is therefore narrower than it first appears. It is not
"a loop is unlikely". It is that **the mesh interface shall not be a member of
a bridge carrying a shared segment**, which holds the loop off by construction
in every one of those settings, and which is independently the right choice: a
flat layer 2 spanning the mesh and a shared LAN puts all of that segment's
broadcast onto a low-rate bearer, which this template already records as
unsolved work. Two nodes on one LAN is safe. Two nodes bridging that LAN into
the mesh is not, and nothing about sharing a LAN requires bridging it.

The cost of being wrong about that is the loop. The cost of the protection was
thirty seconds of dead air on every join, in every deployment, forever.

## Fallback

Re-enable it, which is one setting and no structural change. The signal that
would call for it is any design that bridges `bat0`, and the fallback is not
merely re-enabling it but pairing it with a measured warm-up figure, because
this decision records what that costs.

If a topology needs both fast join and loop protection, there are two better
answers than a global re-enable.

Prevent the loop by construction: keep the mesh interface unbridged and route
rather than bridge between the mesh and any other segment. This is the
preferred answer, and the one the accepted cost above relies on.

Failing that, make the setting a function of topology rather than a constant.
It is a runtime setting, so a node that brings the mesh interface up inside a
bridge may enable loop avoidance and one that does not may leave it off. That
pays the thirty seconds only where it buys something, which is the tactical
operations centre and the update bench rather than every field join. This is
recorded as available, not selected: it is more machinery than a program with
no networking configuration yet should build, and it should be decided when
that configuration is written.

## Superseded by

`FML-ADR-056`.

## Verification dependency

`TBD`, pending `TBR-RF-01`.

The condition above is enforced rather than merely written down.
`tools/validate-docs.sh` check 19 fails when any configuration under `os/` puts
the mesh interface in a bridge while loop avoidance is disabled, and when the
access point is bridged onto a named bridge whose membership nothing records.
It has been watched to fire on all five spellings of bridge membership, and the
first version of it silently passed `ip link set bat0 master br0`, which is the
most common one.

The warm-up figure is asserted on every run of
`.github/workflows/mesh-probe.yml`, which fails if a cold mesh does not carry
traffic within ten seconds of attach. That check has been watched to fail: the
configuration this ADR replaces measures 31.5 seconds against it.

That is a regression check on the mechanism, not verification of the decision.
`TBR-RF-01` owns the question of what the figure becomes on a real bearer, where
a held frame competes with contention, loss and rate adaptation rather than with
a perfect wire.
