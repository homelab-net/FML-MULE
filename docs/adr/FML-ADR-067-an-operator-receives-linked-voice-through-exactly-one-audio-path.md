---
id: FML-ADR-067
title: An operator receives linked voice through exactly one audio path
status: PROPOSED
date: 2026-08-31
supersedes: none
superseded-by: none
trades: [TBR-VOICE-01]
verification: Stage 4
---

# FML-ADR-067 An operator receives linked voice through exactly one audio path

**Source of rationale:** `docs/change-requests/CCR-03-integrated-rf-dm32-roip-voice.md`,
section 7 (the double-audio rule) and the radio-primary headset decision.
CONOPS section 45 external integration, and section 5 familiar-interface
principle.

## Context

`PROPOSED`. Deconflicted from the handoff's `FML-ADR-054`, which is assigned to
bridge loop avoidance.

An operator wears one headset on their **personal** DM-32UV and hears voice over
local RF, the way they always have. The MULE extends *remote* voice to them, and
the hazard is that the same voice arrives twice: once by one route and once by
another, producing echo or doubled speech in the ear. This ADR makes "exactly
one copy reaches the operator" a baseline invariant rather than a tuning goal,
which is what the Program Owner asked for.

## Decision

**For any linked voice session, an operator's headset shall receive it through
exactly one audio path.** In the v1 baseline that path is always the operator's
own radio over the local RF net. Three requirements make that hold, and all
three are baseline, not optional:

1. **No direct MULE-to-headset audio in v1.** The MULE does not mix audio into
   an operator's headset. Remote voice reaches the operator only by the MULE
   keying the **local gateway radio** onto the local RF net, where the
   operator's own radio receives it. There is one egress to the operator, the
   local RF net, and the direct path does not exist to compete with it. Future
   direct-to-headset audio for non-radio content (alerts, assistant) is a
   separate dual-comm design and is out of this baseline.

2. **Self-echo suppression.** A stream shall not be retransmitted onto a net it
   originated from or has already traversed. Every session carries an origin
   node ID and session ID, and a gateway shall not key its local radio with a
   session that entered from that same local net. Without this, an operator
   keying up hears themselves returned a moment later.

3. **Single active egress per voice group per local net.** At most one gateway
   shall retransmit a given linked voice group onto a given local RF net at one
   time. Where two RoIP-capable MULEs are in RF range of the same net and both
   carry the group, they arbitrate so exactly one is the egress. Without this,
   an operator in range of two gateways hears the remote talker twice.

The invariant is the requirement; the three are how it is met. A test that plays
one remote talker and confirms the operator's radio reproduces it once, with no
echo of the operator's own transmission and no doubling from a second gateway,
is the acceptance.

## Status

`PROPOSED`. Depends on `CCR-03` and CONOPS v1.1 approval. Within the voice
capability, the invariant is **non-optional**: a voice baseline that can deliver
two copies to an ear is not acceptable, so if the capability is adopted this ADR
is adopted with it.

## Consequences

The gateway service (`FML-ADR-066`, `TBR-VOICE-01`) owns loop and arbitration
state: origin/session IDs, a per-group active-egress election, and a rule that a
local-origin session is never keyed back onto its local net. These are the same
mechanisms `CCR-03` section 10 lists as loop control and half-duplex
arbitration, stated here as a single user-facing invariant they must satisfy.

Keeping the MULE off the headset also keeps the MULE off the critical path for
ordinary voice: an operator whose MULE fails still hears local RF normally,
which is `FML-ADR-064`'s PACE point from the audio side.

## Accepted cost

**Remote voice is heard at local-RF quality, having been decoded, carried as IP,
and re-transmitted over RF.** It is not hi-fi and it inherits the local net's
characteristics. Accepted, because the alternative that would improve it,
feeding MULE audio straight to the headset, is exactly the second path this ADR
forbids.

**No private or per-operator remote audio in v1.** Everyone on the local net
hears a retransmitted remote talker, because the egress is the shared RF net.
Selective or private delivery would need the direct-to-headset path and its
own design.

## Fallback

If single-egress arbitration cannot be made reliable across gateways in shared
RF range, the fallback is to permit only one RoIP-capable gateway per local RF
net by configuration, which satisfies the invariant by construction at the cost
of redundancy.

## Superseded by

None.

## Verification dependency

Stage 4. GATE VOICE-06 (loop/contention) in the BOM is where requirements 2 and
3 are tested; requirement 1 is an architecture property verified by there being
no headset audio interface in the baseline design.
