---
id: FML-ADR-066
title: The RF voice gateway is an integrated dedicated radio per RoIP-capable node
status: PROPOSED
date: 2026-08-31
supersedes: none
superseded-by: none
trades: [TBR-VOICE-01, TBR-COMP-01, TBR-RF-02]
verification: Stage 4
---

# FML-ADR-066 The RF voice gateway is an integrated dedicated radio per RoIP-capable node

**Source of rationale:** `docs/change-requests/CCR-03-integrated-rf-dm32-roip-voice.md`.
CONOPS section 45.2, RF gateway.

## Context

`PROPOSED`. Deconflicted from the handoff's `FML-ADR-053`, which is assigned to
BATMAN-IV routing.

A RoIP-capable MULE needs a radio it can key and listen on. That gateway radio
is distinct from an operator's personal handheld, so that using the gateway does
not require an operator to surrender the only radio they carry.

## Decision

Each RoIP-capable MULE has a **dedicated gateway radio**, integrated into or
mechanically retained as part of the node, reached through a controlled
audio/PTT interface.

The prototype interface is a DigiRig Mobile-class USB device: CM108 USB audio
and a CP2102 serial line whose RTS controls an open-collector PTT. Production
may replace the external DigiRig with equivalent integrated USB-audio and PTT
electronics after electrical qualification.

**A gateway MULE is not a distinct hardware variant.** The gateway role is
configuration on a standard node (`CCR-03`, VOICE-L1-014), so the fleet stays
field-replaceable per CONOPS.

## Status

`PROPOSED`. Depends on `CCR-03` and CONOPS v1.1 approval.

## Consequences

The node gains one USB audio device and one serial PTT endpoint, which the BOM
budgets and which `TBR-COMP-01` must include in the worst-case service-host test
alongside an active RoIP session.

**A transmitting radio moves inside the enclosure with HaLow and LoRa.** RF
coexistence and desense are `TBR-RF-02` and `FML-ADR-027`, and the BOM's GATE
VOICE-01 and VOICE-09 are where they are measured.

## Accepted cost

**Cost, volume and a transmitting emitter in the pouch.** A dedicated gateway
radio is about $90 COTS, plus interface and cabling, and it adds an RF source
next to the sub-GHz receivers. Accepted because the alternative, borrowing an
operator's handheld, breaks voice PACE the moment the gateway is needed.

## Fallback

`ARTICLE 0` in the BOM: the DigiRig stays external for functional verification
before any integration is committed. If integration fails PACK or thermal, the
gateway remains an external tethered unit.

## Superseded by

None.

## Verification dependency

Stage 4. GATE VOICE-01 electrical, VOICE-09 pack/thermal, and the `TBR-RF-02`
coexistence work.
