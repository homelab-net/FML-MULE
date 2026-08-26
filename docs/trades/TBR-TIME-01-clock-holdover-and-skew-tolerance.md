---
id: TBR-TIME-01
title: Clock holdover and skew tolerance
status: OPEN
owner: TBD
area: TIME
critical-path: false
depends-on: []
feeds: [TBR-HW-01, TBR-SEC-01]
evidence: docs/evidence/TBR-TIME-01/
adr: [FML-ADR-042]
---

# TBR-TIME-01 Clock holdover and skew tolerance

## Question

How long must a node hold credible time without an external reference, what
skew is tolerable for credential validation, and how is time distributed and
reconciled across a partitioned mesh?

## Why it matters

`FML-ADR-042` decides the **rule**: a battery-backed real-time clock, and trust
validation that never fails open on invalid time. It deliberately does not
decide the **values**, and without them the rule cannot be implemented.

Get the tolerance too tight and nodes refuse to talk to each other after a
weekend in storage. Too loose and expired or revoked credentials are accepted,
which makes the credential system decorative. The plausibility criteria matter
as much as the skew: a node must be able to tell "my clock is wrong" from "my
clock is fine", and a restored-from-shutdown timestamp looks fine while being
wrong.

Distribution across a partition is the harder half. Two groups of nodes, out of
contact, drifting apart, then rejoining, is the normal case for this program.

## Options

Axes: required holdover duration, RTC accuracy and its temperature dependence,
acceptable validation skew window, plausibility criteria at boot, whether time
is distributed peer to peer within a partition and by what rule, whether any
node is authoritative, and what happens when partitions with divergent time
rejoin.

## Closure evidence

Committed under `docs/evidence/TBR-TIME-01/`:

- Measured RTC drift over a recorded interval at recorded temperatures, on
  candidate hardware, over at least the required holdover duration.
- Backup cell service life, from the archived datasheet and from the measured
  standby current of the candidate RTC.
- Demonstrated boot behaviour with a dead backup cell: the node must refuse
  validation and say why, per `FML-ADR-042`.
- Demonstrated rejoin behaviour between two nodes whose clocks have been
  deliberately skewed by more than the tolerance.

## Closure gate

Measured drift over the stated holdover duration stays inside the selected
validation skew window at the ambient range from `TBR-THERM-01`, and a node
with an implausible clock refuses validation with an operator-visible reason.
The partition rejoin rule is written and demonstrated.

## Dependencies

- **Depends on:** none, though ambient range comes from `TBR-THERM-01` when it
  is available.
- **Feeds:** `TBR-HW-01` (RTC as a mandatory bill-of-material line),
  `TBR-SEC-01`.
- **Requires hardware:** yes for drift measurement. The skew window analysis
  and the partition rule can be worked without.
