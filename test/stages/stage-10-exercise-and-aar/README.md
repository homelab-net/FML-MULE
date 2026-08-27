# Stage 10 - Exercise and AAR

**Status: not defined.** This directory records the CONOPS scope for the
stage.
The executable stage definition does not exist.

**Source:** CONOPS v1.01 section 78, Stage 10.

## Scope

From the CONOPS:

- EXERCISE profile;
- exercise and live separation;
- white-cell fault injection;
- diagnostic tier;
- AAR export and retention behavior;
- comms-out drill.

## Why this stage

CONOPS section 50.13 requires exercise data to be distinguishable from live
incident data and **prevented from crossing into real operations where
technically feasible**. That is a correctness property, not a convenience.

CONOPS section 51 requires that exercise control not create an undocumented
production backdoor.

The **comms-out drill** validates criterion 28, that non-digital PACE is
trained and usable. CONOPS section 4 requires recurring training with MULE
deliberately unavailable for a meaningful portion of the problem. A program
that cannot pass this criterion has built a single point of failure into its
operations.

## What it validates

- **Section 79 success criteria:** 23, 24, 25, 28
- **Decisions:** `FML-ADR-046`
- **Trades expected to close or advance here:** none

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
