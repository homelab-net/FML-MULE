# Stage 12 - NOMAD Integration

**Status: not defined.** This directory records the CONOPS scope for the
stage.
The executable stage definition does not exist.

**Source:** CONOPS v1.01 section 78, Stage 12.

## Scope

From the CONOPS:

- same standard field nodes;
- NOMAD-hosted services;
- parent Homelab authorization boundaries;
- no field-node hardware changes required for integration.

## Why this stage

The stage that validates `PBCR-01`. The parent baseline currently allocates
TAK and communications-gateway functions to NOMAD only; MULE generalizes that
to the Field Service Plane. See
`docs/change-requests/PBCR-01-field-service-plane.md`.

The fourth item is the load-bearing one: **no field-node hardware changes
required for integration.** If integrating with NOMAD needs a different node,
the one-standard-device principle in CONOPS section 5.1 has failed.

## What it validates

- **Section 79 success criteria:** none directly
- **Decisions:** `FML-ADR-039`
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
