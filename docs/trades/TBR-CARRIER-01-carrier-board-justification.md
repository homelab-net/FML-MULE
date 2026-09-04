---
id: TBR-CARRIER-01
title: Carrier board justification
status: OPEN
owner: Cameron Zobrist
area: CARRIER
priority: 16
function-owner: Builder + Power + RF
critical-path: false
depends-on: [TBR-HW-01, TBR-RF-03, TBR-PWR-01, TBR-THERM-01, TBR-TIME-01, TBR-SEC-01]
feeds: []
requires-hardware: yes
evidence: docs/evidence/TBR-CARRIER-01/
adr: [FML-ADR-021]
target-date: 2026-09-30
---

# TBR-CARRIER-01 Carrier board justification

**Source:** SAD v0.31 section 25.6, and the TBR register in SAD section
30.2 (priority 16 of 16).

**Function owner:** Builder + Power + RF. **Named owner:** `TBD-SRR`.

SAD section 30.2 records an SRR exit action: the Program Owner assigns one named
individual and one calendar target date to every open TBR. The named individual
is assigned as of 2026-08-31. The target date was set to 2026-09-30 on 2026-09-04; for a hardware-gated
trade it is a target the program drives toward, not a claim the capability
exists by then.

## Question

Does repeatability justify custom/semi-custom carrier hardware?

## Why it matters

SAD section 25.6 defers a custom or semi-custom carrier unless prototype evidence
justifies it, and CONOPS section 81 lists "custom PCB unless prototype results
justify it" as out of scope for v1.

A custom carrier is the point at which a volunteer software program becomes a
hardware manufacturing program: a design owner, a fabrication and assembly
supply chain, a minimum order quantity, revisions, stock, and lead time.

It also brings real benefits: power distribution, battery and charger interface,
module retention, internal RF mounting, bulkhead RF routing, RTC and GNSS
interfaces, status and control interfaces, and repeatability across the fleet.

The failure mode this trade guards against is drifting into a custom board
because each individual wiring problem seemed easier to solve with one.

## Options

1. **Commercial boards and a wiring harness only.** No manufacturing. Right
   answer if a documented repeatable assembly can be achieved and survives
   handling.
2. **Passive interconnect board** carrying connectors and power distribution, no
   active components. Much of the mechanical benefit, far less design and
   qualification burden.
3. **Full custom carrier** integrating power, RTC, radio interfaces and
   mounting. Best assembly, highest commitment.
4. **Defer**, building the first block by wiring and revisiting once the parts
   are settled. Legitimate and probably right for the prototype, provided it is
   a decision rather than a drift.

## Closure evidence

SAD section 25.6 fixes the closure evidence: per-unit assembly time; number of
hand-terminated electrical and RF connections; repeatability across multiple
prototypes; field-serviceability; mechanical retention; power loss; RF path
loss; BOM cost; and volunteer-builder skill burden.

SAD section 25.4.1 adds the antenna determination: actual stream count, internal
versus external antennas, diversity and MIMO requirements, approved connector
family, tactile differentiation, replacement method, minimum antenna spacing,
pigtail count and loss, and snag and guarding strategy.

Where a board is proposed: a **named design owner**, an estimated cost at a
realistic quantity, a lead time, and a statement of what happens to the program
if that owner becomes unavailable.

A `BUILD-ACCEPTANCE.md` completed by someone other than the assembly's author.

Evidence is committed under `docs/evidence/TBR-CARRIER-01/`.

## Closure gate

Either a wiring-only assembly is demonstrated repeatable by a second builder
following the written guide, or a board is justified with a named owner, a
costed supply chain, and an explicit acknowledgement that the program has taken
on a manufacturing commitment.

A custom PCB is approved **only if** the evidence shows that a commercial
carrier or wiring approach materially harms repeatability, fieldability or
safety.

**Closure gate per SAD section 30.2:** Before production hardware-block lock / Stages 8, 13.

No TBR closes on document wording alone. It closes only when its listed evidence
exists, the named owner accepts the evidence, and the resulting architecture
decision is entered into the persistent ADR register.

## Dependencies

- **Depends on:** `TBR-HW-01`, `TBR-RF-03`, `TBR-PWR-01`, `TBR-THERM-01`, `TBR-TIME-01`, `TBR-SEC-01`
- **Feeds:** none
- **Related decisions:** `FML-ADR-021`
- **Validating stage:** Stage 8 (CONOPS section 78)
- **Requires hardware:** Requires the assembly attempt with candidate hardware.
