---
id: TBR-NET-03
title: How do two deployments converge on one mesh
status: OPEN
owner: Cameron Zobrist
area: NET
priority: 99
function-owner: Network
critical-path: false
depends-on: []
feeds: [TBR-NET-01]
requires-hardware: no
evidence: docs/evidence/TBR-NET-03/
adr: [FML-ADR-053, FML-ADR-045]
target-date: TBD-SRR
---

# TBR-NET-03 How do two deployments converge on one mesh

## Question

When two independently built deployments decide at an incident to work
together, by what mechanism do they come to share one mesh?

## Why it matters

`mission/schema/mission-package.schema.json` describes the `network` object as
holding values that "differ between deployments so that two independently built
deployments meeting at an incident do not collide", and makes `mesh_id`
required. That is a deliberate separation and it works: with different
`mesh_id`, two deployments on one channel in one place do not associate, and
identical address prefixes with identical host addresses are harmless. Measured
in `docs/evidence/TBR-NET-01/2026-08-30-mesh-id-separates-deployments.md`.

**Separation by default is the right starting point and it is only half an
answer.** CONOPS describes volunteer groups responding to the same incident.
`TBR-NET-01` states the requirement they impose on each other: two groups that
built nodes independently "must be able to interoperate or at least coexist".
Coexistence is now established. Interoperation has no mechanism at all.

Nothing in this repository says how a deployment changes its `mesh_id`, who
decides the new value, whether both sides adopt one side's value or a third,
what happens to nodes that do not get the message, or whether the change is
reversible. A field decision to cooperate currently has no defined procedure
behind it.

**The consequence of converging is already documented and it is bad.** The
moment two deployments share a `mesh_id`, they share a layer 2 domain, and
`docs/evidence/TBR-NET-01/2026-08-30-collision-exercise.md` shows what happens
if they also share an address prefix: one deployment wins ARP, the other sees a
`REACHABLE` neighbour it cannot reach and loses everything it sends, and no
kernel message or `batctl` table reports it. That fires at the moment of an
operational decision rather than at random, which is the worst time for it.

**This is upstream of `TBR-NET-01`.** Answering the address prefix question
without this one settles a consequence before its cause. If deployments can
never converge, the prefix hardly matters, because nothing that differs between
deployments can ever meet. If they can, the prefix matters entirely and in
exactly the way the collision exercise shows.

## Options

**A fixed program-wide `mesh_id`.** Every deployment built from this repository
uses one value, so any two nodes that meet are already on one mesh.
Interoperation is automatic and needs no procedure. It would be the right
answer if interoperation at an incident is common and the addressing can be
made collision-free by construction. It makes the collision case the normal
case rather than the exceptional one, and it makes the mesh identifier a
constant that anyone who has seen the repository knows, which
`THREAT_MODEL.md` should be asked about.

**Per-deployment `mesh_id` with a defined convergence procedure.** The default
stays as the schema describes, and a procedure exists for adopting a shared
value deliberately. It would be the right answer if convergence is an
occasional, decided act rather than a normal condition. It needs the procedure
written, the value agreed out of band, and the addressing collision solved
before the procedure can be used, so it depends on `TBR-NET-01`'s answer rather
than merely feeding it.

**A third, incident-scoped mesh both sides join.** Neither deployment changes
its own mesh; nodes that need to cooperate join an additional mesh, which
`FML-ADR-045` already permits by having a node carry several bearers into one
`batman-adv` interface. It would be the right answer if partial cooperation is
what is actually wanted: a liaison node from each side rather than two whole
deployments merging. It costs a bearer or a radio, and `TBR-RF-03` is where
that cost lands.

**Deferring.** Deciding that MULE v1 does not support interoperation between
deployments, and saying so. It would be the right answer if the evidence shows
the operational case is rare and the cost of any mechanism is high. It is a
real option and it must be written down as a decision rather than left as an
absence, because the current absence reads as an oversight and the schema's
own description implies the question was considered.

## Closure evidence

**A convergence trace, or a written finding that no mechanism will be
provided.** If a mechanism is selected, an exercise on virtual interfaces
showing two separated deployments adopting a shared mesh and the resulting
state: how long the change takes per node, what happens to traffic in flight,
what happens to a node that does not receive the change, and whether the
deployments can separate again afterwards. Recorded with the number of nodes,
the sequence performed, and the observed state at each step.

**A statement of what an operator does**, in the words an operator would use,
for whichever option is selected. If the procedure cannot be written in a form
a volunteer can follow under stress without a laptop, that is a finding about
the option and belongs in the evidence.

**A `THREAT_MODEL.md` assessment of the selected mechanism.** A mesh identifier
is transmitted in the clear in 802.11s beacons. A fixed program-wide value is a
published constant identifying a MULE deployment; a per-incident value agreed
over voice is something an adversary can hear. Both are disclosure and the
options differ in what they disclose.

**The interaction with `TBR-NET-01` stated explicitly**, since converging is
the event that makes the addressing collision reachable.

No hardware is required for any of it. The separation result was obtained with
`mac80211_hwsim` and the convergence exercise can be too, at tier `SIMULATED`.

## Closure gate

The Program Owner accepts a written decision that names one mechanism, or names
none deliberately, and that answers all four evidence items above.

**This gate is a comparison, not a threshold.** What is compared is what an
operator has to do, and what an adversary learns, under each option, against
the deferral option of providing nothing. There is no measured quantity that
decides this, and inventing a numeric threshold would be inventing a
specification.

A selected mechanism is not accepted while `TBR-NET-01` remains open, because a
procedure that reliably produces the collision in
`2026-08-30-collision-exercise.md` is not a procedure anybody should follow.

## Dependencies

- **Depends on:** none. The question can be analysed today.
- **Feeds:** `TBR-NET-01`. The address prefix answer depends on whether two
  deployments can ever share a layer 2 domain.
- **Related decisions:** `FML-ADR-053` selects the mesh routing protocol and
  `FML-ADR-045` describes a node carrying several bearers into one mesh
  interface, which the third option relies on. No ADR currently decides
  `mesh_id` itself, which is why this trade exists.
- **Validating stage:** `TBD`.
- **Requires hardware:** `no`.

## Frontmatter notes

`priority` is 99 because this trade postdates the SAD section 30.2 register and
therefore has no position in it. `critical-path` is `false` on the same
grounds: the SAD marks the critical path and does not know about this trade.
Neither should be read as a judgement that the question is unimportant. It
feeds `TBR-NET-01`, which the SAD does place at priority 15 of 16.

`owner` is a named individual rather than `TBD-SRR` because this trade was
raised inside the repository by the person who owns it, and recording
`TBD-SRR` would claim an SRR gap that does not exist here.
