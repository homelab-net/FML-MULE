# Stage 6 - WAN Overlay

**Status: not defined.** This directory records the CONOPS scope for the
stage.
The executable stage definition does not exist.

**Source:** CONOPS v1.01 section 78, Stage 6.

## Scope

From the CONOPS:

- local WAN gateway;
- secure overlay;
- remote field services;
- EUD isolation from overlay;
- unauthorized Homelab access denial;
- WAN loss and local continuity.

## Why this stage

Two of the four criteria here are **negative**: EUDs must be shown not to join
the overlay, and unauthorized home, private and administrative infrastructure
must be shown inaccessible. A stage that only demonstrates working reachback
has not tested the boundary.

WAN loss and local continuity is the other half: CONOPS section 41 requires
local EUD access, local mesh, peer ATAK, local S0 and S1 services, and LoRa to
survive it.

## What it validates

- **Section 79 success criteria:** 16, 17, 18, 19
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
