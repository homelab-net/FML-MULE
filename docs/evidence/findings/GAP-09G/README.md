# GAP-09G evidence

This directory records deployment of the Program Owner-selected v0.0.1 Martin
service.

State: IMPLEMENTED -- the catalog and rootless Quadlet pin Martin 1.16.1,
mount one mission MBTiles file read-only, fail closed when that file is not
readable, and expose the backend only on loopback. Independent review is still
required before this finding can close. AP ingress, operator procedure, and
phone acceptance remain GAP-09E, GAP-09H, and GAP-09I.

| Artifact | What it records |
| --- | --- |
| `2026-09-24-implementation.md` | Image resolution, deployment contract, failing-first test, and the limits of the evidence. |
| `2026-09-27-martin-instantiation.md` | First run of the pinned image on x86 (`SIMULATED`): serves `z/x/y`, fails closed on an absent store, the Quadlet unit generates. Notes the rootless-gate caveat and that the image install (G8) is still owed. |
