# Qualification stages

One directory per qualification stage. A stage defines what is being
demonstrated, on what configuration, under what conditions, with what pass
criteria, and what evidence it produces.

**No stage is defined.** Stages depend on a selected hardware block
(`TBR-HW-01`) and on a populated requirement set, and neither exists. Defining
stages now would mean inventing pass criteria for hardware nobody has chosen.

## Where verification actually happens

Stages are where **hardware-in-the-loop** verification lives, and the only
place it does. CI has no radios, no battery, and no enclosure; see
`test/README.md`.

Traceability runs from an operational requirement, to an architecture
allocation, to a validating stage. **A binding requirement with no validating
stage is a defect**, and `tools/gen-traceability.sh --check` fails the build
for it. Stages are therefore not optional documentation: they are one end of a
chain the build enforces.

## What exists today

The **promotion gate** in `os/release/README.md` is the closest thing to a
stage the program has, and it is a build-acceptance gate rather than a
qualification stage. A candidate compatibility set must:

1. Rebuild all out-of-tree modules.
2. Boot.
3. Enumerate every radio.
4. Form a mesh.
5. Serve the access point.
6. Pass a traffic smoke test.
7. Survive a reboot.
8. Demonstrate rollback.

It is likely to become the first stage, or to be absorbed into one.

## What a stage definition must contain

- **Stage identifier**, stable and permanent, on the same terms as ADR and
  trade identifiers. Referenced from requirement frontmatter.
- **Purpose**: which requirements this stage validates.
- **Configuration under test**: hardware block, compatibility set version,
  region profile, mission profile.
- **Preconditions**, including what must have passed before.
- **Procedure**, step by step, each with an explicit pass criterion. Not "check
  it works": a stated command, a stated expected result, a stated tolerance.
- **Instrumentation**: what is measured and with what.
- **Pass criteria**, written **before** the stage is run.
- **Evidence produced**, and where it is filed in `test/results/`.
- **What a failure means**: retest after rework, or a return to a trade.

## Stages this program will need

Named so the shape is visible, not as a commitment. None is defined.

| Likely stage | Validates |
| --- | --- |
| Build and boot | The promotion gate, `FML-ADR-040`. |
| Radio enumeration and bring-up | `TBR-LINUX-01`, `FML-ADR-022`. |
| Mesh formation and multi-hop traffic | `FML-ADR-024`, `TBR-RF-01`. |
| Access point and concurrent load | `FML-ADR-045`, `TBR-RF-03`. |
| Coexistence | `TBR-RF-02`. |
| Endurance | `TBR-PWR-01`. |
| Thermal | `TBR-THERM-01`. |
| Time retention and fail-closed behaviour | `FML-ADR-042`, `TBR-TIME-01`. |
| Rollback and recovery | `FML-ADR-041`, `TBR-REC-01`. |
| Field usability | The cold start drill, `docs/verification/`. |
