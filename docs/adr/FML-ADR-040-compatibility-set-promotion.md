---
id: FML-ADR-040
title: Field kernel/radio-driver promotion is gated and pinned as a tested compatibility set
status: SELECTED
date: 2026-08-25
supersedes: none
superseded-by: none
trades: [TBR-LINUX-01, TBR-REC-01, TBR-HW-01]
verification: Stage 2
---

# FML-ADR-040 Field kernel/radio-driver promotion is gated and pinned as a tested compatibility set

**Source of rationale:** SAD v0.31 section 20.2. See also sections 0.3 principle
13, 20.1, 20.3, 20.4 and 30.1.

New in SAD v0.3.

## Context

The Wi-Fi HaLow driver path is out-of-tree (source `SR-011`). Out-of-tree kernel
modules are coupled to a specific kernel version, radio firmware to a driver
version, and the userspace that configures the radio to both. Updating one
independently is how a fleet stops enumerating its radios in the field, all at
once, remotely, with no operator present.

## Decision

The field kernel, the Morse Micro or other out-of-tree radio driver set, the
radio firmware, and the required userspace radio tooling **shall** be promoted
as **one tested compatibility set**. No component **shall** be promoted
independently.

The policy is fixed by SAD section 20.2:

1. field-release kernels are pinned;
2. kernel security updates are evaluated promptly but staged outside the field
   fleet first;
3. DKMS is preferred when supported cleanly by the selected driver package;
4. where DKMS is not the supported path, the driver or module build is pinned to
   the approved kernel package;
5. every candidate kernel promotion **shall** rebuild and load all required
   out-of-tree modules;
6. the candidate **shall** pass automated boot, radio enumeration, HaLow mesh
   formation, high-rate radio, EUD AP and representative traffic smoke tests;
7. the candidate **shall** survive at least one reboot and rollback exercise;
8. no kernel **shall** be promoted during the deployment freeze window except
   through an approved urgent-security exception.

## Status

`SELECTED`.

**`TBR-LINUX-01` closes on a repeatable kernel-promotion pipeline, not merely a
one-time successful driver build** (SAD section 20.2).

The pipeline requires a permanent hardware-in-the-loop bench: two representative
nodes, representative HaLow, EUD AP, high-rate and LoRa radios, an EUD test
client, a controllable Ethernet/WAN path and power measurement (SAD section
20.4). **Bench hardware is a program asset reserved in the prototype BOM, not
borrowed from the deployable fleet.**

## Consequences

- A change to any pin creates a **new candidate set** that must pass the full
  promotion gate in `os/release/README.md`.
- Dependency bots are advisory. Automated update proposals are opened and never
  auto-merged; see `renovate.json`.
- A green CI run is not evidence the set works, because CI has no radios. See
  `test/README.md`.
- A security update to one component cannot ship without re-qualifying the set.
  That is a real cost during an active vulnerability and the program has no
  exception process beyond the urgent-security case in item 8.
- Rollback matters more, because a bad set fails everything at once. See
  `FML-ADR-041`.
- Every field node is identified by a single set version, which makes a fault
  report actionable.
- SAD section 20.4 states plainly: **a field kernel/radio compatibility set
  cannot be promoted solely from a successful package build.**

## Accepted cost

The program accepts slower patch delivery and a heavier qualification burden in
exchange for a fleet whose radios still work after an update. It accepts that
this will at some point mean knowingly running a component with a published
vulnerability while the set is re-qualified.

It accepts the standing cost of maintaining a two-node HIL bench and a named
release owner, and SAD section 31 records the risk that the pipeline degrades
into a manual checklist if that ownership is not held.

## Fallback

None that preserves the property. Promoting components independently is exactly
the failure mode this decision prevents, so there is no partial version of it.
Structural.

## Superseded by

None.

## Verification dependency

Stage 2, with Stages 1 and 13 for the pipeline itself. The promotion gate in
`os/release/README.md` is the verification. Pins are recorded in
`os/kernel/PINS.md`.
