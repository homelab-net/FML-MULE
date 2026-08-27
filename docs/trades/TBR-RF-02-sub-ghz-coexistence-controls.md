---
id: TBR-RF-02
title: Sub-GHz coexistence controls
status: OPEN
owner: TBD-SRR
area: RF
priority: 11
function-owner: RF/Spectrum
critical-path: false
depends-on: [TBR-RF-03]
feeds: [TBR-HW-01, TBR-CARRIER-01]
requires-hardware: yes
evidence: docs/evidence/TBR-RF-02/
adr: [FML-ADR-027, FML-ADR-026]
target-date: TBD-SRR
---

# TBR-RF-02 Sub-GHz coexistence controls

**Source:** SAD v0.31 section 8.2, and the TBR register in SAD section
30.2 (priority 11 of 16).

**Function owner:** RF/Spectrum. **Named owner:** `TBD-SRR`.

SAD section 30.2 records an SRR exit action: the Program Owner assigns one named
individual and one calendar target date to every open TBR. `TBD-SRR` marks the
gap explicitly rather than hiding it behind a functional organization.

## Question

What LoRa availability is preserved during HaLow recovery and what supported controls exist?

## Why it matters

HaLow and LoRa may share 902-928 MHz, centimetres apart, in one enclosure. If
HaLow desensitizes the LoRa receiver, the degraded-communications fallback fails
at exactly the moment it is needed, and it fails silently.

CONOPS section 36 gives LoRa preservation priority over aggressive HaLow
reacquisition, and requires System Architecture to **state a LoRa availability or
duty-cycle figure** so the coexistence design has a verifiable target. That
figure does not yet exist; producing it is this trade.

`FML-ADR-027` also makes this trade decide whether a MULE-original coexistence
policy service is needed at all.

## Options

Axes from SAD section 8.1: channel separation, antenna separation, filtering,
time-domain coordination, scan timing, transmit suppression, and duty-cycle
limits.

`FML-ADR-027` requires the trade to first determine whether supported driver,
netlink/nl80211, `iw`, `wpa_supplicant`, Morse Micro or equivalent controls are
sufficient. **Original coexistence software is permitted only if a thin policy
layer is still necessary after that test**, and no driver fork is authorised.

Where a builder enables amateur-band operation, encryption is unlawful in many
jurisdictions, so coexistence policy cannot assume every sub-GHz emission is
confidential.

## Closure evidence

SAD section 30.2: desense; a **supported-control inventory**; recovery; and a
no-fork assessment.

Measured LoRa receive sensitivity with the HaLow radio idle and with it
transmitting at maximum duty, in the assembled enclosure, with antenna positions
recorded. The reciprocal measurement: HaLow link quality with LoRa
transmitting.

Measurements at the antenna separations physically achievable in the candidate
enclosure, not on a bench with the radios far apart. The region profile each
measurement was taken under.

Evidence is committed under `docs/evidence/TBR-RF-02/`.

## Closure gate

A stated LoRa availability or duty-cycle figure to be maintained while HaLow
reacquisition is active, and measured degradation of each bearer in the presence
of the other characterised and either inside that figure or brought inside it by
a demonstrated control.

The figure is written before the measurement. "No interference was observed" is
not closure; the measurement must show the sensitivity figure with and without
the interferer.

**Closure gate per SAD section 30.2:** Before RF design lock / Stage 3.

No TBR closes on document wording alone. It closes only when its listed evidence
exists, the named owner accepts the evidence, and the resulting architecture
decision is entered into the persistent ADR register.

## Dependencies

- **Depends on:** `TBR-RF-03`
- **Feeds:** `TBR-HW-01`, `TBR-CARRIER-01`
- **Related decisions:** `FML-ADR-027`, `FML-ADR-026`
- **Validating stage:** Stage 3 (CONOPS section 78)
- **Requires hardware:** Requires the assembled enclosure and the final radio
  topology from `TBR-RF-03`.
Bench measurements with separated radios do not answer this question.
