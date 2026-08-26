# Mission trust

**PLACEHOLDER. DO NOT IMPLEMENT.**

This directory contains this `README.md` and nothing else, by decision. See
`AGENTS.md`, constraint one, and `services/README.md`, the placeholder rule.

## What this component will do

Decide which nodes and which participants are admitted to a given mission, and
enforce that decision on a network that partitions by design.

Node identity sits below this, in `services/identity/`: a program PKI credential
saying a node is a member of the program. Mission trust sits above it. Being a
valid node does not admit you to a particular mission.

Expected to cover:

- Admission of a node to a mission, and its revocation.
- Admission of a participant, and its revocation.
- Distribution of mission trust material without central infrastructure.
- Behaviour on partition, and reconciliation on rejoin.
- Refusal behaviour when time is not credible (`FML-ADR-042`).

## Decision reference

`FML-ADR-042` binds this component directly: **trust validation shall not fail
open on invalid, implausible, or unavailable time.** A node that cannot
establish credible time refuses to validate rather than accepting material it
cannot check.

Execution model follows `FML-ADR-029`.

## What must close before implementation starts

| Question | Trade |
| --- | --- |
| How an unattended node unlocks protected storage | `TBR-SEC-01` |
| Clock holdover, skew tolerance, partition reconciliation | `TBR-TIME-01` |
| What mission state exists and what must be protected | `TBR-TAK-01` |

## Why not build it anyway

This is the component where building early does the most damage, because a
trust system that is wrong is worse than no trust system: a decorative control
gets relied on.

Three specific reasons:

**Unattended unlock is unsolved.** `TBR-SEC-01` is open, and every purely local
answer reduces to keeping the key next to the data it protects. An
implementation written now would embed one of those answers as though it were
adequate.

**Revocation on a partitioned network is unsolved.** A credential revoked
centrally is still valid on a partition that has not learned of the revocation.
Assume a revoked credential remains usable there. Whether that window can be
bounded at all is `TBD`.

**The trust boundary is not decided.** `THREAT_MODEL.md` records that there is
no meaningful compartmentation between admitted participants: a participant
admitted to a mission sees the mission. Whether any compartmentation is
possible is part of `TBR-TAK-01`, and it determines what this component is even
for.

## What can be done now

- **Close `TBR-TAK-01`**, which requires no hardware and determines the trust
  boundary this component enforces.
- **Work `TBR-SEC-01`'s analysis half**, which also requires no hardware:
  evaluate each unlock option against the capture scenarios in
  `THREAT_MODEL.md`, stating what an adversary holding a powered-off node
  obtains and what one holding a powered-on node obtains.
- **Do not commit key material of any kind**, in any form, at any stage. See
  `SECURITY.md`.
