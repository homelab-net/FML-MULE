# Stage 9 - Identity and Capture

**Status: not defined.** This directory records the CONOPS scope for the
stage.
The executable stage definition does not exist.

**Source:** CONOPS v1.01 section 78, Stage 9.

## Scope

From the CONOPS:

- lost EUD;
- replacement EUD;
- mission credential expiry;
- revocation propagation;
- disconnected revocation lag;
- lost node;
- node revocation;
- zeroize;
- encrypted storage.

## Why this stage

**Disconnected revocation lag is a test item, not a defect.** CONOPS section
15 accepts that offline operation and instantaneous revocation are
incompatible; this stage measures the window and confirms that bounded
credential lifetimes make it fail safe by expiry.

SAD section 30.1 records zeroize as OPEN until **destructive test**. Verifying
that sensitive data does not survive zeroize means actually attempting
recovery afterwards.

`FML-ADR-042` fail-closed behaviour is exercised here: a node with a dead
clock backup cell must refuse validation and say why.

## What it validates

- **Section 79 success criteria:** 5, 6, 19, 26, 27
- **Decisions:** `FML-ADR-036`, `FML-ADR-038`, `FML-ADR-042`, `FML-ADR-043`, `FML-ADR-044`, `FML-ADR-047`
- **Trades expected to close or advance here:** `TBR-SEC-01`, `TBR-TIME-01`, `TBR-ID-01`

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
