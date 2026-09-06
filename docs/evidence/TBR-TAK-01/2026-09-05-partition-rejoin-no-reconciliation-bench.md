# Partition and rejoin on the bench: reconciliation is structurally impossible

**Trade:** `TBR-TAK-01`.
**Date:** 2026-09-05.
**Taken by:** Cameron Zobrist, on the lab development machine.
**Status of this artifact:** `SIMULATED`. The containerised OTS 1.7.13 stack
(`fml-ots` + PostgreSQL), read-only code, config and database inspection. No
hardware, no writes to the running service.

## What this supplies, and its scope

The `2026-08-27` analysis **describes** the durable set's partition and rejoin
behaviour and a proposed conflict-resolution rule -- the gate's "described" half.
The Program Owner asked (2026-09-05) for that to be **exercised on the bench**
before acceptance. This is that exercise, and its scope was fixed in advance by
an independent assessment, not after seeing the result.

**An independent assessor was dispatched** (per the before-blocked rule, CLAUDE.md
Done criterion 7) to test the claim that a bench partition test at this stage can
only demonstrate unreconciled divergence and the hazards, not the proposed rule.
**Verdict: CONFIRMED, no route found.** The proposed rule
(authority-retains-authority, surface-not-merge, last-writer-wins rejected) is a
property of a mechanism that would sit above OTS and PostgreSQL -- exactly
`TBR-HA-01`, which is downstream and unselected. Nothing on the bench implements
lease, quorum or witness authority, so the rule has nothing to run against. This
artifact therefore proves the **problem** the rule exists to solve, empirically,
and leaves the rule itself `TBR-HA-01`'s to demonstrate.

## Proof 1: no reconciliation mechanism exists

**OTS never originates or consumes a federated change.** The TAK federation flag
exists on the model but is written `False` at every site, and no federation
manager, peer or listener exists:

```text
mission_marti_api.py:558,1915,2002,2085  mission_change.isFederatedChange = False
cot_parser.py:1096                        mission_change.isFederatedChange = False
app.py                                    no federation listener started
```

So two OTS instances have **no channel** to exchange each other's
`MissionChange`s. The Data Sync / Mission API is client-to-server (EUD clients
subscribe and pull); it is not server-to-server.

**PostgreSQL replication is unconfigured.** Queried on the running database:

```text
pg_is_in_recovery()          f
pg_replication_slots          0
pg_stat_replication           0   (WAL senders)
pg_publication                0
pg_subscription               0
primary_conninfo              <empty>
synchronous_standby_names     <empty>
```

One node, no standby, nothing streaming. **A partition of the durable set cannot
be healed, because there is nothing that reconciles it.** This is stronger than
observing one partition fail to converge: it is the structural reason it always
will.

## Proof 2: divergence is unbounded, by identity

Each host owns **independent primary-key spaces**: `missions.name` is the
mission primary key, a data package or DataSync item is keyed by content hash,
and a certificate is a common name signed by the host's **own** CA (per
`2026-08-31-shared-credentials-across-mules-and-euds.md`, trust is per-node).
With no federation and no replication, two partitioned hosts that each create a
mission `OPS`, or each issue `CN=alpha`, produce **two unrelated authoritative
rows that can never meet**. Nothing detects the collision; nothing merges it.

## Proof 3: the append log offers only a wall-clock signal

The `mission_changes` append log -- the ordered record a reconciler would have to
use -- carries these columns:

```text
id, isFederatedChange, timestamp, server_time, content_uid, creator_uid,
mission_uid, change_type, mission_name
```

There is **no authority, epoch, lease or version field.** The only ordering
signals are `timestamp` (client-supplied) and `server_time`, and `server_time` is
the host's own wall clock (`datetime.datetime.now(...)` at the write sites). So
the only cross-host merge signal the schema even offers is a wall-clock
comparison -- last-writer-wins -- which `FML-ADR-042` explicitly permits to be
`TIME_DEGRADED`. A host with a failed RTC backup cell or no credible time would
win every timestamp comparison, silently, with correct state from a healthy host.

This is the empirical teeth behind the analysis's **"why not last-writer-wins"**:
the hazard is not hypothetical, it is the only merge the current schema could
support.

## What this confirms and what it does not

**Confirms** finding 5 of the analysis: database high availability alone cannot
protect the durable set, and here more sharply -- there is no reconciliation of
*any* kind, in OTS or in PostgreSQL, and the schema's only ordering signal is the
degradable clock. `TBR-HA-01` must supply authority by lease, quorum or witness,
never by comparing wall clocks, and it must also carry the filesystem-shaped
durable set (`config.yml`, `ca/`, `uploads/`) that lives outside SQL.

**Does not** demonstrate the proposed conflict-resolution rule. Per the assessor,
that requires a `TBR-HA-01` mechanism to exist first; the rule remains
**described** in the `2026-08-27` analysis, not demonstrated, and this artifact
does not close that gap because nothing on the bench can.

## Reproduction

The `isFederatedChange` and `server_time` sites are grep of the OTS package under
`/app/venv/lib/python3.12/site-packages/opentakserver`. The replication figures
are the `pg_*` queries above against `fml-pg`. The append-log columns are
`information_schema.columns` for `mission_changes`. All read-only; nothing was
written to the running service.

Nothing real: no deployment location, member identity, callsign, or credential.
Table and mission names used illustratively (`OPS`, `alpha`) are synthetic. See
`SECURITY.md`.
