---
id: FML-ADR-034
title: PostgreSQL is preferred only if the TAK state study demonstrates it is the correct continuity boundary
status: CONDITIONAL
date: 2026-08-25
supersedes: none
superseded-by: none
trades: [TBR-TAK-01, TBR-COMP-01, TBR-HA-01]
verification: Stage 5
---

# FML-ADR-034 PostgreSQL is preferred only if the TAK state study demonstrates it is the correct continuity boundary

**Source of rationale:** SAD v0.31 section 14.2. See also sections 14.1, 14.5,
25.3, 25.8 and 29.

Supersedes draft `AD-014`; see SAD section 0.8.

## Context

Selecting a database implies selecting a replication and continuity mechanism
around it. Doing that before knowing **where** mission-critical TAK state
actually lives would build an HA stack around the wrong boundary.

SAD section 14.1 makes state classification the design gate:

> No database-HA mechanism will be selected until the program identifies where
> OpenTAKServer or another chosen TAK implementation actually stores all
> mission-critical persistent state.

## Decision

PostgreSQL **shall** be the preferred relational database **if and only if**
Stage 5 demonstrates both that mission-critical TAK state requiring
authoritative continuity is stored in the SQL backend, and that the chosen TAK
server implementation supports the required workflows correctly on PostgreSQL.

SQLite remains acceptable for non-HA prototypes and bench testing where its
limitations are understood.

**Database support claimed by an ORM is not sufficient acceptance evidence.**
Stage 5 must test the actual MULE TAK workflows against the selected backend.

## Status

`CONDITIONAL`.

The condition is `TBR-TAK-01`. If the state study shows that the mission-critical
set is not principally in the SQL backend — for example that DataSync content,
mission packages, uploaded files or certificate enrollment state dominate — then
PostgreSQL is not the correct continuity boundary and this preference does not
take effect.

If the condition fails, the fallback applies and this ADR is superseded by
whatever decision the evidence supports.

## Consequences

- No replication mechanism is selected here. SAD section 14.5 lists candidates
  including PostgreSQL streaming replication, application-supported replication
  or export, controlled filesystem replication, a signed mission configuration
  package, immutable predeployment content, and checkpoint or snapshot transfer.
- **Syncthing may be used only for data whose conflict and consistency semantics
  are compatible with file synchronization. It must not be used as a substitute
  for transactional database replication** (SAD section 14.5).
- PostgreSQL, if selected, adds write amplification on a node whose storage
  endurance is bounded by `FML-ADR-050`: WAL activity is named there as a
  write-producing workload.
- It also adds to the memory budget that `TBR-COMP-01` must size.

## Accepted cost

The program accepts that it cannot begin building continuity tooling until
`TBR-TAK-01` closes, and that this leaves the 60-second recovery objective
unaddressed for longer. SAD section 14.6 accepts that cost explicitly rather
than introducing an unjustified HA stack to preserve the number.

## Fallback

SQLite with a non-HA posture, or an application-level export and restore path,
if the state study shows the SQL backend is not the continuity boundary. Either
outcome supersedes this ADR.

## Superseded by

None.

## Verification dependency

Stage 5. `TBR-TAK-01` closure evidence includes a state inventory, a
different-node restore, and PostgreSQL DataSync, mission-package, certificate
and map-cache tests.
