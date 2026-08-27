# Qualification stages

One directory per qualification stage. A stage defines what is being
demonstrated, on what configuration, under what conditions, with what pass
criteria, and what evidence it produces.

**No stage is defined.** Each of the thirteen directories here records the
CONOPS section 78 scope for its stage, what it validates, and what it is blocked
on. That is not a definition: a definition needs pass criteria, and pass criteria
need a selected hardware block (`TBR-HW-01`) and measured baselines. Writing
thresholds now would mean inventing them for hardware nobody has chosen.

The requirement set **is** populated: see `docs/verification/requirements.md`.

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

## The thirteen stages

From CONOPS section 78. Directory names carry a zero-padded number so they sort.

| Stage | Subject | Trades expected to close or advance |
| ---: | --- | --- |
| 1 | Local Node | `TBR-COMP-01`, `TBR-REC-01` |
| 2 | HaLow MANET | `TBR-LINUX-01`, `TBR-RF-01`, `TBR-NET-01` |
| 3 | LoRa Continuity | `TBR-RF-02` |
| 4 | High-Throughput IP | `TBR-RF-01`, `TBR-RF-03` |
| 5 | TAK Service Continuity | `TBR-TAK-01`, `TBR-HA-01`, `TBR-COMP-01` |
| 6 | WAN Overlay | none |
| 7 | Sustainment | `TBR-PWR-01`, `TBR-COMP-01`, `TBR-THERM-01` |
| 8 | Physical Field Qualification | `TBR-THERM-01`, `TBR-CARRIER-01`, `TBR-RF-02` |
| 9 | Identity and Capture | `TBR-SEC-01`, `TBR-TIME-01`, `TBR-ID-01` |
| 10 | Exercise and AAR | none |
| 11 | External Interoperability | none |
| 12 | NOMAD Integration | none, validates `PBCR-01` |
| 13 | Program and Fleet Readiness | `TBR-HW-01`, `TBR-CARRIER-01` |

**Stage 2 cannot be run with two nodes.** Multi-hop, relay, topology change and
BATMAN reconvergence all need a third, which is why the prototype BOM adds a
minimal relay node and calls it the highest-value line in the BOM.
