# Hardware blocks

One directory per qualified hardware block.

A **block** is a whole qualified configuration, not a compute module: compute,
carrier or wiring, radios, antennas, pack, enclosure, and the acceptance
procedure that says a built node is a member of it.

**No block is qualified.** `block-a` is a named placeholder with no parts
selected. See `TBR-HW-01`.

## Why there is a directory per block rather than one design

The program promises that **a spare node replaces any node within the same
block**, and expects blocks to change as components reach end of life. Both at
once means the repository must hold **more than one qualified configuration
simultaneously**, and must have been able to from the start.

Retrofitting multi-block support onto a repository that assumed a single
configuration is a large, tedious change, and it always becomes necessary at the
worst moment: when the current parts stop being available. This program has
already had a key module reach end of life before it could be purchased.

## Contents

| Directory | State |
| --- | --- |
| `_template/` | Copy this to start a block. Complete enough to copy. |
| `block-a/` | First candidate block. `CANDIDATE`, contents `TBD`. |

## Starting a block

Copy `_template/` to `hardware/blocks/<block-id>/`. Identifiers are short,
stable, and deliberately say nothing about the parts: a block named after its
compute module becomes misleading the moment that module is substituted, and the
identifier is permanent.

Each block's README states its **qualification status** and **what
requalification a substitution demands**. Where it does not say, a reader must
assume full requalification.

Material shared across blocks goes in `hardware/common/`, and only once it has
been shown to be block-independent across at least two blocks. See
`hardware/README.md`.
