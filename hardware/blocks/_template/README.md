# Block template

Copy this directory to `hardware/blocks/<block-id>/` to start a new hardware
block, and replace this README.

A **block** is a whole qualified configuration, not a compute module. The
program's promise is that a spare node replaces any node **within the same
block**. That promise is what the acceptance procedure exists to make true.

## Block identifiers

Short, stable, and not descriptive of the parts: `block-a`, `block-b`. A block
named after its compute module becomes misleading the moment that module is
substituted, and the identifier is permanent.

## What the block README must state

1. **Qualification status.** One of:
   - `CANDIDATE` - proposed, nothing built or measured.
   - `IN QUALIFICATION` - a node exists, the acceptance procedure is being run.
   - `QUALIFIED` - a node has passed the acceptance procedure, which is a
     written repeatable document, not a single successful build.
   - `SUPERSEDED` - replaced by a later block. Retained; nodes in the field
     still belong to it.
   - `RETIRED` - no longer buildable, usually because parts are unobtainable.
2. **What requalification a substitution demands.** Component by component, or
   by class. This is the section that gets skipped and the section that matters
   when a part goes end-of-life. Where the README does not say, a reader must
   assume full requalification.
3. **Which region profiles this block is valid under.** A block whose radio
   module is approved in one region is not automatically valid in another. See
   `regions/`.
4. **Which trades this block's qualification closed**, and which remain open
   for it.
5. **Known limitations**, plainly. Every block has some.

## Directory contents

| Directory | Contents |
| --- | --- |
| `bom/` | Bill of material: exact part numbers, sources, quantities, archived datasheets. |
| `mechanical/` | Enclosure, mounting, cable routing. Native CAD source **and** a rendered PDF or PNG. |
| `rf/` | Antennas, gains, placement, module approval identifiers, integration conditions. |
| `power/` | Pack, charging, distribution, protection, fusing. |
| `assembly/` | Build guide, and `BUILD-ACCEPTANCE.md` for a first-time builder. |
| `acceptance/` | The procedure that qualifies a built node as a member of this block. |

Every directory keeps its `README.md`. A directory with no README is a
directory whose purpose the next contributor has to guess.

## Rules

- **No invented values.** Unknown is `TBD` with the trade that will decide it.
  Never a plausible-looking current draw, mass, or temperature.
- **Nothing is tested until it is.** `UNVERIFIED` where status is unknown.
- **Archive every datasheet** into `docs/evidence/` when you cite it.
- **CAD and rendered drawings are tracked by Git LFS**; check `.gitattributes`
  before adding a format that is not already listed.
- **Read `SAFETY.md`** before assembling anything, particularly the lithium and
  thermal sections.
- **Read `REGULATORY.md`** before selecting a radio module. Substituting an
  antenna can void a modular approval.

## Disqualifying constraints

A candidate that fails any of these is out, regardless of its other merits.
These are recorded before candidates are evaluated, because holding this line
is much harder once someone has a board they like in front of them.

- No viable kernel path for the HaLow driver. `TBR-LINUX-01`.
- No battery-backed real-time clock. `FML-ADR-042` makes it mandatory.
- No boot medium supporting a known-good path independent of the active root.
  `FML-ADR-041`.
