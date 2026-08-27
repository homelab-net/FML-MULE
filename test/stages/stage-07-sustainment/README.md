# Stage 7 - Sustainment

**Status: not defined.** This directory records the CONOPS scope for the
stage.
The executable stage definition does not exist.

**Source:** CONOPS v1.01 section 78, Stage 7.

## Scope

From the CONOPS:

- nominal 8-hour objective;
- service-host power penalty;
- 24-72 hour mission battery model;
- external-power operation;
- charge-while-operating behavior;
- cold-weather endurance.

## Why this stage

`TBR-PWR-01` is priority 1 in the SAD register and this is where it closes.
The stage measures the eight load states in SAD section 25.1 and produces the
pack model.

CONOPS section 61 requires the verified endurance requirement to include
**defined cold-temperature conditions**, and states that the nominal 8-hour
objective is not guaranteed winter endurance in any planning product.

SAD section 25.7 directs that the same instrumented rig collect thermal
evidence for `TBR-THERM-01`, to avoid duplicate prototype builds.

## What it validates

- **Section 79 success criteria:** 21, 22
- **Decisions:** `FML-ADR-021`, `FML-ADR-045`
- **Trades expected to close or advance here:** `TBR-PWR-01`, `TBR-COMP-01`, `TBR-THERM-01`

The criterion-to-stage mapping is CONOPS section 85 and is transcribed as
structured requirements in `docs/verification/requirements.md`, from which
`tools/gen-traceability.sh` generates the matrix.

## What a definition must contain

Per `test/stages/README.md`: a stable stage identifier, purpose, the
configuration under test (hardware block, compatibility set version, region
profile, mission profile), preconditions, a step-by-step procedure with
explicit
pass criteria, instrumentation, **pass criteria written before the stage is
run**, the evidence produced and where it is filed in `test/results/`, and
what
a failure means.

## Blocked on

Stage definitions depend on a selected hardware block (`TBR-HW-01`) and on a
populated requirement set. Neither exists. Defining pass criteria now would
mean
inventing thresholds for hardware nobody has chosen.

The exception is the promotion gate in `os/release/README.md`, which is a
build-acceptance gate rather than a qualification stage and exists today.
