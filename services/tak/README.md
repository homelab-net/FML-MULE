# TAK-compatible service

Deployment and state notes for the TAK-compatible situational-awareness service
in the mission-service plane.

**Nothing is loadable yet.** `FML-ADR-032` makes **OpenTAKServer** the
preferred initial implementation, and the architecture remains
**TAK-compatible, not OpenTAKServer-exclusive**. `FML-ADR-033` makes PyTAK
the preferred library for custom CoT clients and translation gateways.
`TBR-TAK-01` is `CLOSED` on `FML-ADR-071`.

The service is three processes, one image. `services/tak/Containerfile`
installs release `1.7.13` on a digest-pinned Python 3.12 base. The Quadlet
texts are `services/quadlets/opentakserver.container.disabled`,
`eud-handler.container.disabled`, and `cot-parser.container.disabled`.
They share `/var/lib/fml/ots`. PostgreSQL and RabbitMQ are the same kind
of disabled unit, using the digests recorded on 2026-08-31. None of these
files is a loadable unit: the application image has no digest until that
Containerfile is built, and no registry publishes one. A database-only
copy is not a restore.

## What this is

TAK (Team Awareness Kit) is a family of situational-awareness clients and
servers, originally military and now widely used by civilian response
organisations. Clients exchange **CoT** (Cursor on Target) messages: position
reports, markers, chat, tasking.

MULE hosts a **TAK-compatible** service so that operators can use clients they
already have on devices they already carry. The program does not define the
protocol and does not redefine CoT; it consumes an interface defined elsewhere.
See `docs/NON-GOALS.md`.

## The state boundary is decided

`TBR-TAK-01` is `CLOSED`. The durable set is the SQL backend plus
`config.yml`, `ca/`, and `uploads/` inside `OTS_DATA_FOLDER`
(`FML-ADR-071`). The units mount that folder at `/var/lib/fml/ots`.

What is still open is deployment, not the classification: the built image
digest, `TBR-HA-01` for recovery, and `TBR-COMP-01` for the field budget.
`GAP-09F` has not selected the `v0.0.1` milestone service. These units do
not make that selection.

### Known internal dependencies

SAD section 13.3 records that OpenTAKServer currently uses multiple Python
processes, **RabbitMQ** for internal CoT messaging, and SQLAlchemy-backed
storage. RabbitMQ is treated as **local transient service infrastructure**, not
a field-wide clustered message bus. All three land on the compute budget
`TBR-COMP-01` must size.

## What is already recorded, and what is not

The state inventory, the partition result, and the durable set are in
`docs/evidence/TBR-TAK-01/`. They are not repeated here. Still open:

- The digest of the image `services/tak/Containerfile` builds.
- Recovery and rollback, which are `TBR-HA-01` and `TBR-REC-01`.
- The field resource envelope, which is `TBR-COMP-01`. The x86 idle
  measurement is not that envelope.

## Threat model notes

Two conditions recorded in `THREAT_MODEL.md` bear directly on this service, and
neither is a defect to be fixed here:

- **Peer traffic is visible to authenticated participants.** A participant
  admitted to a mission sees the position and mission traffic of other
  participants on that mission. That is the function of the system. There is no
  meaningful compartmentation between admitted participants, and whether any is
  possible at all is part of `TBR-TAK-01`.
- **Position reporting is periodic**, which is exactly the regularity that
  makes traffic analysis easy on encrypted traffic. Participant location is the
  asset whose compromise causes direct physical harm, and this service
  generates it continuously by design.

Logging follows the plane-wide rule: **no location data in logs by default**. A
debug log recording position reports is a location history in plain text on a
device that is expected to be captured.
