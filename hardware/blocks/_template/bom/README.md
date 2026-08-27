# Bill of material

Every part needed to build one node of this block.

**Status: `TBD`. No parts selected.** See `TBR-HW-01`.

## What a bill of material row records

| Field | Notes |
| --- | --- |
| Reference | A stable label used by the assembly guide and the wiring diagram. |
| Part number | The manufacturer's, exactly, including revision or variant suffix. |
| Manufacturer | Not the distributor. |
| Description | One line, so a reader knows what it is without a search. |
| Quantity | Per node. |
| Source | Where the program actually buys it, with a link. |
| Approximate cost | With the date and currency. Costs age; undated costs mislead. |
| Datasheet | A path under `docs/evidence/`, not a vendor URL. |
| Lifecycle | Cross-reference to `hardware/lifecycle/`. |
| Notes | Substitution constraints, handling requirements, long lead time. |

## Rules

- **Exact part numbers.** A module whose RF front end changed between
  revisions is a different part for this program's purposes, whatever the
  vendor calls it.
- **Archive the datasheet** into `docs/evidence/` when the part is selected.
  Vendors delete PDFs and this program has already lost a module to end of life
  before purchase.
- **Register every part** in `hardware/lifecycle/`.
- **Mark single-source parts** as a risk, not as a neutral fact.
- **Date every cost.** An undated price is worse than none.
- **No invented values.** No estimated cost, mass, or current draw that has not
  been read from a datasheet or measured.

## Consumables and tools

Keep a separate list of what a builder needs but does not become part of the
node: wire, heat-shrink, thread-lock, and the tools the assembly guide assumes.
A build guide that assumes a spot welder without saying so has failed a
first-time builder before they start.

## Structure

Machine-readable is preferred once there is anything to record; a CSV that a
tool can check against the lifecycle register beats a table only a human reads.
The format is `TBD` and will be settled when the first real bill of material
lands.
