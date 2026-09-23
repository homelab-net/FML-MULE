# Public front door

This directory is a generated reading of the repository, for GitHub Pages.
It is not evidence. It is not a node. It does not select hardware.

The pages repeat CONOPS v1.01 and the decision register in shorter words,
and they label what is still `UNVERIFIED` or only `SIMULATED`. If a sentence
here disagrees with `docs/conops/` or with `STATUS.md`, those win.

## What the pictures are

`media/concept-node.jpg` is a study still of an unlabeled enclosure and spare
antennas. No enclosure, antenna, battery, or compute module is selected.

`media/canyon-conops.jpg` places the CONOPS section 77 deployment in a canyon:
three identical nodes, HaLow via the ridge team, an assumed direct LoRa path.
It is not a propagation study and not a field trace.

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
