# FML-ADR-048 option 1 on the bench: OpenTAKServer's Meshtastic path through a real radio

**Tier: real-hardware bench result; formal `HARDWARE-VERIFIED` held.** A
time-boxed trial of the first upstream gateway option, run because
FML-ADR-048 orders gateways upstream-first. Option 2, the TAK Meshtastic
Gateway, was tried on 2026-10-18
(`2026-10-18-tak-meshtastic-gateway-option-2-trial.md`).

| Item | Value |
| --- | --- |
| Dates | Setup and round 1 on 2026-10-19; rounds 2 to 4 on 2026-10-23, about 08:20 to 08:55 local |
| Taken by | Claude Code operating the bench at the Program Owner's direction |
| Server | OpenTAKServer 1.7.13, the bench's rootless stack on pi-mule-1, with its own RabbitMQ |
| OTS side radio | the RAK4631 on pi-mule-1, with its MQTT client proxy on |
| LoRa side radio | the T1000-E on pi-mule-2 |
| Channel | the private `MULE-TEST` channel only; the primary and the live server's channels untouched |
| Hosts | power not checked during these runs, so every timing here is provisional |

## Method

- **OTS.** `OTS_ENABLE_MESHTASTIC: true`, and one channel row for `MULE-TEST`
  with uplink and downlink on and **no key**. The radio uplinked in plaintext
  (`mqtt.encryption_enabled` off), so no channel key ever reached the server.
- **The radio on pi-mule-1.** MQTT on with `proxy_to_client_enabled`, a
  non-resolvable broker address so it could never reach a public server, and
  uplink and downlink on `MULE-TEST` only. Its prior settings were saved first
  and restored afterwards, verified field by field.
- **A relay, because OTS does not talk to a radio.** OTS consumes Meshtastic
  `ServiceEnvelope`s from RabbitMQ (`amq.topic`, any key not ending `outgoing`,
  channel name as the fourth word) and publishes its own to
  `opentakserver.2.e.<channel>.outgoing`. A trial relay in a container on OTS's
  private network, holding the radio's serial port, moved the radio's
  client-proxy messages to and from those keys. It relayed `MULE-TEST` only.
  It rewrote each downlinked packet to hop limit 1, so the far radio does not
  rebroadcast it, and spaced downlinks 4 s apart.
- **Endpoints.** On the OTS side, a synthetic TAK client on OTS's plain-TCP CoT
  port inside the private network. This stack publishes no ports, and the
  host's 8089 belongs to TAK Server. On the LoRa side, a synthetic endpoint on
  the T1000-E that sends `TAKPacket`s compressed (upstream's form) or plain
  (the bench gateway's form) and decodes both.
- **Round 4 only:** a read-only tap on OTS's `firehose` exchange, to see what
  CoT OTS made of LoRa input. See finding 7 for why this, rather than a client.

The relay and endpoints are trial instruments and are not committed.

## Findings

1. **OTS to LoRa works.** Across rounds 2 and 3, the far radio received all
   28 packets OTS emitted (9 and 19). Every chat arrived, and so did every
   position.
2. **A room chat loses its sender's TAK identity on LoRa.** OTS sends an
   All Chat Rooms GeoChat as a plain `TEXT_MESSAGE_APP` holding only the
   message text. It sends no `TAKPacket` GeoChat, as the comment in its
   `cot_parser` says it intends. The only trace of the sender is the packet's
   `from`, a random Meshtastic node number OTS assigns per EUD. A far TAK user
   behind the bench gateway would see the message, but not from its sender.
3. **One chat costs three transmissions.** Each GeoChat also carried its point
   as a position update. So it left as a `POSITION_APP`, a compressed
   `TAKPacket` PLI (sender callsign, with the uid in `device_callsign`) and the
   text, 28, 60 and 21 payload bytes. SAs left as the first two only. The
   client sent its SA every 60 s. Chat text reached the far endpoint 9.1 to
   10.0 s after the client sent it (5 chats). Up to 8.2 s of that is the
   relay's own spacing, because the text is the third packet queued.
4. **OTS's strings are compressed, and the bench gateway's are not.** OTS
   writes every `TAKPacket` string compressed with unishox2
   (`is_compressed=true`), and it decompresses every one it receives
   unconditionally.
   - **Bench gateway format into OTS:** a plain chat raised
     `UnicodeDecodeError` and was dropped. A plain PLI was "decompressed" into
     noise, and OTS registered a new EUD with a garbage uid and callsign and
     published its SA. That row was deleted after the trial.
   - **OTS output into the bench gateway:** not run. By reading its code,
     `fml-lora-gw.py` parses with upstream's protobuf, whose string fields
     reject the compressed bytes, so it would drop them.
5. **A LoRa sender must opt in before the OTS radio will uplink it.** In
   round 1 the relay received nothing from the far radio's chat. After that
   radio's `lora.config_ok_to_mqtt` was set (and restored afterwards), uplink
   was 12 of 12 across rounds 2 to 4. The firmware withholds another node's
   packet from MQTT unless its originator allowed it. Every node whose traffic
   should reach OTS needs that flag.
6. **LoRa to OTS: positions convert, chats never do.**
   - A compressed PLI became an SA on OTS's firehose 1.6 s after transmission.
     The SA carried the sender's own uid from `device_callsign`, its callsign
     and `takv`, with contact endpoint `MQTT`.
   - **0 of 7 compressed chats became CoT.** `atak_plugin()` passes the
     sender's TAK uid to `cot()`, which looks devices up by Meshtastic id. It
     registers the sender's uid from `device_callsign` just before, so every
     chat from a sender carrying a uid raises `KeyError`. One-line upstream
     fix.
7. **Two defects in this stack hid the path, and neither is Meshtastic's.**
   - **The socket.io queue has no broker credentials.** OTS builds its
     socket.io message-queue URL as `amqp://<host>` (`app.py`, and again in
     `cot_parser.py`). So kombu logs in as `guest`, which this broker does not
     have, and is refused.
   - Every CoT path that emits to socket.io failed with it. That covers each
     SA `cot_parser` handled and every Meshtastic packet that registered an
     EUD, so round 2 converted nothing.
   - Rounds 3 and 4 ran with a bench-only patch: patched copies of the two
     files, bind-mounted by a quadlet drop-in, taking the credentials from the
     environment. The patch was removed afterwards and the stock files
     confirmed.
   - The first refusal in `cot_parser`'s log is on 2026-10-19, the first CoT
     it handled after the trial's restart. Why the 2026-09-28 and 2026-10-03
     OTS runs did not hit it is not established.
   - **Plain-TCP client delivery is broken on this stack.** Two synthetic
     clients on the TCP port saw none of each other's chats (0 of 2), with
     Meshtastic not involved. That fits the `eud_handler` defect recorded on
     2026-09-28 (`rabbit_channel` is `None` after a connection closes); here a
     health check closes a connection every 6 s. That is why round 4 measured
     at the firehose rather than at a client.
   - `cot_parser` also raised `'BlockingChannel' object has no attribute
     'is_closing'` when sending a client's disconnect.

## What this means for the gateway justification

Option 1 carries positions both ways and room text outward, and it keeps each
user's uid on a PLI, the convention the bench gateway adopted on 2026-10-18.
But as published:

- it does not turn LoRa chat into TAK chat (finding 6);
- it strips the sender from room chat going out (finding 2);
- it needs a relay or an MQTT broker beside it, and an opt-in on every LoRa
  node (finding 5).

None of that is a protocol limit, so the record is "**not usable as published,
fixable**", the same as option 2.

**One result applies to the bench gateway whichever option is chosen.**
Upstream's `TAKPacket` (OTS, and the ATAK plugin it follows) uses unishox2, and
the bench gateway does not (finding 4). FML-ADR-070 chose upstream's fields. So
the gateway should at least **read** compressed packets, and whether it should
**send** them is a choice to record before D-1's mixed-node runs.

## Not established

- Delivery to a real TAK client on OTS, and so the iTAK reply rule on OTS,
  including whether a contact with endpoint `MQTT` counts. That needs an OTS
  TLS listener the phone can reach.
- Direct messages in either direction.
- Encrypted uplink, with OTS holding the channel key.
- Received-signal figures, withheld because antenna, separation and ambient
  conditions were not recorded (`docs/evidence/README.md`).

## Bench state afterwards

Both radios are back on their saved settings. OTS's `config.yml` is
byte-identical to its pre-trial copy, the channel row and the trial's drop-ins
are gone, and the containers run the stock image files. Four synthetic EUD
rows the trial created on this bench server remain (`FML-LORA-OTS-UID`,
`FML-OTS-SIM-UID`, `FML-TCP-A`, `FML-TCP-B`).

## Scrubbing

The radios' node ids and the Meshtastic ids OTS assigned are omitted. All uids
and callsigns here are synthetic. No channel key reached OTS, and no position
was logged.
