---
id: FML-ADR-044
title: Zeroize is primarily cryptographic key/credential invalidation, not flash overwrite
status: SELECTED PRINCIPLE
date: 2026-08-25
supersedes: none
superseded-by: none
trades: [TBR-SEC-01]
verification: Stage 9
---

# FML-ADR-044 Zeroize is primarily cryptographic key/credential invalidation, not flash overwrite

**Source of rationale:** SAD v0.31 section 27.5.3. See also sections 27.5.1,
27.5.4 and CONOPS section 70.

New in SAD v0.3.

## Context

CONOPS section 70 requires an approved administrative procedure that removes or
invalidates sensitive field information **without WAN dependency**.

Overwriting every block is slow and unreliable on flash media: wear levelling
means the controller may not expose the physical blocks that hold the data.

## Decision

MULE zeroize **shall** be primarily a **cryptographic erase and trust
invalidation** operation.

An approved zeroize action **shall** remove or invalidate, as applicable: LUKS
mission-volume key material and key slots, mission-scoped private keys, the
WAN-overlay node identity, locally cached mission secrets, privileged tokens,
and current mission configuration secrets.

Zeroize **shall not** rely on overwriting every flash block.

The mechanism **shall** be executable without WAN.

Zeroize **shall** leave the node in a clearly non-operational and untrusted
state requiring controlled reprovisioning before return to service.

## Status

`SELECTED PRINCIPLE`.

The exact activation method, authentication, physical control and recoverability
are Security Architecture and TRD items. The effectiveness of cryptographic
erase depends on `FML-ADR-043` and on the unlock method selected by
`TBR-SEC-01`: destroying key material only helps if the key was the thing
protecting the data.

## Consequences

- Zeroize is fast enough to be usable under pressure, which a full overwrite
  would not be.
- It is only as strong as the encryption it invalidates. A volume whose key was
  stored beside it gains nothing from key destruction, which is why
  `FML-ADR-043` rejects that arrangement.
- A zeroized node is deliberately non-operational. It cannot be used to continue
  the mission, and CONOPS section 73 routes it into the controlled maintenance
  path.
- CONOPS section 18 requires zeroize actions to be recorded as security-relevant
  administrative events.
- CONOPS section 69 requires that a missing node be revocable **without
  cooperation from that node**, so zeroize is a complement to revocation, not a
  substitute for it.

## Accepted cost

The program accepts that data remains physically present on the flash medium
after zeroize, and that its confidentiality then rests entirely on the
encryption and on key destruction having actually succeeded. It accepts that
this is not equivalent to physical destruction, and does not claim otherwise.

## Fallback

Physical destruction of the storage medium, which is outside what an operator
can reliably do in the field and is an organizational procedure rather than a
system function.

## Superseded by

None.

## Verification dependency

Stage 9. SAD section 30.1 records zeroize as OPEN until **destructive test**.
The risk register (SAD section 31) carries "sensitive data survives zeroize" as
OPEN pending Stage 9 destructive verification.
