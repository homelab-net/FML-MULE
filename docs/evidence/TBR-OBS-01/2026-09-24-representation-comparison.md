# What the reviewed representations already say about a mission observation

**Trade:** `TBR-OBS-01`.
**Date:** 2026-09-24.
**Taken by:** written comparison. No node was run, no software digital twin was run, and
nothing here is `SIMULATED` or `HARDWARE-VERIFIED`.

## What this is

A comparison of four existing representations against the eight sentences in
CONOPS v1.2 section 28A. The question it answers is which of those sentences
the cited sources already define, and which they do not, without adding new
FML semantics.

It does not select a representation. It does not close the trade. It does
not issue an ADR. It does not decide which layer would supply a semantic the
reviewed sources do not define. Owner acceptance is still pending.

A cell in the score counts only when the cited source already gives the
field the meaning the sentence needs. A mapping convention, a profile, a
detail schema this file did not read, or a new element is not that meaning.
This comparison does not write any of those.

## Two kinds of sentence

Section 28A mixes data on a record with behavior around that record. Asking
whether one message carries all eight treats both kinds as fields. They are
not. A payload can stay in an upstream form while presentation, correlation,
retention, and queue policy sit beside it. This file does not choose that
split. It only keeps the two kinds separate so a later decision does not
invent one record for all eight.

Data. A representation can carry these as native semantics.

| Criterion | What would be on the record |
| --- | --- |
| `FML-REQ-034` | Time observed, the source, and one of the six lifecycle words. |
| `FML-REQ-040` | A derived product names the observations it came from and does not replace them. A model product is labeled as one. |

Behavior. These need not be fields in the message. Local policy can carry
them.

| Criterion | The behavior |
| --- | --- |
| `FML-REQ-035` | A stale or expired observation is not presented as current. |
| `FML-REQ-036` | Relaying or queuing does not replace the time of observation with the time of delivery. |
| `FML-REQ-037` | Expiry keeps history for the retention the mission profile sets. Expiry is not deletion. |
| `FML-REQ-038` | An observation of one subject is not merged with an observation of a different subject. A possible match is not presented as a confirmed identity. |
| `FML-REQ-039` | A report that a link was heard is not presented as a usable path or as an emitter location. |
| `FML-REQ-041` | While the node cannot deliver, locally produced observations stay, up to a bound. A discard to stay inside the bound is recorded. The bound does not by itself end local participation. |

## Candidates

These already exist. A new observation document is not a candidate. The four
below are the representations this file read. They are not a claim that every
upstream message was read.

1. A Cursor on Target event, as `Event.xsd` Version 2.0 defines it. The
   program does not redefine CoT (`docs/interfaces/README.md`,
   `services/tak/README.md`). Base `detail` contents are defined outside
   that schema. This file did not inventory those detail schemas.
2. The `cot` row OpenTAKServer 1.7.13 already stores for such an event.
   `FML-ADR-032` prefers that server. `FML-ADR-071` classed the table as
   reconstructable PLI.
3. A Meshtastic `Position`, and the `MeshPacket` fields that carry it.
4. A Meshtastic `Neighbor` inside `NeighborInfo`. This is the existing
   "a link was heard" message, scored on its own and not stretched into a
   general observation. Other messages in the same protobuf were not scored.
   This file does not show that none of them can carry a sensor reading.

Also looked at, and not scored as representations, because none of them is an
observation record of the kind above. Setting them aside is not an inventory
of every OpenTAKServer table or every local log:

- `mule/status.py` defines a class named `Observations`. The module is the
  CONOPS section 67 status view. The class docstring says it is everything the
  node observed, gathered in one place: boot, bearers, power, thermal, and
  modes. It is not a section 28A mission observation, and it has none of the
  six state words.
- SAD section 16.6 records administrative events (credential, role, scope,
  mission-profile). It does not record an observation.
- `FML-ADR-050` bounds logs and telemetry writes. It does not define an
  observation, a queue of them, or a discard record.
- OpenTAKServer `markers`, `alerts`, `mission_logs`, and `geochat` are
  classified in
  `docs/evidence/TBR-TAK-01/2026-08-31-relational-state-decomposed-into-conops-classes.md`.
  They are an operator symbol, an alert with `start_time` and `cancel_time`,
  a written log, and a chat message. None of those columns is the six state
  words.

## Sources

Retrieved 2026-09-24. Short quotations below are the words the score uses.
The CoT schema is archived beside this file. Its MITRE copyright stays on
that copy.

| Source | Pin |
| --- | --- |
| `Event.xsd` header: "Schema for Cursor-On-Target (CoT) Event data model (Version 2.0) 13-June-2003" | Archived at `docs/evidence/TBR-OBS-01/2026-09-24-event-xsd-version-2.0.xsd`. Retrieved 2026-09-24 from `docjason/XmlValidate` commit `89ced733e661d14cd21f58fce5a60ed5fa60f067`, file `schemas/Event.xsd`. SHA-256 `c3416f653638cffa3354ba8556fa7855cfc9bec4ed1a4e23a0e979bded3b9365`. |
| OpenTAKServer `opentakserver/models/CoT.py` | Archived verbatim at `docs/evidence/TBR-OBS-01/2026-09-24-opentakserver-1.7.13-cot.py.txt`. Tag `1.7.13`, commit `67903c26d95552738d85be4bc3c3ff3321378dbe`. GPL-3.0-only. License text: `docs/evidence/licenses/GPL-3.0.txt`. Not relicensed. |
| Meshtastic `meshtastic/mesh.proto` | Archived verbatim at `docs/evidence/TBR-OBS-01/2026-09-24-meshtastic-mesh.proto`. `meshtastic/protobufs` commit `8f97d66a63ce10cfb12f94203e361691647f5ad3` (2026-09-21). GPL-3.0-only. License text: `docs/evidence/licenses/GPL-3.0.txt`. Not relicensed. |

The CoT copy in this directory is the file retrieved from that commit. It is
not a download from the DISA XML registry. The header in that file is the
identification used here. MITRE's copyright notice stays on the file. It is
not relicensed as CC BY 4.0. No ATAK, iTAK, or WinTAK binary was run, so this
file does not say how a client draws a marker.

## The eight sentences

From CONOPS v1.2 section 28A, verbatim:

```text
A mission observation shall record the time it was observed, the
source that produced it, and whether it is new, active, stale, expired,
merged, or superseded.

A stale or expired observation shall not be presented as current.

Relaying, queuing, or later delivery shall not replace the time of
observation with the time of delivery.

An expired observation shall remain history for the retention the
mission profile sets. Expiry shall not be treated as deletion.

An observation of one subject shall not be merged with an observation
of a different subject. A possible match shall not be presented as a confirmed
identity.

A report that a link was heard shall not be presented as proof that
the path can carry traffic, and shall not be presented as the location of an
emitter.

A summary, alert, or other derived product shall identify the
observations it came from and shall not replace those observations. A product
of a model shall be labeled as a model product and shall not be presented as
an observation.

While the node cannot deliver, locally produced observations shall
still be kept, up to a bound set by the mission profile. Discarding one to
stay inside that bound shall be recorded. The bound shall not by itself end
local participation.
```

## What each field is documented to mean

`Event.xsd` on `uid`:

```text
The "uid" attribute is a globally unique name for this specific piece of
information. Several "events" may be associated with one UID, but in that
case, the latest (ordered by timestamp), overwrites all previous events for
that UID.
```

`Event.xsd` on `time`, `start`, and `stale`:

```text
"time" is a time stamp placed on the event when generated.
start and stale define an interval in time for which the event is valid.
In V2.0, time indicates the "birth" of an event and the start and stale
pair define the validity interval.
The "start" attribute defines the starting time of the event's validity
interval.
The "stale" attribute defines the ending time of the event's validity
interval.
```

The schema's own example puts generation at noon and validity from 1300 until
1330. Those are three different facts. CoT does not define `time` as
observation time. It defines `time` as event-generation time. An FML gateway
could generate the event at the moment of observation and map that moment
onto `time`. That would be a mapping convention, not a meaning the schema
states. `stale` is a timestamp, the end of the validity interval. It is not
one of the six state words, and the schema has no attribute whose values are
`new`, `active`, `stale`, `expired`, `merged`, or `superseded`.

`Event.xsd` on `how`: a hint about how the coordinates were generated, so a
fuser can weight errors. The documented tokens include `g` (GPS), `s`
(simulated), `f` (fused, "corroborated from multiple sources"), `p`
(predicted), and `r` (relayed, "imported from another system"). That is a
hint about coordinates, not the identity of the producer, and not a label
that the event is not an observation.

`Event.xsd` on `qos`, which is `use="optional"`:

```text
The more recent event (by timestamp) may supersede the older event
(deleting the old event)
r - replace - new event replaces (deletes) old event
d - deadline (message dropped only after "stale" time)
c - congestion - message dropped when link congestion encountered
Priority determines queuing order at a bottleneck.
```

The schema uses "supersede" to mean delete. Assurance `d` and `c` drop the
message. Neither records a retained state, a mission-profile retention, or a
discard entry, and neither says local participation continues. Priority is
queuing order, not one of the six words.

`Event.xsd` on `point`: `lat`, `lon`, `hae`, `ce`, and `le` are required.
`ce` is a circular area around the point, "not necessarily an error". It is
still an area around a point. The base schema has no field meaning "this is
not a location" or "this path cannot be assumed to carry traffic".

`Event.xsd` on `detail`: information for a smaller community, "defined
outside of this document". The base schema therefore does not define a
lifecycle word, a source list, or a model-product label inside `detail`.
That is not the same claim as "no existing CoT representation defines
them." This comparison did not inventory detail schemas outside `Event.xsd`.

A newly invented private element inside `detail` is not shown to be
acceptable by this file. It would need its own interface decision, evidence
that the upstream semantics already in use are insufficient, and a check
that the TAK clients this program actually uses can read it. This file
does not make that decision.

OpenTAKServer 1.7.13 `CoT` columns are `how`, `type`, `uid`,
`sender_callsign`, `sender_device_name`, `sender_uid`, `recipients`,
`timestamp`, `start`, `stale`, `xml`, and `mission_name`. `uid` is not
unique. There is no state column and no retention column. `sender_uid`
references `euds.uid`. That column is not a CoT attribute. The archived
model declares it and the foreign key. It does not show the code that
writes `sender_uid` or `sender_callsign`. This file did not read that
path, so it does not establish that the value is the connected endpoint,
or that a relay can be that value. `FML-ADR-071` classed this table as
reconstructable: loss and regeneration are acceptable for it. The
`TBR-TAK-01` bench found the only CoT queue, `cot_parser`, non-durable.
`delete_old_data` in the archived
`2026-09-24-opentakserver-1.7.13-scheduled-jobs.py.txt` executes
`delete(CoT).where(CoT.timestamp <= timestamp)`. The default cutoff includes
`OTS_DELETE_OLD_DATA_WEEKS` from the environment, defaulting to `1`. That
passage is archived as
`2026-09-24-opentakserver-1.7.13-delete-old-data-default.txt`. The rest of
`defaultconfig.py` is not archived: it contains upstream default
credentials, which this repository does not store. The cutoff deletes the
row on a server clock. It is not a mission-profile retention, and it is
deletion.

Meshtastic `Position.timestamp` is "Positional timestamp (actual timestamp of
GPS solution) in integer epoch seconds". For a position fix, that documented
meaning is a time of observation of that fix. `Position.time` is "usually not
sent over the mesh" and exists so a phone can set a device clock.
`location_source` is "How the location was acquired: manual, onboard GPS,
external (EUD) GPS". `sensor_id` is "Sensor ID - in case multiple positioning
sensors are being used." That is which positioning sensor produced the fix,
not the source of an observation of some other subject. The enum value
comments on `location_source` in that commit are `TODO: REPLACE`, so they are
not used here. `MeshPacket.from` is "The sending node number."
`MeshPacket.rx_time` is "The time this message was received", "never sent on
the radio link", and "may still be re-timestamped once a valid clock becomes
available, before the phone ever sees it."

Meshtastic `Neighbor.snr` is "SNR of last heard message". `Neighbor` has a
`node_id` and no latitude or longitude. `Neighbor.last_rx_time` is reception
time and "will not be sent out over the mesh." `NeighborInfo.node_id` is "The
node ID of the node sending info on its neighbors."

For a link-heard observation those are different roles.
`NeighborInfo.node_id` is the source: the node reporting what it heard.
`Neighbor.node_id` is the subject: the neighbor it reports. The message
still has no lifecycle word, and it does not say the path can carry traffic.

## Score

A behavior row that names no field means the record does not state that
policy. It does not mean the sentence can be met only by adding a field.

| Sentence | CoT event | OpenTAKServer `cot` row | Meshtastic `Position` | Meshtastic `Neighbor` |
| --- | --- | --- | --- | --- |
| Time observed | Not defined as observation time. `time` is event generation. `start` is validity start. Mapping observation time onto `time` would be a convention. | Copies those two, plus the row's `timestamp` from the event `time`. | `timestamp` is the GPS solution time, for this position only. | None. `last_rx_time` is when a message was received, and it is not sent. |
| Source | `how` is how the coordinates were made, not who produced the observation. | `sender_uid` is a foreign key to `euds.uid`. `sender_callsign` is a column. The code that writes them was not read, so this file does not establish that either value is the connected endpoint. | `from` is the sending node number. `location_source` is how the fix was acquired. | `NeighborInfo.node_id` is the source: the node reporting its neighbors. `Neighbor.node_id` is the subject: the neighbor reported. Those are distinct. |
| Six state words | No such values. Optional `qos` uses "supersede" to mean the newer event deletes the older one. | No state column. | None. `sensor_id` names a positioning sensor. | None. |
| Not presented as current | After `stale`, the event is outside its validity interval. One timestamp covers both "stale" and "expired", so the record cannot say which. Presentation of a past-`stale` event is not defined here. | Same timestamps. No presentation rule. | No validity end. | No validity end. |
| Delivery must not replace observation time | No delivery-time field. A forwarded event can keep `time` and `start`. A newly generated event has a new birth time, which is what `time` means. | Stores the event times it was given. | `timestamp` is in the position. `rx_time` is reception, is not sent on the radio, and may be rewritten before a phone sees it. Using `rx_time` as the observed time would be the replacement the sentence forbids. | `last_rx_time` is reception time and is local only. |
| Expiry is history, not deletion | The `uid` rule overwrites every previous event for that UID with the latest. Optional `qos` value `r` is "new event replaces (deletes) old event". | `uid` is not unique, so more than one row can exist. `delete_old_data` then deletes rows older than a server cutoff, default one week. That is not a mission-profile retention. `FML-ADR-071` does not require the table to survive. | A position is the position. No retention field. | Local only. No retention field. |
| Two subjects; possible match is not identity | Distinct UIDs are distinct pieces of information. Nothing records "possible" versus "confirmed". `how` value `f` means fused, "corroborated from multiple sources", which is a confirmation hint, not a caution. | Same. | One sending node. No match field. | Reporter and neighbor are already two ids. Nothing records "possible" versus "confirmed". |
| Heard link is not a usable path or an emitter location | A point is required, so the event is a location. No field says the path can or cannot carry traffic. | A `point` row is stored with the event. | The message is a location. | SNR of the last heard message, with no coordinates. It does not say the path can carry traffic. It also does not say it cannot. |
| Derived product names sources, does not replace them; a model is labeled and is not an observation | `detail` is outside the schema. `how` can say predicted, simulated, or fused, and the event is still an event with a point. Reusing a source UID overwrites that source. | Same stored XML. | None of these fields. | None of these fields. |
| Full queue records the discard and does not end participation | No bound and no participation flag. Optional `qos` value `c` drops a message on congestion and does not record that drop. | The bench's `cot_parser` queue was non-durable and records no discard. | `MeshPacket` priority can keep a background position from being sent on a congested link. That comment does not say the drop is recorded, and it does not speak about participation. | None. |

## Finding

None of the reviewed representations, using only the meanings their cited
sources already define, satisfies the complete section 28A contract without
new FML semantics.

That is the finding this file supports. It is not a finding that no existing
representation anywhere can carry the contract. Detail schemas outside
`Event.xsd` were not read. `Position` and `Neighbor` are not every
Meshtastic message.

What those sources do already define:

- `Position.timestamp` is a GPS solution time, for that position only. It is
  the one reviewed field whose documented meaning is a time of observation,
  and only for that fix.
- For a heard link, `NeighborInfo.node_id` is the source, the node
  reporting its neighbors, and `Neighbor.node_id` is the subject, the
  neighbor reported. Those roles are already distinct. The message has no
  coordinates. It does not say the path can carry traffic, and it does not
  say it cannot. It is not a general observation, and it has no lifecycle
  word.
- CoT `how` is a hint about how coordinates were generated, including fused,
  predicted, simulated, and relayed. It is not the producer of an
  observation, and it does not say the event is not an observation.
- CoT `uid` names one piece of information. The latest event for that `uid`
  overwrites the earlier ones.
- The OpenTAKServer row can keep more than one event for a `uid`.
  `sender_uid` is a foreign key to `euds.uid`, and `sender_callsign` is a
  column. The code that writes them was not read. This file does not
  establish that either value is the connected endpoint, or that a relay
  can be that value.

What those sources do not define as native semantics:

- None of the four defines `new`, `active`, `stale`, `expired`, `merged`, or
  `superseded` as values of a field.
- CoT `stale` is the end of a validity interval. One timestamp cannot say
  both "stale" and "expired".
- CoT `time` is event-generation time. It is not defined as observation
  time. Mapping one onto the other would be a convention.
- Optional `qos` uses "supersede" to mean the newer event deletes the older
  one. The `uid` rule overwrites the previous event. Neither is a retained
  superseded state, and neither is the retention a mission profile sets.
- OpenTAKServer `delete_old_data` deletes `cot` rows past a server cutoff
  that defaults to one week. That is deletion on a server clock.
  `FML-ADR-071` already classed that table as reconstructable PLI, so it is
  not the history the retention sentence requires.
- No reviewed field names the source observations of a derived product and
  also keeps those observations from being overwritten. `how` does not say
  the event is not an observation. Whether some existing detail schema does
  is outside this file.
- None of the four is a bounded observation queue that records a discard
  and says local participation continues. Optional `qos` value `c` drops a
  message on congestion and does not record the drop.

The behavior sentences are not shown to be missing fields that one new
record would have to add. This file does not choose a payload, local
metadata, or local policy. A definition that does not state a behavior is
not a finding that the upstream consumer lacks it. No TAK client source
and no Meshtastic firmware source were read for those sentences.

## What this does not establish

No client, server, or radio was run for this comparison. No TAK client
source and no Meshtastic firmware source were read. The OpenTAKServer
behavior cited from `TBR-TAK-01` was already recorded there; it was not
repeated. Where a consumer was not read, that is a limit of this file.
It is not proof that the behavior is absent. Stage 1 was not run.
Nothing in `mule/` changed. `v0.0.1` is unchanged.

The named owner has not accepted the finding. `TBR-OBS-01` stays `OPEN`.
No representation is selected. No custom observation format is adopted.
No schema is added.
