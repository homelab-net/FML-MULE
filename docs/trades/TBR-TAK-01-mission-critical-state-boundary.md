---
id: TBR-TAK-01
title: Mission-critical state boundary
status: OPEN
owner: TBD
area: TAK
critical-path: true
depends-on: []
feeds: [TBR-HA-01, TBR-SEC-01, TBR-REC-01]
evidence: docs/evidence/TBR-TAK-01/
adr: []
---

# TBR-TAK-01 Mission-critical state boundary

## Question

Which mission state must survive a node loss, a partition, or a rejoin, and
which state may be discarded and regenerated?

## Why it matters

This is on the critical path, and it is the one critical-path trade that can be
worked today by anyone.

Everything in the mission-service plane depends on the answer. If position
reports are transient and regenerable, the service plane needs no durable store
for them and a node that reboots simply catches up. If operator-authored
markers, tasking or annotations must survive, the plane needs durable storage,
a replication story across a partitioned mesh, and a conflict resolution rule
for what happens when two partitions edit the same object and later rejoin.

Downstream, it determines what `TBR-HA-01` must protect during a restart, what
`TBR-SEC-01` must encrypt at rest, and what `TBR-REC-01` must preserve across a
rollback. Getting it wrong in the permissive direction means building a
distributed database nobody needed; getting it wrong in the other means losing
an operator's work during an incident, which is unrecoverable and visible.

## Options

1. **All mission state is transient.** Everything regenerates from live
   participants. Simplest by a wide margin. Right answer if the operational
   concept never depends on an artifact outliving the node that made it.
2. **A narrow durable set.** Operator-authored objects are durable; observed
   and derived state is transient. Right answer if the durable set can be kept
   genuinely small and low-rate.
3. **Full replication of mission state across the mesh.** Right answer only if
   the operational concept demands it, and expensive over a bearer whose
   capacity is `TBD`.
4. **Defer to the upstream service's own behaviour**, accepting whatever it
   does. Recorded because it is the default outcome. The risk is inheriting a
   consistency model nobody examined against a partitioning mesh.

## Closure evidence

Committed under `docs/evidence/TBR-TAK-01/`:

- A written enumeration of every state object the mission-service plane holds,
  classified transient or durable, with the operational justification for each
  classification traced to the CONOPS.
- Documented behaviour of the upstream TAK-compatible service under partition
  and rejoin, cited to its documentation or protocol specification, or
  determined by observation against fakes and recorded as such.
- A partition and rejoin walkthrough for at least three scenarios: single node
  lost and returning, mesh split into two groups then rejoined, and a node
  rejoining after a rollback to an older image.
- Where behaviour was observed rather than read, the fixtures under
  `test/fixtures/` and the procedure used.

## Closure gate

The state enumeration is complete, every object is classified with a stated
justification, and the partition and rejoin behaviour of the durable set is
described including its conflict resolution rule. An ADR records the boundary.

The gate does **not** require the durable mechanism to be implemented, only for
the boundary to be decided and defensible.

## Dependencies

- **Depends on:** none.
- **Feeds:** `TBR-HA-01`, `TBR-SEC-01`, `TBR-REC-01`, and the service catalog.
- **Requires hardware:** **no.** This is a design and analysis trade,
  resolvable against documentation, protocol behaviour, and reasoning about
  partition, running against fakes on an ordinary laptop. It is the highest
  value work available to a contributor who owns no hardware.
