# Stage 3 - LoRa Continuity

**Status: not defined.** This directory records the CONOPS scope for the
stage.
The executable stage definition does not exist.

**Source:** CONOPS v1.01 section 78, Stage 3.

## Scope

From the CONOPS:

- degraded messaging;
- independent LoRa operation;
- HaLow loss and reacquisition;
- HaLow/LoRa coexistence controls.

## Why this stage

CONOPS section 36 gives LoRa preservation priority over aggressive HaLow
reacquisition. This stage measures whether that priority is achievable, and
`TBR-RF-02` must produce a **stated LoRa availability or duty-cycle figure**
so the coexistence design has a verifiable target.

Measurement must be in the assembled enclosure at achievable antenna
separations. A bench measurement with the radios far apart does not answer the
question.

## What it validates

- **Section 79 success criteria:** 13, 14, 15
- **Decisions:** `FML-ADR-026`, `FML-ADR-027`
- **Trades expected to close or advance here:** `TBR-RF-02`

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
