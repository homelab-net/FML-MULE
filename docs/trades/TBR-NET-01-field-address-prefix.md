---
id: TBR-NET-01
title: Field address prefix
status: OPEN
owner: Cameron Zobrist
area: NET
priority: 15
function-owner: Network
critical-path: false
depends-on: [TBR-NET-03]
feeds: []
requires-hardware: no
evidence: docs/evidence/TBR-NET-01/
adr: [FML-ADR-063, FML-ADR-061, FML-ADR-060, FML-ADR-024, FML-ADR-031]
target-date: TBD-SRR
---

# TBR-NET-01 Field address prefix

**Source:** SAD v0.31 section 4.2, and the TBR register in SAD section
30.2 (priority 15 of 16).

**Function owner:** Network. **Named owner:** `TBD-SRR`.

SAD section 30.2 records an SRR exit action: the Program Owner assigns one named
individual and one calendar target date to every open TBR. The named individual
is assigned as of 2026-08-31. **The target date is not**, and `TBD-SRR` still
marks that half of the action rather than hiding it behind an invented date.

## Question

Retain 10.41.0.0/16 or select another field prefix?

## Decision status

**`FML-ADR-063`, `SELECTED`, 2026-08-31.** The field prefix is per-deployment;
`10.41.0.0/16` is not retained as a program-wide constant; the prefix is
generated rather than derived from identity; and **a node never carries an
overlapping uplink silently.**

**This trade is ready to close** on the named owner's acceptance. Its three
closure-evidence items exist, a decision is entered in the ADR register, and SAD
section 30.2 makes acceptance the remaining step. It is not marked `CLOSED`
here, because acceptance is the owner's act and not the author's.

**What the decision does not solve, stated in the ADR:** venue overlap cannot be
solved inside IPv4, and what a node does beyond reporting an overlap is
service-plane policy left to `TBR-TAK-01` and `services/`.

## Why it matters

SAD section 4.2 retains the upstream OpenMANET `10.41.0.0/16` field prefix as the
preferred initial choice, because it does not conflict with the parent Homelab
`10.77.0.0/16` home prefix or the `10.78.0.0/16` rack prefix, reduces divergence
from upstream, and already includes a per-node lease-allocation model.

The open question is collision risk with **expected external networks**. Two
volunteer groups that built nodes independently from this repository, arriving
at the same incident, must be able to interoperate or at least coexist.

The scenario is not hypothetical for a repository published for other makers to
build from: the more successful this program is, the more likely two
independently built deployments meet.

**They do not meet by default, and that is now measured.**
`mission/schema/mission-package.schema.json` makes `mesh_id` required and says
network identity values differ between deployments. With different `mesh_id`
two deployments do not associate at all: identical prefixes and identical host
addresses are harmless, because there is no shared layer 2 domain for them to
be harmful in. See `docs/evidence/TBR-NET-01/2026-08-30-mesh-id-separates-deployments.md`.

So the collision this trade exists for is reachable only once two deployments
**deliberately converge** on one mesh identifier. Whether and how they can do
that is `TBR-NET-03`, which this trade now depends on. Answering the prefix
question first would settle a consequence before establishing that its cause
can occur.

**`TBR-NET-03` also constrains the answer here, not just the sequence.** Every
convergence mechanism it considers fails while two deployments can hold the
same prefix: merging deployments into one layer 2 domain reproduces the
collision, and a routing liaison cannot route between two interfaces in the
same subnet at all. So selecting any mechanism there **removes the fixed-prefix
option here**. Deferral -- deciding MULE v1 supports no interoperation between
deployments -- is the only branch that leaves this trade free to retain
`10.41.0.0/16`.

**`FML-ADR-061` has now made that choice, conditionally on this trade.** It
supersedes `FML-ADR-060`; do not read that one as current. Cross-organization
interoperation is a routed liaison on a separate keyed mesh, and a liaison
cannot be built while two deployments can hold the same prefix. So the
fixed-prefix option is removed here **if** that condition is met, and it is a
condition precisely because this trade has not decided yet. The two are
resolved together or not at all.

**And `FML-ADR-061` raises the stakes here.** MULEs of one deployment now merge
automatically on a shared credential, which makes an addressing collision the
normal condition wherever two credential holders meet rather than an
exceptional one.

**And deferral would not close this trade.** The remaining closure item is the
collision analysis against expected external networks: a venue LAN, the parent
Homelab `10.77.0.0/16` and `10.78.0.0/16`, ranges partner organizations use.
None of that is gated by `mesh_id`, so no answer in `TBR-NET-03` removes it.

## Options

Retain `10.41.0.0/16`, or select another prefix.

**Amended 2026-08-31, twice. First:** the two options above are both IPv4 and a
third existed.
RFC 4193 Unique Local Addresses exist precisely so independently administered
networks that were never coordinated do not collide: a random 40-bit global ID
makes deployment-against-deployment collision about 2^-40 rather than certain,
and a venue handing out IPv4 **cannot claim an `fd00::/8` destination at all**,
so the route-stealing failure measured under this trade does not arise.

SAD section 4.4 gates IPv6 behind controlled change and its only stated reason
is that the parent Homelab disables managed IPv6 -- a parent-baseline
constraint, not a judgement about the field mesh. `docs/change-requests/`
carries the `PBCR-###` mechanism for exactly that, and its README states such
requests "do not block MULE work".

**Then: the Program Owner excluded IPv6 for MULE v1**, on 2026-08-31, for
**broader hardware support and older systems in the mesh.** CONOPS plans four to
eight volunteer-owned EUDs per MULE and the program does not choose what a
volunteer brings; an EUD whose stack does not do IPv6 well does not work at all.
`FML-ADR-038` already treats EUD client compatibility as an operational burden.

**So this trade is decided inside IPv4**, and the option space is now the two
originally stated. See
`docs/evidence/TBR-NET-01/2026-08-31-the-option-the-trade-does-not-list.md`,
which is retained with its disposition because the reasoning behind an exclusion
is worth as much as the reasoning behind a selection.

**What that leaves unsolved, and the decision must address rather than prevent:**
the venue-overlap failure has no clean answer inside IPv4. Policy routing moves
the loss and a VRF requires every mesh-using application to bind into it.

Ancillary questions that belong here: exact reservations and node ranges, which
become ICD-controlled values; how an EUD on the access point is addressed
relative to the mesh; and what DNS names exist in `services/ingress/`.

CONOPS section 5.4 and SAD section 4.4 fix the address family: **MULE v1 is
IPv4-first** and does not introduce a separate managed IPv6 architecture during
initial qualification, because the parent Homelab currently disables managed
IPv6. IPv6 may be reintroduced only through controlled parent and subsystem
change.

## Closure evidence

SAD section 30.2: collision analysis, plus an interoperability exercise.

The collision analysis covers expected external networks a deployment may meet:
incident command networks, partner organizations, and other MULE deployments
built independently from this repository.

The interoperability exercise demonstrates what actually happens when two
independently configured deployments form a mesh: whether they interoperate,
coexist or conflict, and what an operator sees.

Confirmation that the scheme is expressible in the mission configuration package
schema and validated by `mission/schema/`.

Evidence is committed under `docs/evidence/TBR-NET-01/`.

## Closure gate

The prefix decision is recorded with its collision analysis, two independently
configured deployments are demonstrated not to collide, and the mission package
schema validates a deployment's addressing configuration.

Exact reservations and node ranges pass to the ICD.

**Closure gate per SAD section 30.2:** Before ICD baseline / Stages 2, 11.

No TBR closes on document wording alone. It closes only when its listed evidence
exists, the named owner accepts the evidence, and the resulting architecture
decision is entered into the persistent ADR register.

## Dependencies

- **Depends on:** none
- **Feeds:** none
- **Related decisions:** `FML-ADR-024`, `FML-ADR-031`
- **Validating stage:** Stage 2 (CONOPS section 78)
- **Requires hardware:** **No.** The scheme can be analysed and the collision
  case exercised with virtual
interfaces on an ordinary machine. The interoperability exercise benefits from
real nodes but does not require them.
