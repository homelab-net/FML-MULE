---
id: FML-ADR-022
title: Debian stable as production host OS
status: SELECTED
date: 2026-08-25
supersedes: none
superseded-by: none
trades: [TBR-LINUX-01, TBR-HW-01]
verification: Stage 2
---

# FML-ADR-022 Debian stable as production host OS

**Source of rationale:** SAD v0.31 section 3.1. See also sections 3.3, 3.4, 20.2
and 29.

Supersedes the draft-local `AD-002` labels used in SAD v0.1 and v0.2; see SAD
section 0.8.

## Context

The appliance needs a general-purpose Linux userland with long-lived package
availability, broad hardware support, wide contributor familiarity and container
tooling, buildable by makers who are not embedded Linux specialists.

## Decision

The primary MULE compute element **shall** use the current Debian stable release
at build time. At SAD issue, that is **Debian 13.6 "trixie"** (SAD section 3.1,
source `SR-001`).

The production image **shall** use a supported Debian stable kernel and
security-update stream, version-controlled package manifests, controlled kernel
and module configuration, Ansible-managed host configuration, signed or
hash-verified release artifacts, and a field-release freeze before planned
deployments.

The production MULE **shall not** require OpenWrt as its host operating system.

## Status

`SELECTED`, with the kernel-tree question open.

This is the userland half of the two-layer split that governs `os/`. The
userland is portable. The kernel and board support package are hardware-specific
and may require vendor patches.

Whether a stock Debian kernel suffices for the out-of-tree Wi-Fi HaLow driver
path, or a patched vendor tree is required, is `TBR-LINUX-01`. If a patch set is
required it constitutes a maintained fork with a named owner and a rebase
strategy, registered under `docs/forks/`.

## Consequences

- Package pinning and reproducible builds work against a well-understood archive
  format. See `os/image/manifest/`.
- Contributors can reproduce most of the userland on an ordinary laptop.
- The split is drawn at the userland boundary so the program can carry a vendor
  kernel beneath a portable userland if `TBR-LINUX-01` forces it.
- The fleet drops from two general-purpose OS lifecycles to one (SAD section
  20.1).
- A long-lived stable release lags on wireless subsystem work, which is the
  subsystem this program depends on most. `TBR-LINUX-01` resolves that tension.
- Debian's security update cadence is not aligned with the compatibility-set
  promotion rule in `FML-ADR-040`. Reconciling them is ongoing work.

## Accepted cost

The program accepts a larger installed footprint and longer boot than a
purpose-built image would need, in exchange for maintainability by volunteers
and the ability to change compute modules without rebuilding the userland story.

It accepts that a general-purpose distribution's update cadence conflicts with
promoting the compatibility set as a unit, and that this will at some point mean
knowingly running a component with a published vulnerability while the set is
re-qualified.

## Fallback

Changing distribution within the Debian family is a moderate cost, largely in
the Ansible roles and the image manifest. Leaving the Debian family entirely
would supersede this ADR and invalidate most of `os/`.

## Superseded by

None.

## Verification dependency

Stage 2. SAD section 30.1 records the OpenMANET firmware dependency as OPEN
until a mesh equivalence test demonstrates that native Debian reproduces the
reference behaviour. Source limitation `SR-002`/`SR-003` states that OpenMANET
behaviour is evidence for the reference implementation, not proof that native
Debian reproduces it until Stage 2.

Minimally, a candidate image must rebuild all out-of-tree modules and enumerate
every radio, which is the first gate in `os/release/README.md`.
