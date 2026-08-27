---
id: TBR-COMP-01
title: CPU and memory budget
status: OPEN
owner: TBD-SRR
area: COMP
priority: 2
function-owner: Platform + TAK
critical-path: true
depends-on: [TBR-TAK-01]
feeds: [TBR-HW-01, TBR-PWR-01]
requires-hardware: partly
evidence: docs/evidence/TBR-COMP-01/
adr: [FML-ADR-021, FML-ADR-028, FML-ADR-029, FML-ADR-030]
target-date: TBD-SRR
---

# TBR-COMP-01 CPU and memory budget

**Source:** SAD v0.31 section 25.3, and the TBR register in SAD section
30.2 (priority 2 of 16).

**Function owner:** Platform + TAK. **Named owner:** `TBD-SRR`.

SAD section 30.2 records an SRR exit action: the Program Owner assigns one named
individual and one calendar target date to every open TBR. `TBD-SRR` marks the
gap explicitly rather than hiding it behind a functional organization.

## Question

What CPU/RAM reserve is required for the complete one-host service catalog?

## Why it matters

SAD section 25.3 marks this **CRITICAL**. The one-host architecture requires an
explicit compute and memory model alongside the power model, and **the host
hardware is not selected until the resource model and power model agree.**

`FML-ADR-021` accepted that a fault in the mission-service plane can starve the
network plane. This trade is where that accepted cost is quantified and bounded.
The failure mode is specific: the service plane takes memory or CPU, the routing
daemon is starved, mesh links flap, and the node appears to have a radio fault
when it has a scheduling fault.

## Options

The axes are memory size, CPU class and core count, storage class and endurance,
whether hardware cryptographic acceleration is required, and how much headroom
is reserved for the Network Plane.

**The reservation mechanism matters as much as the size.** SAD section 10.4
requires critical network functions to receive reserved CPU and memory priority
sufficient to remain responsive during application load. Whether that is a
systemd resource reservation, a dedicated core, or priority alone is part of
this trade.

## Closure evidence

Measured RAM, CPU, OOM and cgroup behaviour for the components SAD section 25.3
enumerates:

- baseline Debian and network stack;
- hostapd and EAP;
- batman-adv and mesh telemetry;
- OpenTAKServer processes;
- RabbitMQ;
- PostgreSQL if selected;
- HAProxy;
- Mission Trust Service;
- MULE service controller;
- MULE Status Aggregator;
- representative rootless browser, file and chat services;
- observability and exporters;
- failover and synchronization workload.

Peak as well as steady state: service start-up, a mesh reconfiguration, and a
client association storm at the access point.

Evidence is committed under `docs/evidence/TBR-COMP-01/`.

## Closure gate

A budget is stated defining normal and peak RAM utilization, swap policy, CPU
utilization under normal and worst representative load, reserve margin, OOM
behaviour and cgroup or service priority.

A node running the full catalog at representative load holds mesh links stable
through a service-plane peak, with the measurement recorded.

**Closure gate per SAD section 30.2:** Before host selection / Stages 1, 5.

No TBR closes on document wording alone. It closes only when its listed evidence
exists, the named owner accepts the evidence, and the resulting architecture
decision is entered into the persistent ADR register.

## Dependencies

- **Depends on:** `TBR-TAK-01`
- **Feeds:** `TBR-HW-01`, `TBR-PWR-01`
- **Related decisions:** `FML-ADR-021`, `FML-ADR-028`, `FML-ADR-029`, `FML-ADR-030`
- **Validating stage:** Stage 1 (CONOPS section 78)
- **Requires hardware:** Service-plane measurements can be taken on an
  ordinary machine against fakes,
per the hardware abstraction rule in `AGENTS.md`. Network-plane measurements and
the association-storm case need radios.
