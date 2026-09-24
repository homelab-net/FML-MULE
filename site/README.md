# Public front door

This directory is a generated reading of the repository, for GitHub Pages.
It is not evidence. It is not a node. It does not select hardware.

The pages were generated against CONOPS v1.01. The generator is not in this
repository. On 2026-09-23 the overlay sentences below were edited in the
published HTML and in the matching bundle scripts. That was not a
regeneration. If a sentence here disagrees with `docs/conops/` or with
`STATUS.md`, those win.

The sentences that were replaced, and the files that served them:

| Was | Now | Files |
| --- | --- | --- |
| WAN stops at the node. | Authorized MULEs use the WAN overlay for approved inter-MULE traffic. It does not extend the RF mesh. | `site/architecture/index.html`, `site/assets/architecture-T36uLmQZ.js` |
| Terminates on the node. Phones do not join it. | Approved inter-MULE overlay. An EUD joins only its assigned MULE, and only if the mission selects that. | same two files |
| EUDs do not join the overlay. | An EUD does not join the overlay unless the mission selects assigned-MULE-only. | `site/architecture/index.html`, `site/assets/index-Bx4hxf0x.js` |
| WAN is optional and terminates on the node | WAN is optional. Authorized MULEs may use the overlay | `site/status/index.html`, `site/assets/index-Bx4hxf0x.js` |

The status card's paragraph now also says the overlay does not extend the RF
mesh, and that an admitted EUD stops at its assigned MULE. Local operation
still does not require WAN. The wording follows CONOPS v1.1 section 43 and
`FML-ADR-082`.

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
bundled scripts as a source you edit by hand. The 2026-09-23 overlay sentences
are the exception, and they are listed above. A later regeneration has to
carry those sentences or it will put the old policy back.
