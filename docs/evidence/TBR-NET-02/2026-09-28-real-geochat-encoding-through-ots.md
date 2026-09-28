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

Synthetic EUDs (`FMLPROBE-ALPHA` sender, `FMLPROBE-BRAVO` recipient) were used, and a
real GeoChat DM and a named-room GeoChat were driven through the encoder
(`cot_parser.py:451-517`). A bench note: the `eud_handler` TCP CoT listener (:8088)
raised `AttributeError: 'NoneType' object has no attribute 'basic_publish'` after its
first connection (`rabbit_channel` cleared on connection close), dropping subsequent
CoTs; the GeoChats were therefore injected directly to the `cot_parser` exchange,
which exercises the identical encoder code path.

## What OpenTAKServer emitted (captured, decoded)

Direct message `FMLPROBE-ALPHA -> FMLPROBE-BRAVO`, portnum `ATAK_PLUGIN`,
`is_compressed=true` (unishox2):

```text
contact.callsign      = "FMLPROBE-ALPHA"     # sender callsign
contact.device_callsign = "FMLPROBE-ALPHA"   # sender UID (uid0)
chat.to               = "FMLPROBE-BRAVO"     # RECIPIENT id (the <__chat id>)
chat.message          = "fml-dm-probe"
```

Named room `FMLPROBE-ALPHA -> FMLPROBE-ROOM`:

```text
contact.callsign      = "FMLPROBE-ALPHA"
chat.to               = "FMLPROBE-ROOM"      # the ROOM NAME
chat.message          = "fml-room-probe"
```

**Live iTAK corroboration (sender side):** a real iTAK client on the bench produced
`ATAK_PLUGIN` PLI `TAKPacket`s with `contact.callsign` = its callsign and
`contact.device_callsign` = its EUD UID (both unishox2), `group{role, team}` --
matching the synthetic run's sender encoding. The real callsign, UID and position
are redacted (see scrub note).

## What this establishes

- **`GeoChat.to` (the `TAKPacket` `chat.to`) holds the recipient's identifier,**
  unishox2-compressed. It is **not uniformly a callsign**: for a **direct message**
  it is the recipient's **id** (the `<__chat id>` -- an EUD UID for a real ATAK
  client); for a **room** it is the **room name**. The sender rides in
  `contact.callsign` (callsign) and `contact.device_callsign` (sender UID).
- Consequence for `mule/recipients.py`: the upstream parser that produces
  `recipient_key` from `GeoChat.to` **must branch** (DM-id vs room-name), and the
  human-readable **callsign<->id binding lives in the client contact list** -- which
  is exactly what a roster would seed. This closes `FML-ADR-070`'s "contents"
  open item; it does **not** close the *resolution* half (that `GeoChat.to` resolves
  to an EUD the node can name), which is the roster question raised in
  `docs/change-requests/CCR-06-eud-roster-and-contact-seeding.md`.

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
(clean, synthetic): the `FMLPROBE-*` EUD names and the `fml-*-probe` markers, and the
non-identifying encoder mechanics. No real identities or locations are committed.
