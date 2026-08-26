---
id: FML-ADR-045
title: EUD access point and high-throughput inter-node mesh are separate logical radio functions
status: SELECTED PLANNING BASELINE
date: TBD
supersedes: none
superseded-by: none
trades: [TBR-RF-03, TBR-RF-01, TBR-HW-01, TBR-PWR-01]
verification: TBD
---

# FML-ADR-045 EUD access point and high-throughput inter-node mesh are separate logical radio functions

This is a stub. The **system architecture description is the source of
rationale**; see `docs/architecture/README.md`.

## Context

Conventional Wi-Fi is used for two different jobs: a high-throughput bearer
between nodes, and an access point that end-user devices associate with. These
have different channel, power, security and availability requirements. An
operator's phone dropping off should not disturb the inter-node link, and a
mesh reconfiguration should not drop every attached device.

Whether these two functions can share one radio, using multiple virtual
interfaces, or need separate radios, is an open hardware question with cost,
power and thermal consequences.

## Decision

The EUD access point and the high-throughput inter-node mesh **shall** be
treated as separate logical radio functions, with independent configuration,
independent channel selection, and independent security parameters.

Whether they are realised on separate physical radios is deliberately **not**
decided here.

## Status

`SELECTED PLANNING BASELINE`.

Adopted so that configuration structure, the network plane design, and the
hardware block templates can proceed. Expected to be revisited when
`TBR-RF-03` closes on whether one radio can carry both functions acceptably.

Dependent work may build on the logical separation. Nobody should assume the
physical arrangement.

## Consequences

- Configuration templates in `os/config/` are written per logical function, not
  per physical interface, so that a later consolidation does not restructure
  them.
- Each hardware block's `rf/` directory must record how the two functions are
  realised on that block, and blocks may differ.
- If consolidation onto one radio proves acceptable, the saving is in cost,
  power and thermal load, all of which feed `TBR-PWR-01` and `TBR-THERM-01`.
  If it does not, the block needs another radio and another antenna, with
  coexistence consequences shared with `TBR-RF-02`.
- Two functions on one radio share airtime. Whether the access point can starve
  the inter-node bearer, or the reverse, is unmeasured.

## Accepted cost

The program accepts carrying a design that may be more general than the
hardware eventually needs, and accepts that some configuration structure will
look redundant if consolidation succeeds. This is cheaper than discovering that
a shared radio cannot meet both sets of requirements after the enclosure and
antenna arrangement are fixed.

## Fallback

If separation proves unaffordable in power, cost or space, consolidation is the
fallback, and it is the outcome `TBR-RF-03` may well reach. Because the
separation here is logical, taking that path revises this baseline rather than
invalidating the configuration structure.

## Superseded by

None.

## Verification dependency

`TBD` pending `TBR-RF-03`. Requires concurrent access point and inter-node
traffic measurement on candidate hardware, under `test/stages/`. Nothing has
been measured.
