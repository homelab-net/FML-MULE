# Block A

**Qualification status: `CANDIDATE`. Contents `TBD`.**

Nothing is selected. No compute module, no radio, no antenna, no enclosure, no
pack. No node has been built and nothing has been measured. This directory is a
named placeholder so that the first candidate block has somewhere to land, and
so that the repository's multi-block structure is exercised from the start
rather than retrofitted.

Do not read `block-a` as "the current design". There is no current design.

## Why the name is not descriptive

Block identifiers are short, stable, and deliberately say nothing about the
parts. A block named after its compute module becomes misleading the moment
that module is substituted, and the identifier is permanent.

## What must close before this block can be populated

| Question | Trade |
| --- | --- |
| Kernel and out-of-tree driver viability | `TBR-LINUX-01` |
| CPU and memory budget | `TBR-COMP-01` |
| Endurance and battery mass | `TBR-PWR-01` |
| Thermal architecture | `TBR-THERM-01` |
| High-rate mesh implementation | `TBR-RF-01` |
| Sub-GHz coexistence controls | `TBR-RF-02` |
| Access point and mesh radio consolidation | `TBR-RF-03` |
| Carrier board justification | `TBR-CARRIER-01` |
| Rollback implementation | `TBR-REC-01` |
| Clock holdover and skew tolerance | `TBR-TIME-01` |

`TBR-HW-01` is the trade that selects this block, and it depends on all of the
above. Selecting hardware before its constraints are known is how a program
ends up requalifying an enclosure it has already had made.

## Disqualifying constraints

A candidate that fails any of these is out, regardless of its other merits:

- No viable kernel path for the HaLow driver. `TBR-LINUX-01`, `FML-ADR-022`.
- No battery-backed real-time clock. `FML-ADR-042`.
- No boot medium supporting a known-good path independent of the active root.
  `FML-ADR-041`.

## Requalification on substitution

`TBD`. Cannot be stated before there are components to substitute.

## Valid region profiles

`TBD`. A block is valid under the regions its radio modules are approved in.
See `regions/`.

## Populating this block

Copy the structure from `hardware/blocks/_template/`: `bom/`, `mechanical/`,
`rf/`, `power/`, `assembly/`, `acceptance/`, each keeping its README. The
template's rules apply, including the requirement that a build guide is not
complete until someone other than its author has followed it successfully.
