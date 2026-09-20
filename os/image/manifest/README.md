# Pinned manifests

Machine-readable pins for everything that goes into the image.

| File | Contents |
| --- | --- |
| `direct-packages.list` | Eight owner-approved target package roles. |
| `target-lock.json` | Generated exact target dependency closure and provenance. |
| `packages.list` | Generated exact target package specifications consumed by mkosi. |
| `tools-tree-direct-packages.list` | Package intent captured from pinned mkosi plus `debsbom` and its required CycloneDX runtime. |
| `tools-tree-lock.json` | Generated exact build-tools dependency closure and provenance. |
| `tools-tree-packages.list` | Generated exact tools-tree specifications consumed by mkosi. |

The human-readable summary of the compatibility set lives in
`os/kernel/PINS.md`. Both describe the same set, and a mismatch between them is
a defect. The split is deliberate: `PINS.md` is what a person reads to
understand a set, and the files here are what a build consumes.

`FML-ADR-081` selects the minimum Debian 13 x86-64 development package
foundation. The target lock contains 97 packages and the separate build-tools
lock contains 440 packages at the `20260912T000000Z` snapshot boundary. These
are resolver results, not proof that an image was built or that its installed
set matched. Production compatibility remains `TBR-LINUX-01`.

## The pinning rule

Every package is pinned to an exact version. No ranges, no "latest", no
unpinned transitive dependency. A package that cannot be pinned does not go in
the image.

A change to any pin creates a new candidate set that must pass the promotion
gate in `os/release/README.md`.

`tools/resolve-image-packages.py` regenerates the two locks and their package
lists only after APT authenticates the same-time Debian main, security, and
builder-only backports metadata. It requires a separately supplied Debian
archive keyring and never downloads trust roots itself.
