# TAK-compatible service

Deployment and state notes for the TAK-compatible situational-awareness service
in the mission-service plane.

**Nothing is deployed and no service implementation has been selected.**

## What this is

TAK (Team Awareness Kit) is a family of situational-awareness clients and
servers, originally military and now widely used by civilian response
organisations. Clients exchange **CoT** (Cursor on Target) messages: position
reports, markers, chat, tasking.

MULE hosts a **TAK-compatible** service so that operators can use clients they
already have on devices they already carry. The program does not define the
protocol and does not redefine CoT; it consumes an interface defined elsewhere.
See `docs/NON-GOALS.md`.

## The open question that blocks everything here

`TBR-TAK-01`, **mission-critical state boundary**, is on the critical path and
is the trade this directory waits on.

The question: which mission state must survive a node loss, a partition, or a
rejoin, and which may be discarded and regenerated?

The consequences are not subtle:

- If position reports are transient and regenerable, this service needs no
  durable store for them, and a node that reboots simply catches up.
- If operator-authored markers, tasking or annotations must survive, the plane
  needs durable storage, a replication story across a **partitioned mesh**, and
  a conflict resolution rule for two partitions that edited the same object and
  later rejoined.

Getting it wrong in the permissive direction builds a distributed database
nobody needed. Getting it wrong in the other loses an operator's work during an
incident, which is unrecoverable and visible.

**`TBR-TAK-01` requires no hardware.** It is a design and analysis trade,
resolvable against documentation, protocol behaviour, and reasoning about
partition, running against fakes on an ordinary laptop. It is the highest-value
work available to a contributor who owns no hardware, and nobody has picked it
up.

## What must be recorded here when work starts

- **State inventory.** Every object the service holds, classified transient or
  durable, with the operational justification traced to the CONOPS.
- **Partition behaviour.** What the service does when the mesh splits, and what
  it does when it rejoins. Documented from the upstream service's actual
  behaviour, cited, not assumed.
- **Conflict resolution.** For the durable set, the rule when two partitions
  diverged.
- **Rollback behaviour.** What happens to state when a node rolls back to the
  known-good path (`FML-ADR-041`, `TBR-REC-01`).
- **Resource envelope.** Measured, feeding `TBR-COMP-01`.
- **Catalog entry** in `services/catalog/`, with the image referenced by
  immutable digest.

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
