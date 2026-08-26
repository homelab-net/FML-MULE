---
id: TBR-CARRIER-01
title: Carrier board justification
status: OPEN
owner: TBD
area: CARRIER
critical-path: false
depends-on: [TBR-COMP-01, TBR-LINUX-01]
feeds: [TBR-HW-01]
evidence: docs/evidence/TBR-CARRIER-01/
adr: [FML-ADR-021]
---

# TBR-CARRIER-01 Carrier board justification

## Question

Does this program need a custom carrier board, or can a qualified block be
assembled entirely from commercially available boards and wiring?

## Why it matters

A custom carrier is the point at which a volunteer software program becomes a
hardware manufacturing program. It brings a design owner, a fabrication and
assembly supply chain, a minimum order quantity, revisions, stock, and a lead
time measured in weeks. It also brings a real advantage: fewer connectors, less
wiring to work loose, better power distribution, defined RF layout, and an
assembly a first-time builder can actually complete.

The failure mode this trade guards against is drifting into a custom board
because each individual wiring problem seemed easier to solve with one, without
anyone deciding that the program is now manufacturing hardware.

The counter-failure is a rat's nest of adapter boards and jumper wires that
nobody can reproduce, which fails the "a stranger can build one" criterion in
`README.md` just as thoroughly.

## Options

1. **Commercial boards and a wiring harness only.** No manufacturing. Right
   answer if a documented, repeatable assembly can be achieved and survives
   handling. Lowest barrier for a contributor building their first node.
2. **Passive interconnect board.** A simple board carrying connectors and power
   distribution, no active components. Much of the mechanical benefit, far less
   design and qualification burden.
3. **Full custom carrier** integrating power, RTC, radio interfaces and
   mounting. Best assembly, highest commitment.
4. **Defer**, building the first block by wiring and revisiting once the parts
   are settled. Legitimate and probably right for `v0.0.1`, provided it is a
   decision rather than a drift.

## Closure evidence

Committed under `docs/evidence/TBR-CARRIER-01/`:

- An assembly attempt using commercial boards only, documented, with the time
  taken and every point where the builder was uncertain recorded.
- Evidence of whether that assembly survives handling and transport: continuity
  after a recorded handling regime.
- Where a board is proposed: a named design owner, an estimated cost at a
  realistic quantity, a lead time, and a statement of what happens to the
  program if that owner becomes unavailable, per `MAINTAINERS.md`.
- A `BUILD-ACCEPTANCE.md` completed by someone other than the assembly's
  author.

## Closure gate

Either a wiring-only assembly is demonstrated repeatable by a second builder
following the written guide, or a board is justified with a named owner, a
costed supply chain, and an explicit acknowledgement that the program has taken
on a manufacturing commitment.

## Dependencies

- **Depends on:** `TBR-COMP-01`, `TBR-LINUX-01`.
- **Feeds:** `TBR-HW-01`.
- **Requires hardware:** yes for the assembly attempt.
