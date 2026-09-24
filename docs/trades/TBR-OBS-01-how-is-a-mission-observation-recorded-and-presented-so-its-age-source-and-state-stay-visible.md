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
adr: [FML-ADR-048, FML-ADR-050]
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

The comparison is evidence. Accepting its bounded finding does not close
this trade and does not select a representation.

The named owner closes it only by accepting how an observation is recorded
and presented. An ADR records that choice and cites the comparison. For any
semantic that choice does not take from the four reviewed representations,
the ADR also cites a reading of the CoT detail schemas and the other
Meshtastic messages the comparison names as unread. If that reading is
absent, assigning the semantic to local metadata or local policy does not
close the trade. Until the choice is recorded this trade stays `OPEN`.
The Stage 1 demonstrations in CONOPS section 85 are not this gate.

## Comparison

Written 2026-09-24 in
`docs/evidence/TBR-OBS-01/2026-09-24-representation-comparison.md`.

None of the reviewed representations, using only the meanings their cited
sources already define, satisfies the complete section 28A contract without
new FML semantics. The review covers a CoT event, the OpenTAKServer 1.7.13
`cot` row, a Meshtastic `Position`, and a Meshtastic `Neighbor`. It does not
claim every existing representation was examined. It separates sentences that
are data on a record from sentences that are presentation, retention,
correlation, or queue behavior. It selects no representation and decides no
implementation layer.

**Not closed.** The named owner has not accepted how an observation is
recorded and presented. Accepting the bounded finding would not close this
trade. It stays `OPEN`.

## Dependencies

- **Depends on:** none.
- **Feeds:** none yet.
- **Related decisions:** `FML-ADR-048` and `FML-ADR-050`. Neither selects an
  observation record.
- **Validating stage:** Stage 1, after a representation exists. Not run.
- **Requires hardware:** no. The comparison is a document.
