---
id: FML-ADR-056
title: What may share a bridge with the mesh interface
status: SELECTED
date: 2026-08-29
supersedes: FML-ADR-054
superseded-by: none
trades: [TBR-RF-01, TBR-NET-01]
verification: TBD
---

# FML-ADR-056 What may share a bridge with the mesh interface

## Context

`FML-ADR-054` disabled `bridge_loop_avoidance` on the strength of a
measurement: 31.5 seconds to first reply with it enabled against 2.150 seconds
with it disabled, one variable, both legs of one run. That measurement stands
and this ADR does not revisit it.

**Its stated premise was wrong.** `FML-ADR-054` said the setting was safe
because "bat0 is bridged to nothing here: the EUD access point is a separate
logical radio function per `FML-ADR-045`". `FML-ADR-045` separates *radio
functions*; it says nothing about layer 2 domains. The architecture is explicit
in the other direction. SAD section 4.3:

> Local EUD access is bridged into the field BATMAN domain so: peer ATAK
> multicast can traverse the mesh; a team retains local connectivity if the
> mesh fragments; clients do not require awareness of MANET routing.

`FML-ADR-024` records the same, and adds that ordinary EUD broadcast is
therefore not free. So the mesh interface is bridged **by design**, and it
always was.

Two things followed from the error. The safety condition in `FML-ADR-054` read
as a future risk when it was a present contradiction. And
`tools/validate-docs.sh` check 19, written to enforce that condition, fails on
any bridge containing the mesh interface, which means it forbade the baselined
architecture and would have fired the first time anyone implemented SAD
section 4.3.

The Program Owner has directed that bridge loop avoidance stays off and that
the shared-LAN case is handled by design rather than by paying the warm-up.
This ADR is that design.

The loop bridge loop avoidance protects against needs **two** things: the mesh
interface in a bridge, and a second path between the same layer 2 domain
outside the mesh. The first is the architecture. The second is not required by
anything, and that is the opening.

## Decision

The bridge carrying the mesh interface **shall** contain only EUD access point
interfaces alongside it.

An interface that reaches a segment shared with any other node — a wired
uplink, a management port, a venue or partner LAN — **shall not** be a member
of that bridge.

A wired link that is intended to carry field traffic **shall** join the mesh as
a `batman-adv` hard interface rather than as a bridge port, because
`batman-adv` performs its own loop-free path selection across multiple hard
interfaces.

A wired link used for configuration, over-the-air update or operations-centre
connectivity **shall** be a routed interface with its own address, and shall
not be a bridge port.

`bridge_loop_avoidance` remains disabled.

## Status

`SELECTED`. Supersedes `FML-ADR-054`.

The warm-up measurement behind it is `SIMULATED`, taken over `veth` in hosted
CI. The rule stated here is structural and does not depend on that measurement.

## Consequences

The tactical operations centre, configuration bench and over-the-air update
cases are safe without loop avoidance, because in all three the shared LAN is a
routed management interface rather than a bridge port. Several MULEs on one
switch cannot form a loop if none of them bridges that switch into the field
domain.

Two nodes deliberately cabled together for field traffic are also safe, and get
a better result than bridging would have given: `batman-adv` sees a second hard
interface, includes it in path selection, and routes over it without a loop.

Check 19 must be rewritten. It currently forbids the architecture, which is a
defect introduced by the same premise error, and leaving it would train
contributors to work around a check rather than trust it.

The warm-up figure is kept: about two seconds at one hop rather than 31.5.
On a bearer where a team is waiting to communicate, that is the difference
between an appliance that works when switched on and one an operator starts
diagnosing.

## Accepted cost

**The protection is now structural rather than automatic, and structure can be
violated by one command.** Bridge loop avoidance would have broken a loop
however it was created, including by a person with `ip link` and good
intentions at two in the morning. This decision replaces that with a rule, a
check that reads configuration, and an expectation of discipline.

The failure mode if the rule is broken is severe and not graceful: a broadcast
storm on a low-rate sub-GHz bearer takes the mesh down rather than slowing it,
and it presents as a radio fault. That is the same diagnostic trap this program
has already spent runs inside.

The program accepts this because the alternative was paying thirty seconds of
dead air on every join, in every deployment, forever, to insure against a
topology the design does not require and the rule above forbids.

**The residual risk creates work rather than being waved away.** A node should
be able to notice that it is in a loop and say so, rather than leaving an
operator to infer it from a dead mesh. `batman-adv` already exposes what is
needed: a client address appearing in the translation table under more than one
originator, or the node's own bridge address arriving from the mesh, are both
loop signatures readable with `batctl`. That detector does not exist and is
named here so it is not forgotten. It belongs with the interface bring-up work
in `docs/ROADMAP-DEV.md`.

## Fallback

Re-enable `bridge_loop_avoidance`. One runtime setting, no structural change,
and the cost is the measured warm-up returning.

The signal to take it is evidence that the rule above cannot be held in
practice: a deployment where the field domain genuinely must be bridged to a
shared segment, or a recorded incident where the rule was broken in the field
and the detector did not catch it in time.

## Superseded by

None.

## Verification dependency

`TBD`.

The structural rule is checked by `tools/validate-docs.sh`, which reads
configuration rather than behaviour, and that is the weaker half. The stronger
half is a loop that is deliberately created and then detected, which needs two
nodes and a shared segment. CONOPS section 78 stage 2 is the first stage with
the topology to do it.
