---
id: TBR-COMP-01
title: CPU and memory budget
status: OPEN
owner: TBD
area: COMP
critical-path: false
depends-on: [TBR-TAK-01]
feeds: [TBR-HW-01, TBR-PWR-01, TBR-CARRIER-01]
evidence: docs/evidence/TBR-COMP-01/
adr: [FML-ADR-021, FML-ADR-029]
---

# TBR-COMP-01 CPU and memory budget

## Question

What CPU and memory does the combined network plane and mission-service plane
require, with enough margin to survive a peak without the mesh degrading?

## Why it matters

`FML-ADR-021` puts both planes on one host, so they compete. The failure mode
is specific and nasty: the mission-service plane takes memory or CPU under
load, the network plane's routing daemon is starved, mesh links flap, and the
node appears to have a radio fault when it has a scheduling fault.

The budget sets the floor for hardware selection, and every module below the
floor is disqualified. Set it too high and the program buys power and heat it
did not need, which feeds straight into `TBR-PWR-01` and `TBR-THERM-01`.

No CPU class, core count, memory size or storage size appears anywhere in this
repository. None has been chosen.

## Options

The axes, rather than invented options: memory size, CPU class and core count,
storage class and endurance, whether hardware cryptographic acceleration is
required, and how much headroom is reserved for the network plane.

Reservation mechanism matters as much as size. Whether the network plane gets a
systemd resource reservation, a dedicated core, or nothing but priority is part
of this trade.

## Closure evidence

Committed under `docs/evidence/TBR-COMP-01/`:

- Measured resident memory and CPU utilisation for each service in the catalog,
  under a representative mission load, recorded with the image build.
- The same for the network plane: routing daemon, mesh interface handling,
  firewall, DNS and DHCP.
- A peak measurement, not only a steady-state one, including service start-up,
  a mesh reconfiguration, and a client association storm at the access point.
- A stated reservation policy and evidence that the network plane keeps its
  reservation while the service plane is at peak.

## Closure gate

A budget is stated with headroom, and a node running the full catalog at a
representative load holds mesh links stable through a service-plane peak, with
the measurement recorded. The budget document names the reservation mechanism.

## Dependencies

- **Depends on:** `TBR-TAK-01`, which determines whether durable mission state
  and its storage are in the budget at all.
- **Feeds:** `TBR-HW-01`, `TBR-PWR-01`, `TBR-CARRIER-01`.
- **Requires hardware:** partly. Service-plane measurements can be taken on an
  ordinary machine against fakes, per the hardware abstraction rule in
  `AGENTS.md`. Network-plane measurements need radios.
