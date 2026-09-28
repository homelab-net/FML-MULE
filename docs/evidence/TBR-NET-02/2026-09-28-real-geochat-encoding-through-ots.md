# What OpenTAKServer puts in GeoChat.to and Contact.callsign, on the wire

**Tier:** `SIMULATED` / real-OTS-encoder + real-client. This drives OpenTAKServer's
**real** outbound encoder (`cot_parser.py`) and captures what it emits; the message
inputs are synthetic EUDs, and the capture is at the encoder's MQTT output, not over
LoRa RF. It is a real advance over `2026-09-06-geochat-to-survives-the-meshtastic-bearer.md`
(which hand-built the `TAKPacket` in a Python client): here OpenTAKServer itself
builds it, and a live iTAK client corroborates the sender fields. It says nothing
about RF -- delivery over a real hop is `2026-09-27-one-lora-hop-to-a-partner-node.md`.

**Date:** 2026-09-28. **Taken by:** Cameron Zobrist. **Instrument/software:**
OpenTAKServer 1.7.13 (`fml-ots`), its `cot_parser` outbound encoder, and a live iTAK
client on the bench.

## Why this was done

`FML-ADR-070` carries the LoRa recipient in `GeoChat.to` and the sender in
`Contact.callsign`, but recorded an open item: *"`GeoChat.to`'s contents are not yet
established… the recipient-resolution step cannot be implemented until a follow-up
establishes it."* `mule/recipients.py.decide_delivery` is blocked on it: its
`recipient_key` is *"whatever a future upstream step parsed from `GeoChat.to`, not
decided here."* This establishes those contents.

## Method

OpenTAKServer's outbound Meshtastic encoder was enabled (`OTS_ENABLE_MESHTASTIC:
true` plus one `downlink_enabled` channel). `cot_parser.publish_to_meshtastic`
(`cot_parser.py:915-929`) publishes the encoded `ServiceEnvelope` to `amq.topic`
routing key `opentakserver.2.e.<channel>.outgoing` -- plain AMQP, no `rabbitmq_mqtt`
plugin needed. A `pika` consumer bound to `opentakserver.2.e.*.outgoing` captured
each envelope; it was decoded `ServiceEnvelope -> MeshPacket.decoded.payload ->
atak_pb2.TAKPacket`, and the unishox2-compressed string fields were decompressed.

A synthetic sender (`FMLPROBE-ALPHA`) drove a DM and a named-room GeoChat through
the encoder (`cot_parser.py:451-517`). **The recipient's id and callsign were set
deliberately different** so the capture distinguishes which one `chat.to` carries: a
first run with `id == callsign` could not (it produced the same string either way);
this run uses recipient **id `UID-CHARLIE-9999`** and **callsign `CHARLIE-CS`**. A
bench note: the `eud_handler` TCP CoT listener (:8088) raised `AttributeError:
'NoneType' object has no attribute 'basic_publish'` after its first connection
(`rabbit_channel` cleared on connection close), dropping subsequent CoTs; the
GeoChats were injected directly to the `cot_parser` exchange, which exercises the
identical encoder code path.

## What OpenTAKServer emitted (captured, decoded)

Direct message to a recipient whose id (`UID-CHARLIE-9999`) differs from its callsign
(`CHARLIE-CS`), portnum `ATAK_PLUGIN`, `is_compressed=true` (unishox2):

```text
contact.callsign      = "FMLPROBE-ALPHA"     # sender callsign
contact.device_callsign = "FMLPROBE-ALPHA"   # sender UID (uid0)
chat.to               = "UID-CHARLIE-9999"   # the recipient's UID (<__chat id>) --
                                             # NOT the callsign "CHARLIE-CS"
chat.message          = "fml-dm-distinct"
```

The recipient's callsign (`CHARLIE-CS`) appears **nowhere** in the packet -- only its
UID rides the wire. Named room:

```text
contact.callsign      = "FMLPROBE-ALPHA"
chat.to               = "OPS-ROOM"           # the ROOM NAME
chat.message          = "fml-room-distinct"
```

**Live iTAK corroboration (sender side):** a real iTAK client on the bench produced
`ATAK_PLUGIN` PLI `TAKPacket`s with `contact.callsign` = its callsign and
`contact.device_callsign` = its EUD UID (both unishox2), `group{role, team}` --
matching the synthetic run's sender encoding. The real callsign, UID and position
are redacted (see scrub note).

## What this establishes

- **For a direct message, `GeoChat.to` (the `TAKPacket` `chat.to`) holds the
  recipient's UID, not its callsign** -- demonstrated by setting the two different:
  `chat.to` came back the UID (`UID-CHARLIE-9999`), and the callsign (`CHARLIE-CS`)
  was absent from the packet. For a **room**, `chat.to` holds the **room name**. So
  it is **not uniformly a callsign, and never the recipient callsign** on a DM. The
  sender rides in `contact.callsign` (callsign) and `contact.device_callsign`
  (sender UID).
- Consequence for `mule/recipients.py`: the upstream parser that produces
  `recipient_key` from `GeoChat.to` **must branch** (DM: the recipient UID; room:
  the room name). Since the wire carries the **UID**, `decide_delivery`'s roster is
  keyed by that UID (`UID -> delivery device`); the human-readable
  **callsign -> UID** binding is a **separate** step that lives in the client
  contact list. "DM the callsign" therefore needs two bindings, not one: the client
  maps callsign to UID, and the node/gateway maps UID to device. This closes
  `FML-ADR-070`'s "contents" open item; it does **not** close the *resolution* half
  (that `GeoChat.to` resolves to an EUD the node can name), the roster question
  raised in `docs/change-requests/CCR-06-eud-roster-and-contact-seeding.md`.

## What this does not establish

- **RF delivery** -- captured at the encoder's MQTT output, nothing transmitted;
  the real hop is the 2026-09-27 note.
- **The roster / recipient resolution** -- `CCR-06` (source, uniqueness, presence).
- **The 231-byte composition limit under real modulation** (`FML-ADR-070` /
  `TBR-RF-02`).
- It is **not** a hardware/RF result and must not read as one. `TBR-NET-02` stays
  CLOSED (this is confirming/ grounding evidence for `FML-ADR-070`).

## What was scrubbed (SECURITY.md)

Redacted: the live iTAK client's real callsign, EUD UID and position. Retained
(clean, synthetic): the `FMLPROBE-ALPHA` sender, the synthetic recipient
(`UID-CHARLIE-9999` / `CHARLIE-CS`), the `fml-*-distinct` markers, and the
non-identifying encoder mechanics. No real identities or locations are committed.
