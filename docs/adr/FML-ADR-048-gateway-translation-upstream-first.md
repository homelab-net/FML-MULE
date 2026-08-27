---
id: FML-ADR-048
title: Gateway translation uses existing OTS/Meshtastic/PyTAK interfaces first; custom translation is protocol-specific glue only
status: SELECTED
date: 2026-08-25
supersedes: none
superseded-by: none
trades: [TBR-TAK-01, TBR-RF-02]
verification: Stage 11
---

# FML-ADR-048 Gateway translation uses existing OTS/Meshtastic/PyTAK interfaces first; custom translation is protocol-specific glue only

**Source of rationale:** SAD v0.31 section 29.5. See also sections 7.3, 13.2,
24 and CONOPS sections 45, 47 and 48.

New in SAD v0.3.

## Context

Several paths may need normalization into CoT or MQTT: the Meshtastic plane,
external VHF/UHF/HF radios, and handoff to organizations that do not use TAK.
Each is an opportunity to write a translation layer that grows into a second
protocol stack.

## Decision

Gateway translation **shall** use existing integrations first, in this priority
order for the LoRa path (SAD section 7.3):

1. existing OpenTAKServer Meshtastic support where it satisfies the mission
   need;
2. the TAK Meshtastic Gateway;
3. PyTAK plus the Meshtastic Python API for only the translation logic not
   already provided upstream.

**Custom translation shall be protocol-specific glue only.** Custom LoRa
protocol development is out of scope.

Approved external VHF/UHF/HF integrations connect through standard interfaces
where possible: USB serial, audio, TNC, Bluetooth, TCP/UDP, or a documented
vendor API. Normalization runs native radio protocol, then approved gateway,
then CoT and/or MQTT, then field services.

## Status

`SELECTED` as a rule, with owner TAK / Integration in the MULE-original software
inventory (SAD section 29.5).

The Gateway Translation Layer is listed there as approved but scope-limited:
"existing OTS/Meshtastic/PyTAK integration first; custom code only for missing
protocol semantics".

Implementation waits on `TBR-TAK-01`, which determines which mission state
matters and therefore what is worth translating, and on `TBR-RF-02` for the
coexistence half of `services/gateways/`.

## Consequences

- `FML-ADR-033` keeps CoT transport out of scope for this layer, so it stays
  translation logic.
- Dire Wolf is the preferred initial AX.25/APRS software modem candidate for
  amateur packet workflows (SAD section 24).
- **Amateur RF remains off by default** and requires the distinct control
  operator role in CONOPS section 7.8. CONOPS section 46 forbids mirroring TAK
  update rates onto shared amateur networks.
- CONOPS section 47 requires operational handoff to organizations that do not
  use TAK. The objective is information useful to the supported incident
  organization, **not universal protocol compatibility**.
- Deciding what crosses to the degraded LoRa plane is deciding what matters when
  everything else has failed. That is a CONOPS question informed by
  `TBR-TAK-01`, not a coding decision.

## Accepted cost

The program accepts dependence on upstream integrations whose scope it does not
control, and accepts that where upstream nearly fits, the program will use it
rather than write a better-fitting custom path.

## Fallback

Custom translation for a specific protocol where no upstream integration exists.
That is permitted by this rule, provided it stays protocol-specific glue and
carries the SAD section 29.5 requirements: an owner, an interface contract, a
reason upstream cannot do it, tests, a resource budget and a sustainment owner.

## Superseded by

None.

## Verification dependency

Stage 11 for external interoperability, Stage 3 for the Meshtastic path.
`services/gateways/` holds a README and nothing else until `TBR-TAK-01` and
`TBR-RF-02` close.
