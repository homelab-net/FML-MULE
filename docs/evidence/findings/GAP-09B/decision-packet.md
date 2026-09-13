# GAP-09B decision packet

## 1. Decision requested

Select the mechanism that describes and builds the Debian 13 x86-64
development image for the `v0.0.1` vertical slice. This does not select the
GAP-09C package set or a production compute block.

## 2. Governing constraints

- `FML-ADR-022` selects Debian stable.
- `FML-ADR-040` requires exact compatibility-set inputs and promotion as one
  set.
- `FML-ADR-041` requires a later known-good boot path but does not select its
  mechanism.
- GAP-09A selects the existing Intel N150 system for development use only.
- The root roadmap requires a bootable image built by following this repository
  alone.
- Project N.O.M.A.D. and OpenMANET prior art prohibit floating build inputs and
  favour explicit configuration, but neither whole-system image is adopted.

## 3. Options compared

| Option | Strength | Limitation |
| --- | --- | --- |
| Debian mkosi 25.3-7 | Native Debian package; raw GPT, boot, architecture, snapshot, and cache controls in one configuration | Older than current upstream; root-capable Linux build host required |
| debos 1.1.5-1+deb13u1 | Debian-native declarative image actions | More recipe machinery for the same development disk |
| live-build 1:20250505+deb13u1 | Mature Debian live/install-media tooling | Optimized for live/install media rather than the node disk required now |
| mmdebstrap 1.5.7-1+deb13u1 | Small, auditable Debian root bootstrap | Requires a separate partition, bootloader, and output pipeline |
| Installed Debian plus Ansible | Lowest initial setup cost | Produces no boot artifact and retains undocumented machine drift |
| OpenMANET firmware | Strong board/feed pinning lessons | Replaces Debian with OpenWrt and conflicts with the selected OS direction |

## 4. Evidence

Read-only package inventory on the selected Debian 13 development article
reported mkosi `25.3-7`, debos `1.1.5-1+deb13u1`, live-build
`1:20250505+deb13u1`, and mmdebstrap `1.5.7-1+deb13u1`. The pinned mkosi v25.3
manual and Debian backend expose raw GPT output, Debian and architecture
selection, bootloader integration, package caching, cache-only mode, repository
key checks, and source-date epoch. The Debian package and upstream Git objects
are recorded in `os/image/build-inputs.yml` and `docs/prior-art/mkosi.md`.

## 5. Recommendation

Retain Debian 13 and use Debian's mkosi `25.3-7` package for the x86-64
development image. Use an uncompressed raw GPT output, a single dated Debian
snapshot, explicit repository-key checking, and separate cache-populating and
cache-only invocations.

## 6. Consequences and risks

The source tree becomes the image definition and can reject a live mirror,
floating builder version, unsigned source, or host-derived architecture. The
cost is dependence on an older distro-carried mkosi and on root-capable Linux
image facilities. The initial cache population still requires a network, and a
dated snapshot does not receive security fixes automatically. Package closure,
licenses, SBOM, target-side apt source cleanup, two-build identity, and VM boot
remain GAP-09C work. mkosi v25.3's generated target sources can still contain
live Debian debug and security URLs even though the build itself is constrained
to the snapshot. Enabling the pinned tools tree also creates a separate package
closure that GAP-09C must enumerate and retain.

## 7. Verification and rollback

The repository validator compares the mkosi file with its governed input file;
tests corrupt the mirror, key check, and builder version and require rejection.
The build wrapper exposes a rootless `--check`, refuses an empty package
manifest, authenticates the installed Debian package version, and uses
`CacheOnly=always` for the offline path. A superseding ADR can replace mkosi;
debos is the first fallback if the selected mechanism cannot build the later
kernel or board profile.

## 8. Owner disposition

Approved. In the Codex thread on 2026-09-12, the Program Owner explicitly
approved retaining Debian 13 and using Debian's mkosi `25.3-7` package for
GAP-09B.
