---
id: TBR-PWR-01
title: Endurance and battery mass
status: OPEN
owner: TBD
area: PWR
critical-path: false
depends-on: [TBR-COMP-01, TBR-RF-03]
feeds: [TBR-HW-01, TBR-THERM-01]
evidence: docs/evidence/TBR-PWR-01/
adr: [FML-ADR-021, FML-ADR-045]
---

# TBR-PWR-01 Endurance and battery mass

## Question

What endurance does the operational concept require, and what battery mass and
volume does that imply for a device a volunteer carries?

## Why it matters

Endurance and portability are in direct tension, and both are stated
requirements. Endurance drives cell count, which drives mass, volume, thermal
load, charging time, and transport rules. A device that meets its endurance
target and is too heavy to carry has failed, and so has the reverse.

Nothing here is known. No endurance figure, no power budget, no cell chemistry
and no mass target appears anywhere in this repository, because none has been
set. Any number encountered elsewhere claiming to be a MULE endurance figure
did not come from this program.

## Options

Options cannot be enumerated until the endurance requirement is stated by the
operational concept and the load is bounded by `TBR-COMP-01` and `TBR-RF-03`.
The axes are: required endurance, duty cycle assumed, chemistry, whether the
pack is user-swappable in the field, and whether external charging or a solar
input is in scope.

Recording the axes rather than inventing options is deliberate.

## Closure evidence

Committed under `docs/evidence/TBR-PWR-01/`:

- A stated endurance requirement traced to the CONOPS, with the duty cycle it
  assumes.
- Measured current draw of the assembled compute and radio load at idle, at a
  representative mission duty cycle, and at sustained maximum, recorded with
  instrument, date, node, image build, and ambient temperature.
- Archived cell datasheets for every candidate, including capacity at the
  discharge rate actually used rather than the headline figure.
- A calculated pack size with the derivation shown, and the resulting mass and
  volume.
- A discharge run of the assembled pack under a representative load, to the
  protection cutoff, with the curve recorded.

## Closure gate

Measured endurance of an assembled node under a representative duty cycle meets
the stated requirement, with the pack mass and volume within the portability
constraint that the CONOPS states. Both the requirement and the constraint must
be written down before the measurement is taken.

A calculation alone does not close this trade. Cells do not deliver their
datasheet capacity under real loads at real temperatures.

## Dependencies

- **Depends on:** `TBR-COMP-01` (load), `TBR-RF-03` (radio count).
- **Feeds:** `TBR-HW-01`, `TBR-THERM-01`.
- **Requires hardware:** yes, for the measurement. The requirement statement
  and the CONOPS tracing can be done without.
