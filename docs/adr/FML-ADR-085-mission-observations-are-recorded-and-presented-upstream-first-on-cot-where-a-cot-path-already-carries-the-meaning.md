---
id: FML-ADR-085
title: Mission observations are recorded and presented upstream-first on CoT where a CoT path already carries the meaning
status: SELECTED PRINCIPLE
date: 2026-09-27
supersedes: none
superseded-by: none
trades: [TBR-OBS-01]
verification: Stage 1
---

# FML-ADR-085 Mission observations are recorded and presented upstream-first on CoT where a CoT path already carries the meaning

**Source of rationale:** `docs/evidence/TBR-OBS-01/2026-09-27-representation-decision-packet.md`,
citing the 2026-09-24 representation comparison and consumer reading and the live
OTS bench observation in that packet's section 2a. CONOPS v1.2 section 28A
(`FML-REQ-034`-`041`). This ADR records the Owner's acceptance of the packet's
frame; it does not adopt the packet's section 4 as a completed selection.

## Context

CONOPS v1.2 section 28A commits the program to a mission observation that carries
its age, source, and state, is not presented as current once stale or expired,
keeps its observed time through relaying, is retained as history after expiry, is
not merged across subjects, whose link reports are not read as paths or emitter
locations, and whose derived products cite their sources. `TBR-OBS-01` owns how
that is recorded and presented and is `OPEN`: its trade file bars any of this
behavior from entering `mule/` until an ADR records the choice, and its closure
gate forbids assigning a behavior to local FML policy until an ADR cites a reading
of the upstream consumer (the TAK client or the OpenTAKServer code) that performs
it.

The 2026-09-24 comparison found that no reviewed representation, using only its
native semantics, satisfies the complete section 28A contract. The consumer
reading read OpenTAKServer 1.7.13 and Meshtastic firmware; the live OTS bench
(packet section 2a) confirmed at runtime that the stored `cot` record carries the
CoT `time`/`start`/`stale` trio and a sender but holds no field for the six state
words, and that retention runs as deletion. What remains genuinely unread is a
TAK client's handling of a past-`stale` event and of CoT `detail` extensions.
Doing nothing leaves the whole awareness enhancement blocked, because every part
of it produces or consumes observations.

## Decision

A mission observation **shall** be recorded and presented **upstream-first**: it
**shall** use CoT as its carrier for every meaning an upstream CoT path already
carries, and **shall not** introduce a bespoke program-wide observation wire
format (`FML-ADR-048`). The observed time **shall** be preserved through relaying
and queuing rather than replaced by a delivery time; this is the one section 28A
behavior a read consumer already performs (`route_cot` does not restamp).

For every section 28A behavior no read consumer performs -- the six explicit state
words (`FML-REQ-034`), retention of an expired observation as bounded history
(`FML-REQ-037`), deterministic keyed correlation and the refusal to present a
possible match as a confirmed identity (`FML-REQ-038`), provenance and the
model-product label (`FML-REQ-040`), the link-report guard (`FML-REQ-039`), and the
bounded-queue discard record (`FML-REQ-041`) -- FML **shall** supply the semantic,
and a later **implementation ADR shall** fix how. That implementation ADR **shall
not** assign any of those semantics to local policy, and **shall not** fix the
metadata carrier (CoT `detail`, node-local state, or mission-profile data), the
stale/expired thresholds, or the retention-as-history bound, until it has read,
per this trade's closure gate, (a) the CoT `detail` schemas and (b) a TAK client's
handling of a past-`stale` event and of unknown `detail`. A retention-as-history
duration, when fixed, **shall** be bounded, reconciled with `FML-ADR-050`.

An observation with no upstream CoT path -- a mesh-only link-heard report is the
worked example (`FML-REQ-039`) -- is a distinct sub-case the implementation ADR
**shall** address through conversion glue (`FML-ADR-048`), not by assuming a CoT
path exists.

## Status

`SELECTED PRINCIPLE`. Decided: observations are upstream-first, CoT-carried where a
CoT path already carries the meaning, with the observed time preserved through
relay. Deliberately left to a later implementation ADR, after the owed readings:
the carrier for the FML-added semantics, the stale/expired thresholds, the
retention-as-history bound, and the assignment of `FML-REQ-034`/`035`/`037`/`038`/
`040` to local policy. `TBR-OBS-01` stays `OPEN`; this ADR records the frame, not
its closure.

## Consequences

- Downstream awareness work (sensing, tasking, comms-terrain, SITREP, EMCON
  collection) gains a cited principle to build on and a single carrier direction,
  rather than each inventing its own record.
- It forecloses a bespoke mesh-wide observation JSON as the wire format
  (consistent with `FML-ADR-048`/`070`); FML JSON stays a semantic contract for
  fixtures and local boundaries, not a transport.
- It creates the owed-readings work as the next gate: whether the six-word state,
  provenance, and correlation ride CoT `detail` turns entirely on whether the TAK
  clients this program uses preserve and forward unknown `detail` on round-trip.
  CoT carries only one validity timestamp (`stale`), so the stale-versus-expired
  distinction and the six words cannot travel on native CoT fields alone.
- Nothing enters `mule/` on this ADR: it fixes a principle, not an implementation.

## Accepted cost

The frame commits the program to CoT's expressiveness where a CoT path exists, and
CoT does not natively carry the six state words, provenance, or a stale/expired
split. FML therefore takes on a mapping-and-maintenance burden, and a real risk
that the eventual `detail` carriage is discarded by a stock client the same way a
custom encoding on a private port was measured to be discarded (`FML-ADR-070`).
The magnitude of that cost is not yet quantified; the owed CoT-`detail` and
TAK-client readings named in the Decision are what will quantify it, and until
they are done this ADR has deliberately fixed no carrier.

## Fallback

If the owed readings show the target TAK clients do not preserve unknown CoT
`detail`, the implementation ADR carries the FML-added semantics as node-local
state plus mission-profile data, and the shared COP shows only what CoT natively
carries between nodes -- accepting a thinner cross-node picture rather than a
custom wire tag. If CoT proves the wrong carrier entirely, this ADR is superseded
by one selecting a different representation; because nothing was written into
`mule/` or a schema here, that reversal supersedes a principle and rewrites no
code.

## Superseded by

None.

## Verification dependency

The software digital twin shall exercise the lifecycle and correlation semantics
once the implementation ADR fixes them; the section 28A criteria are Stage 1
(`FML-REQ-034`-`041`). The client-side presentation of a past-`stale` event and
the round-trip fate of CoT `detail` remain unverified until the owed TAK-client
reading and, ultimately, a hardware exercise with a real client; this ADR claims
neither.
