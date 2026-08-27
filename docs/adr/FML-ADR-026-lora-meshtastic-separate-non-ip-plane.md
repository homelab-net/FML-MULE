---
id: FML-ADR-026
title: Meshtastic/LoRa remains a separate non-IP degraded plane
status: SELECTED
date: 2026-08-25
supersedes: none
superseded-by: none
trades: [TBR-RF-02]
verification: Stage 3
---

# FML-ADR-026 Meshtastic/LoRa remains a separate non-IP degraded plane

**Source of rationale:** SAD v0.31 section 7.1. See also sections 7.2, 7.3, 8
and CONOPS sections 35 and 36.

Carries forward the v0.1/v0.2 `AD-006` decision; see SAD section 0.8.

## Context

LoRa/Meshtastic provides degraded low-bandwidth communications: PLI, short text,
status, alerts, selected geospatial events and compact sensor reports. CONOPS
section 35 states it **shall not** be relied upon to carry arbitrary normal IP
traffic.

Its whole operational value is that it still works when the IP plane does not.

## Decision

LoRa/Meshtastic **shall** be a separate non-IP communications plane.

It **shall not** be bridged into batman-adv and **shall not** be used as an
arbitrary IP tunnel.

The radio attaches to the host through an approved standard interface: USB
serial, UART, or TCP where the radio provides it.

## Status

`SELECTED`.

TAK integration priority is fixed by SAD section 7.3: existing OpenTAKServer
Meshtastic support first, then the TAK Meshtastic Gateway, then PyTAK plus the
Meshtastic Python API for only the translation logic not already provided
upstream. Custom LoRa protocol development is out of scope. See `FML-ADR-048`.

## Consequences

- Plane independence is preserved. A gateway between the planes is a coupling
  and therefore a way for failure to propagate; `services/gateways/` remains a
  placeholder pending `TBR-TAK-01` and `TBR-RF-02`.
- Where the selected Meshtastic hardware contains its own controller and native
  mesh firmware, **host failure should not prevent that radio continuing its
  native Meshtastic participation while independently powered** (SAD section
  7.2). Loss of the primary host may still interrupt TAK translation.
- HaLow and LoRa may share the 902-928 MHz US band and must be treated as
  colocated potentially interfering systems. See `FML-ADR-027` and `TBR-RF-02`.
- CONOPS section 36 requires independent RF chains and independent antennas, and
  gives LoRa preservation priority over aggressive HaLow reacquisition.

## Accepted cost

The program accepts a second sub-GHz radio in the same enclosure, with the
coexistence risk that creates, in exchange for a degraded-communications path
that does not share a failure mode with the IP plane.

It accepts that the bearer carries no arbitrary IP, so any information that must
survive IP loss has to be explicitly selected for translation.

## Fallback

None that preserves the property. Bridging LoRa into the IP mesh would remove
the independence this decision exists to create.

## Superseded by

None.

## Verification dependency

Stage 3. Degraded messaging, independent LoRa operation, HaLow loss and
reacquisition, and HaLow/LoRa coexistence controls. `TBR-RF-02` defines the
measurable LoRa availability target while HaLow recovery is active.
