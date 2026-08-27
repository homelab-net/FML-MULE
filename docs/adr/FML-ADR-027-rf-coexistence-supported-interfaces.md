---
id: FML-ADR-027
title: RF coexistence controlled through supported host/radio interfaces; no assumed openmanetd primitive
status: SELECTED
date: 2026-08-25
supersedes: none
superseded-by: none
trades: [TBR-RF-02, TBR-RF-03]
verification: Stage 3
---

# FML-ADR-027 RF coexistence controlled through supported host/radio interfaces; no assumed openmanetd primitive

**Source of rationale:** SAD v0.31 sections 8.1 and 8.2. See also sections 7.1,
21.2, 29.5 and CONOPS section 36.

Supersedes the v0.1/v0.2 `AD-007` implementation assumption; see SAD section
0.8.

## Context

HaLow and LoRa may share the 902-928 MHz US band, centimetres apart, in one
enclosure. If HaLow desensitizes the LoRa receiver, the degraded-communications
fallback fails at exactly the moment it is needed, and it fails silently.

The earlier draft assumed `openmanetd` would expose the primitives needed to
coordinate the two radios. That assumption was not supported by evidence.

## Decision

RF coexistence **shall** be controlled through a dedicated cross-plane policy
interface built on **documented supported host and radio controls**.

The Network Plane **shall** expose or consume a supported control interface for
HaLow scan and reacquisition state, current channel, transmit state where
available, and temporary transmit suppression or scan control where supported.

The coexistence architecture **shall not** assume that the `openmanetd` API
provides deterministic scan or transmit-suppression primitives. `openmanetd`
**may** be reused where portable and where it exposes the required supported
controls.

The operational priority is fixed by CONOPS section 36:

> When IP is lost, preservation of LoRa degraded communications takes priority
> over aggressive HaLow reacquisition that materially desensitizes the LoRa
> receiver.

## Status

`SELECTED`.

**A MULE-specific coexistence policy service is not yet selected.** `TBR-RF-02`
first determines whether supported driver, netlink/nl80211, `iw`,
`wpa_supplicant`, Morse Micro or equivalent controls are sufficient. Original
coexistence software is permitted only if a thin policy layer is still necessary
after that test, and it appears in the MULE-original software inventory (SAD
section 29.5) as NOT YET SELECTED.

No driver fork is authorised by this decision.

## Consequences

- The implementation may use channel separation, antenna separation, filtering,
  time-domain coordination, scan timing, transmit suppression or duty-cycle
  limits. The mechanism is not fixed here.
- `TBR-RF-02` must produce a **supported-control inventory** as closure
  evidence, not merely a measurement, so the program knows what it can actually
  command.
- Coexistence measurement must be taken in the assembled enclosure at achievable
  antenna separations. Bench measurements with the radios far apart do not
  answer the question.
- The final radio topology from `TBR-RF-03` feeds this trade (SAD section 30.3).
- Where a builder enables amateur-band operation, encryption is unlawful in many
  jurisdictions, so coexistence policy cannot assume every sub-GHz emission is
  confidential.

## Accepted cost

The program accepts that it may not be able to command deterministic transmit
suppression at all, and that the achievable coexistence control may be weaker
than the operational priority would prefer. `TBR-RF-02` is required to state a
measurable LoRa availability or duty-cycle target so the design has a verifiable
figure rather than an intention.

## Fallback

If supported controls prove insufficient and a thin policy service is still not
enough, the remaining levers are physical: antenna separation, filtering, and
channel plan separation within the band, or accepting and characterising the
degradation. CONOPS section 36 permits any of these.

## Superseded by

None.

## Verification dependency

Stage 3. Measured LoRa receive sensitivity with the HaLow radio idle and
transmitting, the reciprocal measurement, at achievable enclosure separations,
with the region profile recorded. See `TBR-RF-02`.
