# Image build

The image build produces the deployable artifact: a bootable root filesystem
containing the compatibility set defined in `os/kernel/PINS.md` and
`manifest/`.

**Nothing here builds yet.** There is no build definition, because the kernel
question in `TBR-LINUX-01` decides how the kernel enters the image, and that
decision changes the pipeline's shape rather than one of its steps.

## Intended pipeline

Each property below is a requirement on the build, and each has a reason that
is specific to this program rather than general good practice.

### Reproducible build from pinned manifests

The same inputs produce the same output. Package versions come from
`manifest/`, kernel and driver versions from `os/kernel/PINS.md`, and nothing
is resolved at build time.

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

Pinned package manifests. `packages.list` is present, commented, and
deliberately **empty of packages**: there is no package set, because there is
no selected userland release and no selected kernel.

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

None of this exists yet.
