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
decided here."* This grounds what the encoder puts there (and rules out the
callsign), advancing that item; the live-client half is called out below.

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

## What this establishes (and the one thing it does not)

- **The encoder copies the client-supplied `<__chat id>` verbatim into `chat.to`,
  and it is not the recipient callsign.** With the DM's `<__chat id>` set to
  `UID-CHARLIE-9999` and the recipient callsign to `CHARLIE-CS`, `chat.to` came back
  `UID-CHARLIE-9999` and `CHARLIE-CS` was **absent** from the packet. For a **room**,
  `chat.to` is the **room name**. So the field is not uniformly a callsign, and in
  this run the encoder placed the supplied id -- not the recipient callsign -- in the
  DM. Whether a *live* client ever places a callsign in `<__chat id>` is not decided
  here (the id was injected); that is the owed live-client capture below.
- **Not established here:** that a *live ATAK/iTAK client* places the recipient's
  **UID** in `<__chat id>` when an operator picks a contact. This run injected the
  `<__chat id>` synthetically, so it proves the **encoder faithfully copies whatever
  the client sends** -- not the client's selection logic. By ATAK convention the DM
  `<__chat id>` is the destination UID, but confirming that needs a **live-client DM
  capture** (owed; a live iTAK DM to a known contact). The roster design must not
  assume the stronger conclusion until then.
- Consequence for `mule/recipients.py`: the upstream parser that produces
  `recipient_key` from `GeoChat.to` **must branch** -- a DM key is the id the client
  put in `<__chat id>` (a UID by convention), a room key is the room name. For a DM,
  `decide_delivery`'s roster is keyed by that id (`id -> delivery device`), and the
  human-readable **callsign -> id** binding is a **separate** client-side step. A
  **room** names a **group**, not one device, so room fan-out is separate group
  routing, not `decide_delivery`. This **advances** `FML-ADR-070`'s "contents" item
  (the encoder/field behavior); the client-side field population and the *resolution*
  half (where the roster comes from) remain open -- the roster question is
  `docs/change-requests/CCR-06-eud-roster-and-contact-seeding.md`.

## What this does not establish

- **What a live client places in `<__chat id>`** -- the `<__chat id>` was injected
  here, so this shows the encoder's copy, not the client's selection. A live iTAK DM
  to a known contact (owed) would confirm the ATAK convention that it is the UID.
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
