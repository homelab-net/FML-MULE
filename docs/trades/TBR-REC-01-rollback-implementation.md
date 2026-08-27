---
id: TBR-REC-01
title: Rollback implementation
status: OPEN
owner: TBD-SRR
area: REC
priority: 13
function-owner: Platform + CM
critical-path: false
depends-on: [TBR-HW-01, TBR-SEC-01]
feeds: [TBR-LINUX-01]
requires-hardware: yes
evidence: docs/evidence/TBR-REC-01/
adr: [FML-ADR-041, FML-ADR-040]
target-date: TBD-SRR
---

# TBR-REC-01 Rollback implementation

**Source:** SAD v0.31 section 20.3, and the TBR register in SAD section
30.2 (priority 13 of 16).

**Function owner:** Platform + CM. **Named owner:** `TBD-SRR`.

SAD section 30.2 records an SRR exit action: the Program Owner assigns one named
individual and one calendar target date to every open TBR. `TBD-SRR` marks the
gap explicitly rather than hiding it behind a functional organization.

## Question

What A/B or equivalent bootable rollback implementation is used?

## Why it matters

`FML-ADR-041` decides the **principle** as `SELECTED PRINCIPLE`: a bootable
known-good path independent of the active root, recoverable without disassembly
and without a host computer. This trade selects the **mechanism**, and the ADR
that records that selection will not supersede `FML-ADR-041`.

SAD section 20.3 states that a filesystem snapshot which cannot boot when the
active root is damaged **is not sufficient by itself**.

The subtle part is not the mechanism but its currency. A known-good image that
is two years old may not understand the current mission package format, may hold
expired trust material, and may not speak to the current mesh.

## Options

1. **A/B root filesystem or image slots**, alternating, with the previous slot
   as the known-good path. Keeps the fallback current automatically, at roughly
   double the root storage.
2. **Dedicated recovery image**, minimal and separate from both roots. Smaller,
   and stale by construction unless deliberately maintained.
3. **Read-only fallback root** with state on a separate volume.
4. **Network recovery from a peer node.** Fails for a node deployed alone, so at
   best a supplement.

`FML-ADR-041` names A/B slots first but does not mandate them.

## Closure evidence

SAD section 20.3 acceptance: failed update; corrupt active image; failed
radio-driver promotion; operator-initiated rollback; and restoration to a
known-good fleet baseline **without WAN**.

Plus storage layout with sizes and the resulting requirement on the boot medium;
the interaction with `TBR-SEC-01` showing what unlocks the rollback path and
that it is not a way to boot the node without its protections; and the stated
currency policy with evidence it was followed across at least two promotions.

Evidence is committed under `docs/evidence/TBR-REC-01/`.

## Closure gate

A node with a deliberately broken active root is recovered to a working state by
a volunteer following the written procedure, using no tools beyond what the
operational concept says they carry, with no disassembly and no host computer.

Demonstrated rollback is already a required step in the promotion gate in
`os/release/README.md` and step 12 of the SAD section 20.4 release suite.

**Closure gate per SAD section 30.2:** Before production image baseline / Stages 1, 13.

No TBR closes on document wording alone. It closes only when its listed evidence
exists, the named owner accepts the evidence, and the resulting architecture
decision is entered into the persistent ADR register.

## Dependencies

- **Depends on:** `TBR-HW-01`, `TBR-SEC-01`
- **Feeds:** `TBR-LINUX-01`
- **Related decisions:** `FML-ADR-041`, `FML-ADR-040`
- **Validating stage:** Stage 1 (CONOPS section 78)
- **Requires hardware:** Requires the selected boot chain from `TBR-HW-01`.
