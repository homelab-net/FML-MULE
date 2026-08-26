---
id: TBR-RF-03
title: Access point and mesh radio consolidation
status: OPEN
owner: TBD
area: RF
critical-path: false
depends-on: [TBR-RF-01, TBR-LINUX-01]
feeds: [TBR-HW-01, TBR-PWR-01]
evidence: docs/evidence/TBR-RF-03/
adr: [FML-ADR-045]
---

# TBR-RF-03 Access point and mesh radio consolidation

## Question

Can the EUD access point and the high-throughput inter-node mesh share one
conventional Wi-Fi radio acceptably, or do they require separate radios?

## Why it matters

`FML-ADR-045` decides that these are separate **logical** functions and
deliberately leaves the physical arrangement open, as a
`SELECTED PLANNING BASELINE` that this trade will revisit.

Consolidation saves a radio, its power, its heat, its antenna and its cost,
all of which feed `TBR-PWR-01`, `TBR-THERM-01` and `TBR-HW-01`. Against that,
two functions on one radio share airtime and, in most arrangements, a channel.
The operational risks are concrete: an operator's phone associating disturbs
the inter-node link; a mesh reconfiguration drops every attached device; a
device with a poor link drags the whole radio's rate down.

## Options

1. **One radio, multiple virtual interfaces, same channel.** Cheapest. Both
   functions constrained to one channel, which may be unacceptable given they
   have different coverage requirements.
2. **One radio, multiple virtual interfaces, different channels.** Requires
   driver support for concurrent operation and typically costs airtime to
   channel switching. Support is `UNVERIFIED`.
3. **Two radios.** Independent channels, independent failure. Costs power,
   heat, space and an antenna, and adds a coexistence question in the 2.4 or 5
   GHz band comparable to `TBR-RF-02` in sub-GHz.
4. **Access point only when needed**, brought up on operator action rather than
   continuously. Reduces contention and emissions; complicates operation.

## Closure evidence

Committed under `docs/evidence/TBR-RF-03/`:

- Measured throughput on the inter-node bearer with zero, one and several
  clients associated to the access point, at recorded offered load.
- Client-visible access point behaviour during a mesh reconfiguration:
  association retained or dropped, and for how long.
- Driver capability evidence for concurrent virtual interface operation, cited
  to the driver documentation and confirmed by observation.
- Power measurements for the one-radio and two-radio arrangements, feeding
  `TBR-PWR-01`.

## Closure gate

A selected arrangement sustains stated inter-node throughput with a stated
number of associated clients, and associated clients survive a mesh
reconfiguration, both recorded. If consolidation cannot meet those, the trade
closes on separate radios and `FML-ADR-045`'s baseline is revised accordingly.

## Dependencies

- **Depends on:** `TBR-RF-01`, `TBR-LINUX-01`.
- **Feeds:** `TBR-HW-01`, `TBR-PWR-01`, and revisits `FML-ADR-045`.
- **Requires hardware:** yes, at least two nodes and several client devices.
