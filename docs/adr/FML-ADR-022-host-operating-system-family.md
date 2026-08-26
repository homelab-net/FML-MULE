---
id: FML-ADR-022
title: Host operating system family
status: SELECTED
date: TBD
supersedes: none
superseded-by: none
trades: [TBR-LINUX-01, TBR-HW-01]
verification: TBD
---

# FML-ADR-022 Host operating system family

This is a stub. The **system architecture description is the source of
rationale**; see `docs/architecture/README.md`.

## Context

The appliance needs a general-purpose Linux userland with long-lived package
availability, broad hardware support, wide contributor familiarity, and
container tooling. Alternatives considered included a build-system-generated
image with no package manager on the device, and a non-Debian general-purpose
distribution.

The program also has to be buildable by makers who are not embedded Linux
specialists.

## Decision

The MULE host **shall** run a Debian-family userland.

The specific distribution and release within that family are `TBD`. The
**kernel tree is explicitly not decided by this ADR**; see below.

## Status

`SELECTED`, with the kernel-tree question open.

This is the userland half of the two-layer split that governs `os/`. The
userland is portable and is expected to move between compute modules with
configuration changes only. The kernel and board support package are
hardware-specific and may require vendor patches. Whether a stock kernel
suffices for the Wi-Fi HaLow driver path or whether a patched vendor tree is
required is open: `TBR-LINUX-01`. If a patch set turns out to be required, it
constitutes a maintained fork with an owner and a rebase strategy, registered
under `docs/forks/`.

## Consequences

- Package pinning and reproducible builds work against a well-understood
  archive format. See `os/image/manifest/`.
- Contributors can reproduce most of the userland on an ordinary laptop.
- A Debian-family userland does not constrain the kernel, so the program can
  carry a vendor kernel beneath a portable userland if `TBR-LINUX-01` forces
  it. That is the reason the split is drawn here rather than at the image.
- Long-lived releases lag on wireless subsystem work, which is exactly the
  subsystem this program depends on most. This tension is `TBR-LINUX-01`'s
  problem to resolve.

## Accepted cost

The program accepts a larger installed footprint and a longer boot than a
purpose-built image would need, in exchange for maintainability by volunteers
and for the ability to change compute modules without rebuilding the userland
story. It also accepts that a general-purpose distribution's security update
cadence is not aligned with the compatibility-set promotion rule in
`FML-ADR-040`, and that reconciling the two is ongoing work.

## Fallback

Changing distribution within the Debian family is a moderate cost, largely in
the Ansible roles and the image manifest. Leaving the Debian family entirely
would supersede this ADR and would invalidate most of `os/`.

## Superseded by

None.

## Verification dependency

`TBD`. Depends on `TBR-LINUX-01`. Minimally, a candidate image must rebuild all
out-of-tree modules and enumerate every radio, which is the first gate in
`os/release/README.md`.
