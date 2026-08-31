---
id: FML-ADR-063
title: The field prefix is per-deployment and an overlapping uplink is never silent
status: SELECTED
date: 2026-08-31
supersedes: none
superseded-by: none
trades: [TBR-NET-01, TBR-NET-03, TBR-NET-02]
verification: Stage 2
---

# FML-ADR-063 The field prefix is per-deployment and an overlapping uplink is never silent

**Source of rationale:** `TBR-NET-01`, and the five evidence artifacts under
`docs/evidence/TBR-NET-01/`.

## Context

SAD section 4.2 prefers retaining the upstream OpenMANET `10.41.0.0/16` field
prefix, and `TBR-NET-01` asks whether that creates unacceptable collision risk.
Five artifacts answer it, and the answer is worse than "some risk":

- **Two deployments sharing a prefix conflict silently.** One wins ARP, the
  other sees a `REACHABLE` neighbour and loses everything it sends, with no
  kernel message and nothing in `batctl`.
- **`FML-ADR-061` makes that the normal case.** MULEs of one deployment share a
  credential and merge automatically, so wherever two credential holders meet
  the collision is reached by default rather than by accident.
- **Any external route more specific than the mesh prefix takes that slice of
  the mesh away**, and the rest keeps working, which is harder to diagnose than
  total failure.
- **No routing mechanism fixes that.** Policy routing moves the loss; a VRF
  separates the two networks only per application, and no application sees both.
- **IPv6 was excluded** on 2026-08-31 for broader hardware support and older
  systems in the mesh, closing the option space inside IPv4.

Every one of those failures is silent, and every one presents to an operator as
a radio fault.

## Decision

**The field prefix is per-deployment. `10.41.0.0/16` is not retained as a
program-wide constant.**

It is carried in the mission package as `network.address_prefix`, which already
exists as a field and whose description records the question this ADR answers.

**The prefix shall be generated, not derived from node or deployment identity.**
`THREAT_MODEL.md` records that an address derived from a durable node identifier
is itself a durable identifier visible to any observer. A generated prefix
carries no identity.

**A node shall never carry an uplink whose address range overlaps its mesh
prefix without reporting it.** Detection is the requirement; silence is what is
prohibited.

**What a node does beyond reporting is not decided here.** Refusing the lease
costs the WAN overlay `FML-ADR-039` puts on MULE infrastructure; accepting it
costs part of the mesh. Which is right depends on whether the uplink is
load-bearing for the mission in progress, which is service-plane policy and
belongs with `TBR-TAK-01` and `services/`.

## Status

`SELECTED`.

**Not conditional.** `FML-ADR-061`'s liaison half was conditional on this trade
selecting per-deployment prefixes. It does, so that condition is met and
`FML-ADR-061`'s routed liaison becomes buildable.

## Consequences

`FML-ADR-061`'s cross-organization liaison can be built. Two interfaces in one
subnet cannot be routed between, and per-deployment prefixes remove that
obstacle.

**Deployment-against-deployment collision stops being certain.** It does not
become impossible, and this ADR does not claim otherwise.

**Venue overlap is not solved and cannot be, inside IPv4.** A venue chooses the
range it hands out. What changes is that the node says so.

`mission/schema/mission-package.schema.json` needs `network.address_prefix`
tightened from a bare `string` whose description says everything is open. That
is a schema change this ADR requires and does not itself make.

`TBR-NET-02`'s one-byte EUD index is unaffected by this ADR and remains
undecided; its own collision problem is on the LoRa bearer, which has no
per-deployment boundary at all.

## Accepted cost

**Divergence from upstream OpenMANET**, which SAD section 4.2 lists as a reason
to retain the fixed prefix. Accepted: the reason to diverge is a measured
failure and the reason to converge is familiarity.

**No collision-free guarantee.** A generated prefix inside `10.0.0.0/8` reduces
collision; it does not eliminate it. The scheme that would have -- RFC 4193 --
was excluded for hardware reasons this ADR does not reopen.

**A detection requirement with no implementation.** Nothing in `mule/` performs
this check today. Stating the requirement without building it is deliberate:
`FML-ADR-052` governs what a `mule/` decision function may do, and the check
belongs behind a reading interface with a fake rather than being written into an
ADR as though it existed.

**The generation mechanism is unspecified.** How a builder produces a prefix,
and where the randomness comes from, is not decided here. Naming a mechanism
without evidence is what `FML-ADR-060` was superseded for.

## Fallback

If per-deployment prefixes prove unworkable -- most plausibly because the
mission package tooling cannot produce them, or because operators cannot manage
distinct prefixes across a fleet -- the fallback is the measured status quo:
retain `10.41.0.0/16` and accept that any two deployments that meet conflict
silently. That is a worse position and is recorded so nobody arrives at it by
drift.

## Superseded by

None.

## Verification dependency

Stage 2 and Stage 11. `test/bench/route-isolation.sh` reproduces the failure this
ADR responds to; nothing yet verifies the detection requirement, because nothing
implements it.
