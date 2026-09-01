---
id: FML-ADR-065
title: Handheld voice is extended by audio and PTT over IP not native DMR
status: PROPOSED
date: 2026-08-31
supersedes: none
superseded-by: none
trades: [TBR-VOICE-01, TBR-RF-01]
verification: Stage 4
---

# FML-ADR-065 Handheld voice is extended by audio and PTT over IP not native DMR

**Source of rationale:** `docs/change-requests/CCR-03-integrated-rf-dm32-roip-voice.md`.
CONOPS section 45.2, RF gateway, and section 45.3, IP-enabled radio.

## Context

`PROPOSED`. Deconflicted from the handoff's `FML-ADR-052`, which is assigned.

When a MULE extends handheld voice over IP, it can either tunnel the native DMR
protocol (MMDVM-class) or carry decoded audio plus PTT state. The choice sets
what the MULE has to understand about radio.

## Decision

MULE extends handheld-radio voice by carrying **audio and PTT state over IP**.
Native DMR protocol tunnelling and MMDVM are **not** required for the baseline.

A consequence stated so it is not lost: because the MULE carries audio and not
the RF waveform, **the local and remote gateway radios need not share a
frequency**. Each gateway matches its own local net; the MULE bridges audio
between them.

## Status

`PROPOSED`. Depends on `CCR-03` and CONOPS v1.1 approval.

## Consequences

The MULE stays out of the RF-protocol business, which `docs/NON-GOALS.md`
requires: it does not become a DMR router. The gateway is radio-agnostic, so
`FML-ADR-064`'s radio can be replaced without touching the transport.

**It adds a real-time audio flow to the bearer.** That flow rides the same mesh
whose addressing is `FML-ADR-063` and whose behaviour under load is
`TBR-RF-01`, and it needs the QoS treatment `CCR-03` proposes.

## Accepted cost

**Audio quality and added latency of decode-recode**, versus a native protocol
tunnel that would preserve the digital stream. Accepted because a tunnel would
make one radio protocol the architectural core and forbid the analog and
mixed-fleet cases the group actually has.

Native DMR/MMDVM remains an **optional future capability** if talkgroup-level
integration is ever shown to be worth it; this ADR does not foreclose it.

## Fallback

If audio/PTT RoIP cannot meet intelligibility or latency criteria on the field
bearers, the fallback is direct RF only, with no IP voice extension. Local voice
never depended on the IP path (`FML-ADR-067`), so this degrades reach, not
safety.

## Superseded by

None.

## Verification dependency

Stage 4. GATE VOICE-02 (local RoIP) and VOICE-03 (different frequencies) in the
BOM.
