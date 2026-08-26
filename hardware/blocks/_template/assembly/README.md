# Assembly

The build guide for this block, and the acceptance criterion that says whether
the build guide works.

**Status: `TBD`. No block is selected and no build guide exists.** See
`TBR-HW-01`.

## The acceptance criterion for a build guide

> **A build guide is not considered complete until someone other than its
> author has followed it successfully.**

Not reviewed. Not read. **Followed, to a working node, by a different person.**

Every hardware project believes its instructions are complete. None are. An
author cannot see the steps they perform without noticing, and those invisible
steps are exactly where a first-time builder stops.

`BUILD-ACCEPTANCE.md` in this directory is the checklist that first builder
works through, with space to record where they got stuck. Every point where
they got stuck is a defect in the guide, and it is filed as an issue.

## What the build guide must contain

- **Tools and consumables required**, before step one. A guide that assumes a
  spot welder without saying so has already failed.
- **Skills assumed**, honestly. Soldering, crimping, basic RF handling.
- **Estimated time**, from the second builder's actual measurement, not the
  author's.
- **Steps in the order they are performed**, each with what "done correctly"
  looks like. A photograph where words will not do.
- **The checks performed as you go**, particularly polarity, before first
  power-on, with a meter, every time.
- **What to do when a step goes wrong.**
- **Safety warnings in line, at the step they apply to**, not collected in a
  preamble nobody rereads. See `SAFETY.md`.

## Photographs

Photographs belong here where words are insufficient, and they are tracked by
Git LFS. Strip metadata before committing: a photograph carries GPS coordinates
and a timestamp, and the publication rule in `SECURITY.md` covers deployment
locations.
