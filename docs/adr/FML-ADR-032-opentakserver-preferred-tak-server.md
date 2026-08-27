---
id: FML-ADR-032
title: OpenTAKServer is preferred initial TAK-compatible server
status: PREFERRED
date: 2026-08-25
supersedes: none
superseded-by: none
trades: [TBR-TAK-01, TBR-COMP-01, TBR-HA-01]
verification: Stage 5
---

# FML-ADR-032 OpenTAKServer is preferred initial TAK-compatible server

**Source of rationale:** SAD v0.31 section 13.1. See also sections 9.4, 13.3,
14 and 29.

Carries forward draft `AD-012`; see SAD section 0.8.

## Context

CONOPS section 24 does not mandate a specific TAK implementation. The program
needs a TAK-compatible server that runs on an SBC, supports ATAK/iTAK/WinTAK,
and provides the enrollment and mission functions the operating concept assumes.

## Decision

**OpenTAKServer** is the **preferred initial** TAK-compatible server
implementation, for its existing support for ATAK/iTAK/WinTAK, TLS CoT
streaming, client certificate enrollment, groups and channels, DataSync and the
Mission API, data packages, Meshtastic integration, a web UI, SBC deployment, a
documented API and SQLAlchemy databases.

The architecture remains **TAK-compatible, not OpenTAKServer-exclusive**.

## Status

`PREFERRED`, not `SELECTED`.

Nothing may depend on OpenTAKServer specifically. The logical service identity
`tak.field` (`FML-ADR-031`), the state classes (CONOPS section 26) and the
continuity pattern (SAD section 14.3) are all expressed in implementation-neutral
terms so that a different TAK-compatible server can be substituted.

## Consequences

- OpenTAKServer currently uses multiple Python processes, RabbitMQ for internal
  CoT messaging, and SQLAlchemy-backed persistent storage (SAD section 13.3).
  **RabbitMQ is treated as local transient service infrastructure**, not a
  field-wide clustered message bus.
- That process and dependency footprint lands on a compute budget that is not
  yet set. `TBR-COMP-01` must measure OpenTAKServer processes, RabbitMQ and
  PostgreSQL if selected.
- It is currently a valid candidate for the native-service exception in
  `FML-ADR-029`, which imposes the reproducibility requirements in SAD section
  9.4 including a restore demonstrated onto a **different eligible node**.
- Where its Meshtastic support satisfies the mission need, it is the first
  integration option before the TAK Meshtastic Gateway or custom PyTAK work
  (`FML-ADR-048`).

## Accepted cost

The program accepts a multi-process Python service with a message broker on a
power- and memory-constrained node, before that budget is measured. It accepts
that "preferred" gives no protection if the project's direction changes, and
mitigates that by keeping every dependent decision implementation-neutral.

## Fallback

Another TAK-compatible server. Because the architecture is expressed in terms of
CoT, the logical service identity and the state classes, substitution is a BOM
and configuration change rather than a re-architecture. It would supersede this
ADR.

## Superseded by

None.

## Verification dependency

Stage 5. `TBR-TAK-01` must classify where this implementation actually stores
mission-critical persistent state before any HA mechanism is selected. SAD
section 14.2 warns that database support claimed by an ORM is not sufficient
acceptance evidence.
