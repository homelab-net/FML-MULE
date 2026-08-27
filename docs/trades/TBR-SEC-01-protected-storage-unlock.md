---
id: TBR-SEC-01
title: Protected storage unlock
status: OPEN
owner: TBD-SRR
area: SEC
priority: 6
function-owner: Security + Hardware
critical-path: false
depends-on: [TBR-TAK-01]
feeds: [TBR-HW-01, TBR-CARRIER-01, TBR-REC-01]
requires-hardware: partly
evidence: docs/evidence/TBR-SEC-01/
adr: [FML-ADR-043, FML-ADR-044, FML-ADR-041, FML-ADR-042]
target-date: TBD-SRR
---

# TBR-SEC-01 Protected storage unlock

**Source:** SAD v0.31 section 27.5.2, and the TBR register in SAD section
30.2 (priority 6 of 16).

**Function owner:** Security + Hardware. **Named owner:** `TBD-SRR`.

SAD section 30.2 records an SRR exit action: the Program Owner assigns one named
individual and one calendar target date to every open TBR. `TBD-SRR` marks the
gap explicitly rather than hiding it behind a functional organization.

## Question

How is protected mission storage unlocked on a headless captured-risk node?

## Why it matters

`FML-ADR-043` requires LUKS2-class encryption and **rejects an unattended key
stored plainly on the same media as the data**. That leaves the unlock method
unsolved, and it must be solved before the hardware block is locked because it
may add a hardware root of trust requirement to `TBR-HW-01` and
`TBR-CARRIER-01`.

The problem is genuinely hard. A node boots in a field with no operator, no
network and no reachback. Every purely local answer reduces to keeping the key
on the device.

Until it closes, `THREAT_MODEL.md` states that at-rest encryption protects
against a casual finder and not against a motivated adversary.

## Options

SAD section 27.5.2 fixes the comparison set:

1. **operator-entered mission or recovery passphrase** - secure against
   capture-at-rest, incompatible with unattended operation;
2. **TPM 2.0 or equivalent hardware-backed sealed key** plus controlled
   recovery - protects against pulling the storage medium, not against a
   captured node being powered on;
3. **secure-element-assisted mission key architecture**;
4. **combinations** of hardware sealing and operator authorization.

Note the interaction with `FML-ADR-041`: whatever unlocks the active root must
also work for the known-good rollback path, or rollback becomes a way to boot
the node without its protections. And with `FML-ADR-042`: if unlock depends on
validation, a dead clock battery becomes a node that will not unlock.

## Closure evidence

SAD section 27.5.2 requires the trade to address unattended restart after
brownout or battery change; a captured intact node; removed storage media; a
compromised boot image; field recovery in gloves and darkness; loss of the
authorized operator; fleet rekey; and hardware availability and carrier-board
impact.

Plus: demonstrated unlock and boot on candidate hardware; demonstrated behaviour
of the rollback path under the same scheme; demonstrated behaviour when the
clock is not credible; and the zeroize test that verifies `FML-ADR-044`.

Evidence is committed under `docs/evidence/TBR-SEC-01/`.

## Closure gate

A selected scheme boots an unattended node, is analysed against the capture
scenarios in `THREAT_MODEL.md` with its residual exposure stated there, and
works for both the active root and the rollback path.

**The residual exposure statement is mandatory.** A scheme that leaves a
captured running node fully readable closes this trade only if that is written
down where an operator will see it.

**Closure gate per SAD section 30.2:** Before hardware block lock / Stage 9.

No TBR closes on document wording alone. It closes only when its listed evidence
exists, the named owner accepts the evidence, and the resulting architecture
decision is entered into the persistent ADR register.

## Dependencies

- **Depends on:** `TBR-TAK-01`
- **Feeds:** `TBR-HW-01`, `TBR-CARRIER-01`, `TBR-REC-01`
- **Related decisions:** `FML-ADR-043`, `FML-ADR-044`, `FML-ADR-041`, `FML-ADR-042`
- **Validating stage:** Stage 9 (CONOPS section 78)
- **Requires hardware:** The analysis against capture scenarios is the larger
  half and needs no hardware.
Demonstrated unlock needs candidate trust and storage hardware.
