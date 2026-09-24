# Stage 6 - WAN Overlay

**Status: not defined.** This directory records the CONOPS scope for the
stage. The executable stage definition does not exist.

**Source:** CONOPS v1.1 section 78, Stage 6. `FML-ADR-082`. CONOPS v1.2 adds
two bullets and does not remove these. Linked voice between authorized MULEs,
when WAN exists, does not require an EUD to join the overlay. Loss of WAN
leaves local and direct RF voice usable. Neither addition has been run. The
overlay cases stay NOT RUN.

## Scope

From CONOPS v1.1:

- local WAN gateway;
- secure overlay between authorized MULEs, without extending the local RF
  mesh across the WAN;
- remote field services;
- default remote-EUD posture: EUD isolation from the overlay;
- `ASSIGNED_MULE_ONLY`: an authorized EUD reaches only its assigned MULE's
  approved remote-EUD ingress;
- that grant does not place the EUD on the local RF mesh; an approved mission
  service the assigned MULE reaches over that mesh is still reached through
  the assigned ingress;
- loss of the assigned MULE does not attach that EUD through another MULE;
- unauthorized Homelab access denial;
- WAN loss and local continuity;
- declining remote-EUD continuity does not remove local EUD operation;
- the admitted EUD carries one tag naming the mission and the assigned team,
  not a role, and not a grant built from several broad tags.

`docs/evidence/stage-06-wan-overlay/` records each case. None of those files
is a result. No case has been run.

## Why this stage

The default posture is still a negative: an EUD is shown not to join the
overlay, and unauthorized home, private and administrative infrastructure is
shown inaccessible. A stage that only demonstrates working reachback has not
tested the boundary.

The opt-in adds a positive and two further negatives: the authorized EUD
reaches only the assigned ingress, it is not placed on the local RF mesh, and
loss of that MULE does not attach it through another. A service the assigned
MULE reaches over the RF mesh is the MULE's path, not a failure of the mesh
negative.

WAN loss and local continuity is the other half: CONOPS section 41 requires
local EUD access, local mesh, peer ATAK, local S0 and S1 services, and LoRa to
survive it.

## What it validates

- **Section 79 success criteria:** 16, 17, 18, 19, 54, 56. Criteria 54 and
  56 are CONOPS v1.2 and have not been run.
- **Decisions:** `FML-ADR-082`
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
