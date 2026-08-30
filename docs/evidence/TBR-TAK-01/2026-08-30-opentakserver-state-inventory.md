# What state OpenTAKServer actually holds

**Trade:** `TBR-TAK-01`.
**Date:** 2026-08-30.
**Taken by:** Cameron Zobrist, on the lab development machine.
**Status of this artifact:** an inventory taken from the upstream package's
schema. **The server was not run.** It is an input to the state study the
closure gate requires, and it is not that study.

## What this is for

`TBR-TAK-01` asks which mission state must survive a node loss, a partition or
a rejoin, and which may be discarded and regenerated. Its closure evidence is a
state inventory classified against SAD section 14.1's ten categories.

This supplies the first half of that: **what state exists at all**, for the
implementation `FML-ADR-032` prefers. It classifies nothing. Classification is
a judgement about operational consequence and belongs to the named owner and
the study, not to a file listing.

The trade records that it "requires no hardware" and is "the highest-value work
available to a contributor who owns no hardware". This is that work started,
not finished.

## Configuration

| Item | Value |
| --- | --- |
| Package | `OpenTAKServer` 1.7.13, from PyPI, upstream's own channel |
| Host | Debian 13, Python 3.13 |
| Method | Enumerating `opentakserver/models/*.py` and their `__tablename__` |

## The relational tables

Thirty-five, from the shipped models:

```text
alerts                apscheduler_jobs      casevac
certificates          chatrooms             chatrooms_uids
cot                   data_packages         device_profiles
euds                  eud_stats             geochat
groups                groups_missions       groups_users
icons                 iconsets              markers
meshtastic_channels   mission_changes       mission_content
mission_content_mission                     mission_invitations
mission_logs          mission_roles         missions
mission_uids          packages              plugins
points                rb_lines              teams
tokens                video_recordings      video_streams
zmist
```

## Mapped onto the ten categories SAD 14.1 requires

Where a category has no table, that is itself a finding and is stated rather
than left blank.

| SAD 14.1 category | Tables, or absence |
| --- | --- |
| Relational database state | All thirty-five above |
| DataSync and Mission API state | `missions`, `mission_changes`, `mission_content`, `mission_content_mission`, `mission_invitations`, `mission_logs`, `mission_roles`, `mission_uids`, `groups_missions` |
| Mission packages and uploaded files | `data_packages`, `packages` |
| Certificate enrollment, issuance, authorization | `certificates`, `tokens`, and the `WebAuthn` model |
| Group and channel configuration | `groups`, `groups_users`, `teams`, `chatrooms`, `chatrooms_uids`, `meshtastic_channels` |
| Server configuration | `device_profiles`, `plugins`, `apscheduler_jobs` |
| RabbitMQ and transient messaging | **No table.** SAD 13.3 records RabbitMQ as local transient service infrastructure; its state is outside the database and this inventory does not reach it. |
| Reconstructable PLI, presence, session | `cot`, `points`, `euds`, `eud_stats` |
| Local map, tile and cache state | `icons`, `iconsets`, `video_streams`, `video_recordings`. **Map tiles are not here**; whether a tile cache exists on disk is not established by a schema read. |
| Immutable mission-package state | `data_packages`, `packages`, same tables as above. Whether immutability is enforced anywhere is **not** visible in the model definitions. |

Three tables map to no SAD category and are operational content in their own
right: `alerts`, `casevac`, `zmist`, `markers`, `rb_lines`. Casualty and
medical records under `casevac` and `zmist` are the sharpest case in the whole
inventory for the "loses an operator's work" side of the trade's own framing.

## Two findings the study will need

**RabbitMQ state is not in the database and is not covered by a schema read.**
SAD 14.1 lists it as a category to classify, and nothing here classifies it.
Any study that inventories only the relational schema will miss it, which is
worth saying because the schema is the easy part to enumerate.

**Immutability is not visible in the models.** SAD 14.1 asks for immutable
mission-package state as its own category. Nothing in the model definitions
distinguishes it, so whether it is enforced in application logic, by
convention, or not at all is an open question a schema read cannot answer.

## Compute footprint, which belongs to a different trade

Recorded here because it was measured in passing and `TBR-COMP-01` is critical
path and unowned.

| Measure | Value |
| --- | --- |
| Packages installed | 197 |
| Disk, virtualenv only | 684 MB |
| Build requirement | A C toolchain. `unishox2-py3` has no wheel and fails without Python headers. |

That last is an image-build constraint rather than a runtime one, and it is the
kind of thing found late: the image either ships a compiler, which nobody
wants on a field node, or a prebuilt wheel for the target architecture, which
`arm64` makes a real question rather than a formality.

684 MB is the Python environment alone. It excludes the operating system, the
kernel, RabbitMQ, the container runtime under `FML-ADR-029`, and every other
service. SAD 13.3 already notes that OpenTAKServer's processes, RabbitMQ and
storage all land on the compute budget; this is a number for the first of
those.

## What this does not establish

The server was not run, so nothing here is a runtime measurement: no memory
figure, no CPU figure, no behaviour under partition, and no test of any MULE
workflow against any backend. **SAD 14.2 warns specifically that database
support claimed by an ORM is not sufficient acceptance evidence.** This
artifact is a read of exactly that ORM, and therefore is not acceptance
evidence for anything. It is a starting inventory.

Nothing is classified. The trade closes when every item is placed in a CONOPS
section 26 class with a stated justification, the partition and rejoin
behaviour of the durable set is described including its conflict resolution
rule, and a named owner accepts it. None of that is here.
