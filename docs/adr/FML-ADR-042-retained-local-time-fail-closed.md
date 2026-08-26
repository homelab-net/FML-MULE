---
id: FML-ADR-042
title: Retained local time via battery-backed RTC, trust validation never fails open on invalid time
status: SELECTED
date: TBD
supersedes: none
superseded-by: none
trades: [TBR-TIME-01, TBR-SEC-01, TBR-HW-01]
verification: TBD
---

# FML-ADR-042 Retained local time via battery-backed RTC, trust validation never fails open on invalid time

This is a stub. The **system architecture description is the source of
rationale**; see `docs/architecture/README.md`.

## Context

The system is local-first: no internet, no central server, no reachable time
source. Certificate validity, credential expiry and revocation freshness all
depend on time. A node that boots believing it is 1970 will either reject
everything or, if it is written carelessly, accept everything.

Many single-board computers have no battery-backed real-time clock and restore
a plausible-looking time from the last shutdown, which is worse than having
none, because it looks valid.

## Decision

Every node **shall** carry a battery-backed real-time clock that retains time
across power loss.

Trust validation **shall not** fail open on invalid, implausible, or
unavailable time. A node that cannot establish credible time **shall** refuse
to validate credentials rather than accept material it cannot check.

The node **shall** be able to report that its time is not credible, so an
operator can see why validation is refusing.

## Status

`SELECTED`.

Holdover duration, acceptable skew, plausibility criteria, and behaviour on
partition are `TBD`: `TBR-TIME-01`. The fail-closed rule is decided
independently of those values and does not wait on them.

## Consequences

- A real-time clock and its backup cell become mandatory line items in every
  hardware block's bill of material, and a hardware block without one is
  disqualified. Feeds `TBR-HW-01`.
- The backup cell is a consumable with a service life and a disposal path. See
  `SAFETY.md` and `hardware/lifecycle/`.
- Fail-closed means a node with a dead clock battery will refuse to join, in
  the field, during an incident. That is the intended behaviour and it will be
  unwelcome when it happens. The operator-visible reporting requirement exists
  so it is diagnosable rather than mysterious.
- Time distribution across a partitioned mesh is unsolved and is not decided
  here.
- This is a direct dependency of the identity and mission trust design.

## Accepted cost

The program accepts that a node may refuse to operate for a reason unrelated to
radio or power, and accepts the recurring maintenance of a backup cell, in
exchange for not silently accepting expired or revoked credentials. Failing
open would make the credential system decorative.

## Fallback

None on the fail-closed rule; it is a security property, not a preference.
The retained-clock mechanism could in principle be replaced by a trusted local
time source elsewhere in the deployment, but nothing of that kind exists in the
operational concept.

## Superseded by

None.

## Verification dependency

`TBD` pending `TBR-TIME-01`. Requires a stage that powers a node down for a
recorded interval, restarts it disconnected, and confirms both retained time
and correct refusal behaviour with a deliberately dead clock.
