---
id: FML-ADR-040
title: Kernel, driver, firmware and userspace promote as one tested set
status: SELECTED
date: TBD
supersedes: none
superseded-by: none
trades: [TBR-LINUX-01, TBR-REC-01]
verification: TBD
---

# FML-ADR-040 Kernel, driver, firmware and userspace promote as one tested set

This is a stub. The **system architecture description is the source of
rationale**; see `docs/architecture/README.md`.

## Context

The Wi-Fi HaLow driver path is out-of-tree. Out-of-tree kernel modules are
coupled to a specific kernel version, radio firmware is coupled to a specific
driver version, and the userspace tooling that configures the radio is coupled
to both. Updating any one of these independently is how a fleet of nodes stops
enumerating its radios in the field.

## Decision

The kernel, the out-of-tree radio driver, the radio firmware, and the required
userspace **shall** be versioned, tested and promoted as a **single
compatibility set**. No component of the set **shall** be promoted
independently.

Version pins for the set are recorded in `os/kernel/PINS.md` and
`os/image/manifest/`. A change to any pin creates a new candidate set that must
pass the full promotion gate in `os/release/README.md`.

## Status

`SELECTED`.

This is the rule that makes the two-layer split in `os/README.md` safe. It is
the reason automated dependency updates in this repository open proposals and
never auto-merge.

## Consequences

- A security update to one component cannot be shipped without re-qualifying
  the set. This is a real cost during an active vulnerability, and the program
  has no exception process for it yet. That gap is acknowledged, not solved.
- The promotion gate becomes the only path to a deployable artifact, which
  makes `os/release/` load-bearing early.
- Dependency bots are advisory. A green CI run is not evidence that the set
  still works, because CI has no radios; see `test/README.md`.
- Rollback matters more, because a bad set is an all-at-once failure. See
  `FML-ADR-041` and `TBR-REC-01`.
- Every field node can be identified by a single set version, which makes a
  fault report actionable.

## Accepted cost

The program accepts slower patch delivery and a heavier qualification burden in
exchange for a fleet whose radios still work after an update. It accepts that
this will at some point mean knowingly running a component with a published
vulnerability while the set is re-qualified.

## Fallback

None that preserves the property. Promoting components independently is
precisely the failure mode this decision exists to prevent, so there is no
partial version of it. Structural.

## Superseded by

None.

## Verification dependency

`TBD`. The promotion gate in `os/release/README.md` is the verification: a
candidate must rebuild all out-of-tree modules, boot, enumerate every radio,
form a mesh, serve the access point, pass a traffic smoke test, survive a
reboot, and demonstrate rollback.
