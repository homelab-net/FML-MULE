# GAP-09C decision packet

## 1. Decisions requested

Approve all three parts of the Debian 13 x86-64 development-image package and
provenance boundary:

1. Start with the minimum boot foundation listed below. Do not preselect the
   runtime, access-point, ingress, or service packages owned by GAP-09D through
   GAP-09G.
2. Resolve target and builder packages from authenticated Debian `trixie`,
   `trixie-security`, and builder-only `trixie-backports` metadata captured at
   the `20260912T000000Z` snapshot boundary. Never use a live security feed.
3. Generate a CycloneDX JSON SBOM from each built filesystem with Debian's
   `debsbom`, including declared licence data. Keep `debsbom` in the build
   environment, not in the target image.

Approval authorizes implementation and verification of this development-image
baseline only. It does not select a production kernel, hardware block, service,
network design, runtime entry point, image-signing key, or rollback mechanism.

## 2. Governing constraints

- `FML-ADR-022` selects Debian stable.
- `FML-ADR-040` requires the kernel and required userspace to be versioned and
  promoted as one compatibility set.
- `FML-ADR-079` selects Debian mkosi `25.3-7`, the x86-64 development image,
  and the `20260912T000000Z` snapshot boundary.
- GAP-09C requires exact package versions and sources, an SBOM, licence and
  signature checks, and freedom from floating branch heads and image tags.
- Package installation belongs in the image, not in Ansible. The target must
  not depend on package installation after deployment.
- GAP-09D through GAP-09G retain their separate owner gates. A package included
  now must be necessary to boot and inspect the base image, not merely expected
  to become useful later.

## 3. Package-scope options

| Option | Advantage | Defect or cost |
| --- | --- | --- |
| Minimum boot foundation | Proves the image path without deciding downstream runtime, AP, ingress, or service details | Later approved capabilities create new candidate package locks |
| Entire `v0.0.1` stack now | Could reduce the number of image rebuilds | Pre-decides GAP-09D through GAP-09G before their required owner gates |
| Debian standard system task | Familiar interactive host | Large implicit package set with no MULE requirement for much of it |
| Clone the working lab installation | Matches one currently working machine | Reproduces undocumented mutable state rather than the repository |

The recommendation is the minimum boot foundation.

## 4. Recommended direct target packages

| Package | Why it is direct rather than merely transitive |
| --- | --- |
| `dbus` | Supplies the system bus that systemd services expect when recommended packages are disabled. |
| `initramfs-tools` | Makes the selected initramfs implementation explicit instead of accepting either provider of the kernel package's virtual dependency. |
| `linux-image-amd64` | Selects the Debian kernel meta-package for the approved x86-64 development article only. |
| `systemd` | Supplies the selected service manager and boot userspace. |
| `systemd-boot` | Supplies Debian's systemd-boot integration and services. |
| `systemd-boot-efi` | Makes the UEFI binary payload required by mkosi's bootloader choice explicit. |
| `systemd-sysv` | Installs the init-system compatibility links; Debian states that `systemd` alone does not switch the init system. |
| `udev` | Supplies device discovery and hotplug for a booted hardware-development article. |

Every direct package and every transitive package will be locked to the exact
version, architecture, source package, archive suite, package filename, and
SHA-256 recorded in the authenticated snapshot metadata. The table approves
package roles, not whichever versions happen to be live when implementation
runs.

The target intentionally excludes `apt`. mkosi uses the build environment's
package manager to populate the filesystem; the deployed image has no reason to
install packages. Absence of target-side `apt` also removes the live debug and
security source files that mkosi `25.3` otherwise writes. The built filesystem
will be checked for both the package and repository files rather than trusting
the input list.

The target also excludes Python, Podman, hostapd, dnsmasq, HAProxy, nftables,
and radio utilities at this gate. Existing decisions may make some likely, but
their installation and behavior belong to later approved child tasks.

## 5. Lock and archive policy

Use a reviewed direct-package input and generated lock artifacts rather than
asking one file to be both human intent and package-manager output:

- The target intent lists only the eight approved direct packages.
- The target lock lists the complete exact closure that mkosi must install.
- A separate tools-tree lock records the complete exact closure of mkosi's
  built-in Debian tools tree. That tree is much larger than the target and must
  not be mistaken for deployed software.
- The retained package cache contains every referenced `.deb`; an offline build
  may read only that cache.
- The post-build installed set must equal the target lock exactly. An extra,
  missing, substituted, or differently versioned package fails the build.

The initial resolver uses three signed suites at one time boundary:

- `trixie` from `archive/debian` for the stable base;
- `trixie-security` from `archive/debian-security` so the frozen image does not
  omit security updates that Debian publishes separately; and
- `trixie-backports` from `archive/debian` only for the pinned build-time
  `debsbom` package.

The target lock may draw from the first two. No backports package may enter the
target. The build records and verifies each signed `InRelease`, the
Release-to-Packages checksum, and the Packages-to-`.deb` SHA-256 chain. A live
mirror, unsigned repository, floating suite, or unrecorded package is rejected.

## 6. SBOM options

| Option | Advantage | Defect or cost |
| --- | --- | --- |
| Debian `debsbom`, CycloneDX JSON | Reads the built root, works offline, includes binary and source packages, dependency edges, checksums, and declared licences | Tool is in `trixie-backports`; CycloneDX identifies source packages through their package URLs rather than a dedicated purpose field |
| Debian `debsbom`, SPDX JSON | Expresses binary/source purpose directly | The required SPDX Python library is not available in Debian 13 stable |
| mkosi JSON manifest alone | Already generated by the selected builder | Not a standard SBOM and does not provide the required licence result |
| Syft | Broad ecosystem and SPDX/CycloneDX support | Adds a non-Debian binary supply chain and is less specific to Debian source-package relationships |
| New repository generator | Full local control | Creates avoidable original provenance software and a permanent maintenance burden |

The recommendation is a pinned Debian `debsbom` package producing CycloneDX
JSON from the mounted built filesystem. Its documented `generate` path reads
the target's dpkg status, apt metadata, and copyright files, operates offline,
and accepts an alternate root. It remains a build tool and is never installed
in the target.

`debsbom` conservatively omits a licence expression it cannot identify. Closure
therefore requires two outputs: the CycloneDX SBOM with declared licences, and a
machine-readable exception report naming every installed package for which no
SPDX-normalized declared licence was produced. Every exception must still have
its Debian copyright file retained and must be reviewed before GAP-09C closes.
No missing copyright file may pass.

## 7. Verification contract

Implementation must prove all of the following:

1. Corrupting each archive signature or any link in the checksum chain fails.
2. Omitting, adding, or changing any direct, transitive, or tools-tree package
   fails before the result is accepted.
3. No package comes from a live source, backports never enters the target, and
   the final target contains neither `apt` nor an apt source file.
4. The SBOM is generated from the built filesystem, covers the installed lock,
   includes source-package relationships, and reports licence exceptions.
5. Two clean networked builds and one cache-only build consume the same locks
   and produce identical raw-image SHA-256 values. If they do not, stop and
   report the differing bytes or metadata; do not weaken the identity claim.
6. The cache-only build runs with external network access unavailable, not only
   with a package-manager flag set.
7. The resulting image boots under QEMU/OVMF without WAN and reaches the named
   systemd target. This is `SIMULATED` evidence and says nothing about physical
   hardware.
8. The full repository gate passes with no skipped tools, and an independent
   reviewer authenticates the exact implementation commit.

## 8. Sources reviewed

- Pinned mkosi `25.3` manual and implementation at commit
  `54c625c380ef5500f17460981a3c67b109b6a847`.
- Debian package metadata for `linux-image-amd64`, `systemd`,
  `systemd-boot-efi`, and `initramfs-tools`.
- Debian Sources package metadata and copyright service.
- `debsbom` documentation for alternate-root, offline generation, package and
  source relationships, checksums, and declared-licence behavior.
- `debsbom` upstream repository for maintenance, licence, signed-release, and
  limitation information.

## 9. Owner disposition

Approved. The Program Owner approved the minimum target package set, same-time
main/security archive policy, builder-only backports, and CycloneDX `debsbom`
choice in the Codex thread on 2026-09-14.
