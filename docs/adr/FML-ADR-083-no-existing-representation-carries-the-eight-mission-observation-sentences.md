---
id: FML-ADR-083
title: No existing representation carries the eight mission-observation sentences
status: PROPOSED
date: 2026-09-24
supersedes: none
superseded-by: none
trades: [TBR-OBS-01]
verification: Stage 1
---

# FML-ADR-083 No existing representation carries the eight mission-observation sentences

## Context

CONOPS v1.2 section 28A is binding. `TBR-OBS-01` asks which existing
representation records a mission observation so that its time, source, and
state stay visible. `FML-ADR-048` says prefer an existing TAK or Meshtastic
representation, and custom translation only for semantics that representation
does not have. `FML-ADR-050` bounds writes. Neither ADR selects an
observation record.

The comparison is
`docs/evidence/TBR-OBS-01/2026-09-24-representation-comparison.md`. It scores
a CoT event (`Event.xsd` Version 2.0), the OpenTAKServer 1.7.13 `cot` row,
a Meshtastic `Position`, and a Meshtastic `Neighbor` against the eight
sentences. No candidate carries all eight. The six state words are not values
of any field those sources define. CoT `stale` is the end of a validity
interval, not a state word. Optional `qos` uses "supersede" to mean the newer
event deletes the older one. The `uid` rule overwrites previous events for
that UID. The `cot` table is the reconstructable PLI store from `FML-ADR-071`,
and OpenTAKServer 1.7.13 `delete_old_data` deletes `cot` rows past a server
cutoff that defaults to one week. That is not a mission-profile retention.

Doing nothing would leave the next change free to treat a CoT event as if it
already recorded those words, or to add an observation document in `mule/`
before the gap was written down. This proposal writes the gap down. It does
not fill it.

Known at the time: the schema text, the 1.7.13 model, the pinned Meshtastic
`mesh.proto`, and the `TBR-TAK-01` classification. Not known, because it was
not run: how a particular TAK client draws a past-`stale` marker. The
comparison does not use that.

`TBR-OBS-01` is open. This proposal does not close it.

## Decision

No existing representation **shall** be treated as already carrying the eight
CONOPS v1.2 section 28A sentences. A custom observation format **shall not**
be adopted by this decision.

The missing semantics stay missing until a later decision specifies them.
That later decision, if any, is protocol-specific glue under `FML-ADR-048`.
This decision does not specify it.

## Status

`PROPOSED`. In the vocabulary of `docs/adr/README.md`, a proposed decision
carries no weight. It is not accepted, and `TBR-OBS-01` stays `OPEN` until
the named owner accepts this finding or accepts a different representation.

What is proposed is the negative finding above. What is deliberately not
decided is the record that would carry the sentences the existing fields do
not.

## Consequences

- `FML-REQ-034` through `FML-REQ-041` stay allocated to `TBR-OBS-01`. Pointing
  them at this ADR would claim a mechanism this decision does not select.
- An observation lifecycle is not implemented from this proposal. Nothing
  enters `mule/`. No schema is added. `v0.0.1` does not change.
- `FML-ADR-048` is not superseded. It remains the rule that forbids a private
  format where an existing field already has the meaning. The comparison says
  where that meaning is absent.
- `FML-ADR-071` is not reopened. The `cot` table stays reconstructable PLI.
  Observation history, if a later decision needs it retained, is not that
  table.
- A contributor without hardware can read the comparison. Closing the trade
  is still the named owner's acceptance, not a further document.

## Accepted cost

The program does not start the observation lifecycle on a CoT event. The
tempting smaller step was to declare `start` the time observed, `stale` the
state, and the sender the source. That declaration is a new document: the
schema does not give those fields those meanings, and it still has no values
for the six words. Refusing that shortcut delays the lifecycle. The cost is
that delay, taken so a stale timestamp is not later called one of six
recorded states.

## Fallback

If a field already defined by the cited sources is shown to carry a sentence
this proposal says it does not, the proposal is wrong and **shall not** be
accepted. The signal is a quotation from those sources, not a new convention.

If the named owner accepts a representation this proposal rejects, a later
ADR records that acceptance and this one stays `PROPOSED` or is retired. It
does not get rewritten into the opposite decision.

## Superseded by

None.

## Verification dependency

Stage 1 (`test/stages/`), which is the validating stage for criteria 34-41.
Stage 1 has not been run. This proposal is a document comparison, not that
demonstration, and not a flat-sat. `TBR-OBS-01` remains the trade that has to
be accepted before an implementation exists to verify.
