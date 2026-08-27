---
id: FML-ADR-042
title: Battery-backed local RTC + chrony; optional GNSS discipline; credential validity never fails open
status: SELECTED
date: 2026-08-25
supersedes: none
superseded-by: none
trades: [TBR-TIME-01, TBR-HW-01, TBR-SEC-01, TBR-HA-01]
verification: Stage 9
---

# FML-ADR-042 Battery-backed local RTC + chrony; optional GNSS discipline; credential validity never fails open

**Source of rationale:** SAD v0.31 section 24.5. See also sections 14.4, 16.3,
22, 25.2 and CONOPS sections 14 and 15.

New in SAD v0.3.

## Context

The system is local-first: no internet, no central server, no reachable time
source. Certificate validity, credential expiry and revocation freshness all
depend on time. Many single-board computers have no battery-backed real-time
clock and restore a plausible-looking time from the last shutdown, which is
worse than having none because it looks valid.

## Decision

Every production MULE hardware block **shall** provide a battery-backed hardware
real-time clock or equivalent retained local time source.

The software time hierarchy is an approved GNSS or NTP source when available,
then `chrony`, then local system time, then a peer or local NTP service as
required, feeding logs, TAK, certificates, MQTT and audit.

**GNSS is optional mission hardware, not a prerequisite for baseline boot. WAN
time is opportunistic and never the only time source.**

On boot the node **shall** evaluate whether retained time is plausible before
trust-sensitive operations proceed. If local time is invalid or exceeds the
approved uncertainty or skew threshold, the node **shall** enter `TIME_DEGRADED`
and:

- certificate validity and expiry checks **shall not** fail open;
- basic local networking **may** continue where safe;
- trust-sensitive enrollment, credential renewal and authoritative service
  promotion **may** be restricted;
- the operator **shall** receive a clear recovery indication.

## Status

`SELECTED`.

The **rule** is decided independently of the **values**. Holdover duration,
acceptable skew, plausibility criteria, automatic correction from peer or GNSS
time, behaviour when sources disagree, and maximum disconnected mission duration
are `TBR-TIME-01`.

`TBR-TIME-01` also gates `TBR-HA-01`: any time-sensitive authority mechanism
needs the clock and holdover bounds first (SAD sections 14.4 and 14.7).

## Consequences

- An RTC and its backup cell become mandatory bill-of-material lines, and a
  compute module without one is disqualified. Feeds `TBR-HW-01`. SAD section
  24.5.3 makes RTC availability, backup-cell interface, RTC current draw,
  optional GNSS/PPS interface and time-state retention through battery
  replacement inputs to the compute and carrier trade.
- The backup cell is a consumable with a service life and a disposal path. See
  `SAFETY.md` and `hardware/lifecycle/`.
- **Fail-closed means a node with a dead clock battery will refuse to join, in
  the field, during an incident.** That is intended, and it will be unwelcome.
  The operator-visible reporting requirement exists so it is diagnosable rather
  than mysterious; `FML-ADR-046` requires the Status Aggregator to report time
  state.
- Time distribution across a partitioned mesh is unsolved and is not decided
  here.
- CONOPS section 15 depends on this: bounded credential lifetimes only fail safe
  by expiry if the node can tell what time it is.

## Accepted cost

The program accepts that a node may refuse to operate for a reason unrelated to
radio or power, and accepts the recurring maintenance of a backup cell, in
exchange for not silently accepting expired or revoked credentials. Failing open
would make the credential system decorative, which is worse than having none,
because a decorative control gets relied on.

## Fallback

None on the fail-closed rule; it is a security property, not a preference. The
retained-clock mechanism could in principle be replaced by a trusted local time
source elsewhere in the deployment, but nothing of that kind exists in the
operational concept.

## Superseded by

None.

## Verification dependency

Stage 9, with Stage 1 for boot behaviour. `TBR-TIME-01` closure requires RTC
drift measurement, battery-change holdover, invalid-time boot, a
conflicting-source test and the HA timing constraints.
