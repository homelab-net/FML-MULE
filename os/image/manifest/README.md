# Pinned manifests

Machine-readable pins for everything that goes into the image.

| File | Contents |
| --- | --- |
| `packages.list` | Userland packages, exact versions. Currently empty. |

The human-readable summary of the compatibility set lives in
`os/kernel/PINS.md`. Both describe the same set, and a mismatch between them is
a defect. The split is deliberate: `PINS.md` is what a person reads to
understand a set, and the files here are what a build consumes.

**Nothing is pinned.** No userland release, no kernel, and no package set has
been selected. See `TBR-LINUX-01` and `FML-ADR-022`.

## The pinning rule

Every package is pinned to an exact version. No ranges, no "latest", no
unpinned transitive dependency. A package that cannot be pinned does not go in
the image.

A change to any pin creates a new candidate set that must pass the promotion
gate in `os/release/README.md`.
