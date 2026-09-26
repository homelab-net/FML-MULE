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
adr: [FML-ADR-048, FML-ADR-050, FML-ADR-085]
target-date: 2026-09-30
---

# TBR-OBS-01 How is a mission observation recorded and presented so its age, source, and state stay visible

**Source:** CONOPS v1.2 section 28A, accepted with `CCR-05`. No ADR selects a
store, a schema, or an encoding. `FML-ADR-048` says prefer an existing
representation. `FML-ADR-050` bounds writes. This trade does not select either.

**Frame accepted (2026-09-26), still `OPEN`.** `FML-ADR-085` (`SELECTED
PRINCIPLE`) records the Owner's acceptance of an upstream-first frame -- CoT as the
carrier where a CoT path already carries the meaning, FML supplying the section 28A
semantics CoT lacks -- from the decision packet
`docs/evidence/TBR-OBS-01/2026-09-27-representation-decision-packet.md`. That ADR
fixes only the frame. Closure still needs the owed readings its Decision names (the
CoT `detail` schemas and a TAK client's handling of a past-`stale` event and of
unknown `detail`), the metadata carrier, and the state-model thresholds, in a later
implementation ADR. The trade stays `OPEN`.

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
queue. No code, and no claim that a software digital twin was run.

## Closure gate

The comparison is evidence. Accepting its bounded finding does not close
this trade and does not select a representation.

The named owner closes it only by accepting how an observation is recorded
and presented. An ADR records that choice and cites the comparison.

For any behavior the reviewed definitions do not state, that ADR does not
assign the behavior to local FML policy until it cites a reading of the
upstream consumer that would perform it. For a CoT behavior that is the
TAK client or the OpenTAKServer code. For a Meshtastic behavior that is
the firmware. A schema or a message definition is not that reading. CoT
detail schemas and other Meshtastic messages the comparison names as
unread still have to be read before a semantic they might carry is
assigned to local metadata.

If that consumer cannot be read, the ADR records the limitation. It does
not treat the unread consumer as proof that the behavior is absent.
Until the choice is recorded this trade stays `OPEN`. The Stage 1
demonstrations in CONOPS section 85 are not this gate.

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

A later reading of the consumers the comparison left unread is
`docs/evidence/TBR-OBS-01/2026-09-24-consumer-reading.md`. It covers the
OpenTAKServer 1.7.13 streaming writer, the web map query, the
Meshtastic-to-CoT builder, and Meshtastic firmware `v2.8.0.47db0e3` for
the neighbor send, the position timestamp copy, and a full receive queue.
It does not read a TAK client. It selects no representation. Accepting it
would not close this trade.

## Dependencies

- **Depends on:** none.
- **Feeds:** none yet.
- **Related decisions:** `FML-ADR-048` and `FML-ADR-050`. Neither selects an
  observation record. `FML-ADR-085` (`SELECTED PRINCIPLE`) accepts the
  upstream-first frame but selects no representation and leaves the carrier and
  state model to a later implementation ADR; this trade stays `OPEN`.
- **Validating stage:** Stage 1, after a representation exists. Not run.
- **Requires hardware:** no. The comparison is a document.
