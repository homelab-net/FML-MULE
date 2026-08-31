# Mission-critical state classification, analysis half

**Trade:** `TBR-TAK-01`, mission-critical state boundary.
**Date:** 2026-08-27.
**Produced by:** analysis against controlling documents. No hardware, no
running service, no measurement.
**Status of this artifact:** `UNVERIFIED`. It is reasoning, not a result.

## What this is, and what it is not

`TBR-TAK-01`'s closure gate has two halves. This is the first:

> Enumerate every state object the mission-service plane holds against the ten
> categories in SAD section 14.1, classify each into a CONOPS section 26 class
> with a stated justification, and describe partition and rejoin behaviour for
> the durable set including its conflict resolution rule.

**It does not close the trade**, for three reasons, each of which is a rule
this program wrote down in advance:

1. The second half of the listed evidence is empirical: a different-node
   restore, plus DataSync, mission-package, certificate and map-cache tests.
   None has been performed.
2. SAD section 14.2: **database support claimed by an ORM is not sufficient
   acceptance evidence.** By the same standard, a classification derived from
   documentation is not evidence about where an implementation actually puts
   things. This document says what each category *is*; only a running instance
   says where it *lives*.
3. The trade's named owner is `TBD-SRR`. A trade closes when its evidence
   exists **and a named owner accepts it**. No name exists to do that.
   **Superseded 2026-08-31: every trade now names an owner.** This reason no
   longer holds; reasons 1 and 2 do.

This artifact deliberately names **no OpenTAKServer table, schema, endpoint or
file path.** Writing one from memory would be inventing a specification, and it
would be the most plausible-looking kind: specific, confident, and unsourced.

## Method

Each of the ten categories in SAD section 14.1 is placed into one of the three
CONOPS section 26 classes. Where a category does not fit one class, that is
recorded as a finding rather than resolved by choosing the nearest.

The classes, from CONOPS section 26:

| Class | Defining property |
| --- | --- |
| Common trust and configuration (26.1) | Shall be **consistent** across all eligible service hosts. |
| Mission-critical persistent state (26.2) | Shall **survive failover** before a replacement service is fully authoritative. |
| Reconstructable or ephemeral (26.3) | **May be rebuilt** from reconnecting clients or new network activity. |

The test applied throughout is CONOPS section 26.3's own: *can this be rebuilt
from reconnecting clients or new network activity?* If yes, it is ephemeral. If
no, the next question is whether it must merely survive (26.2) or must also be
identical everywhere (26.1).

## Classification

| SAD 14.1 category | Class | Justification |
| --- | --- | --- |
| Relational database state | **Spans all three** | Not a class of state. A container holding items from every class. See finding 1. |
| DataSync and Mission API state | 26.2 | CONOPS 26.2 names "selected DataSync content" explicitly. "Selected" is load-bearing: the boundary is a TRD deliverable, per CONOPS 26.2. |
| Mission packages and uploaded files | 26.2 | Cannot be rebuilt from reconnecting clients. A team that loses an overlay loses work product, not a cache. |
| Certificate enrollment, issuance, authorization | **26.1 and 26.2** | Trust anchors, issued-identity validity and revocation are 26.1: "certificate trust" is an explicit 26.1 example, and inconsistency here is a security boundary failure. Enrollment-authorization records are 26.2. See finding 2. |
| Group and channel configuration | 26.1 | "Role definitions" and "shared service configuration" are explicit 26.1 examples. Two hosts disagreeing about who may see a channel is a disclosure fault, not a convenience fault. |
| Server configuration | 26.1 | Same. Configuration divergence between eligible hosts makes "which host is authoritative" unanswerable. |
| RabbitMQ and transient messaging | 26.3 | Transient by construction; rebuilt as clients reconnect. Conditional on finding 3. |
| Reconstructable PLI, presence, session | 26.3 | Named verbatim in CONOPS 26.3. Position reports are replaced by the next report. |
| Local map, tile and cache state | **26.3 by default, 26.2 where it is the only copy** | The SAD's own qualifier, "whose loss would be operationally visible after failover", is the classification. See finding 4. |
| Immutable mission-package state | 26.1 | Part of the approved mission configuration, a 26.1 example. Immutability makes it the only category that cannot conflict. |

**The durable set** is everything classified 26.1 or 26.2: DataSync and mission
API content within the TRD boundary, mission packages and uploaded files, the
whole of the certificate and trust category, group and channel configuration,
server configuration, immutable mission-package state, and any map or cache
content that is the only copy.

## Findings

### 1. Relational database state is not a class and must be decomposed

It is the largest of the ten categories and the only one that cannot be
classified as a unit. It holds 26.1, 26.2 and 26.3 items simultaneously, and
which rows fall where is a property of the implementation rather than of the
architecture.

This is the single strongest reason the empirical half is mandatory rather than
desirable. No amount of further reading resolves it.

### 2. Losing revocation state fails open

Certificate enrollment splits across two classes, and the 26.1 half carries a
specific hazard: a failover that loses or lags revocation state produces a
replacement service that **accepts an identity the program has revoked**.

This is the same shape as `FML-ADR-042`, which forbids trust validation failing
open on invalid time. A revocation set that silently reverts is a trust
validation failing open on stale state. Recommend the same posture: a
replacement host that cannot demonstrate current revocation data refuses to
validate rather than validating against what it has.

That posture is a proposal, not a decision. It belongs to `TBR-HA-01` and the
security architecture; recorded here because this analysis is where the hazard
becomes visible.

### 3. A durable queue holding the only copy of a mission-critical item

Messaging state is 26.3 **if** it is genuinely transient. If any durable queue
holds the sole copy of an item in flight at the moment of failover, that item is
26.2 and the queue is part of the durable set.

Confirmable only against a running instance. Recorded so the empirical half
looks for it, because the natural assumption is that a message broker is
ephemeral and the natural assumption is what this trade exists to test.

### 4. Cache is not ephemeral in a disconnected deployment

The ordinary reason cached tiles are ephemeral is that they can be re-fetched.
A MULE deployment is defined by the WAN being absent, so the upstream that would
serve a re-fetch is exactly what is unavailable when the cache is needed.

The distinguishing test is therefore not "is this a cache" but **"will the
source be reachable at failover time?"** Where it will not, the cache is the
only copy and belongs in the durable set. This inverts the intuitive answer and
is the kind of inversion that gets discovered in the field otherwise.

### 5. Database high availability alone cannot protect the durable set

`FML-ADR-034` makes PostgreSQL preferred **conditional on** Stage 5 showing
that mission-critical state requiring authoritative continuity is stored in the
SQL backend.

This classification puts at least two members of the durable set outside any
plausible SQL backend: mission packages and uploaded files, and map or cache
content that is the only copy. Both are filesystem-shaped.

If that holds empirically, then a database HA mechanism is **necessary and not
sufficient**, and `TBR-HA-01` is selecting a mechanism for a subset of the
problem. The program would need a second continuity mechanism for
filesystem-shaped state, or an explicit decision that such state is not
protected and the operator is told so.

This is the most consequential finding here and the one most likely to change
the shape of `TBR-HA-01`. It is stated as a conditional because the empirical
half has not run.

## Partition and rejoin behaviour of the durable set

### Common trust and configuration (26.1)

**Not writable during a partition.** Trust anchors, revocation, roles, channel
and server configuration change through the mission package supply path, which
is administrative and deliberately out of band. A partitioned host has no
authority to alter them.

On rejoin, divergence in 26.1 is **a fault to report, not a difference to
merge**. The mission package version is the authority. A host whose 26.1 state
does not match the current package is not eligible to be authoritative, and says
so.

### Mission-critical persistent state (26.2)

This is where conflict is real: two partitions can both accept edits.

**Proposed conflict resolution rule.** The partition that held authority
retains it. On rejoin:

1. The authoritative side's 26.2 state is the surviving state.
2. The non-authoritative side's divergent writes are **retained and surfaced**,
   never silently discarded and never automatically merged.
3. The operator is told the state is not fully authoritative, using the SAD
   section 22 reason codes: `PARTITION` while split, `STATE_LAG` where a
   replacement is behind, `NO_SAFE_AUTHORITY` where neither side may claim it.

This satisfies CONOPS section 14.3's requirement that recovered state be
explicitly marked authoritative, degraded, partial, non-authoritative or
unknown.

### Why not last-writer-wins

**Timestamp-based conflict resolution is unavailable to this program.**

`FML-ADR-042` permits a node to run with `TIME_DEGRADED`: an RTC whose backup
cell has failed, or a node that never established credible time. Under
last-writer-wins, the node with the **least** trustworthy clock wins every
conflict, and wins it silently. A node whose clock reads far in the future would
overwrite correct mission state from a healthy node, and nothing in the
resolution would notice.

This constrains `TBR-HA-01` before it starts: any mechanism it selects must
establish authority by something other than comparing wall-clock timestamps
across hosts. Lease, quorum and witness approaches remain available; naive
last-write-wins does not.

### Why not automatic merge

Merging requires understanding what mission state means. A mission package,
a tasking and a DataSync item have no general merge semantics, and a merge that
guesses produces a plausible mission picture that no participant authored. The
program's stated posture on non-authoritative data is to mark it, not to
reconcile it.

## What must be confirmed against a running instance

Everything in this section is outstanding. It needs a laptop and a container,
not MULE hardware, and it is the remaining half of `ITEP-C01` item 1.

1. ~~**Decompose the relational database state.**~~ **Done 2026-08-31.** All
   41 tables classified; see
   `2026-08-31-relational-state-decomposed-into-conops-classes.md` and the
   correction in `2026-08-31-opentakserver-actually-run.md`.
2. ~~**Locate every durable-set member.**~~ **Done 2026-08-31.** Three
   locations outside SQL: `config.yml`, `ca/` and `uploads/`. See
   `2026-08-31-durable-state-outside-the-database.md`, confirmed by the restore.
3. ~~**Inspect durable queues** for sole-copy mission-critical items.~~
   **Closed 2026-08-31: no durable queue exists.** One non-durable queue,
   `cot_parser`, and the durable exchanges have nothing bound to them. See
   `2026-08-31-no-durable-queue-holds-anything.md`.
4. ~~**Different-node restore.**~~ **Done 2026-08-31.** Every row survived and
   nothing was usable: authentication fails because the salt is not in the
   database, and the replacement silently generated a different certificate
   authority. It reported healthy throughout. See
   `2026-08-31-different-node-restore.md`.
5. **The four workflow tests** named in the trade: DataSync, mission package,
   certificate, map cache.
6. **Confirm the cache question empirically**: what a client observes after
   failover when the tile source is unreachable. Finding 4.

## What this changes if accepted

`TBR-HA-01` gains two constraints and one open question before it begins:

- No timestamp-comparison authority mechanism.
- A replacement host that cannot demonstrate current revocation refuses to
  validate.
- Whether a second, filesystem-shaped continuity mechanism is required, or
  whether the program accepts unprotected state and tells the operator.
  **Answered 2026-08-31: it is required.** `config.yml` holds
  `SECURITY_PASSWORD_SALT`, without which every stored password hash is
  unverifiable, and the certificate authority is a directory. Neither is in the
  database. See `2026-08-31-durable-state-outside-the-database.md`.

`FML-ADR-034`'s condition is testable rather than assumed, and finding 5
suggests it may not hold in the form the ADR anticipates.

## Provenance

Derived from: CONOPS v1.01 sections 26 and 14.3; SAD v0.31 sections 14.1, 14.2,
14.3, 14.4 and 22; `FML-ADR-034`; `FML-ADR-042`; the closure gate in
`docs/trades/TBR-TAK-01-mission-critical-state-boundary.md`.

No external source was consulted, and no claim here rests on one. Where a
statement depends on how an implementation behaves, it is written as a condition
to be tested rather than as a fact.
