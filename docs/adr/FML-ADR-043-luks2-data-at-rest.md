---
id: FML-ADR-043
title: Sensitive local mission data uses LUKS2-class block encryption; key-on-same-media unattended unlock is rejected
status: SELECTED PRINCIPLE
date: 2026-08-25
supersedes: none
superseded-by: none
trades: [TBR-SEC-01, TBR-HW-01, TBR-CARRIER-01, TBR-REC-01]
verification: Stage 9
---

# FML-ADR-043 Sensitive local mission data uses LUKS2-class block encryption; key-on-same-media unattended unlock is rejected

**Source of rationale:** SAD v0.31 sections 27.5.1 and 27.5.2. See also sections
27.5.3, 27.5.4, 28, 29 and CONOPS section 69.

New in SAD v0.3.

## Context

CONOPS section 69 requires that loss or capture of one MULE **shall not**
automatically compromise the entire organization, and lists encrypted data at
rest among the required production controls. Capture is an expected condition,
not an edge case.

## Decision

Sensitive local mission data **shall** be stored on a **LUKS2-class encrypted
block volume**, or an equivalent open, reviewed Linux block-encryption
implementation.

The production design **should** separate a rebuildable boot and base-system
area sufficient to start controlled recovery and baseline networking, from
protected mission-sensitive state requiring an approved unlock method.

**The architecture rejects an unattended encryption key stored plainly on the
same removable or storage media as the encrypted data**, because that provides
little capture protection.

## Status

`SELECTED PRINCIPLE`.

The **property** is decided; the **unlock method** is not. `TBR-SEC-01` selects
it before the hardware block is locked, comparing at minimum an operator-entered
mission or recovery passphrase, a TPM 2.0 or equivalent hardware-backed sealed
key with controlled recovery, a secure-element-assisted mission key
architecture, and combinations of hardware sealing with operator authorization.

The trade **shall** address unattended restart after brownout or battery change,
a captured intact node, removed storage media, a compromised boot image, field
recovery in gloves and darkness, loss of the authorized operator, fleet rekey,
and hardware availability and carrier-board impact.

**If a hardware root of trust is required, that requirement becomes part of
`TBR-HW-01` and `TBR-CARRIER-01`.**

## Consequences

- Until `TBR-SEC-01` closes, at-rest encryption protects a powered-off node
  against a casual finder and not against a motivated adversary holding a
  running one. `THREAT_MODEL.md` says exactly that.
- The unlock method must also work for the known-good rollback path
  (`FML-ADR-041`), or rollback becomes a way to boot the node without its
  protections.
- It interacts with `FML-ADR-042`: if unlock depends on trust validation, a node
  with an implausible clock may refuse to unlock.
- The split between a rebuildable base area and protected state is what allows a
  captured or failed node to be recovered without exposing mission data.
- A recovered former node **shall not** simply rejoin with stale trust or state;
  it enters the controlled maintenance, rekey and reimage path (SAD section
  27.5.4).

## Accepted cost

The program accepts that the strength of this control depends entirely on an
unresolved trade, and states that limitation publicly rather than implying that
"encrypted at rest" is a complete answer. It accepts that a hardware root of
trust may become a hardware requirement, constraining module selection.

## Fallback

Operator-entered passphrase at boot, which is secure against capture-at-rest and
incompatible with unattended operation. CONOPS section 69 does not permit
abandoning at-rest encryption, so the fallback is a usability cost rather than a
removal of the control.

## Superseded by

None.

## Verification dependency

Stage 9. Encrypted storage, zeroize and capture scenarios. `TBR-SEC-01` closure
requires the passphrase versus TPM or secure-element trade plus capture,
brownout, recovery and zeroize tests.
