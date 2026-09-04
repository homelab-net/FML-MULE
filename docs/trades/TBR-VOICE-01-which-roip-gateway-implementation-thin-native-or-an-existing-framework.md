---
id: TBR-VOICE-01
title: Which RoIP gateway implementation, thin native or an existing framework
status: OPEN
owner: Cameron Zobrist
area: VOICE
priority: 99
function-owner: Network
critical-path: false
depends-on: []
feeds: []
requires-hardware: partly
evidence: docs/evidence/TBR-VOICE-01/
adr: [FML-ADR-065, FML-ADR-066, FML-ADR-067]
target-date: 2026-09-30
---

# TBR-VOICE-01 Which RoIP gateway implementation, thin native or an existing framework

**Source:** `docs/change-requests/CCR-03-integrated-rf-dm32-roip-voice.md`,
software implementation trade. CONOPS section 45.

## Question

Does the MULE RoIP voice gateway run as a thin FML-native service, or on an
existing open-source RoIP framework?

## Why it matters

`FML-ADR-065` decides the transport is audio and PTT over IP, and `FML-ADR-066`
gives the node a gateway radio, but neither says what software drives it.
`FML-ADR-067` requires that an operator receive linked voice through exactly one
path, which the implementation must guarantee through loop suppression and
single-egress arbitration. The choice sets what has to be built, what has to be
maintained, and what competes with the routing daemon for the one compute
element (`FML-ADR-021`, `services/catalog/`).

Getting it wrong toward "reuse" risks a heavy telephony stack that starves
routing; getting it wrong toward "build" risks reimplementing solved transport
and PTT signalling.

## Options

- **A thin FML-native service:** ALSA capture and playback, Opus, an
  authenticated IP transport, and PTT via serial RTS, with FML owning the
  session, authorization and loop/arbitration logic. Right if the mature
  frameworks are too heavy or too coupled to public infrastructure.
- **SvxLink-class:** a mature amateur-radio linking stack. Right if it runs
  local-first on Debian ARM64, takes USB audio and external PTT, and can be
  policy-controlled by FML.
- **AllStar / Asterisk-class:** a full linking platform. Right only if its
  capability is needed and its footprint is acceptable on the shared host.
- **Another actively maintained open-source RoIP component** meeting the same
  criteria.

## Closure evidence

For each candidate: measured RAM and CPU on the CM4 during an active session
alongside the representative service-host load (`TBR-COMP-01`); one-way latency,
jitter and PTT acquisition/release on the local mesh and over Tailscale; whether
it runs with no public Internet; whether FML mission policy can gate a voice
group; and whether `FML-ADR-067`'s single-egress invariant can be enforced in or
around it. Committed under `docs/evidence/TBR-VOICE-01/`.

## Closure gate

A selection with the measured basis above, accepted by the named owner, and an
ADR entered for the chosen implementation. The gate is a comparison against the
selection criteria in `CCR-03` section 11, not a single threshold.

Not accepted while `CCR-03` is unapproved: the whole voice capability is a
proposed CONOPS v1.1 change, and selecting an implementation for an unadopted
capability decides a consequence before its cause.

## Dependencies

- **Depends on:** `CCR-03` approval for the capability to exist.
- **Feeds:** the voice gateway entry in `services/catalog/` and its Quadlet.
- **Related decisions:** `FML-ADR-065`, `FML-ADR-066`, `FML-ADR-067`, and
  `TBR-COMP-01` for the compute budget.
- **Validating stage:** Stage 4.
- **Requires hardware:** `partly`. The implementation comparison can start
  against a loopback and virtual peers; latency and PTT timing need the DigiRig
  and a DM-32UV, which is the BOM's GATE VOICE-01 hardware.

## Frontmatter notes

`priority` is 99 because this trade postdates the SAD section 30.2 register.
`critical-path` is `false` on the same grounds; it is not a judgement of
importance. `owner` is a named individual because the trade was raised inside
the repository.
