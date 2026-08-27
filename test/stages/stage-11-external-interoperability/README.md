# Stage 11 - External Interoperability

**Status: not defined.** This directory records the CONOPS scope for the
stage.
The executable stage definition does not exist.

**Source:** CONOPS v1.01 section 78, Stage 11.

## Scope

From the CONOPS:

- AHJ and COML handoff;
- position and resource-status export;
- voice tasking path;
- incident communications integration;
- approved amateur-radio gateway procedures.

## Why this stage

CONOPS section 47 sets the objective: not universal protocol compatibility,
but information in a form **useful to the supported incident organization**.

SAD section 32.1 item 6 recommends beginning the AHJ and operational
stakeholder conversation **before** the final hardware architecture is
selected, so interoperability work is driven by real operational utility
rather than guesswork.

Amateur gateway procedures are verified here, and CONOPS section 46 requires
that egress be disabled by default and governed by a distinct control operator
role.

## What it validates

- **Section 79 success criteria:** 29, 30
- **Decisions:** `FML-ADR-033`, `FML-ADR-048`
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
