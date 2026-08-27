# Permitted modules - region template

Replace this file with the region's permitted module list.

**Status: `TBD`.** No module has been qualified for any region. See
`TBR-HW-01`.

## What to write

| Module | Manufacturer | Bearer | Approval identifier | Antenna | Max gain | Datasheet | Status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `TBD` | `TBD` | `TBD` | `TBD` | `TBD` | `TBD` | `TBD` | `UNVERIFIED` |

For each module record:

- The **approval identifier** issued by the region's regulator, exactly as
  printed. Not "certified", not "FCC approved": the identifier.
- The **antenna** the approval was granted with, or the antenna class it
  permits, and the **maximum gain**.
- The **integration conditions** attached to the approval: shielding, ground
  plane, separation distance from a user, labelling.
- A path to the **archived datasheet** under `docs/evidence/`. Archive it when
  you cite it. Vendors delete PDFs, and this program has already had a key
  module reach end of life before purchase.
- The module's **lifecycle status**, cross-referenced to
  `hardware/lifecycle/`.

## Why the approval detail matters

Modular approval is granted against a specific test configuration. Substituting
an antenna can void it. A higher-gain antenna raises radiated power; an antenna
of a different type may fall outside the permitted class. "It has the same
connector" is not a compliance argument.

Compliance of the **assembled device** remains the builder's responsibility.
Combining several individually approved modules in one enclosure does not
automatically produce a compliant device. See `REGULATORY.md`.

## Modules known to be unavailable

Record modules that were considered and are end-of-life, unobtainable, or
withdrawn, with the date. A future contributor should not have to rediscover
that a part cannot be bought.
