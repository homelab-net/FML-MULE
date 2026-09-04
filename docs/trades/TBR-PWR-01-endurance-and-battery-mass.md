---
id: TBR-PWR-01
title: Endurance and battery mass
status: OPEN
owner: Cameron Zobrist
area: PWR
priority: 1
function-owner: Power/Mechanical
critical-path: true
depends-on: [TBR-RF-03]
feeds: [TBR-THERM-01, TBR-HW-01, TBR-CARRIER-01]
requires-hardware: yes
evidence: docs/evidence/TBR-PWR-01/
adr: [FML-ADR-021, FML-ADR-045]
target-date: 2026-09-30
---

# TBR-PWR-01 Endurance and battery mass

**Source:** SAD v0.31 section 25.1, and the TBR register in SAD section
30.2 (priority 1 of 16).

**Function owner:** Power/Mechanical. **Named owner:** `TBD-SRR`.

SAD section 30.2 records an SRR exit action: the Program Owner assigns one named
individual and one calendar target date to every open TBR. The named individual
is assigned as of 2026-08-31. The target date was set to 2026-09-30 on 2026-09-04; for a hardware-gated
trade it is a target the program drives toward, not a claim the capability
exists by then.

## Question

Does the one-host/four-radio planning architecture close endurance with acceptable mass?

## Why it matters

SAD section 25.1 marks this **CRITICAL / FIRST HARDWARE TRADE**. Power
testing is not a late validation activity; it is a primary input to compute,
radio, service-hosting, enclosure and battery architecture.

The initial hardware architecture will not be locked until representative
measurements exist. `TBR-HW-01` waits on it, and so does the enclosure.

CONOPS section 59 sets an approximately 8-hour single-pack planning objective
and states plainly that it is a planning objective, not a verified minimum. SAD
section 25.1 adds that it is **not permission to build an impractically heavy
battery**.

## Options

Options cannot be enumerated until the load is bounded. The axes are the eight
measured load states below, the duty cycle assumed, cell chemistry and pack
topology, whether the pack is user-swappable in the field, and whether external,
vehicle, solar or generator support is in scope.

If the architecture cannot meet 8 hours with acceptable operator-carried pack
mass and reasonable reserve, SAD section 25.1 fixes the response order:

1. evaluate architecture reductions that do not violate required capability,
   including radio consolidation proven by `TBR-RF-03` and service-power
   management;
2. evaluate sustainment through approved external, vehicle or alternate packs as
   CONOPS section 60 permits;
3. if the objective still drives disproportionate mass, cost or complexity,
   **raise a controlled CONOPS change request against the endurance objective
   rather than conceal the problem in the battery BOM.**

That third step is the change-control trigger added in SAD v0.31.

## Closure evidence

Measured power for the eight load states in SAD section 25.1:

1. host idle with all required radios initialized;
2. EUD AP with representative EUD clients;
3. normal HaLow MANET operation;
4. representative TAK and local-service load;
5. high-throughput inter-node transfer and replication load;
6. active shared-service-host load;
7. representative LoRa activity;
8. combined worst credible mission load.

The resulting model must answer average watts, peak watts, 8-hour energy
requirement, battery reserve margin, pack mass, the 24-72 hour pack and charging
sustainment burden, service-host runtime penalty, cold-weather derating, and
charger and external-power burden.

Also required: a discharge run of the assembled pack under representative load
to the protection cutoff, and the change-control disposition if 8 hours proves
disproportionate.

Instrument, date, node, image build, configuration and ambient conditions are
recorded for every measurement.

Evidence is committed under `docs/evidence/TBR-PWR-01/`.

## Closure gate

Measured endurance of an assembled node under a representative duty cycle meets
the stated requirement with pack mass and volume inside the portability
constraint, **or** the change-control disposition above has been raised.

A calculation alone does not close this trade. Cells do not deliver datasheet
capacity under real loads at real temperatures, and CONOPS section 61 requires
the verified endurance requirement to include defined cold-temperature
conditions.

**Closure gate per SAD section 30.2:** Before hardware PDR / Stage 7.

No TBR closes on document wording alone. It closes only when its listed evidence
exists, the named owner accepts the evidence, and the resulting architecture
decision is entered into the persistent ADR register.

## Dependencies

- **Depends on:** `TBR-RF-03`
- **Feeds:** `TBR-THERM-01`, `TBR-HW-01`, `TBR-CARRIER-01`
- **Related decisions:** `FML-ADR-021`, `FML-ADR-045`
- **Validating stage:** Stage 7 (CONOPS section 78)
- **Requires hardware:** Requires an instrumented prototype. SAD section 25.7
  directs that the same rig
collect thermal evidence for `TBR-THERM-01`, to avoid duplicate prototype
builds. The prototype BOM decouples this trade from pack sourcing by powering
the prototype from USB-C PD.
