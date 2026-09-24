---
id: TBR-OBS-01
title: How is a mission observation recorded and presented so its age, source, and state stay visible
status: OPEN
owner: Cameron Zobrist
area: OBS
priority: 99
function-owner: Mission services
critical-path: false
depends-on: []
feeds: []
requires-hardware: no
evidence: docs/evidence/TBR-OBS-01/
adr: [FML-ADR-048, FML-ADR-050, FML-ADR-083]
target-date: 2026-09-30
---

# TBR-OBS-01 How is a mission observation recorded and presented so its age, source, and state stay visible

**Source:** CONOPS v1.2 section 28A, accepted with `CCR-05`. No ADR selects a
store, a schema, or an encoding. `FML-ADR-048` says prefer an existing
representation. `FML-ADR-050` bounds writes. This trade does not select either.

## Question

How is a mission observation recorded and presented so that its time, source,
and state stay visible, including when the node cannot deliver?

## Why it matters

CONOPS v1.2 section 28A is binding. Criteria `FML-REQ-034` through
`FML-REQ-041` allocate here. A reader who treats a stale report as current, or
a link report as an emitter location, acts on a false claim. No representation
has been selected, and none of those criteria has been run. SAD v0.32 does not
transcribe the clauses. Nothing enters `mule/`.

## Options

- Reuse a field an existing TAK or message representation already carries
  (`FML-ADR-048`). Right if that field can show time, source, and one of the
  six state words without a new document.
- A bounded local record the node already keeps, presented as itself. Right
  if no existing field can carry those words without calling a stale record
  current.
- Drop the obligation. Not acceptable. Acceptance already made the sentences
  binding. This trade chooses a representation, not whether they bind.

## Closure evidence

A written comparison under `docs/evidence/TBR-OBS-01/` of the candidate
representations against the eight section 28A sentences. The comparison names
what each candidate does with time, source, state, a queued delivery, an
expired record, two subjects, a link report, a derived product, and a full
queue. No code, and no claim that a flat-sat was run.

## Closure gate

The named owner accepts one representation, or accepts a finding that none of
the existing representations can carry the eight sentences. An ADR records
that choice and cites the comparison. Until then this trade stays `OPEN`.
The Stage 1 demonstrations in CONOPS section 85 are not this gate.

## Comparison

Written 2026-09-24 in
`docs/evidence/TBR-OBS-01/2026-09-24-representation-comparison.md`. No
candidate carries all eight sentences. `FML-ADR-083` is `PROPOSED` to record
that finding. It does not select a format. While `PROPOSED` it carries no
weight.

**Not closed.** The named owner has not accepted the finding and has not
accepted a representation. This trade stays `OPEN`.

## Dependencies

- **Depends on:** none.
- **Feeds:** none yet. `FML-ADR-083` cites this trade and is `PROPOSED`.
- **Related decisions:** `FML-ADR-048`, `FML-ADR-050`, and proposed `FML-ADR-083`.
- **Validating stage:** Stage 1, after a representation exists. Not run.
- **Requires hardware:** no. The comparison is a document.
