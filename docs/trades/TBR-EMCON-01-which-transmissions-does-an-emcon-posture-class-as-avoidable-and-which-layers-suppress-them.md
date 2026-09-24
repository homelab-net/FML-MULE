---
id: TBR-EMCON-01
title: Which transmissions does an EMCON posture class as avoidable, and which layers suppress them
status: OPEN
owner: Cameron Zobrist
area: EMCON
priority: 99
function-owner: RF/Spectrum
critical-path: false
depends-on: []
feeds: []
requires-hardware: no
evidence: docs/evidence/TBR-EMCON-01/
adr: [FML-ADR-046]
target-date: 2026-09-30
---

# TBR-EMCON-01 Which transmissions does an EMCON posture class as avoidable, and which layers suppress them

**Source:** CONOPS v1.2 section 50.12, accepted with `CCR-05`. SAD section 23
already names the layers that can suppress emissions. It does not name which
transmissions a posture classes as avoidable. `FML-ADR-046` owns what the
status view may claim about EMCON. It does not choose what the radios send.
This trade does not add an EMCON mode name.

## Question

Which transmissions does an EMCON posture class as avoidable, and which of the
SAD section 23 layers suppress them?

## Why it matters

`FML-REQ-049` allocates here. Without a class list, a later flat-sat cannot
show that an avoidable transmission was absent, and someone can treat the mode
as measured radio silence. Measured silence is not this trade and is not a
mode. The Stage 10 criteria have not been run. Nothing enters `mule/`.

## Options

- A class list in the mission profile, mapped onto the layers SAD section 23
  already names. Right if those layers can suppress each class.
- A new suppression layer. Right only if a class has no existing layer. That
  choice would be an ADR, not a silent addition.
- Report EMCON as measured silence. Not acceptable. `FML-ADR-046` forbids
  that claim.

## Closure evidence

A written class list under `docs/evidence/TBR-EMCON-01/`, each class mapped to
one or more SAD section 23 layers, or to a named gap. No radio measurement.
No claim that a transmission was observed or absent on hardware.

## Closure gate

The named owner accepts the class list and the layer map, or accepts an ADR
for a layer the list shows is missing. Until then this trade stays `OPEN`.
A flat-sat of what the node reports is CONOPS section 85, Stage 10, and is
not a measurement of silence. It is not this gate.

## Dependencies

- **Depends on:** none.
- **Feeds:** none yet.
- **Related decisions:** `FML-ADR-046`, for the words the status view may use.
  Criteria `FML-REQ-050` and `FML-REQ-051` allocate there, not here.
- **Validating stage:** Stage 10, after the class list exists. Not run.
- **Requires hardware:** no, for the class list. A later demonstration is
  still not an RF measurement.
