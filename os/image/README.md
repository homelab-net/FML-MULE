# Image build

The image build produces the deployable artifact: a bootable root filesystem
containing the compatibility set defined in `os/kernel/PINS.md` and
`manifest/`.

`FML-ADR-079` selects Debian mkosi `25.3-7` for the Debian 13 x86-64
development image. `FML-ADR-081` selects its package and CycloneDX provenance
boundary. `build-inputs.yml` governs the builder, snapshot, package, and SBOM
policy; `mkosi.conf` describes the raw GPT output; and
`tools/build-image.sh --check` validates them without root.

The exact resolver inputs now contain a 97-package target closure and a
separate 414-package mkosi tools-tree closure. No image has yet been built,
compared, or booted, so those locks remain build inputs rather than accepted
installed-root evidence. The production kernel and board-support path remain
open under `TBR-LINUX-01` and `TBR-HW-01`.

## Intended pipeline

Each property below is a requirement on the build, and each has a reason that
is specific to this program rather than general good practice.

### Reproducible build from pinned manifests

The intended contract is that the same retained inputs produce the same output.
The builder, repositories, target closure, and tools-tree closure are pinned.
Package versions come from `manifest/`, kernel and driver versions from
`os/kernel/PINS.md`, and nothing may resolve from a live source at build time.
GAP-09C must still exercise the closure and compare the artifacts before the
claim is earned.

*Why:* because a node in the field is diagnosed by its set version. If two
builds of the same set version differ, that identifier means nothing, and the
compatibility-set rule in `FML-ADR-040` has no teeth.

### Hashed output

Every artifact carries a content hash, recorded alongside it.

*Why:* so a node can report what it is running, and so a builder can confirm
they have the artifact they think they have.

### Signed artifacts

Images are signed as part of the release process. See `os/release/README.md`.

*Why:* the update path is the most valuable thing to compromise on a fleet of
nodes. It is also the only remote code execution path the design deliberately
provides.

### A/B slot deployment

The image is deployed into one of two root slots, with the other retained as
the bootable known-good path. See `FML-ADR-041`; the **mechanism** is
`TBR-REC-01` and A/B slots are one candidate, not a decision.

*Why:* a bad promotion fails everything at once, because the whole
compatibility set moves together. A volunteer must be able to recover a node
without disassembly and without a host computer.

### Buildable on a constrained connection

Prefer vendored or cached dependencies. It must be possible to build twice
without downloading twice.

*Why:* builders will have poor connectivity, some of them for the same reason
the equipment exists. See `os/README.md`.

## `manifest/`

Pinned package manifests separate human-reviewed direct intent from generated
exact target and tools-tree closures. See `manifest/README.md` for each file.
The development kernel meta-package is selected for this x86-64 article only;
`TBR-LINUX-01` still owns the production compatibility set.

The pinning rule is in the file's header comment and is repeated here because
it is the rule most likely to be broken by someone in a hurry:

> Every package is pinned to an exact version. No version ranges, no "latest",
> no unpinned transitive dependency. A package that cannot be pinned does not
> go in the image.

## Relationship to Ansible

The image build produces a base artifact. `os/ansible/` provisions
configuration on top of it. The boundary between the two is `TBD`, and it is a
real decision rather than an implementation detail: configuration baked into
the image is reproducible and requires a promotion to change; configuration
applied by Ansible is flexible and is state that can drift.

The program's bias is toward baking, because drift is invisible and a node that
differs from its set version is undiagnosable. Where that bias is not followed,
the reason belongs in the role.

## What a build must produce

- The root filesystem image, hashed.
- A manifest of exactly what went in, including the compatibility set version.
- An SBOM. See `os/release/SBOM.md`.
- A build log, retained.

The source-controlled mechanism and requested-output contract now exist. No
artifact, SBOM, retained build log, signature, or boot evidence exists yet.

## Package-manager sandboxes and build scripts

`sandbox-target/etc/apt/sources.list.d/mkosi.sources` supplies only the dated
main and security archives. `sandbox-tools/etc/apt/sources.list.d/mkosi.sources`
adds same-time backports for the pinned build-only `debsbom` package. These
trees configure mkosi's package-manager sandboxes and are not copied into the
target.

`mkosi.postinst` removes bootstrap-only `apt` and every target repository file.
`mkosi.finalize` generates CycloneDX and licence-exception outputs from the
completed root, validates the installed set against `target-lock.json`, then
removes the APT metadata used for that scan. Both scripts reject an invalid
build-root path before altering it.

`tools/resolve-mkosi-builder.sh` authenticates the exact Debian package archive
and returns its package-owned executable. Both image construction and QEMU boot
use that absolute path, so a different `mkosi` earlier on `PATH` cannot enter
the evidence chain.

## Commands

```sh
tools/build-image.sh --check
sudo tools/build-image.sh --populate-cache
sudo tools/build-image.sh --offline
sudo tools/verify-image-reproducibility.sh
```

The first command is safe on a contributor machine. The other modes require the
pinned Debian builder and root-capable Linux image facilities. `--offline`
combines mkosi cache-only mode with a new network namespace, so an unavailable
external network is demonstrated rather than inferred from configuration.
Set `FML_MKOSI_PACKAGE_DEB` to the retained `mkosi_25.3-7_all.deb` path when it
is not in APT's archive cache. The reproducibility command creates two fresh
networked output/cache pairs, then gives one authenticated populated cache to a
fresh network-isolated output. `FML_IMAGE_OUTPUT_DIR` and
`FML_IMAGE_PACKAGE_CACHE` are internal orchestration overrides used to keep
those three build states separate.
