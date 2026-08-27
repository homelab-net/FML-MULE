# Component lifecycle and obsolescence register

Components reach end of life, and they do it quietly. A vendor stops
manufacturing, a distributor sells the last of its stock, and the next person
to follow the build guide finds a part that cannot be bought. Nobody is
notified.

**This program has already had a key module reach end of life before it could
be purchased.** That is the reason this register exists early, before there is
anything to put in it.

## Current entries

**None.** No component has been selected for any block. See `TBR-HW-01`.

## What the register tracks

One entry per part that a qualified block depends on:

| Field | Meaning |
| --- | --- |
| Part | Manufacturer part number, exactly. Not a description. |
| Manufacturer | And the distributor the program actually buys from. |
| Used in | Which blocks depend on it. |
| Lifecycle status | Active, not recommended for new designs, last-time-buy, end-of-life, unobtainable. |
| Source of that status | Vendor page, product change notice, distributor stock, or observation. With a date. |
| Last checked | Date. A status with no date is not a status. |
| Substitution | Known alternatives, and what requalification a substitution demands. |
| If it disappears | What the program does. The question that matters. |

## Entry template

```markdown
### <manufacturer part number>

- **Manufacturer:** <name>
- **Distributor:** <where the program buys it>
- **Used in:** <block ids>
- **Function:** <one line: what it does in the design>
- **Lifecycle status:** <status>
- **Status source:** <vendor PCN, product page, distributor stock> retrieved <date>
- **Last checked:** <date>
- **Datasheet:** <path under docs/evidence/>
- **Substitution:** <alternatives, or none known>
- **Requalification on substitution:** <what the block's README demands>
- **If it disappears:** <what the program does>
```

## Practices

- **Archive the datasheet when the part is selected**, not when it is needed
  again. Vendors delete PDFs. See `docs/evidence/README.md`.
- **Record the exact part number**, including the revision or variant suffix. A
  module that changed its RF front end between revisions is a different part
  for this program's purposes even where the vendor says otherwise.
- **Check the register at each cold start drill**, quarterly. It is a cheap
  check and the failure it catches is expensive.
- **A single-source part is a risk**, not a fact to be recorded neutrally. Note
  it as a risk and say what happens if the source goes.
- **A part with no substitution and no plan is a program risk**, and belongs in
  the program risk discussion rather than only in this file.

## Relationship to blocks

The register records status; the **block** decides what a substitution costs.
Each block's README states what requalification a substitution demands, and
this register points at it rather than restating it.

A part going end-of-life is one of the two reasons the repository is built to
hold more than one qualified block at a time. See `hardware/README.md`.
