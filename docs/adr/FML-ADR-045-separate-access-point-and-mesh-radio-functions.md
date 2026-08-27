---
id: FML-ADR-045
title: EUD WLAN and high-throughput inter-node mesh are separate logical radio functions; power/BOM planning assumes separate radios until concurrency is proven
status: SELECTED PLANNING BASELINE
date: 2026-08-25
supersedes: none
superseded-by: none
trades: [TBR-RF-03, TBR-RF-01, TBR-PWR-01, TBR-THERM-01, TBR-HW-01, TBR-CARRIER-01]
verification: Stage 4
---

# FML-ADR-045 EUD WLAN and high-throughput inter-node mesh are separate logical radio functions; power/BOM planning assumes separate radios until concurrency is proven

**Source of rationale:** SAD v0.31 section 5.2. See also sections 25.4, 25.4.1,
28 and 31.

New in SAD v0.3.

## Context

Conventional Wi-Fi serves two different jobs: a high-throughput bearer between
nodes, and an access point that end-user devices associate with. These have
different channel, power, security and availability requirements. An operator's
phone dropping off should not disturb the inter-node link, and a mesh
reconfiguration should not drop every attached device.

Whether one chipset can carry both concurrently is a hardware question with
cost, power, thermal and antenna consequences.

## Decision

The EUD-access WLAN and the high-throughput inter-node bearer **shall** be
treated as two separate **logical radio functions**, with independent
configuration, channel selection and security parameters.

For power, RF, carrier and BOM planning, the architecture **shall assume they
are implemented by separate physical conventional-Wi-Fi radio interfaces**
unless testing proves that one selected chipset provides stable concurrent AP
plus 802.11s or mesh operation without unacceptable channel coupling, throughput
loss, multicast impairment or recovery complexity.

The conservative production reference topology is therefore four radios: EUD
access, high-rate inter-node, HaLow, and LoRa.

Where a selected compute module has suitable integrated Wi-Fi, that integrated
radio is the **preferred first candidate for the EUD AP role**, with a separate
validated radio owning the high-rate inter-node function.

**Sharing EUD AP and high-rate mesh on one physical radio is an optimization,
not a baseline assumption.**

## Status

`SELECTED PLANNING BASELINE`.

Adopted so that configuration structure, network plane design and hardware block
templates can proceed. **`TBR-RF-03` determines whether physical consolidation is
permitted**, and its closure evidence must include supported concurrent
interface modes, AP plus mesh stability, channel-coupling constraints, EUD
compatibility, multicast and roaming behaviour, radio recovery behaviour, power
delta, supported spatial-stream count, antenna and feed count, and whether
antennas can be internal, external or must be field replaceable.

Dependent work may build on the logical separation. Nobody should assume the
physical arrangement.

## Consequences

- Configuration templates in `os/config/` are written per logical function, not
  per physical interface, so a later consolidation changes the generation
  mapping rather than restructuring every file.
- The four-radio assumption drives the **six-feed antenna planning envelope** in
  SAD section 25.4.1: EUD AP up to 2x2, high-rate up to 2x2, HaLow one feed,
  LoRa one feed, with optional GNSS adding a seventh. SAD states the enclosure
  **must not be dimensioned around the earlier three-radio mental model**.
- Power and thermal models assume four radios until `TBR-RF-03` closes, feeding
  `TBR-PWR-01` and `TBR-THERM-01`.
- Two functions on one radio share airtime. Whether the access point can starve
  the inter-node bearer, or the reverse, is unmeasured.
- SAD section 31 records "EUD/high-rate radio undercount" as MITIGATED
  specifically by this planning baseline.

## Accepted cost

The program accepts carrying a design and a power, antenna and BOM envelope that
may be larger than the hardware eventually needs, and accepts that some
configuration structure will look redundant if consolidation succeeds.

SAD section 5.2 states the reason directly: this **intentionally avoids
underestimating power, antenna count, RF coexistence or carrier-board I/O during
early trades.** Discovering that a shared radio cannot meet both requirement
sets after the enclosure and antenna arrangement are fixed is the more expensive
error.

## Fallback

Consolidation onto one radio, which is the outcome `TBR-RF-03` may well reach.
Because the separation here is logical, taking that path **revises this planning
baseline** rather than invalidating the configuration structure, and does not
supersede this ADR.

## Superseded by

None.

## Verification dependency

Stages 1 and 4. Concurrent access point and inter-node traffic measurement on
candidate hardware, with stream and antenna-feed counts recorded. Nothing has
been measured.
