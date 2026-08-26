---
id: FML-ADR-041
title: Bootable known-good rollback path independent of the active root
status: SELECTED PRINCIPLE
date: TBD
supersedes: none
superseded-by: none
trades: [TBR-REC-01, TBR-SEC-01, TBR-HW-01]
verification: TBD
---

# FML-ADR-041 Bootable known-good rollback path independent of the active root

This is a stub. The **system architecture description is the source of
rationale**; see `docs/architecture/README.md`.

## Context

A node is deployed by volunteers, often without a keyboard, a display, or
anyone present who can recover a failed boot. An update that leaves the device
unbootable is not an inconvenience; it is the loss of a scarce asset during an
incident.

Because kernel, driver, firmware and userspace promote as one set
(`FML-ADR-040`), a bad promotion fails everything at once.

## Decision

Every node **shall** provide a bootable known-good path that does not depend on
the integrity of the active root filesystem.

Rollback to that path **shall** be possible without physical disassembly and
without a host computer.

## Status

`SELECTED PRINCIPLE`.

The **property** is decided. The **mechanism** is not: A/B root slots, a
separate recovery image, a read-only fallback root, or something else. That is
`TBR-REC-01`, and the ADR that selects a mechanism will **not** supersede this
one, because the principle continues to hold.

The mechanism interacts with protected storage unlock (`TBR-SEC-01`) and with
whatever boot arrangement the selected hardware block offers (`TBR-HW-01`).

## Consequences

- Storage layout is constrained before a compute module is chosen: a device
  with a single small non-partitionable boot medium may be disqualified on this
  ground alone. Feeds `TBR-HW-01`.
- Storage capacity requirements roughly double for the root, which feeds
  `TBR-COMP-01` indirectly and the bill of material for any block.
- The promotion gate must demonstrate rollback, not merely provide it. That is
  already required in `os/release/README.md`.
- The rollback path is a second thing to keep current, and a known-good image
  that is two years old is a weak guarantee. Managing that is part of
  `TBR-REC-01`.
- The rollback path is also an attack surface and a capture-time asset. See
  `THREAT_MODEL.md`.

## Accepted cost

The program accepts additional storage cost, additional build and promotion
complexity, and a constraint on hardware selection, in exchange for a node that
a volunteer can recover in the field.

## Fallback

None. A device that cannot be recovered without disassembly fails the
operational concept. If no selected hardware can provide this, the hardware is
wrong, not the principle.

## Superseded by

None.

## Verification dependency

`TBD` pending `TBR-REC-01`. Demonstrated rollback is an explicit gate in
`os/release/README.md` and will map to a stage under `test/stages/`.
