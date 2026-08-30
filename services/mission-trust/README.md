# Mission trust

**APPROVED, NOT YET IMPLEMENTABLE. This directory contains this `README.md` and
nothing else.**

The fail-closed time decision this component depends on already exists as a
pure function in `mule/`, under `FML-ADR-052`. See "what already exists in
`mule/`" below.

`FML-ADR-047` approves the Mission Trust Service as **thin original software**,
and states that it **is not a CA**.

Approval is not permission to start. This is the component where building early
does the most damage, because a trust system that is wrong is worse than none: a
decorative control gets relied on.

## What it does

**Source:** SAD v0.31 section 16.2.

Local enforcement and distribution of signed mission authorization state:

- the current mission trust bundle;
- credential-expiry policy;
- signed revocation records;
- signed role and scope policy data where used;
- node revocation data;
- trust-state status for administrators;
- propagation over available approved IP paths.

It distributes validated signed state issued by an authorized mission or
enrollment function. `FML-ADR-036` makes Smallstep `step-ca` the preferred
initial PKI, with the root signing key offline and never required on a MULE.

It also supplies the local trust and revocation material the hostapd integrated
EAP server needs for offline EUD admission (`FML-ADR-038`).

## Scope limit

From SAD section 29.5:

> Not a CA; validates and distributes signed mission trust state.

**Owner:** Security / Identity.

## What already exists in `mule/`

Two modules act on `FML-ADR-042`, the fail-closed time decision this component
depends on. Neither is part of this component, and both are named here so that
a reader does not conclude the decision is unimplemented.

- `mule/timekeeping.py` decides whether the node's own clock is credible, and
  refuses with a diagnosable reason when it is not.
- `mule/admission.py` consumes that assessment, so a node with untrustworthy
  time does not admit a user.
- `mule/status.py` cites the same decision, and only as a precedent: it reads
  an unknown LoRa stack state as unavailable on the same fail-closed grounds
  `FML-ADR-042` applies to retained time. It decides nothing about time and
  nothing about trust.

`FML-ADR-042` binds any component that validates trust, and this one will
inherit those functions rather than repeat them: a second implementation of
"is the time credible" is a second answer, and the two would eventually differ.

Nothing else here exists. No trust bundle, no revocation record, no expiry
policy, no propagation, and no signature validation of any kind. `mule/` decides
nothing about trust; it decides whether the clock underneath trust can be
believed, which is a precondition, not a part.

## What must close before implementation starts

| Question | Trade | Priority |
| --- | --- | ---: |
| How an unattended node unlocks protected storage | `TBR-SEC-01` | 6 |
| Clock holdover, skew tolerance, partition reconciliation | `TBR-TIME-01` | 5 |
| What mission state exists and what must be protected | `TBR-TAK-01` | 9, `CRITICAL` |
| Whether a common browser-service IdP is needed | `TBR-ID-01` | 14 |

## Why not build it anyway

**Unattended unlock is unsolved.** `TBR-SEC-01` is open, and every purely local
answer reduces to keeping the key near the data it protects. An implementation
written now would embed one of those answers as though it were adequate.

**Revocation on a partitioned network is bounded by nothing yet.**
`FML-ADR-047` states plainly that the architecture **does not claim
instantaneous offline revocation**. A credential revoked centrally stays valid
on a partition that has not learned of it, until it expires. CONOPS section 15
requires that limitation to appear in administrator and Team Lead training
material.

**The trust boundary is not decided.** `THREAT_MODEL.md` and CONOPS section 23
both record that there is no meaningful compartmentation between admitted
participants: a participant admitted to a mission sees the mission. Whether any
compartmentation is possible is part of `TBR-TAK-01`, and it determines what
this component is even for.

## What can be done now

- **Close `TBR-TAK-01`**, which needs no hardware and determines the trust
  boundary this component enforces.
- **Work the `TBR-SEC-01` analysis half**, which also needs no hardware:
  evaluate each unlock option against the capture scenarios in
  `THREAT_MODEL.md`, stating what an adversary holding a powered-off node
  obtains and what one holding a powered-on node obtains.
- **Work `TBR-ID-01`**, which needs no hardware.
- **Do not commit key material of any kind**, in any form, at any stage. See
  `SECURITY.md`.

## Fail closed

`FML-ADR-042` binds this component directly: trust validation **shall not** fail
open on invalid, implausible or unavailable time. A node in `TIME_DEGRADED`
refuses to validate rather than accepting material it cannot check, and reports
why.

That will be unwelcome the first time a node with a dead clock battery refuses
to join during an incident. Failing open would make the credential system
decorative, which is worse.
