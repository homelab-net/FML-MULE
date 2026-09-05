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

## The M.2 slot is radio-versus-storage, and that is now a stated requirement

Added 2026-09-04 after a bench session that provisioned a real EUD map. The
Waveshare CM4-IO-BASE-C has **one M.2 M-key slot, and the BOM spends it on the
QCA6174 high-rate mesh radio** ("no NVMe path", `prototype-bom-revA.csv`); the
carrier is USB2-only, so even USB storage is throttled. Committed storage in the
BOM is 32 GB eMMC plus a *USB2 SSD test article* -- no production SSD.

The Program Owner's stated direction: **M.2 hosting is a baseline capability, and
the design shall keep the option and the path for large on-node map/service
storage** -- storage need not be fitted on every commercial node, but a node
that carries it becomes a **map/service server for its EUDs and for the mesh**
(`TBR-MAP-01`, the WAN-gateway share pattern of CONOPS section 42). The map-storage
arithmetic makes the size concrete: an AO is tens of MB, a multi-state region at
street detail is hundreds of GB, so the requirement is a **>=256 GB SSD, M.2
preferred** (`docs/evidence/TBR-MAP-01/2026-09-04-real-eud-offline-map-and-storage.md`).

That cannot coexist with the QCA6174 on this carrier's single M.2. The carrier
selection therefore has to answer one of:

- a carrier with a **second M.2** (radio in one, NVMe storage in the other);
- **relocating the high-rate radio off M.2** so the slot carries storage -- the
  option-1 AP+mesh consolidation in `TBR-RF-03`, shown feasible at the
  interface-combination level on the bench, is the enabler;
- accepting **USB storage** (the current BOM path), at USB2 speed and with the
  Postgres-survivability question in `FML-ADR-050`/`TBR-COMP-01`.

This is a genuine input the carrier justification must now carry, alongside the
assembly and RF evidence below.

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
