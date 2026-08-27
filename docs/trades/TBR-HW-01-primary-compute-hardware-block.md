---
id: TBR-HW-01
title: Primary compute hardware block
status: OPEN
owner: TBD-SRR
area: HW
priority: 7
function-owner: Systems + Builder
critical-path: false
depends-on: [TBR-PWR-01, TBR-COMP-01, TBR-THERM-01, TBR-RF-03, TBR-TIME-01, TBR-SEC-01]
feeds: [TBR-REC-01, TBR-CARRIER-01, TBR-LINUX-01]
requires-hardware: yes
evidence: docs/evidence/TBR-HW-01/
adr: [FML-ADR-021, FML-ADR-041, FML-ADR-042, FML-ADR-050]
target-date: TBD-SRR
---

# TBR-HW-01 Primary compute hardware block

**Source:** SAD v0.31 section 25.2, and the TBR register in SAD section
30.2 (priority 7 of 16).

**Function owner:** Systems + Builder. **Named owner:** `TBD-SRR`.

SAD section 30.2 records an SRR exit action: the Program Owner assigns one named
individual and one calendar target date to every open TBR. `TBD-SRR` marks the
gap explicitly rather than hiding it behind a functional organization.

## Question

Which CM4/CM5/industrial-SBC class becomes the first hardware block?

## Why it matters

SAD section 30.3 states it directly: **HW-01 is a convergence decision, not an
independent early choice.** Six trades feed it.

It is also the trade under the most pressure to close early, because until it
closes nobody can build a node. Selecting hardware before its constraints are
known is how a program ends up requalifying an enclosure it has already had
made.

A block is not a compute module. It is the whole qualified configuration, and
the program's promise is that a spare node replaces any node **within the same
block** (CONOPS section 5.1).

## Options

SAD section 25.2 requires the trade to include at minimum:

- Raspberry Pi CM4-class - lower resource and power potential, public production
  commitment through at least January 2034 (source `SR-007`);
- Raspberry Pi CM5-class - substantially greater compute, RAM and I/O, public
  production commitment through at least January 2036 (source `SR-008`);
- at least one low-power industrial SBC family with a credible Linux and HaLow
  integration path.

**Neither Pi variant wins before measurement.** Gateworks Venice-class hardware
is noted in SAD section 6.2 as architecture-compatible.

Some constraints are **disqualifying rather than scoring**: no viable kernel
path (`TBR-LINUX-01`), no battery-backed RTC (`FML-ADR-042`), and no boot medium
supporting a known-good path independent of the active root (`FML-ADR-041`).

## Closure evidence

SAD section 30.2: Linux support; RAM, storage, endurance and I/O; RTC and trust
hardware; radios; measured power and thermal; lifecycle; cost.

SAD section 25.8 adds storage evidence: storage technology, rated endurance
where published, expected write workload, capacity reserve, SMART/NVMe/eMMC
health visibility, and the replaceability and reimage procedure.

Plus the closure evidence from every trade in the depends-on list, a complete
bill of material with archived datasheets, lifecycle status per
`hardware/lifecycle/`, and regulatory records per `REGULATORY.md`.

Evidence is committed under `docs/evidence/TBR-HW-01/`.

## Closure gate

A physical node built from the block's bill of material passes the block
acceptance procedure, every dependency trade is `CLOSED`, and the block README
states its qualification status and the requalification a substitution demands.

A block does not become qualified because one node was built and worked once.
The gate requires the acceptance procedure, which is a written repeatable
document. CONOPS section 74 requires operational interchangeability to be
**verified, not assumed**.

**Closure gate per SAD section 30.2:** Before hardware PDR / Stages 1, 7, 8.

No TBR closes on document wording alone. It closes only when its listed evidence
exists, the named owner accepts the evidence, and the resulting architecture
decision is entered into the persistent ADR register.

## Dependencies

- **Depends on:** `TBR-PWR-01`, `TBR-COMP-01`, `TBR-THERM-01`, `TBR-RF-03`, `TBR-TIME-01`, `TBR-SEC-01`
- **Feeds:** `TBR-REC-01`, `TBR-CARRIER-01`, `TBR-LINUX-01`
- **Related decisions:** `FML-ADR-021`, `FML-ADR-041`, `FML-ADR-042`, `FML-ADR-050`
- **Validating stage:** Stage 8 (CONOPS section 78)
- **Requires hardware:** Yes, by definition.
