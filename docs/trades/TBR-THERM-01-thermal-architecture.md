---
id: TBR-THERM-01
title: Thermal architecture
status: OPEN
owner: Cameron Zobrist
area: THERM
priority: 3
function-owner: Power/Mechanical + Platform
critical-path: true
depends-on: [TBR-PWR-01, TBR-COMP-01]
feeds: [TBR-HW-01, TBR-CARRIER-01]
requires-hardware: yes
evidence: docs/evidence/TBR-THERM-01/
adr: [FML-ADR-050]
target-date: 2026-09-30
---

# TBR-THERM-01 Thermal architecture

**Source:** SAD v0.31 section 25.7, and the TBR register in SAD section
30.2 (priority 3 of 16).

**Function owner:** Power/Mechanical + Platform. **Named owner:** `TBD-SRR`.

SAD section 30.2 records an SRR exit action: the Program Owner assigns one named
individual and one calendar target date to every open TBR. The named individual
is assigned as of 2026-08-31. The target date was set to 2026-09-30 on 2026-09-04; for a hardware-gated
trade it is a target the program drives toward, not a claim the capability
exists by then.

## Question

Can the host/radios operate across field thermal load without unacceptable throttling or cooling burden?

## Why it matters

SAD section 25.7 marks this **CRITICAL** and separates it from `TBR-PWR-01`:
power consumption and thermal rejection are related but distinct trades.

Sealing and cooling work against each other, and both are required. Ingress
protection removes the airflow every component inside was characterised with. A
module rated for a given ambient in free air is not rated for that ambient
inside a closed box in sun.

SAD section 26 defines the consequence when it fails: preserve Network Plane
priority, shed or degrade S3 then nonessential S2 workload, raise
`THERMAL_DEGRADED`, and shut down in a controlled way if safe temperature cannot
be maintained.

## Options

SAD section 25.7 requires comparing the consequences of:

- passive conductive enclosure and heatsink design;
- vents;
- fan-assisted cooling;
- fanless industrial SBC alternatives;
- compute and radio duty-cycle reduction.

**A fan is not assumed.** If required, the design must account for its power,
acoustic signature, mechanical lifetime, dust and water ingress path, and field
replaceability. An acoustic signature is an operational cost under CONOPS
section 65's signature controls, not only an engineering one.

Cell placement relative to heat sources is a separate axis and a safety matter.

## Closure evidence

Measured, per SAD section 25.7: processor temperature, radio and module
temperature, battery, BMS and charger temperature, enclosure internal
temperature, ambient temperature, thermal throttling, packet loss and latency
while thermally constrained, service-host performance, solar-load sensitivity
where practical, and passive-versus-active cooling behaviour.

External surface temperature at the hottest accessible point, for touch safety.

**The same instrumented rig used for `TBR-PWR-01` should collect this evidence**,
to avoid duplicate prototype builds.

Evidence is committed under `docs/evidence/TBR-THERM-01/`.

## Closure gate

At the worst-case ambient the CONOPS states, the node sustains its representative
duty cycle without the compute element throttling below the budget set by
`TBR-COMP-01`, with cell temperature inside the manufacturer's operating range
and external surfaces below a stated touch-safe limit.

Where any of those cannot be met, the closure records the duty-cycle derating
required instead, and that derating becomes a stated operating limit rather than
a footnote.

**Closure gate per SAD section 30.2:** Before hardware/enclosure PDR / Stages 7, 8.

No TBR closes on document wording alone. It closes only when its listed evidence
exists, the named owner accepts the evidence, and the resulting architecture
decision is entered into the persistent ADR register.

## Dependencies

- **Depends on:** `TBR-PWR-01`, `TBR-COMP-01`
- **Feeds:** `TBR-HW-01`, `TBR-CARRIER-01`
- **Related decisions:** `FML-ADR-050`
- **Validating stage:** Stage 8 (CONOPS section 78)
- **Requires hardware:** Requires a candidate enclosure, not only boards. The
  prototype BOM includes a
thermal bridge line because the extruded aluminium shell only helps if the
compute module is conductively coupled to the wall, and notes that a printed
sled must not sit between the module and the extrusion because printed plastic
is an insulator.
