---
id: FML-ADR-050
title: Local-storage write amplification is bounded by design through controlled logging/telemetry retention and endurance-qualified storage
status: SELECTED PRINCIPLE
date: 2026-08-25
supersedes: none
superseded-by: none
trades: [TBR-HW-01, TBR-COMP-01, TBR-TAK-01]
verification: Stage 13
---

# FML-ADR-050 Local-storage write amplification is bounded by design through controlled logging/telemetry retention and endurance-qualified storage

**Source of rationale:** SAD v0.31 section 25.8. See also sections 14.2, 21,
26, 31 and CONOPS sections 55-56 and 72.

New in SAD v0.31.

## Context

A field node writes continuously: database and WAL activity, RabbitMQ state,
journald, application logs, local telemetry, TAK mission data, audit logs, and
update and rollback image activity. Flash endurance is finite, and the failure
is slow, silent and fleet-wide.

## Decision

The primary MULE storage path **shall** be selected and configured for sustained
field-service writes, not only nominal capacity.

The architecture rules are fixed by SAD section 25.8:

1. **SD-card storage is not the production database or system-state baseline.**
2. eMMC and NVMe endurance and vendor lifecycle are inputs to `TBR-HW-01`.
3. journald **shall** receive explicit size and retention caps.
4. application logs **shall** use rotation and bounded retention.
5. high-rate observability data **shall** be aggregated, downsampled or
   forwarded rather than retained indefinitely on-node.
6. derived or rebuildable telemetry **shall** be purged before mission-critical
   state.
7. database durability settings **may** be tuned only with documented data-loss
   semantics.
8. storage health and endurance indicators **shall** be included in maintenance
   checks where the hardware exposes them.

## Status

`SELECTED PRINCIPLE`.

Exact byte-per-day limits are TRD and qualification outputs after representative
service testing. `TBR-HW-01` closure evidence must include storage technology,
rated endurance where published, expected write workload, capacity reserve,
SMART/NVMe/eMMC health visibility, and the replaceability and reimage procedure.

## Consequences

- Rule 6 encodes a priority: telemetry that can be rebuilt is discarded before
  mission data that cannot. That priority must be implemented, not assumed.
- Rule 7 constrains a common performance fix. Reducing database durability to
  cut writes trades data loss for endurance, and the semantics must be written
  down.
- The bounded-retention rules align with CONOPS sections 55 and 56, which
  require data minimization and forbid retention defaulting to indefinite
  storage. Endurance and privacy point the same way here.
- The prototype BOM flags a related open problem: on the reference CM4 carrier
  the single M.2 M-key slot is consumed by the Wi-Fi card, leaving 32 GB eMMC
  for PostgreSQL, journald and Prometheus. A USB2 SSD test article is included
  to characterize whether that is survivable.
- Storage failure has a defined behaviour: preserve the network plane where the
  host remains bootable, mark affected stateful services `DEGRADED` or
  `NON-AUTHORITATIVE`, and restore from a validated backup or standby before
  authority is claimed (SAD section 26).

## Accepted cost

The program accepts reduced on-node observability history and reduced log depth,
which makes some field faults harder to diagnose after the fact, in exchange for
storage that survives the fleet's service life. SAD section 31 records
"eMMC/NVMe write wear corrupts state over fleet life" as OPEN.

## Fallback

Larger or replaceable storage, or forwarding telemetry off-node wherever a path
exists. Neither removes the need for bounded retention, because a field node
frequently has no path.

## Superseded by

None.

## Verification dependency

Stages 1 and 13. SAD section 30.1 records storage endurance as OPEN until
hardware and load evidence exists.
