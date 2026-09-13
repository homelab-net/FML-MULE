---
id: FML-ADR-079
title: mkosi builds the Debian development image
status: SELECTED PLANNING BASELINE
date: 2026-09-13
supersedes: none
superseded-by: none
trades: [TBR-LINUX-01, TBR-HW-01]
verification: GAP-09B
---

# FML-ADR-079 mkosi builds the Debian development image

## Context

`FML-ADR-022` selects Debian stable, `FML-ADR-040` requires a reproducible
compatibility set, and the root roadmap requires a bootable image for the
development milestone. The repository nevertheless contained only an empty
package manifest and explicitly stated that nothing built an image. The
hand-configured lab system cannot be the build definition because its package,
service, and local-administration history is not reproducible from this tree.

The credible mechanisms were Debian's `mkosi`, `debos`, `live-build`, and
`mmdebstrap`; retaining stock Debian plus Ansible was also considered. Project
N.O.M.A.D. demonstrated the operational risk of mutable image tags and
branch-head downloads. OpenMANET demonstrated the value of exact feed and
configuration inputs, but its OpenWrt image would depart from the selected host
OS and `FML-ADR-023` retains it as reference material only.

The available development article is x86-64 Debian 13, but `TBR-HW-01` and
`TBR-LINUX-01` still own the production compute and compatibility-set choices.
This decision therefore selects a development pipeline, not a production image.

## Decision

The Debian 13 x86-64 development image **shall** be described and built with the
Debian `mkosi` package at exact version `25.3-7`. Build inputs **shall** use one
dated Debian snapshot with repository signature checking enabled. The pipeline
**shall** provide a cache-populating mode and a cache-only mode that instructs
the package manager not to contact the network.

The development artifact **shall** be an uncompressed raw GPT disk image. This
avoids claiming compressed-output reproducibility that mkosi v25.3 does not
establish. Its disk seed and its build-tools distribution, release, and mirror
**shall** be deterministic rather than inherited from the host. Package
selection and package-level provenance remain GAP-09C; this ADR selects the
mechanism that consumes them.

## Status

SELECTED PLANNING BASELINE. `TBR-LINUX-01` may require a different kernel or
board-support path, and `TBR-HW-01` may select a non-x86 production compute
article. Either trade can trigger a replacement image mechanism or architecture
profile without invalidating this development result.

## Consequences

- Image configuration, builder version, repository snapshot, architecture, and
  reproducibility epoch become reviewable source-controlled inputs.
- Contributors can validate the contract without root or hardware. Producing a
  disk still requires the pinned builder, root-capable Linux image facilities,
  the GAP-09C package manifest, and an initially populated package cache.
- The image is not derived from the working lab system, so undocumented local
  state cannot silently enter the artifact.
- A dated snapshot does not receive later security fixes automatically. Every
  update is an explicit candidate-set change and must be reviewed and rebuilt.
- No password, key, certificate, host identity, or mission data is baked into
  the base image.

## Accepted cost

Debian 13 carries mkosi 25.3 while upstream has newer releases. Selecting the
distribution package favours a builder maintained with the selected OS over
newer upstream behavior. It also makes the first cache population a networked
operation; offline rebuildability begins only after the exact packages have
been retained. GAP-09C must measure and preserve that package closure.

## Fallback

Reversible by a superseding ADR. `debos` is the first fallback for a Debian raw
disk pipeline; `live-build` is the fallback if a live/install medium becomes the
required artifact. Take the fallback if the pinned mkosi package cannot build
the selected kernel or board profile, cannot rebuild from the retained package
cache, or cannot produce a bootable artifact on the approved build host.

## Superseded by

None.

## Verification dependency

GAP-09B validates the exact builder and snapshot contract and exercises the
cache-only invocation path against fakes. GAP-09C must then populate the exact
package closure, build twice, rebuild with network access unavailable, compare
the declared image identities, and boot the artifact in a virtual machine.
`TBR-LINUX-01` and `TBR-HW-01` retain production and hardware verification.
