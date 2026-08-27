---
id: FML-ADR-033
title: PyTAK is preferred custom CoT transport/gateway library
status: SELECTED
date: 2026-08-25
supersedes: none
superseded-by: none
trades: []
verification: Stage 11
---

# FML-ADR-033 PyTAK is preferred custom CoT transport/gateway library

**Source of rationale:** SAD v0.31 section 13.2. See also sections 7.3, 24 and
29.5.

Carries forward draft `AD-013`; see SAD section 0.8.

## Context

Several integration paths may need to emit or consume CoT: the Meshtastic
gateway, external VHF/UHF/HF gateways, and any future translation from a
non-TAK-native system. Each is a temptation to write another CoT transport.

## Decision

**PyTAK shall be the preferred library** for custom CoT clients and translation
gateways where no existing integration satisfies the requirement.

Generic CoT transport **shall not** be reimplemented without cause.

## Status

`SELECTED`.

This is a rule about what custom code may do, not a component selection. It
constrains `FML-ADR-048`: existing OpenTAKServer, Meshtastic and PyTAK
interfaces are used first, and custom translation is protocol-specific glue
only.

## Consequences

- Gateway work becomes translation logic rather than protocol implementation,
  which is the difference between a maintainable integration and a second CoT
  stack.
- The MULE-original software inventory (SAD section 29.5) can hold the Gateway
  Translation Layer to a narrow scope, because transport is not its job.
- A dependency on PyTAK's maintenance is accepted in exchange for not owning CoT
  transport.

## Accepted cost

The program accepts a Python dependency in the gateway path and whatever
performance that implies, in exchange for not maintaining a CoT implementation.
Custom LoRa protocol development is separately out of scope (SAD section 7.3).

## Fallback

If PyTAK proves unsuitable for a specific integration, that integration uses the
upstream project's own supported interface. Writing a replacement CoT transport
would require a superseding ADR stating why upstream interfaces were
insufficient, per the fork rule in SAD section 20.1.

## Superseded by

None.

## Verification dependency

Stage 11 for external interoperability, Stage 3 for the Meshtastic path. No
gateway has been built.
