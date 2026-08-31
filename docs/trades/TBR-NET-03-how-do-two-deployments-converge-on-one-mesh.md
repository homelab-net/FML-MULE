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
adr: [FML-ADR-061, FML-ADR-062, FML-ADR-060, FML-ADR-053, FML-ADR-045]
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

**A liaison node that ROUTES between deployments.** Neither deployment changes
its own mesh. One node on each side takes an additional bearer, both join a
third incident-scoped mesh, and each liaison **routes** between that mesh and
its own. Only one node per deployment is reconfigured.

**The word "routes" is the whole option, and getting it wrong reverses the
result.** `FML-ADR-045` describes a node carrying several bearers into **one**
`batman-adv` interface, which is what `test/bench/80211s-mesh.sh` builds in its
line topology. A liaison that does that is a **bridge**: the two deployments
become one layer 2 domain and
`docs/evidence/TBR-NET-01/2026-08-30-collision-exercise.md` applies in full. The
value here comes from the liaison holding the two meshes in **separate** layer 2
domains and forwarding at layer 3 between them, so no ARP resolution ever
crosses a deployment boundary and the collision is structurally impossible
rather than avoided by agreement.

It would be the right answer if partial cooperation is what is wanted -- a
liaison from each side rather than two whole deployments merging -- and if the
trust boundary below is acceptable.

It costs a bearer or a radio on one node per deployment, and `TBR-RF-03` is
where that cost lands. **It also creates a trust boundary and a single point of
failure**: the liaison carries traffic between two organizations that have not
authenticated each other, and nothing in this program says who authorises one or
what the liaison is permitted to forward. That is a smaller exposure than a
layer 2 merge, where every node reaches every node rather than one, but it is
not nothing and `THREAT_MODEL.md` has to be asked about it.

**Deferring.** Deciding that MULE v1 does not support interoperation between
deployments, and saying so. It would be the right answer if the evidence shows
the operational case is rare and the cost of any mechanism is high. It is a
real option and it must be written down as a decision rather than left as an
absence, because the current absence reads as an oversight and the schema's
own description implies the question was considered.

### Every option but deferral forces `TBR-NET-01`'s answer

Not one of the three mechanisms works while two deployments can hold the same
address prefix, and each fails for its own reason:

- A fixed program-wide `mesh_id` puts both deployments in one layer 2 domain,
  which is the collision exercise exactly.
- A convergence procedure produces the same domain deliberately, so it needs
  the collision solved before the procedure is usable at all.
- A routing liaison needs an interface in each deployment. **Two interfaces in
  the same subnet cannot be routed between**, so identical prefixes defeat it
  before any policy question arises. It fails loudly rather than silently,
  which is better, but it fails.

**One counterexample, found after this was written.** IPv6 link-local
addressing needs no prefix agreement and cannot collide: an unconfigured
`batman-adv` interface is assigned an `fe80::` address derived from its MAC, and
two nodes that have never met reach each other immediately. It is on-link only,
so it does nothing for the routing liaison, and whether any service in this
program can use it is untested. See
`docs/evidence/TBR-NET-03/2026-08-30-what-happens-with-no-configuration.md`. The
paragraph below holds for routed IPv4, which is what every mechanism here
assumes, and does not hold universally.

So selecting any mechanism that routes or shares IPv4 **forces `address_prefix`
to be per-deployment**,
which is one of the things `TBR-NET-01` is open to decide and which its schema
field records as undecided: "whether the prefix is fixed or per-deployment ...
[is] open".

**The dependency therefore runs both ways, and the frontmatter shows only one
of them.** `TBR-NET-01` cannot be decided before this trade, because whether
the collision is reachable depends on whether deployments can converge. And
this trade's answer constrains `TBR-NET-01`'s, because every answer except
deferral removes the fixed-prefix option. Deferral is the only branch that
leaves `TBR-NET-01` free.

**Deferral does not close `TBR-NET-01` either, and it should not be sold as
doing so.** That trade's remaining evidence item is a collision analysis
against expected external networks -- a venue LAN, the parent Homelab
`10.77.0.0/16` and `10.78.0.0/16`, ranges partner organizations use. None of
that is gated by `mesh_id`. Deferring removes the deployment-to-deployment
collision path and leaves the external one untouched.

### The LoRa bearer is not covered, by this trade or by anything else

The mission package's `network` object contains `mesh_id`, `local_domain`,
`address_prefix` and `ap_ssid`, and **no LoRa field**. Nothing in the repository
specifies a Meshtastic channel name or pre-shared key. `regions/` carries RF
parameters, which are regulatory and not a logical identity: two deployments on
one frequency are neither separated nor joined by that fact.

**And the LoRa bearer behaves in the opposite direction, read from the firmware
source.** `src/mesh/Channels.h` describes its compiled-in key as "our _public_
default channel that all devices power up on", `initDefaultChannel` sets a
one-byte key of value 1 and an empty channel name, and `getKey` expands that to
the constant unchanged. Two stock nodes in one region on one preset therefore
share a name, a key and a channel hash. See
`docs/evidence/TBR-NET-03/2026-08-30-what-happens-with-no-configuration.md`.

So a MULE node is **separated from another deployment on 802.11s and joined to
it on LoRa, at the same time**, and neither state was chosen. Whatever mechanism
this trade selects for the mesh bearer, the LoRa bearer needs the opposite kind
of answer: not how to converge, but whether and how to separate. That may need a
trade of its own. It is recorded here so that selecting a mechanism for one
bearer is not mistaken for answering the question, and because the default key
being a published constant is a `THREAT_MODEL.md` matter that nothing in this
program currently records.

## Decision status

**The live decision is `FML-ADR-061`, dated 2026-08-31, status `SELECTED`.** It
supersedes `FML-ADR-060` of the same day, which is retained as `SUPERSEDED` and
should not be read as current.

The mesh is keyed with `key_mgmt=SAE`; an open field mesh is prohibited; MULEs
of one deployment share one credential and merge automatically; and
cross-organization interoperation is a **separate keyed mesh** on a liaison
node, routed and never bridged, rather than a shared deployment credential.
MULE v1 ships no cross-organization mechanism.

**Why `FML-ADR-060` did not survive a day.** It prohibited merging outright,
arguing that merging bypasses admission control. That is true of an **open**
mesh and false of a keyed one, and mesh security was
`key_mgmt=TBD` at the time, so it decided a consequence of an undecided
question. Measured afterwards: a node without the credential never reaches
`ESTAB` and gets 100% packet loss. `FML-ADR-061` keeps `FML-ADR-060`'s routing
requirements in full and changes only who may merge.

**This trade does not close on it yet.** Its own closure gate says a selected
mechanism is not accepted while `TBR-NET-01` remains open, and `FML-ADR-061`'s
liaison half stays conditional on that trade selecting per-deployment prefixes.
One closure item also remains unsupplied: what a liaison may forward and who
authorises one.

All four evidence items and their state:

| Item | State |
| --- | --- |
| Convergence trace, or a finding that no mechanism is provided | `2026-08-30-liaison-routing-exercise.md` |
| What an operator does | `2026-08-31-what-it-discloses-and-what-an-operator-does.md`. The typed procedure **fails** this trade's own test and is only acceptable declared. |
| `THREAT_MODEL.md` assessment | Same artifact. Merging meshes is an admission decision taken by radio configuration, bypassing admission control. |
| Interaction with `TBR-NET-01` stated explicitly | This file, and the condition `FML-ADR-061` carries forward. |
| **What a liaison may forward, and who authorises one** | **Not supplied.** |

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

**If the selected mechanism is a liaison, a statement of what it is permitted
to forward and who authorises one.** A node routing between two organizations
that have not authenticated each other is a trust boundary, and an unstated
boundary is one nobody is enforcing.

**The interaction with `TBR-NET-01` stated explicitly**, since converging is the
event that makes the addressing collision reachable, and since every mechanism
forces that trade to a per-deployment prefix.

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
