# Two deployments do not meet by default, and that changes the question

**Trade:** `TBR-NET-01`.
**Date:** 2026-08-30.
**Taken by:** Cameron Zobrist, on the lab development machine.
**Status of this artifact:** `SIMULATED`. Four `mac80211_hwsim` radios in
network namespaces. **No radio was involved.**

## Why this exists

The two exercises before it, `2026-08-30-collision-exercise.md` and
`2026-08-30-distinct-prefix-exercise.md`, both put two deployments **on one
802.11s mesh** and asked what the addressing did. Neither said why the two
deployments were on one mesh, and I chose the shared mesh identifier myself
when building the bench.

`mission/schema/mission-package.schema.json` had already answered that, and
says the opposite:

> Network identity for this deployment. **Values here differ between
> deployments so that two independently built deployments meeting at an
> incident do not collide.** See `TBR-NET-01`.

`mesh_id` is a **required** field of that object. So under the architecture as
specified, two independently built deployments carry different mesh
identifiers, and the premise of both earlier exercises is not the default
case. This artifact tests the default case.

## The exercise

Four nodes on channel 1 in one place. Deployment A uses its mission package's
`mesh_id`, deployment B uses its own. **Everything else is made as bad as
possible**: both deployments kept `10.41.0.0/16` and both allocated the same
two host addresses, `.1` and `.5`. If `mesh_id` separates them, even this
cannot collide.

## It cannot collide

```text
A1 802.11s peers : 1   (only A2)      B1 802.11s peers : 1   (only B2)
A1 originators   : 1                  B1 originators   : 1

A1 -> 10.41.0.5  : 0% packet loss     B1 -> 10.41.0.5  : 0% packet loss

A2 bat0 MAC = 46:42:c1:de:f2:a7       B2 bat0 MAC = 42:48:e5:89:ee:69
A1 resolved = 46:42:c1:de:f2:a7       B1 resolved = 42:48:e5:89:ee:69
```

Each deployment sees only its own node, resolves its own `.5`, and passes
traffic without loss. **Identical addressing is harmless**, because the
deployments never share a layer 2 domain for it to be harmful in. The
separation happens at the bearer, below anything the address prefix can affect.

## What this does to the earlier two artifacts

It does not retract them. It supplies the premise they were missing, and the
premise is narrower than they implied.

Both exercises describe **what happens once two deployments are on one mesh**.
Under this architecture that is not what happens when they meet; it is what
happens when they **deliberately converge**, by agreeing a mesh identifier. So
the sequence those artifacts document is real and is reached on purpose:

1. Two groups arrive at an incident. They do not interoperate and do not
   interfere. Nothing is broken and nothing is shared.
2. They decide to work together, and agree one `mesh_id` — the only mechanism
   the architecture offers for that.
3. **At that moment the addressing collision in
   `2026-08-30-collision-exercise.md` begins**: one deployment wins ARP, the
   other sees a `REACHABLE` neighbour it cannot reach, and nothing reports it.

The collision is not what happens when deployments meet. It is what happens
when they succeed in agreeing to cooperate, which is worse, because it fires
at the moment of an operational decision rather than at random.

## The question this raises, which no decision owns

Nothing in the repository decides how two deployments converge. `mesh_id` is
required by the mission package schema and is not the subject of any trade or
ADR: a grep across `docs/trades/` and `docs/adr/` returns nothing that decides
whether it is per-deployment, program-wide, or negotiated at an incident.

That value is upstream of `TBR-NET-01`. Answering the address prefix question
without it decides a consequence before its cause:

- If `mesh_id` always differs, deployments can never interoperate, the trade's
  own stated concern that groups "must be able to interoperate or at least
  coexist" is answered "coexist only, by construction", and the prefix hardly
  matters.
- If deployments can agree a `mesh_id`, they interoperate and the prefix
  matters entirely, in exactly the way the collision exercise shows.

The schema's description points at `TBR-NET-01` for the whole `network` object,
but `TBR-NET-01` asks only "Retain `10.41.0.0/16` or select another field
prefix?". The pointer and the question do not cover the same ground.

## What this does not establish

**Nothing about RF coexistence.** Two meshes on one channel contend for
airtime. `hwsim` has no medium, no carrier sense that means anything, and no
contention, so this says only that the two do not associate. What two
deployments cost each other in throughput on a shared channel is a question for
`TBR-RF-01` and needs radios.

**Nothing about the sub-GHz bearer.** The schema calls `mesh_id` the "mesh
identifier for the sub-GHz bearer", and this ran on 2.4 GHz because that is
what the lab has. Whether the HaLow bearer separates deployments the same way
is untested and needs hardware on the BOM.

**One node per deployment, no services, one bearer.** No access point, no EUD,
no DNS, no TAK server and no Meshtastic. `local_domain` is a second collision
of the same shape and is not touched here: its schema description says a fixed
domain across deployments "makes collision certain", and two converged
deployments would have two nodes authoritative for it.

**Nothing about different software.** Both deployments ran one build, one
kernel and one `batman-adv`. Two real deployments may not, and `batman-adv`
refuses to interoperate across a compatibility version mismatch. That is a
third way a rendezvous can fail and it is untested.
