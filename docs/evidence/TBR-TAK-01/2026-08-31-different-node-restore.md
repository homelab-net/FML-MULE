# A different-node restore, performed

**Trade:** `TBR-TAK-01`.
**Date:** 2026-08-31.
**Taken by:** Cameron Zobrist, on the lab development machine.
**Status of this artifact:** `SIMULATED`. Containers on a development machine.

## What this closes

Outstanding item 4, and SAD section 30.2 lists it in this trade's closure
evidence:

> **Different-node restore.** Restore to a host that is not the origin, then
> demonstrate which durable-set members survived and which did not.

`2026-08-31-durable-state-outside-the-database.md` predicted the result from
source. This performs it.

## The exercise

An origin node was built, its default administrator account confirmed working,
and then **a database-only backup** was taken -- `pg_dump`, 7025 lines -- which
is what a database high-availability or backup mechanism gives you.

The origin was destroyed: its container removed, its database dropped and
recreated. The dump was restored, and a replacement node started against it with
an **empty** `OTS_DATA_FOLDER`, which is the state of a host rebuilt from a
database backup.

## The result

| | Origin | Replacement |
| --- | --- | --- |
| `administrator` / `password` | **`200`**, with a CSRF token | **`400`, "Authentication failed - identity or password/passcode invalid"** |
| `/api/health` | `200` | **`200`** |
| `user` rows | 1 | **1, restored** |
| CA SHA-256 fingerprint | `E2:9F:BA:3A:7F:2A:D8:9F...` | **`97:36:8A:FB:BA:65:E9:32...`** |

Config fingerprints, hashed rather than shown:

```text
origin       salt sha256[:12]=65940902bf11   secret_key sha256[:12]=55c4c47a7469
replacement  salt sha256[:12]=376b61267de0   secret_key sha256[:12]=9a6f98cdf0d1
```

## What survived and what did not

**Survived:** every row. The user record restored intact, and so would every
mission, data package, chat message and marker.

**Did not survive:** the ability to use any of it.

- **Authentication is gone.** `SECURITY_PASSWORD_SALT` lives in `config.yml`,
  not the database. The replacement generated a new one, so the restored hash
  cannot be verified. The account exists and cannot log in.
- **The certificate authority is a different authority.** The replacement did
  not fail to find a CA. It **silently generated a new one**, with a different
  fingerprint. Every certificate the restored `certificates` table records was
  issued by an authority that no longer exists, so an enrolled client presenting
  a valid certificate meets a server that will not recognise it.
- **Sessions and signed tokens are invalid**, because `SECRET_KEY` changed too.
- **The node presents a different identity**, because `OTS_NODE_ID` is
  regenerated.

## The shape of the failure is the point

**The replacement reports `/api/health` `200`.**

A restored node is up, serving, holding a complete copy of every record, and
unable to authenticate a single user or honour a single issued certificate. It
does not announce any of this. An operator running a failover during an incident
gets a server that looks like it worked.

That is the same shape as every other failure this program has recorded on the
network side, and it is why `FML-ADR-063` made "never silent" a requirement
rather than a preference.

## What this settles for `TBR-HA-01` and `FML-ADR-034`

`FML-ADR-034` makes PostgreSQL conditional on this state study. The condition
can now be stated as a measurement rather than an expectation:

**A database-level continuity mechanism is necessary and not sufficient.** Any
replacement host must also carry `config.yml` and `ca/` from the origin, or it
is not a replacement, it is a new deployment holding the old deployment's
records.

The 2026-08-27 analysis asked whether a second, filesystem-shaped continuity
mechanism is required. `2026-08-31-durable-state-outside-the-database.md`
answered yes from source. **This demonstrates it.**

## What this does not establish

**The origin held only its default account.** The PyTAK clients from earlier
runs were not re-created before the dump, so `certificates`, `euds` and `cot`
were zero at backup time. The user row is the decisive one and the certificate
finding rests on the CA fingerprints rather than on enrolled clients, but a
restore carrying real enrolled certificates was not performed.

**No attempt was made to restore correctly.** Copying `config.yml` and `ca/`
alongside the database was not tried, so this shows the failure and not the fix.
That is worth doing and is not done here.

**One backup method.** `pg_dump` and restore, not streaming replication, not a
filesystem snapshot, not the `OTS_BACKUP_COUNT` mechanism the configuration
mentions and this artifact did not investigate.

**Not rootless, one machine, containers rather than MULE hardware.**
