---
id: TBR-TIME-01
title: Clock holdover and skew tolerance
status: OPEN
owner: Cameron Zobrist
area: TIME
priority: 5
function-owner: Platform + Security
critical-path: false
depends-on: []
feeds: [TBR-HW-01, TBR-SEC-01, TBR-HA-01, TBR-ID-01, TBR-CARRIER-01]
requires-hardware: yes
evidence: docs/evidence/TBR-TIME-01/
adr: [FML-ADR-042, FML-ADR-036]
target-date: 2026-09-30
---

# TBR-TIME-01 Clock holdover and skew tolerance

**Source:** SAD v0.31 section 24.5.2, and the TBR register in SAD section
30.2 (priority 5 of 16).

**Function owner:** Platform + Security. **Named owner:** `TBD-SRR`.

SAD section 30.2 records an SRR exit action: the Program Owner assigns one named
individual and one calendar target date to every open TBR. The named individual
is assigned as of 2026-08-31. The target date was set to 2026-09-30 on 2026-09-04; for a hardware-gated
trade it is a target the program drives toward, not a claim the capability
exists by then.

## Question

What RTC/GNSS/skew/holdover behavior preserves certificate and authority correctness offline?

## Why it matters

`FML-ADR-042` decides the **rule**: a battery-backed RTC, and trust validation
that never fails open on invalid time. It deliberately does not decide the
**values**, and without them the rule cannot be implemented.

Too tight and nodes refuse to talk to each other after a weekend in storage. Too
loose and expired or revoked credentials are accepted, which makes the credential
system decorative.

SAD sections 14.4 and 14.7 make this a gate on `TBR-HA-01`: any time-sensitive
authority mechanism needs the clock and holdover bounds first. It is also a
hardware input, per SAD section 24.5.3.

## Options

Axes: required holdover duration; RTC accuracy and its temperature dependence;
acceptable validation skew window; plausibility criteria at boot; whether time
is distributed peer to peer within a partition and by what rule; whether any
node is authoritative; and what happens when partitions with divergent time
rejoin.

Distribution across a partition is the harder half. Two groups of nodes, out of
contact, drifting apart, then rejoining, is the normal case for this program.

## Closure evidence

SAD section 30.2 requires: RTC drift; battery-change holdover; invalid-time boot;
a conflicting-source test; and the HA timing constraints.

Specifically:

- measured RTC drift over a recorded interval at recorded temperatures, over at
  least the required holdover duration;
- backup-cell service life, from the archived datasheet and the measured standby
  current of the candidate RTC;
- demonstrated boot behaviour with a dead backup cell: the node must enter
  `TIME_DEGRADED`, refuse validation, and say why;
- demonstrated rejoin behaviour between two nodes deliberately skewed beyond
  tolerance.

Evidence is committed under `docs/evidence/TBR-TIME-01/`.

## Closure gate

Measured drift over the stated holdover duration stays inside the selected
validation skew window at the ambient range from `TBR-THERM-01`, and a node with
an implausible clock refuses validation with an operator-visible reason.

The partition rejoin rule is written and demonstrated.

**Closure gate per SAD section 30.2:** Before HW/HA/security lock / Stages 1, 9.

No TBR closes on document wording alone. It closes only when its listed evidence
exists, the named owner accepts the evidence, and the resulting architecture
decision is entered into the persistent ADR register.

## Dependencies

- **Depends on:** none
- **Feeds:** `TBR-HW-01`, `TBR-SEC-01`, `TBR-HA-01`, `TBR-ID-01`, `TBR-CARRIER-01`
- **Related decisions:** `FML-ADR-042`, `FML-ADR-036`
- **Validating stage:** Stage 9 (CONOPS section 78)
- **Requires hardware:** Drift measurement needs candidate RTC hardware and a temperature-controlled
interval. The skew-window analysis and the partition rule can be worked without
hardware.
