---
id: FML-ADR-081
title: Development image package closure and CycloneDX provenance
status: SELECTED PLANNING BASELINE
date: 2026-09-14
supersedes: none
superseded-by: none
trades: [TBR-LINUX-01, TBR-HW-01]
verification: GAP-09C
---

# FML-ADR-081 Development image package closure and CycloneDX provenance

## Context

`FML-ADR-022` selects Debian stable, `FML-ADR-040` makes the kernel and
userspace one promoted compatibility set, and `FML-ADR-079` selects the
reproducible Debian 13 x86-64 development-image mechanism. That mechanism
deliberately stopped before package selection. An empty package manifest cannot
produce a bootable artifact, while copying the mutable lab installation would
make local history part of the product definition.

The development image needs enough userspace to boot and expose a normal
systemd environment, but selecting packages for runtime, networking, ingress,
or mission services here would bypass the separate GAP-09D through GAP-09G
owner gates. Debian also publishes stable security updates in a distinct
archive, so a dated main archive alone is not the complete package input at a
given time boundary.

The build must retain exact package provenance and generate an SBOM from what
was installed rather than what was requested. `os/release/SBOM.md` requires an
ADR once its format and generator are chosen.

## Decision

The Debian 13 x86-64 development image **shall** begin with these direct target
packages and no application or network-service packages: `dbus`,
`initramfs-tools`, `linux-image-amd64`, `systemd`, `systemd-boot`,
`systemd-boot-efi`, `systemd-sysv`, and `udev`.

The complete target dependency closure **shall** resolve from authenticated
Debian `trixie` and `trixie-security` metadata at the
`20260912T000000Z` snapshot boundary. The target **shall not** contain `apt`, an
APT repository file, or a package from backports. Build-only tooling may resolve
from `trixie-backports` at the same timestamp. Target and tools-tree locks
**shall** record package name, version, architecture, source package, suite,
filename, and SHA-256. Every referenced Debian package **shall** be retained for
a cache-only build.

Each build **shall** generate a CycloneDX JSON SBOM with a pinned Debian
`debsbom` package running in the build environment against the completed target
filesystem. The image **shall not** contain `debsbom`. A machine-readable
licence-exception report **shall** name packages for which no normalized SPDX
expression is produced, and every installed package **shall** retain its Debian
copyright file.

Acceptance **shall** compare the installed package set to the target lock,
authenticate the signed archive-metadata and checksum chain, demonstrate two
clean networked builds plus one build with external network access unavailable,
compare raw-image SHA-256 values, and boot the artifact under QEMU/OVMF without
WAN. This is a development and `SIMULATED` baseline only.

## Status

SELECTED PLANNING BASELINE. The Program Owner approved the package boundary,
same-time archive policy, and CycloneDX generator in the Codex thread on
2026-09-14. `TBR-LINUX-01` or `TBR-HW-01` may require a different production
kernel, architecture, boot chain, or package closure.

## Consequences

- The image can boot without pre-deciding the runtime, AP, ingress, or mission
  service implementation.
- Security updates do not float into a candidate. Moving the snapshot boundary
  creates a new reviewed package closure.
- The reviewed direct-package intent stays small while generated target and
  tools-tree locks expose every transitive package.
- Builders must retain substantially more than the deployed target because the
  mkosi tools tree is a separate Debian filesystem.
- A standard CycloneDX consumer can inventory Debian binary packages; Debian
  source-package relationships and incomplete normalized licence results remain
  explicit review inputs.

## Accepted cost

Omitting `apt` makes the deployed base image intentionally immutable at the
package-manager layer. Even a small target also requires a large separately
locked tools tree and retained package archive. `debsbom` comes from Debian
backports rather than stable, adding a third authenticated build-only suite.

## Fallback

The Program Owner may approve a superseding ADR that replaces `debsbom` if it
cannot describe the completed Debian filesystem without online resolution, or
that adds a package when a demonstrated boot dependency is absent. A package
required only by a later capability remains in that capability's owner gate.
If the three-build identity test fails, retain and diagnose the differing
artifacts; do not weaken the reproducibility requirement.

## Superseded by

None.

## Verification dependency

GAP-09C owns package-resolution, signature and checksum mutation tests,
installed-root validation, SBOM and licence results, cache-only rebuilding,
raw-image identity, and QEMU/OVMF boot evidence. `TBR-LINUX-01` and
`TBR-HW-01` retain production compatibility and physical-device verification.
