# Stage 1 - Local Node

**Status: not defined.** This directory records the CONOPS scope for the
stage.
The executable stage definition does not exist.

**Source:** CONOPS v1.01 section 78, Stage 1.

## Scope

From the CONOPS:

- boot;
- EUD authentication;
- role and scope;
- local services;
- simplified status;
- basic power;
- user quick-reference and training materials.

## Why this stage

The first stage that can run at all. It needs one node, not a mesh, which is
why `ROADMAP.md` scopes the `v0.0.1` milestone to roughly this stage.

## What it validates

- **Section 79 success criteria:** 3, 4, 22
- **Decisions:** `FML-ADR-021`, `FML-ADR-028`, `FML-ADR-029`, `FML-ADR-030`,
  `FML-ADR-035`, `FML-ADR-041`, `FML-ADR-046`
- **Trades expected to close or advance here:** `TBR-COMP-01`, `TBR-REC-01`

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
