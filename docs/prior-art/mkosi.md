# mkosi image builder

**Evaluated:** 2026-09-13. **Selected scope:** Debian package `mkosi`
`25.3-7`, based on upstream v25.3 at commit
`54c625c380ef5500f17460981a3c67b109b6a847`, for the GAP-09B development
image only. Program Owner approval was recorded in the Codex thread on
2026-09-12.

## Fit

mkosi directly produces raw GPT disk images using distribution package
managers and `systemd-repart`. Its v25.3 configuration can name Debian, the
release, target architecture, mirror, output format, bootability, bootloader,
package cache, cache-only behavior, and a source-date epoch. That matches the
source-controlled build boundary required by `FML-ADR-040` without replacing
Debian, the kernel, the package manager, systemd, or the later release gate.

The selected Debian package is version `25.3-7`, whose package index reports
SHA-256
`ef56c81324fd47d65490e944ec4697bb3f6fb21326d0d071bfc2fb5ba5383252`.
The upstream v25.3 tag resolves to commit
`54c625c380ef5500f17460981a3c67b109b6a847`; the signed annotated tag object is
`a31ed1fc8c6901ae3ee40d458761e261adca835e`. The Debian patch revision remains
part of the selected package artifact and is not represented by the upstream
commit alone.

## Alternatives considered

| Option | Useful property | Disposition |
| --- | --- | --- |
| mkosi 25.3-7 | Direct raw GPT image, Debian support, systemd boot integration, cache-only package-manager mode | Selected for the Debian 13 x86-64 development image |
| debos 1.1.5-1+deb13u1 | Debian-native image recipes with explicit actions | First fallback if mkosi cannot build the selected kernel or board profile |
| live-build 1:20250505+deb13u1 | Mature Debian live/install-media workflow | Retained if the required artifact becomes install media rather than a node disk |
| mmdebstrap 1.5.7-1+deb13u1 | Small Debian root-filesystem bootstrap primitive | Retained as a lower-level component, not selected as the full disk pipeline |
| Stock Debian plus Ansible | Reuses the installed operating system | Rejected as the base-image definition because it does not produce the roadmap's bootable artifact and preserves local drift |
| OpenMANET firmware | Exact OpenWrt feed and board-profile lessons | Reference only under `FML-ADR-023`; adopting it would replace the Debian direction |

Project N.O.M.A.D. is not an image-builder alternative, but its mutable image
tags and branch-head helper downloads are the failure pattern this pipeline
shall avoid. The selected build consumes no mutable branch, tag, or container
image reference.

## Reproducibility and offline boundary

The build configuration uses the dated Debian snapshot
`20260912T000000Z` and explicitly enables repository-key checking.
`FML-ADR-081` replaces the GAP-09B single-`LocalMirror` placeholder with an
mkosi package-manager sandbox containing dated `trixie` and
`trixie-security` sources. A separate tools-tree sandbox adds only same-time
`trixie-backports`. This avoids mkosi v25.3's generated live debug and security
feeds during resolution. Bootstrap `apt` and the target sources it causes
mkosi to write are removed before installed-root validation. The
systemd-repart seed is a UUIDv5 derived from `FML-ADR-079`, and the tools-tree
distribution, release, mirror, package closure, and sandbox are explicit.

The first controlled build may populate `os/image/mkosi.pkgcache/`. A second
build uses mkosi's `CacheOnly=always` behavior, which its pinned manual defines
as instructing the package manager not to contact the network. The wrapper also
enters a network namespace with no external interface. The cache is a local
build artifact and is not committed. GAP-09C has enumerated the candidate
target and tools-tree closures, but it must still generate the SBOM and
demonstrate two clean image builds plus the network-unavailable rebuild before
those resolver outputs become accepted build evidence.

The output remains uncompressed. Upstream did not advertise reproducible gzip
output until a later release, so v25.3 is not credited with that behavior. The
raw image's SHA-256, not a filename or timestamp, is its identity.

## Security, privilege, and license

Building a bootable disk requires root-capable Linux image facilities and
executes the distribution package manager and systemd image tools. mkosi opens
no service port and provides no runtime authentication boundary. Optional mkosi
credential files are not used; no password, SSH key, certificate, machine
identity, or mission material belongs in the base image.

The pinned source declares LGPL-2.1-or-later by default in `REUSE.toml`, with
identified GPL-2.0-only, PSF-2.0, and OFL-1.1 files. These licenses are
compatible with using the separately packaged build tool. `FML-ADR-081`
selects `debsbom` to inventory declared package licences and records every
unrecognized expression as an exception. The GitHub security-advisory
endpoint listed no advisories when reviewed. No independent security audit was
identified.

## Exit strategy

The contract ends at a raw disk plus manifests and hashes. Configuration lives
in standard files rather than custom image code, so a replacement builder can
consume the same Debian snapshot and package manifest. A superseding ADR is
required because the builder is now a selected planning baseline.

## Sources

- [Pinned mkosi v25.3 manual](https://github.com/systemd/mkosi/blob/54c625c380ef5500f17460981a3c67b109b6a847/mkosi/resources/man/mkosi.1.md)
- [Pinned Debian backend](https://github.com/systemd/mkosi/blob/54c625c380ef5500f17460981a3c67b109b6a847/mkosi/distributions/debian.py)
- [Pinned license declarations](https://github.com/systemd/mkosi/blob/54c625c380ef5500f17460981a3c67b109b6a847/REUSE.toml)
- [Debian 13 mkosi package](https://packages.debian.org/trixie/mkosi)
- [Debian snapshot](https://snapshot.debian.org/archive/debian/20260912T000000Z/)
- [mkosi security advisories](https://github.com/systemd/mkosi/security/advisories)
- [Project N.O.M.A.D. evaluation](project-nomad.md)
- [OpenMANET firmware evaluation](openmanet-firmware.md)
