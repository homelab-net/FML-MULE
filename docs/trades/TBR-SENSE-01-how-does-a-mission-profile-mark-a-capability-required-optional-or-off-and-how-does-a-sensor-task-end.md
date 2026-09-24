---
id: TBR-SENSE-01
title: How does a mission profile mark a capability required, optional, or off, and how does a sensor task end
status: OPEN
owner: Cameron Zobrist
area: SENSE
priority: 99
function-owner: Mission services
critical-path: false
depends-on: []
feeds: []
requires-hardware: no
evidence: docs/evidence/TBR-SENSE-01/
adr: [FML-ADR-037]
target-date: 2026-09-30
---

# TBR-SENSE-01 How does a mission profile mark a capability required, optional, or off, and how does a sensor task end

**Source:** CONOPS v1.2 section 49, accepted with `CCR-05`. The mission
configuration package already exists (CONOPS section 19). No ADR selects how
a capability is marked, or how a sensor task names its bounds and ends.
`FML-ADR-037` still owns the separation of view, task, and node
administration. This trade does not add a role.

## Question

How does a mission profile mark a capability required, optional, or off, and
how does a sensor task name its sensor, duration, and team scope and then end?

## Why it matters

Criteria `FML-REQ-042` through `FML-REQ-045` and `FML-REQ-047` allocate here.
An optional capability that fails must not, by itself, fail local
participation. A capability marked off must not be tasked. A required
capability that is absent must be shown as missing. No encoding has been
selected. The schema field is not the test. Nothing has been run, and nothing
enters `mule/`.

## Options

- Fields the mission configuration package can already carry, shown through
  the existing status view. Right if required, optional, off, missing, and
  refused stay distinct without a new store.
- A separate sensing record. Right only if the mission package cannot say
  those words without collapsing "off" into "missing".
- Treat the mark as a new role. Not acceptable. Section 7 remains the role
  set.

## Closure evidence

A written comparison under `docs/evidence/TBR-SENSE-01/` showing, for one
candidate encoding, a capability in each of required, optional, and off; a
refused optional capability; a missing required capability; and a task that
names sensor, duration, and team scope and then ends. No code. No run.

## Closure gate

The named owner accepts one encoding, or accepts a finding that the mission
package cannot carry the distinctions. An ADR records that choice. Until then
this trade stays `OPEN`. The Stage 1 and Stage 9 demonstrations are not this
gate.

## Dependencies

- **Depends on:** none. `FML-ADR-037` already separates view, task, and
  administration, and this trade does not reopen it.
- **Feeds:** none yet.
- **Related decisions:** `FML-ADR-037`.
- **Validating stage:** Stage 1 for the mark, Stage 9 for the task. Not run.
- **Requires hardware:** no.
