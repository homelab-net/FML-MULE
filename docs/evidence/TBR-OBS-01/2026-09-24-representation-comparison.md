# What existing representations do with a mission observation

**Trade:** `TBR-OBS-01`.
**Date:** 2026-09-24.
**Taken by:** written comparison. No node was run, no flat-sat was run, and
nothing here is `SIMULATED` or `HARDWARE-VERIFIED`.

## What this is

The closure evidence named in the trade: a comparison of candidate
representations against the eight sentences in CONOPS v1.2 section 28A. It
names what each candidate does with time, source, state, a queued delivery,
an expired record, two subjects, a link report, a derived product, and a full
queue.

It does not select a representation. It does not close the trade. `FML-ADR-083`
is `PROPOSED` to record the finding below, and it carries no weight until the
named owner accepts it. The gate is that acceptance, which is not recorded
in this file.

A field counts only when the source already gives it the meaning the sentence
needs. Putting that meaning into a profile, a `detail` subschema, or a new
element is a new document. `FML-ADR-048` allows that only as protocol-specific
glue for semantics upstream does not have, and this comparison does not write
that glue.

## Candidates

These already exist. A new observation document is not a candidate.

1. A Cursor on Target event, as `Event.xsd` Version 2.0 defines it. The
   program does not redefine CoT (`docs/interfaces/README.md`,
   `services/tak/README.md`).
2. The `cot` row OpenTAKServer 1.7.13 already stores for such an event.
   `FML-ADR-032` prefers that server. `FML-ADR-071` classed the table as
   reconstructable PLI.
3. A Meshtastic `Position`, and the `MeshPacket` fields that carry it.
4. A Meshtastic `Neighbor` inside `NeighborInfo`. This is the existing
   "a link was heard" message, scored on its own and not stretched into a
   general observation.

Also looked at, and not scored as representations, because none of them is an
observation record:

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
The schema file is MITRE's, copyright 2005, and is not copied into this
repository.

| Source | Pin |
| --- | --- |
| `Event.xsd` header: "Schema for Cursor-On-Target (CoT) Event data model (Version 2.0) 13-June-2003" | `docjason/XmlValidate` commit `89ced733e661d14cd21f58fce5a60ed5fa60f067`, file `schemas/Event.xsd` |
| OpenTAKServer `opentakserver/models/CoT.py` | tag `1.7.13`, commit `67903c26d95552738d85be4bc3c3ff3321378dbe`. Same package version as the `TBR-TAK-01` inventory. |
| Meshtastic `meshtastic/mesh.proto` | `meshtastic/protobufs` commit `8f97d66a63ce10cfb12f94203e361691647f5ad3` (2026-09-21) |

The CoT copy is a public repository's file, not a download from the DISA XML
registry. The header in that file is the identification used here. No ATAK,
iTAK, or WinTAK binary was run, so this file does not say how a client draws
a marker.

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
1330. Those are three different facts. None of the three attributes is
defined as the time the thing was observed. `stale` is a timestamp. It is not
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
outside of this document". A state word placed there would be a new
subschema. Stock clients are not required to read it. That is the case
`FML-ADR-048` and `AGENTS.md` already refuse as a private tag.

OpenTAKServer 1.7.13 `CoT` columns are `how`, `type`, `uid`,
`sender_callsign`, `sender_device_name`, `sender_uid`, `recipients`,
`timestamp`, `start`, `stale`, `xml`, and `mission_name`. `uid` is not
unique. There is no state column and no retention column. `sender_uid`
references `euds.uid`. It names the connected endpoint the server associated
with the row. It is not a CoT attribute. `FML-ADR-071` classed this table as
reconstructable: loss and regeneration are acceptable for it. The
`TBR-TAK-01` bench found the only CoT queue, `cot_parser`, non-durable.
`delete_old_data` in `opentakserver/blueprints/scheduled_jobs.py` at tag
`1.7.13` executes `delete(CoT).where(CoT.timestamp <= timestamp)`. The
default cutoff includes `OTS_DELETE_OLD_DATA_WEEKS` from the environment,
defaulting to `1`, in `defaultconfig.py`. That deletes the row on a server
clock. It is not a mission-profile retention, and it is deletion.

Meshtastic `Position.timestamp` is "Positional timestamp (actual timestamp of
GPS solution) in integer epoch seconds". `Position.time` is "usually not sent
over the mesh" and exists so a phone can set a device clock. `location_source`
is "How the location was acquired: manual, onboard GPS, external (EUD) GPS".
`sensor_id` is "Sensor ID - in case multiple positioning sensors are being
used." That is which positioning sensor produced the fix, not the source of
an observation of some other subject. The enum value comments on
`location_source` in that commit are `TODO: REPLACE`, so they are not used
here. `MeshPacket.from` is "The sending node number." `MeshPacket.rx_time`
is "The time this message was received", "never sent on the radio link", and
"may still be re-timestamped once a valid clock becomes available, before the
phone ever sees it."

Meshtastic `Neighbor.snr` is "SNR of last heard message". `Neighbor` has a
`node_id` and no latitude or longitude. `Neighbor.last_rx_time` is reception
time and "will not be sent out over the mesh." `NeighborInfo.node_id` is "The
node ID of the node sending info on its neighbors."

## Score

| Sentence | CoT event | OpenTAKServer `cot` row | Meshtastic `Position` | Meshtastic `Neighbor` |
| --- | --- | --- | --- | --- |
| Time observed | Not defined. `time` is birth. `start` is validity start. | Copies those two, plus the row's `timestamp` from the event `time`. | `timestamp` is the GPS solution time, for this position only. | None. `last_rx_time` is when a message was received, and it is not sent. |
| Source | `how` is how the coordinates were made, not who produced the observation. | `sender_uid` and `sender_callsign` name the connected endpoint. A relay can be that endpoint. | `from` is the sending node number. `location_source` is how the fix was acquired. | `node_id` is the node reporting neighbors, or the neighbor. Neither is a subject separate from the radio. |
| Six state words | No such values. Optional `qos` uses "supersede" to mean the newer event deletes the older one. | No state column. | None. `sensor_id` names a positioning sensor. | None. |
| Not presented as current | After `stale`, the event is outside its validity interval. One timestamp covers both "stale" and "expired", so the record cannot say which. | Same timestamps. | No validity end. | No validity end. |
| Delivery must not replace observation time | No delivery-time field. A forwarded event can keep `time` and `start`. A newly generated event has a new birth time, which is what `time` means. | Stores the event times it was given. | `timestamp` is in the position. `rx_time` is reception, is not sent on the radio, and may be rewritten before a phone sees it. Using `rx_time` as the observed time would be the replacement the sentence forbids. | `last_rx_time` is reception time and is local only. |
| Expiry is history, not deletion | The `uid` rule overwrites every previous event for that UID with the latest. Optional `qos` value `r` is "new event replaces (deletes) old event". | `uid` is not unique, so more than one row can exist. `delete_old_data` then deletes rows older than a server cutoff, default one week. That is not a mission-profile retention. `FML-ADR-071` does not require the table to survive. | A position is the position. No retention field. | Local only. No retention field. |
| Two subjects; possible match is not identity | Distinct UIDs are distinct pieces of information. Nothing records "possible" versus "confirmed". `how` value `f` means fused, "corroborated from multiple sources", which is a confirmation hint, not a caution. | Same. | One sending node. No match field. | One neighbor id. No match field. |
| Heard link is not a usable path or an emitter location | A point is required, so the event is a location. No field says the path can or cannot carry traffic. | A `point` row is stored with the event. | The message is a location. | SNR of the last heard message, with no coordinates. It does not say the path can carry traffic. It also does not say it cannot. |
| Derived product names sources, does not replace them; a model is labeled and is not an observation | `detail` is outside the schema. `how` can say predicted, simulated, or fused, and the event is still an event with a point. Reusing a source UID overwrites that source. | Same stored XML. | None of these fields. | None of these fields. |
| Full queue records the discard and does not end participation | No bound and no participation flag. Optional `qos` value `c` drops a message on congestion and does not record that drop. | The bench's `cot_parser` queue was non-durable and records no discard. | `MeshPacket` priority can keep a background position from being sent on a congested link. That comment does not say the drop is recorded, and it does not speak about participation. | None. |

## Finding

No candidate carries all eight sentences. A separate reading was asked to
falsify that result against the same sentences and the same kinds of source.
It confirmed the result. The `qos` quotations, the `delete_old_data` cutoff,
`sensor_id`, and the `mule/status.py` `Observations` class are in this file
because that reading named them and the pins above support them.

`Position.timestamp` is the one field whose documented meaning is a time of
observation, and only for a GPS fix of that position. `Neighbor` is the one
message that reports a heard link without coordinates. Neither message
records the six state words, a retention rule, a derived product, or a
discard. A mission observation cannot be one of those messages without giving
the other sentences meanings those files do not give.

A CoT event is the exchange form `FML-ADR-048` already prefers, and it is the
closest of the four. It still does not carry the sentences:

- Observed time is not `time` and is not `start`. Using `start` for it is a
  convention the schema does not state. That convention would be a new
  document.
- The six words are not values of any attribute. Collapsing stale and expired
  into the one `stale` timestamp records neither word.
- The `uid` rule overwrites previous events. That treats the previous event
  as replaced. It is not a mission-profile retention, and it is not "expiry
  is not deletion".
- The OpenTAKServer row can keep more than the latest event, and it can name
  a sender. The program has already classed that table as reconstructable
  PLI, so it is not the history the retention sentence requires. The sender
  column is not one of the six words.
- A heard link does not fit in an event whose point is required, unless the
  report is presented as a location.
- A derived or model product has no base-schema place to name its sources
  that also stops a reused UID from overwriting them. `how` does not say the
  event is not an observation.
- Nothing in the event, the row, or `FML-ADR-050` is a bounded observation
  queue that records a discard.

Using CoT for some sentences and `Neighbor` for the link sentence is two
representations, not one, and the CoT half still fails the rest.

The trade's first option therefore does not apply: no existing field shows
time, source, and one of the six state words without a new document. The
second option does not apply either: the node does not already keep an
observation record that can be presented as itself. `FML-ADR-048` still
permits glue for the missing semantics. This file is the reason that glue
would be needed. It does not specify the glue, and it does not adopt a custom
observation format.

## What this does not establish

No client, server, or radio was run for this comparison. The OpenTAKServer
behavior cited from `TBR-TAK-01` was already recorded there; it was not
repeated. Stage 1 was not run. Nothing in `mule/` changed. `v0.0.1` is
unchanged.
