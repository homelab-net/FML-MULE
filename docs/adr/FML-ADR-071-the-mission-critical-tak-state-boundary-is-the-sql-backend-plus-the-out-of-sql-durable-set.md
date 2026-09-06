---
id: FML-ADR-071
title: The mission-critical TAK state boundary is the SQL backend plus the out-of-SQL durable set
status: PROPOSED
date: 2026-09-06
supersedes: none
superseded-by: none
trades: [TBR-TAK-01, TBR-HA-01]
verification: Stage 5
---

# FML-ADR-071 The mission-critical TAK state boundary is the SQL backend plus the out-of-SQL durable set

**Source of rationale:** the `TBR-TAK-01` closure evidence
(`docs/evidence/TBR-TAK-01/`), CONOPS v1.01 sections 26 and 14.3, SAD v0.31
sections 14.1-14.6 and 22, `FML-ADR-034` and `FML-ADR-042`.

## Context

SAD section 14.1 makes state classification the design gate: *no database-HA
mechanism will be selected until the program identifies where OpenTAKServer or
another chosen TAK implementation actually stores all mission-critical persistent
state.* `FML-ADR-034` is `CONDITIONAL` on exactly that study.

The study is now complete: fifteen evidence artifacts under
`docs/evidence/TBR-TAK-01/`, against a running OpenTAKServer and PostgreSQL. It
found three things that decide the boundary, and none was assumed from
documentation:

- **The mission-critical relational state (CONOPS 26.2) is in the SQL backend
  and its workflows run on PostgreSQL.** All 41 tables are classified; the four
  workflow tests SAD section 14.2 demands -- mission API, certificate,
  mission-package, and DataSync content through `mission_content` -- were run
  against PostgreSQL, not asserted from an ORM.
- **Critical durable state lives outside SQL.** `config.yml` holds
  `SECURITY_PASSWORD_SALT` and the node identity, the `ca/` directory is the
  certificate authority, and `uploads/` holds mission packages. A different-node
  restore of the database alone restored every row and authenticated nobody,
  because the salt and the CA are not in the database, and the replacement
  silently generated a **different** certificate authority while reporting
  healthy.
- **Reconciliation is structurally absent.** OpenTAKServer writes
  `isFederatedChange = False` at every site and runs no federation listener;
  PostgreSQL has no replication configured. The only cross-host ordering signal
  in the mission change log is a wall clock, which `FML-ADR-042` permits to run
  `TIME_DEGRADED`.

Doing nothing is not an option because `TBR-HA-01`, `FML-ADR-034` and three
blocked services (`services/mission-trust/`, `services/status-aggregator/`,
`services/gateways/`) all wait on this boundary being decided.

## Decision

The mission-critical persistent state boundary for the TAK service -- the state
a replacement service **shall** restore before it may be considered fully
authoritative -- is the union of the **CONOPS 26.2 relational state held in the
SQL backend** and the **out-of-SQL durable set**: `config.yml` (the password
salt and node identity), the `ca/` certificate authority, and `uploads/`.

Database high availability **shall** therefore be treated as necessary but not
sufficient: any continuity mechanism `TBR-HA-01` selects **shall** carry the
out-of-SQL durable set as well as the SQL backend.

## Status

`PROPOSED`. Written from the `TBR-TAK-01` evidence and under review; it carries
no weight until the named owner accepts that evidence. On acceptance it becomes
`SELECTED` and `TBR-TAK-01` closes; this ADR is the architecture decision SAD
section 30.2 requires be entered into the register at closure.

## Consequences

- **`TBR-HA-01` inherits four constraints before it begins.** (1) Its mechanism
  must carry the out-of-SQL durable set, not database replication alone. (2) It
  must establish cross-host authority by lease, quorum or witness, and **not** by
  comparing wall-clock timestamps, because `FML-ADR-042` permits a degraded
  clock and last-writer-wins would let the least-trustworthy clock win silently.
  (3) Because no reconciliation exists in the stack, authority is single-writer:
  a non-authoritative side's divergent writes are **surfaced, not merged**, using
  the SAD section 22 reason codes (`PARTITION`, `STATE_LAG`, `NO_SAFE_AUTHORITY`).
  (4) A replacement that cannot demonstrate current certificate revocation must
  refuse to validate, since the study found revocation is not consulted and the
  CA is regenerated per node.
- **`FML-ADR-034`'s condition is resolved affirmatively for the relational
  store.** PostgreSQL's workflows are demonstrated on the backend, so its
  preference takes effect; this ADR adds that the boundary extends beyond the SQL
  backend, which `FML-ADR-034` deferred to this study. `FML-ADR-034` is not
  superseded -- its relational-database preference stands -- and the owner may
  flip it `CONDITIONAL` to `SELECTED` on the same acceptance.
- **File synchronization is constrained by content.** Per `FML-ADR-034` and SAD
  section 14.5, a file-sync mechanism may carry only data with compatible
  conflict semantics. The out-of-SQL set is largely administrative and
  write-once (the CA and node identity arrive through the mission-package supply
  path), which may suit it, but `uploads/` and the salt need the same authority
  discipline as the SQL state; `TBR-HA-01` decides.
- It unblocks the three placeholder services named above once `TBR-HA-01` and a
  catalog decision follow.

## Accepted cost

Continuity now requires **two** mechanisms -- a database-HA mechanism and a
filesystem-shaped mechanism for the out-of-SQL set -- which is more complex and
more failure-prone than the single database-HA stack the program would have
preferred. And the prohibition on wall-clock authority forecloses the simplest
timestamp-based designs, pushing `TBR-HA-01` toward lease, quorum or witness
mechanisms that cost more to build and operate. `TBR-HA-01` and `TBR-COMP-01`
quantify that cost; it is accepted here as the price of not building HA around a
boundary that restores rows and authenticates no one.

## Fallback

If `TBR-HA-01` or a later identity decision makes the out-of-SQL durable set
**derivable** rather than node-generated -- the CA and the salt provisioned from
the mission package at deployment instead of generated per node -- the boundary
could shrink toward SQL-only and continuity would simplify. That would be a new
ADR superseding this one. The signal to take it is a node-identity model in
which nothing authenticating survives only on the node's own disk.

## Superseded by

None.

## Verification dependency

Stage 5. This ADR states the boundary; `TBR-HA-01` selects the mechanism that
protects it, and the mechanism is what Stage 5 exercises against a replacement
host. The basis is the `TBR-TAK-01` evidence under `docs/evidence/TBR-TAK-01/`,
in particular the different-node restore and the partition/rejoin exercise.
