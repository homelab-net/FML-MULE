# Every table, classified into a CONOPS section 26 class

**Trade:** `TBR-TAK-01`.
**Date:** 2026-08-31.
**Taken by:** Cameron Zobrist, on the lab development machine.
**Status of this artifact:** `UNVERIFIED`. Classification from the shipped
SQLAlchemy models of `OpenTAKServer` 1.7.13. **The server was not run.**

## What this supplies

`TBR-TAK-01`'s closure gate requires that "every item is classified into a
CONOPS section 26 class with a stated justification". Two artifacts existed and
neither did it:

- `2026-08-27-state-classification-analysis.md` established the method and
  classified the ten SAD section 14.1 **categories**. Its Finding 1 states that
  "relational database state is not a class and must be decomposed", and it
  could not decompose it because no table list existed on that date.
- `2026-08-30-opentakserver-state-inventory.md` enumerated the tables and
  **deliberately classified nothing**, on the ground that classification "belongs
  to the named owner and the study".

**The two compose and nobody joined them.** This is that join. A named owner was
assigned on 2026-08-31, which removes the second artifact's stated reason to
defer.

## A correction to the inventory

The inventory's prose says "Thirty-five". Its own list contains **36**, and 36
is right: counted from `__tablename__` declarations in the installed package,
`opentakserver/models/*.py`.

## The classes, from CONOPS section 26

- **26.1 Common trust and configuration.** `[SHALL]` be consistent across all
  eligible service hosts.
- **26.2 Mission-critical persistent state.** `[SHALL]` survive failover before
  a replacement service may be considered fully authoritative. CONOPS adds that
  "the exact data categories in this class `[SHALL]` be defined in the TRD",
  which is the requirement this artifact feeds.
- **26.3 Reconstructable or ephemeral.** May be rebuilt from reconnecting
  clients or new network activity.

## 26.1 Common trust and configuration, 16 tables

| Table | Justification |
| --- | --- |
| `certificates` | Certificate trust, CONOPS 26.1's own example. Carries `common_name`, `expiration_date`, `server_address`. |
| `tokens` | Enrollment authorization. **Carries `disabled` and `expiration`, so it holds revocation state**, which confirms Finding 2 of the 2026-08-27 analysis in schema rather than by reasoning. |
| `groups`, `groups_users`, `groups_missions` | Group and role definition, and which user is in which. Inconsistency between hosts changes who can see what. |
| `teams` | Role definition. |
| `mission_roles` | `role_type` per user per mission. Role definitions are 26.1's explicit example. |
| `device_profiles` | `preference_key`/`preference_value` pushed to devices, with an `enrollment` flag. Shared service configuration. |
| `plugins` | Which plugins are `enabled`. Service configuration. |
| `packages` | **Reclassified, see below.** `platform`, `plugin_type`, `package_name`, `revision_code`: this is the ATAK plugin distribution repository, not mission content. |
| `meshtastic_channels` | Channel configuration. **It carries a `psk` column, so it holds a credential**, and that is a finding in its own right below. |
| `icons`, `iconsets` | `bitmap` and `shadow` bytes, with `version`. Symbology must be consistent across hosts or clients render the same marker differently. Recoverable by re-upload, which is operator effort rather than lost operational data. |
| `video_streams` | Stream configuration: `path`, `protocol`, `port`, timeouts. Configuration, not content. |
| `chatrooms`, `chatrooms_uids` | Room structure and membership. The **messages** are elsewhere and are classified 26.2. |

## 26.2 Mission-critical persistent state, 15 tables

| Table | Justification |
| --- | --- |
| `missions` | The mission itself: `name`, `classification`, `bbox`, `base_layer`. CONOPS 26.2's "selected mission state". |
| `mission_changes` | The change log with `server_time` and `creator_uid`. Losing it loses the ordering a rejoin needs. |
| `mission_content`, `mission_content_mission` | DataSync content and its association to missions, with `hash` and `submitter`. CONOPS 26.2's "selected DataSync content". |
| `mission_invitations` | Who was invited to what, by whom. |
| `mission_logs` | `content`, `dtg`, `content_hash`. An operator's written record. |
| `mission_uids` | Which UIDs belong to a mission, with `cot_type` and position. |
| `data_packages` | `filename`, `hash`, `submission_user`, `size`. "Shared files and data required for mission continuity". |
| `casevac` | A casualty evacuation request: `ambulatory`, `child`, `enemy`, `urgency` fields. **Not reconstructable from a reconnecting client.** |
| `zmist` | `z`, `m`, `i`, `s`, `t` and `casevac_uid`: a casualty handover report bound to a CASEVAC. A medical record. |
| `markers` | Operator-placed symbols with `affiliation` and `callsign`. Deliberate work product. |
| `rb_lines` | Range and bearing lines: `range`, `bearing`, `anchor_uid`. Deliberate work product. |
| `alerts` | **`start_time` and `cancel_time`**, so an alert has a lifecycle and an uncancelled one is a live emergency. A reconnecting client does not re-declare an emergency, so this cannot be rebuilt. |
| `geochat` | The message content, with `remarks` and `timestamp`. The coordination record. |
| `video_recordings` | `segment_path`, `in_progress`, `duration`. Recorded content, not the stream configuration. |

## 26.3 Reconstructable or ephemeral, 5 tables

| Table | Justification |
| --- | --- |
| `cot` | The CoT event stream. CONOPS 26.3's "current PLI". |
| `points` | `latitude`, `longitude`, `ce`, `hae`, `course`. Position, republished by any connected client. |
| `euds` | Device presence: `callsign`, `os`, `version`, `last_event_time`. Rebuilt as clients reconnect. |
| `eud_stats` | `battery`, `heap_free_size`, `app_framerate`. Client telemetry, of diagnostic value only. |
| `apscheduler_jobs` | `next_run_time` and an opaque pickled `job_state`. **Confirmed 26.3 on 2026-08-31**, no longer provisional: the five rows a running instance holds are all service housekeeping (`purge_data`, `delete_old_data`, `delete_video_recordings`, `get_adsb_data`, `ais`), none encodes mission tasking, and deleting all five and restarting the service re-registers all five. Reconstructable from code. |

16 + 15 + 5 = 36.

**Corrected the same day: there are 41 tables, not 36.** A running PostgreSQL
holds five more, and the enumeration method missed them because their names come
from Flask-Security mixins rather than `__tablename__` literals: `user`, `role`,
`roles_users`, `web_authn` and `alembic_version`. **The first four are the entire
authentication and authorisation store**, which is the most security-critical
26.1 state in the system. All five are **26.1**: a restore whose schema version
disagrees with the code is not a working restore either. See
`2026-08-31-opentakserver-actually-run.md`. Corrected totals: 21, 15, 5.

## Two findings

### `packages` was mapped to the wrong SAD category

The 2026-08-30 inventory grouped `packages` with `data_packages` under "mission
packages and uploaded files". Reading its columns -- `platform`, `plugin_type`,
`package_name`, `version`, `revision_code` -- shows it is the **ATAK plugin
distribution repository**, which is software distribution and not mission
content. It is 26.1.

This is a small correction with a general point behind it: the two tables have
similar names and completely different continuity requirements, and a mapping
made from names would put a plugin repository inside the set that must survive
failover.

### OpenTAKServer stores a Meshtastic pre-shared key in its database

`meshtastic_channels` carries a `psk` column alongside `lora_region`,
`lora_hop_limit` and `lora_tx_enabled`.

That is a **credential at rest inside the TAK relational state**, and it matters
beyond this trade:

- `TBR-SEC-01` holds credentials as protected assets, and
  `docs/evidence/TBR-SEC-01/2026-08-31-two-credentials-have-no-origin.md`
  already records two credentials with no issuing mechanism. This is a third
  location where credential material lives, and unlike the other two it is
  inside a database that `FML-ADR-034` may replicate.
- `docs/evidence/TBR-NET-03/2026-08-30-what-happens-with-no-configuration.md`
  established that two stock Meshtastic deployments converge on a **public**
  default channel whose key is a published constant. A deployment that sets its
  own channel key to avoid that puts the key here.
- Any replication or backup of this database is therefore replicating a
  credential, and any different-node restore restores it.

Nothing here proposes a change. It is recorded because a state study that
classified `meshtastic_channels` as ordinary configuration would miss it.

## What still needs a running instance

The 2026-08-27 analysis listed six outstanding items. This artifact closes the
first and leaves five:

1. ~~Decompose the relational database state.~~ **Done here.**
2. **Locate every durable-set member**, specifically whether any lives outside
   the SQL backend.
3. **Inspect durable queues** for sole-copy mission-critical items. RabbitMQ
   holds no table and a schema read does not reach it.
4. **Different-node restore.**
5. **The four workflow tests**: DataSync, mission package, certificate, map
   cache.
6. **The cache question empirically**: what a client sees after failover when
   the tile source is unreachable.

The `apscheduler_jobs` classification, provisional when this artifact was
written, was confirmed the same day: see the table above.

## What this does not establish

**The server was not run.** SAD section 14.2 warns that database support claimed
by an ORM is not acceptance evidence, and by the same standard a classification
read from models is not evidence about runtime behaviour. It says what each
table *is for*; only a running instance says what actually lands in it.

**Nothing outside the relational schema is classified**, which is most of items
2, 3 and 6 above: RabbitMQ, the filesystem, and any tile cache.

**This does not close the trade.** The gate also requires the partition and
rejoin behaviour of the durable set, which
`2026-08-27-state-classification-analysis.md` supplies, and the named owner's
acceptance, which is not the author's to give.
