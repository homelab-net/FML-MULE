# Stage 5 - TAK Service Continuity

**Status: not defined.** This directory records the CONOPS scope for the
stage.
The executable stage definition does not exist.

**Source:** CONOPS v1.01 section 78, Stage 5.

## Scope

From the CONOPS:

- active host failure;
- replacement host;
- stable service identity;
- trust compatibility;
- state-class continuity;
- authoritative-state indication;
- split-brain avoidance;
- recovery-time objective.

## Why this stage

The stage carrying the most open architecture. `TBR-TAK-01` must classify
mission-critical state here before any HA mechanism is selected, and
`TBR-HA-01` is measured against partition, stale standby, rejoin and
no-authority conditions.

SAD section 9.4 adds a specific requirement for the native-service case: the
OpenTAKServer restore procedure must be demonstrated **onto a different
eligible node**, not merely restored in place, so hostname, certificate,
data-path and service-identity assumptions are exercised.

The CONOPS section 27 60-second objective is assessed here, and SAD section
14.6 permits raising a CONOPS change request against it rather than building
an unjustified HA stack.

## What it validates

- **Section 79 success criteria:** 8, 9, 10, 22
- **Decisions:** `FML-ADR-031`, `FML-ADR-032`, `FML-ADR-034`, `FML-ADR-049`
- **Trades expected to close or advance here:** `TBR-TAK-01`, `TBR-HA-01`, `TBR-COMP-01`

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
