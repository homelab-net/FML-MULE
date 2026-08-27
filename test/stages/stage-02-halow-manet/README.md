# Stage 2 - HaLow MANET

**Status: not defined.** This directory records the CONOPS scope for the
stage.
The executable stage definition does not exist.

**Source:** CONOPS v1.01 section 78, Stage 2.

## Scope

From the CONOPS:

- multiple standardized nodes;
- multi-hop routing;
- mobility;
- topology change;
- peer ATAK;
- multicast scaling;
- PLI-rate effects.

## Why this stage

CONOPS section 22 makes this the stage that **determines usable network size
and hop-count limits**. SAD section 4.3 adds that it must measure ordinary EUD
broadcast, multicast, ARP, mDNS and discovery load, not only CoT and PLI: the
architecture does not assume normal phone broadcast behaviour is free on a
constrained multi-hop mesh.

**Two nodes cannot answer this stage.** Multi-hop, relay, topology change and
BATMAN reconvergence all need a third. The prototype BOM adds a minimal relay
node for exactly this reason and calls it the highest-value line in the BOM.

## What it validates

- **Section 79 success criteria:** 7, 12
- **Decisions:** `FML-ADR-022`, `FML-ADR-023`, `FML-ADR-024`, `FML-ADR-040`
- **Trades expected to close or advance here:** `TBR-LINUX-01`, `TBR-RF-01`, `TBR-NET-01`

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
