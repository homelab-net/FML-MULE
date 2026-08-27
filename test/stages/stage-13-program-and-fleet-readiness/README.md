# Stage 13 - Program and Fleet Readiness

**Status: not defined.** This directory records the CONOPS scope for the
stage.
The executable stage definition does not exist.

**Source:** CONOPS v1.01 section 78, Stage 13.

## Scope

From the CONOPS:

- unit acceptance test executed on every fielded node;
- second qualified builder demonstrates reproducible build;
- imaging, re-key, and spares path exercised end to end;
- training qualification and recurrence standards issued.

## Why this stage

The stage that is about the **program**, not the equipment.

**A second qualified builder demonstrating a reproducible build** is criterion
33 and CONOPS section 76: the system shall not depend on one builder or
originator. It is the same property this repository's cold start drill and
`BUILD-ACCEPTANCE.md` test, and the same property `MAINTAINERS.md` currently
records as unmet with every role `VACANT`.

CONOPS section 74 requires operational interchangeability to be **verified,
not assumed**.

## What it validates

- **Section 79 success criteria:** 1, 32, 33
- **Decisions:** `FML-ADR-040`, `FML-ADR-050`
- **Trades expected to close or advance here:** `TBR-HW-01`, `TBR-CARRIER-01`

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
