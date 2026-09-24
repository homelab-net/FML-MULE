# Public front door

This directory is a generated reading of the repository, for GitHub Pages.
It is not evidence. It is not a node. It does not select hardware.

The pages were generated against CONOPS v1.01 and have not been regenerated
for v1.1. The generator is not in this repository, so the bundled pages were
not rewritten. If a sentence here disagrees with `docs/conops/` or with
`STATUS.md`, those win.

Two captions on the architecture page are the stale ones:

- "WAN stops at the node."
- "Cloud, past the gate: Terminates on the node. Phones do not join it."

The controlling distinction, CONOPS v1.1 section 43 and `FML-ADR-082`, is:

- Authorized MULEs may use the WAN overlay for approved inter-MULE traffic.
  That is routed overlay connectivity. It does not extend the RF mesh.
- The default is that an EUD does not join the overlay.
- An administrator may select assigned-MULE-only remote continuity. That EUD
  reaches only its assigned MULE's remote-EUD ingress. That is not the
  normal path, and local operation does not require it.

## What the pictures are

`media/concept-node.jpg` is a study still of an unlabeled enclosure and spare
antennas. The picture is not a selected enclosure. The Gate-1 list names a
Compute Module 4, radio modules, and a USB-C bench sink. The high-rate radio
is buy-one-then-verify, the pack is held, and nothing on that list is qualified.

`media/canyon-conops.jpg` places the CONOPS section 77 deployment in a canyon:
three identical nodes, HaLow via the ridge team, an assumed direct LoRa path.
It is not a propagation study and not a field trace.

## Layout

`architecture`, `prototypes`, `status`, and `why` are the other pages. Each is
a directory with an `index.html`, so the address has no file name. `assets`
holds the bundled scripts and styles those pages load. `media` holds the two
pictures named above.

## How it is published

`.github/workflows/pages.yml` uploads this directory. It does not build an
image and it does not run a radio. The site is served from `/FML-MULE/`,
which is the project-pages prefix. A green deploy means the files were copied.

Pages has to be set to deploy from GitHub Actions. That setting is in the
repository settings, and this workflow does not turn it on by itself.

## Regeneration

The generator is not part of this repository's toolchain. Do not treat the
bundled scripts as a source you edit by hand. Change the design record first,
then replace this directory in a pull request that says what moved.
