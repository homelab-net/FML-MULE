# What the cited consumers do with an observation

**Trade:** `TBR-OBS-01`.
**Date:** 2026-09-24.
**Taken by:** reading the source named below. No node was run, no software
digital twin was run, and nothing here is `SIMULATED` or
`HARDWARE-VERIFIED`.

## What this is

The comparison in `2026-09-24-representation-comparison.md` scored schemas
and message definitions. It said a definition that does not state a
behavior is not a finding that the consumer lacks it. This file reads the
consumers that comparison left unread, for the behaviors the eight section
28A sentences name.

It does not select a representation. It does not close the trade. It does
not issue an ADR. It does not assign a semantic those consumers do not
state to local FML policy.

## Pins

OpenTAKServer tag `1.7.13`, commit
`67903c26d95552738d85be4bc3c3ff3321378dbe`. Same pin as the comparison.
Excerpts and hashes are in `2026-09-24-consumer-reading.SOURCE.md`.
GPL-3.0-only. Not relicensed.

Meshtastic firmware tag `v2.8.0.47db0e3`, commit
`47db0e3020a608e06fb65cce70cd2f093021bd82`, published 2026-09-01. This is
not the protobufs commit the comparison archived
(`8f97d66a63ce10cfb12f94203e361691647f5ad3`, 2026-09-21). The firmware
reading does not re-score that protobuf.

## Not read

No ATAK, iTAK, or WinTAK client function is cited. The public
`deptofdefense/AndroidTacticalAssaultKit-CIV` repository was archived on
2026-09-22. This file does not extract a presentation path from it. That
limit is not proof that a TAK client lacks a behavior.

CoT detail schemas outside `Event.xsd`, and outside the tags the functions
below actually read, were not inventoried. Other Meshtastic port numbers
were not read. No client, server, or radio was run.

## Who the streaming path stores as the sender

`EudHandler.publish_cot` publishes `{"uid": self.uid, "cot": str(event)}`
to the `cot_parser` exchange. `CotParser.on_message` sets
`uid = body["uid"] or event.attrs["uid"]`, and passes that into
`insert_cot`. `insert_cot` writes `sender_uid=uid` and
`uid=event.attrs["uid"]`. Those are different columns.

`self.uid` is assigned in `parse_device_info`, and only when it is still
empty. The assignment is `event.attrs["uid"]` of an event that has a
`<contact>` tag, is not a ping, and arrives on a socket that already has a
user or is not SSL. The comment above that assignment says a Meshtastic or
DMR relay should use the off-grid EUD uid rather than the relay. The
assignment is not repeated for a later event. After it, a later event on
that socket is stored with the first uid even when `event.attrs["uid"]`
differs. If `self.uid` is still empty, the parser uses the event uid.

`insert_cot` does not write `sender_callsign`.

A different writer, the marker API insert, sets
`sender_callsign` to `current_user.username` and does not set
`sender_uid`. That insert is not the streaming path. Neither writer is a
field whose documented meaning is the producer of an observation of an
arbitrary subject.

## What is still shown after `stale`

`EudHandler.on_message` sends `body["cot"]` as received. It does not
compare `stale` with the clock. It skips a message only when
`body["uid"] == self.uid`.

`get_map_state` is documented as the latest data for the web UI map. It
returns every EUD. It returns markers, range-bearing lines, and casevacs
only when `CoT.stale` is at or after the server clock. `EUD.to_json` sets
`last_point` to `None`. The filter is one timestamp. It does not label
`stale` as distinct from `expired`. A row omitted from that response can
still exist until `delete_old_data`. Omission from the map payload is not
a history view, and it is not one of the six state words.

`GET /Marti/api/cot/xml/<uid>` returns the stored XML for one row. The
function does not filter on `stale`.

## Whether delivery replaces the observation time

`route_cot` republishes `str(event)`. The excerpted streaming path does
not replace event `time` with a delivery time.

The OpenTAKServer Meshtastic controller is a different consumer. It turns
some protobufs into a new CoT event. `cot()` sets `time`, `start`, and
`stale` from `datetime.datetime.now`. `stale` is that clock plus one day.
`position()` sets `Point.timestamp` to the same clock. The excerpted lines
do not copy `Position.timestamp`. A CoT built there has a server
generation time, which is the replacement section 28A forbids if that
event is then treated as the observation.

On the firmware send path, `PositionModule` copies `localPosition.timestamp`
onto the outgoing position only when the `TIMESTAMP` flag is set. This
file did not read the assignment of `localPosition.timestamp`, so it does
not add a claim about what that field contains. It also does not show the
send path writing `MeshPacket.rx_time`.

## A heard link

`NeighborInfoModule::collectNeighborInfo` copies `node_id` and `snr` into
the packet it sends. The comment in that function says `last_rx_time` is
not set because it is not sent over the mesh. The excerpt has no latitude
and no longitude. It does not say the path can carry traffic.

`cleanUpNeighbors` erases a local neighbor when the clock minus
`last_rx_time` exceeds twice that neighbor's broadcast interval, and logs
the removal. That is deletion of a local entry. It is not a recorded
observation discard, and it does not keep a history.

`MeshtasticController.protobuf_to_cot` handles `POSITION_APP`,
`MAP_REPORT_APP`, `NODEINFO_APP`, `TEXT_MESSAGE_APP`, `ATAK_PLUGIN`, and
`TELEMETRY_APP`. It has no `NEIGHBORINFO_APP` branch. This server consumer
does not turn that message into a CoT event.

## A full queue

`Router::enqueueReceivedMessage` drops the oldest packet when
`fromRadioQueue` does not accept another. It logs
`fromRadioQ full, drop oldest!` and releases the packet. The log line is
not an observation-discard record. The function does not mention
participation.

The streaming path sets RabbitMQ `expiration` from
`OTS_RABBITMQ_TTL`. This file did not read that default. `defaultconfig.py`
is still not archived, for the reason already recorded: it contains
upstream default credentials. The property is a broker lifetime of the
queued message. It is not CoT `stale`, and it is not a discard record.

## What these consumers do not define

None of the functions read assigns `new`, `active`, `stale`, `expired`,
`merged`, or `superseded` as a state of an observation. `stale` in the
server code remains the CoT timestamp.

None of them records a possible match as distinct from a confirmed
identity. None names the source observations of a derived product and
keeps those observations. None records a discard made to stay inside a
mission-profile bound, and none says that bound does not end local
participation.

## Finding

The consumers read here do not satisfy the complete section 28A contract.

What they do show:

- On the streaming path, `sender_uid` is the socket's first contact uid
  after that socket has identified, not the uid of each later event.
- The web map omits a past-`stale` marker, range-bearing line, or casevac.
  It does not label the six words, and it does not present the omitted row
  as history.
- The Meshtastic-to-CoT builder stamps the server clock onto `time`,
  `start`, `stale`, and the stored point time.
- A neighbor packet sent by the cited firmware carries a node id and an
  SNR. It does not carry `last_rx_time` or a coordinate, and it does not
  say the path can carry traffic.
- A full radio receive queue drops the oldest packet and logs that drop.

What this file still does not show:

- How a TAK client draws an event after `stale`.
- Whether a CoT detail schema this file did not read already carries a
  lifecycle word, a source list, or a model-product label.
- A selected representation.

The named owner has not accepted how an observation is recorded and
presented. `TBR-OBS-01` stays `OPEN`. No schema is added. Nothing in
`mule/` changed.
