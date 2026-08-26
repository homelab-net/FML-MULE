---
id: TBR-HW-01
title: Primary compute hardware block
status: OPEN
owner: TBD
area: HW
critical-path: false
depends-on: [TBR-LINUX-01, TBR-COMP-01, TBR-PWR-01, TBR-THERM-01, TBR-RF-03, TBR-CARRIER-01, TBR-REC-01, TBR-TIME-01]
feeds: []
evidence: docs/evidence/TBR-HW-01/
adr: [FML-ADR-021, FML-ADR-041, FML-ADR-042, FML-ADR-045]
---

# TBR-HW-01 Primary compute hardware block

## Question

Which compute module, carrier, radios, enclosure, pack and antenna set
constitute the first qualified hardware block?

## Why it matters

This is the trade every other hardware trade feeds. It is deliberately last,
because selecting hardware before its constraints are known is how a program
ends up requalifying an enclosure it has already had made.

It is also the trade under the most pressure to close early, because until it
closes nobody can build a node, and a program that cannot build anything loses
contributors. `ROADMAP.md` addresses that tension by scoping `v0.0.1` to one
node and one service rather than by rushing this trade.

A block is not a compute module. It is the whole qualified configuration, and
the promise the program makes is that a spare node replaces any node **within
the same block**. Substituting a component may require requalification; see
`hardware/README.md`.

Note that several constraints are disqualifying rather than scoring: no viable
kernel path (`TBR-LINUX-01`), no battery-backed real-time clock
(`FML-ADR-042`), or no boot medium that supports an independent known-good path
(`FML-ADR-041`) each rule a candidate out regardless of its other merits.

## Options

Candidate modules are not listed, because listing them now would create the
appearance of a shortlist that has been evaluated. None has been.

`hardware/blocks/block-a/` exists as the placeholder for the first candidate
block. Its contents are `TBD`.

## Closure evidence

Committed under `docs/evidence/TBR-HW-01/`:

- A complete bill of material for the candidate block, with part numbers,
  sources, and archived datasheets for every active component.
- Lifecycle status for every part, per `hardware/lifecycle/`. This program has
  already had a key module reach end of life before purchase.
- Evidence that each disqualifying constraint above is satisfied.
- The closure evidence from every trade in the `depends-on` list.
- A built node passing the acceptance procedure in the block's `acceptance/`
  directory.
- Regulatory records per `REGULATORY.md`: module approvals, antenna and gain,
  and integration conditions, filed under the block's `rf/` directory.

## Closure gate

A physical node built from the block's bill of material passes the block
acceptance procedure, every dependency trade is `CLOSED`, and the block README
states its qualification status and the requalification a substitution demands.

A block does not become qualified because one node was built and worked once.
The gate requires the acceptance procedure, which is a written, repeatable
document.

## Dependencies

- **Depends on:** `TBR-LINUX-01`, `TBR-COMP-01`, `TBR-PWR-01`, `TBR-THERM-01`,
  `TBR-RF-03`, `TBR-CARRIER-01`, `TBR-REC-01`, `TBR-TIME-01`.
- **Feeds:** every build instruction in the repository.
- **Requires hardware:** yes, by definition.
