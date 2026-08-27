---
id: FML-ADR-041
title: MULE requires an A/B or equivalently bootable known-good rollback path
status: SELECTED PRINCIPLE
date: 2026-08-25
supersedes: none
superseded-by: none
trades: [TBR-REC-01, TBR-SEC-01, TBR-HW-01]
verification: Stage 1
---

# FML-ADR-041 MULE requires an A/B or equivalently bootable known-good rollback path

**Source of rationale:** SAD v0.31 section 20.3. See also sections 2.1, 26 and
CONOPS section 73.

New in SAD v0.3.

## Context

`FML-ADR-021` makes the host the per-node compute single point of failure, and
`FML-ADR-040` promotes the whole compatibility set together, so a bad promotion
fails everything at once. A node is deployed by volunteers, often with no
keyboard, no display and nobody present who can recover a failed boot.

## Decision

MULE **shall** provide a bootable recovery path **independent of the newly
promoted root filesystem**.

The production implementation **shall** provide either A/B root filesystem or
image slots, or an equivalently robust bootable known-good image and rollback
mechanism.

**A filesystem snapshot that cannot boot when the active root filesystem is
damaged is not sufficient by itself** (SAD section 20.3).

## Status

`SELECTED PRINCIPLE`.

The **property** is decided. The **mechanism** is not: `TBR-REC-01` selects it
after the compute and carrier boot chain is chosen. The ADR that selects a
mechanism will **not** supersede this one, because the principle continues to
hold.

The mechanism interacts with protected storage unlock (`TBR-SEC-01`) and with
whatever boot arrangement the selected hardware block offers (`TBR-HW-01`).

## Consequences

- Storage layout is constrained before a compute module is chosen. A device with
  a single small non-partitionable boot medium may be disqualified on this
  ground alone. Feeds `TBR-HW-01`.
- Root storage capacity requirements roughly double, which interacts with the
  storage endurance rules in `FML-ADR-050`.
- The promotion gate must **demonstrate** rollback, not merely provide it. That
  is already required in `os/release/README.md` and in SAD section 20.4 item 12.
- Acceptance covers a failed update, a corrupt active image, a failed
  radio-driver promotion, an operator-initiated rollback, and restoration to a
  known-good fleet baseline **without WAN** (SAD section 20.3).
- The rollback path is a second thing to keep current. A known-good image that
  is two years old is a weak guarantee, and may not understand the current
  mission package format. That currency policy is part of `TBR-REC-01`.
- The rollback path is also an attack surface and a capture-time asset, so
  whatever unlocks it must not become a way to boot the node without its
  protections (`TBR-SEC-01`).
- A node that has rolled back remains **out of ready-spare status until
  revalidated** (SAD section 26).

## Accepted cost

The program accepts additional storage cost, additional build and promotion
complexity, and a constraint on hardware selection, in exchange for a node a
volunteer can recover in the field.

## Fallback

None. A device that cannot be recovered without disassembly fails the
operational concept. If no selected hardware can provide this, the hardware is
wrong, not the principle.

## Superseded by

None.

## Verification dependency

Stages 1 and 13. `TBR-REC-01` closure requires failed-update, corrupt-root and
radio-driver rollback demonstrated without WAN.
