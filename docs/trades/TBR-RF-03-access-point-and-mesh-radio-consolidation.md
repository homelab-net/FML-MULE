---
id: TBR-RF-03
title: Access point and mesh radio consolidation
status: OPEN
owner: Cameron Zobrist
area: RF
priority: 4
function-owner: Network + RF
critical-path: false
depends-on: []
feeds: [TBR-PWR-01, TBR-RF-01, TBR-RF-02, TBR-HW-01, TBR-CARRIER-01]
requires-hardware: yes
evidence: docs/evidence/TBR-RF-03/
adr: [FML-ADR-045, FML-ADR-025]
target-date: 2026-09-30
---

# TBR-RF-03 Access point and mesh radio consolidation

**Source:** SAD v0.31 section 5.2, and the TBR register in SAD section
30.2 (priority 4 of 16).

**Function owner:** Network + RF. **Named owner:** `TBD-SRR`.

SAD section 30.2 records an SRR exit action: the Program Owner assigns one named
individual and one calendar target date to every open TBR. The named individual
is assigned as of 2026-08-31. The target date was set to 2026-09-30 on 2026-09-04; for a hardware-gated
trade it is a target the program drives toward, not a claim the capability
exists by then.

## Question

Can EUD AP and high-rate inter-node mesh share one physical radio, and what stream/antenna count results?

## Why it matters

`FML-ADR-045` adopts separate physical radios as the **planning baseline** and
names this trade as the one that revisits it. SAD section 30.3 shows RF-03 at
the head of the dependency graph: it feeds power, thermal, antenna count, the
high-rate architecture and coexistence testing.

Consolidation saves a radio, its power, its heat, its antenna feeds and its
cost. Against that, two functions on one radio share airtime and usually a
channel. The operational risks are concrete: an operator's phone associating
disturbs the inter-node link; a mesh reconfiguration drops every attached
device; a device with a poor link drags the radio's rate down.

The answer also sets the antenna and feed count, which sizes the enclosure. SAD
section 25.4.1 warns the enclosure **must not be dimensioned around the earlier
three-radio mental model**.

## Options

1. **One radio, multiple virtual interfaces, same channel.** Cheapest. Both
   functions constrained to one channel despite different coverage
   requirements.
2. **One radio, multiple virtual interfaces, different channels.** Requires
   driver support for concurrent operation and typically costs airtime to
   channel switching. Support is `UNVERIFIED`.
3. **Two radios**, the `FML-ADR-045` planning baseline. Independent channels and
   independent failure, at the cost of power, heat, space and antenna feeds.
4. **Access point only when needed**, brought up on operator action. Reduces
   contention and emissions; complicates operation.

## Closure evidence

SAD section 5.2 fixes the required closure evidence:

- supported concurrent interface modes;
- AP plus 802.11s or mesh stability;
- channel-coupling constraints;
- EUD and client compatibility;
- multicast and roaming behaviour;
- radio recovery behaviour;
- power delta;
- supported spatial-stream count;
- antenna and feed count;
- whether antennas can be internal, external, or must be field replaceable.

Client-visible access point behaviour during a mesh reconfiguration:
association retained or dropped, and for how long.

Evidence is committed under `docs/evidence/TBR-RF-03/`.

## Closure gate

A selected arrangement sustains stated inter-node throughput with a stated number
of associated clients, and associated clients survive a mesh reconfiguration,
both recorded.

If consolidation cannot meet those, the trade closes on separate radios and the
`FML-ADR-045` planning baseline is confirmed rather than revised.

**Closure gate per SAD section 30.2:** Before RF/BOM lock / Stages 1, 4.

No TBR closes on document wording alone. It closes only when its listed evidence
exists, the named owner accepts the evidence, and the resulting architecture
decision is entered into the persistent ADR register.

## Dependencies

- **Depends on:** none
- **Feeds:** `TBR-PWR-01`, `TBR-RF-01`, `TBR-RF-02`, `TBR-HW-01`, `TBR-CARRIER-01`
- **Related decisions:** `FML-ADR-045`, `FML-ADR-025`
- **Validating stage:** Stage 4 (CONOPS section 78)
- **Requires hardware:** Requires at least two nodes and several client
  devices. The prototype BOM gates
the candidate high-rate Wi-Fi card to one unit pending verification, and records
it as the highest-risk item in the BOM.
