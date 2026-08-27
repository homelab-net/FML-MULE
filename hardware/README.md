# Hardware

**Nothing is selected. No block is qualified. No component has been chosen.**

That statement is the current state of this directory, and every file in it
should be read against it.

## Blocks

The program makes a specific promise: **a spare node can replace any node
within the same qualified hardware block.** It also expects blocks to change as
components reach end of life. This program has already had a key module reach
end of life before it could be purchased.

Both of those together mean the repository must hold **more than one qualified
configuration at once**, and must have done so from the start. Retrofitting
multi-block support onto a repository that assumed one configuration is a large,
tedious, error-prone change, and it always happens at the worst time: when the
current parts stop being available.

So the structure is:

```text
hardware/
  blocks/
    _template/       copy this to start a new block
    block-a/         first candidate block, contents TBD
  common/            genuinely block-independent material only
  lifecycle/         component lifecycle and obsolescence register
  prototype/         prototype and test BOM, NOT a production baseline
```

A **block** is not a compute module. It is the whole qualified configuration:
compute, carrier or wiring, radios, antennas, pack, enclosure, and the
acceptance procedure that says a built node is a member of it.

### What each block directory holds

| Directory | Contents |
| --- | --- |
| `bom/` | Bill of material: part numbers, sources, quantities, archived datasheets. |
| `mechanical/` | Enclosure, mounting, cable routing. Native CAD source and a render. |
| `rf/` | Antennas, gains, placement, module approvals, integration conditions. |
| `power/` | Pack, charging, distribution, protection, fusing. |
| `assembly/` | Build guide and `BUILD-ACCEPTANCE.md`. |
| `acceptance/` | The procedure that qualifies a built node as a member of the block. |

Each block's `README.md` states its **qualification status** and **what
requalification a substitution demands**. That second part is the one that gets
skipped, and it is the one that matters when a part goes end-of-life: a reader
needs to know whether swapping a connector is a paperwork change or a new
qualification cycle.

### Substitution

A substitution within a block is only a substitution if the block says so.
Changing a component may require requalification, and the block's README states
which changes require what. Where it does not say, assume requalification.

## `common/`

`hardware/common/` holds only what is **genuinely block-independent**: material
that would be identical across any plausible configuration.

Resist putting things here. The natural pressure, with one candidate block, is
to treat everything as common, and everything placed in `common/` that is
actually block-specific has to be untangled later. When in doubt, it belongs to
the block.

## `prototype/`

`hardware/prototype/` holds the **prototype and test BOM**: what must be
purchased to make the architecture decisions, per SAD section 33.3.

It is kept out of `blocks/` deliberately. Filing it under `block-a/` would imply
that block A is being defined, and it is not. The prototype BOM buys the minimum
alternatives and instrumentation needed to close the critical trades; a
production BOM does not exist and cannot until `TBR-HW-01` closes.

## `lifecycle/`

Components reach end of life, and they do it without telling you. The
obsolescence register tracks what each block depends on, what the vendor has
said about its lifecycle, and what the program would do if a part disappeared.

This is not optional bookkeeping for this program. It has already been bitten
once.

## Current state

| Item | State |
| --- | --- |
| `block-a` | Placeholder. Contents `TBD`. No parts selected. |
| Qualified blocks | None. |
| Compute module | Not selected. `TBR-HW-01`, `TBR-COMP-01`. |
| Enclosure | Not selected. `TBR-THERM-01`. |
| Battery and pack | Not selected. `TBR-PWR-01`. |
| Antennas | Not selected. `TBR-RF-01`, `TBR-RF-02`, `TBR-RF-03`. |
| Carrier board | Not decided whether one is needed at all. `TBR-CARRIER-01`. |

`TBR-HW-01` is the trade that closes this, and it waits on almost every other
hardware trade. Selecting hardware before its constraints are known is how a
program ends up requalifying an enclosure it has already had made.

## Constraints that disqualify

Some requirements are not scoring criteria. A candidate that fails one is out,
regardless of how well it does elsewhere:

- **No viable kernel path** for the HaLow driver. `TBR-LINUX-01`,
  `FML-ADR-022`.
- **No battery-backed real-time clock.** `FML-ADR-042` makes it mandatory.
- **No boot medium supporting a known-good path independent of the active
  root.** `FML-ADR-041`.

Recording these as disqualifying, before candidates are evaluated, is
deliberate. It is much harder to hold a line like this once someone has a board
they like in front of them.

## Safety and regulation

Read `SAFETY.md` before assembling anything, particularly the lithium and
thermal sections. Read `REGULATORY.md` before buying a radio module:
substituting an antenna can void a modular approval, and compliance of the
assembled device is the builder's responsibility.
