# Stage 4 - High-Throughput IP

**Status: not defined.** This directory records the CONOPS scope for the
stage.
The executable stage definition does not exist.

**Source:** CONOPS v1.01 section 78, Stage 4.

## Scope

From the CONOPS:

- higher-throughput bearer;
- large files;
- maps;
- video;
- bulk synchronization;
- traffic preference.

## Why this stage

Exercises both the high-rate bearer itself and the CONOPS section 40 traffic
preference: video, large files and bulk synchronization on the high-rate path,
mission-critical CoT and PLI on whichever stable viable path exists.

`TBR-RF-03` concurrency testing shares this stage: whether the EUD access
point and the inter-node bearer can share one radio is measured here and in
Stage 1.

## What it validates

- **Section 79 success criteria:** 11, 15
- **Decisions:** `FML-ADR-025`, `FML-ADR-045`
- **Trades expected to close or advance here:** `TBR-RF-01`, `TBR-RF-03`

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
