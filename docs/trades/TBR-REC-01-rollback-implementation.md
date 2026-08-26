---
id: TBR-REC-01
title: Rollback implementation
status: OPEN
owner: TBD
area: REC
critical-path: false
depends-on: [TBR-SEC-01, TBR-TAK-01]
feeds: [TBR-HW-01]
evidence: docs/evidence/TBR-REC-01/
adr: [FML-ADR-040, FML-ADR-041]
---

# TBR-REC-01 Rollback implementation

## Question

By what mechanism is the bootable known-good path provided, and how is it kept
current without becoming a second full maintenance burden?

## Why it matters

`FML-ADR-041` decides the **principle** as `SELECTED PRINCIPLE`: a bootable
known-good path independent of the active root, recoverable without disassembly
and without a host computer. This trade selects the mechanism, and the ADR that
records that selection will not supersede `FML-ADR-041`, because the principle
still holds.

The principle constrains hardware before a module is chosen. A device with a
single small non-partitionable boot medium may be disqualified on this ground
alone, so `TBR-HW-01` waits on this.

The subtle part is not the mechanism but its currency. A known-good image that
is two years old is a weak guarantee: it may not understand the current mission
package format, may hold expired trust material, and may not speak to the
current mesh. Deciding when the known-good path is updated, and what qualifies
it as good, is the part that gets skipped.

## Options

1. **A/B root slots**, alternating, with the previous slot as the known-good
   path. Keeps the fallback current automatically, at roughly double the root
   storage.
2. **Dedicated recovery image**, minimal, separate from both roots. Smaller,
   and stale by construction unless deliberately maintained.
3. **Read-only fallback root** with state on a separate volume.
4. **Network recovery from a peer node.** Fails for a node deployed alone,
   which is the `v0.0.1` case, so at best a supplement.

## Closure evidence

Committed under `docs/evidence/TBR-REC-01/`:

- Demonstrated rollback on candidate hardware, without disassembly and without
  a host computer, from a deliberately broken active root.
- Demonstrated rollback from a root that boots but whose radios do not
  enumerate, which is the failure the compatibility-set rule in `FML-ADR-040`
  exists to catch.
- Storage layout with sizes, and the resulting requirement on the boot medium.
- Interaction with `TBR-SEC-01`: what unlocks the rollback path, and evidence
  that it is not a way to boot the node without its protections.
- The stated currency policy, and evidence it was followed across at least two
  promotions.

## Closure gate

A node with a deliberately broken active root is recovered to a working state
by a volunteer following the written procedure, using no tools beyond what the
operational concept says they carry, with no disassembly and no host computer.
Demonstrated rollback is already a required gate in `os/release/README.md`.

## Dependencies

- **Depends on:** `TBR-SEC-01`, `TBR-TAK-01` (what state must survive a
  rollback).
- **Feeds:** `TBR-HW-01`, and the whole promotion gate.
- **Requires hardware:** yes.
