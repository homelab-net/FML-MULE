---
id: TBR-SEC-01
title: Protected storage unlock
status: OPEN
owner: TBD
area: SEC
critical-path: false
depends-on: [TBR-TAK-01]
feeds: [TBR-HW-01, TBR-REC-01]
evidence: docs/evidence/TBR-SEC-01/
adr: [FML-ADR-041, FML-ADR-042]
---

# TBR-SEC-01 Protected storage unlock

## Question

How does an unattended field node unlock its encrypted storage at boot without
storing the unlock secret next to the data it protects?

## Why it matters

`THREAT_MODEL.md` states that physical capture is an expected condition, not an
edge case. Data-at-rest encryption is the control that limits what a captured
node discloses, and its strength depends entirely on how the volume is
unlocked.

The problem is genuinely hard and does not have a clean local answer. A node
boots in a field with no operator, no network, and no reachback. Every purely
local answer reduces to keeping the key on the device: a key file on an
unencrypted boot partition, a key derived from device identifiers, or a key in
a TPM sealed to a measured boot state that a captured device can simply be
allowed to complete.

Until this closes, treat at-rest encryption as protecting against a casual
finder and not against a motivated adversary. `THREAT_MODEL.md` says exactly
that, and it should keep saying it until there is evidence to say otherwise.

## Options

1. **Operator passphrase at boot.** Genuinely secure against capture-at-rest,
   and incompatible with unattended operation. May still be right for some
   deployment patterns.
2. **TPM or secure element sealed to measured boot.** Protects against pulling
   the storage medium out. Does not protect against a captured node being
   powered on, which is the expected case.
3. **Key from a peer over the mesh.** Requires a quorum of nodes that are
   already unlocked, and fails on a single node deployed alone, which is the
   `v0.0.1` case.
4. **Physical token carried separately from the node.** Moves the problem to
   the operator's procedures, which may be the honest answer.
5. **No at-rest encryption**, with the exposure stated plainly and mission
   material scoped so that capture is survivable. Recorded because an honest
   "we do not protect this" is better than a control that only appears to work.

Note the interaction with `FML-ADR-041`: whatever unlocks the active root must
also work for the known-good rollback path, or rollback becomes a way to boot
the node without its protections.

And with `FML-ADR-042`: a node whose time is not credible refuses to validate
trust material. If unlock depends on validation, a dead clock battery becomes a
node that will not unlock.

## Closure evidence

Committed under `docs/evidence/TBR-SEC-01/`:

- A written analysis of each option against the capture scenarios in
  `THREAT_MODEL.md`, stating for each what an adversary holding the powered-off
  node obtains, and what one holding the powered-on node obtains.
- Demonstrated unlock and boot on candidate hardware for the selected option.
- Demonstrated behaviour of the rollback path under the same scheme.
- Demonstrated behaviour when the clock is not credible.

## Closure gate

A selected scheme boots an unattended node, is analysed against the capture
scenarios with its residual exposure stated in `THREAT_MODEL.md`, and works for
both the active root and the rollback path. The residual exposure statement is
mandatory: a scheme that leaves a captured running node fully readable closes
this trade only if that is written down where an operator will see it.

## Dependencies

- **Depends on:** `TBR-TAK-01` (what must be protected at all).
- **Feeds:** `TBR-HW-01` (secure element availability), `TBR-REC-01`.
- **Requires hardware:** partly. The analysis is the larger half and needs
  none.
