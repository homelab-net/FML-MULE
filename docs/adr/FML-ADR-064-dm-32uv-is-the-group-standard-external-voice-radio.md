---
id: FML-ADR-064
title: DM-32UV is the group-standard external voice radio
status: PROPOSED
date: 2026-08-31
supersedes: none
superseded-by: none
trades: [TBR-VOICE-01]
verification: Stage 4
---

# FML-ADR-064 DM-32UV is the group-standard external voice radio

**Source of rationale:** `docs/change-requests/CCR-03-integrated-rf-dm32-roip-voice.md`
and its received handoffs. CONOPS section 45, external VHF/UHF/HF integration.

## Context

`PROPOSED`, not decided. This ADR reserves the identifier and records the
decision `CCR-03` proposes, so that the number is fixed and consistent while the
CONOPS v1.1 change is under review. It carries no weight until `CCR-03` is
approved. The handoff originally numbered this `FML-ADR-051`, which is already
assigned; the deconflicted number is `FML-ADR-064`.

CONOPS section 45 reserves an integration boundary for external radios and does
not name a radio. The user group has standardised on the Baofeng DM-32UV, and
choosing it as the reference radio lets the audio/PTT interface and the codeplug
control be qualified against real hardware.

## Decision

The **Baofeng DM-32UV** is the group-standard external handheld voice radio for
the current hardware block, analog and DMR capable.

**It is not required for core MULE networking or TAK.** It is an external field
radio, and a different radio may replace it in a later block **provided the
controlled audio/PTT interface contract is preserved and requalified**. The
contract, not the radio, is what this program depends on.

## Status

`PROPOSED`. Depends on `CCR-03` and CONOPS v1.1 approval.

## Consequences

The audio/PTT interface (`FML-ADR-066`) and the codeplug control area can be
qualified against a specific radio rather than an abstraction.

A `VOICE` trade area and `TBR-VOICE-01` are needed regardless of the radio;
this ADR does not create them.

## Accepted cost

**A COTS radio the program does not control.** Firmware, connector and CPS
changes are the vendor's, and `regions/` plus `REGULATORY.md` govern lawful use;
this ADR selects a reference, not a licence to transmit.

## Fallback

Any analog/DMR handheld that meets the audio/PTT interface contract. The
fallback is the reason the contract is the dependency and the radio is not.

## Superseded by

None.

## Verification dependency

Stage 4. The BOM's GATE VOICE-01 is the electrical-interface qualification and
must pass before the DigiRig path in `FML-ADR-066` is committed.
