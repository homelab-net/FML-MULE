# The bench LoRa gateway reads upstream's compressed TAKPackets, OpenTAKServer unchanged

**Tier: real-hardware bench result; formal `HARDWARE-VERIFIED` held.** A
follow-up to the option 1 trial
(`2026-10-23-opentakserver-meshtastic-option-1-trial.md`, finding 4).

That trial found that the bench gateway and upstream Meshtastic TAK senders
cannot read each other. This record is the bench-side fix. OpenTAKServer and
the TAK Meshtastic Gateway were not modified by this work. The bench image
already carries the repository's build-time `EudHandler` fix
(`services/tak/isolate_handler_state.py`), which touches no Meshtastic code.

| Item | Value |
| --- | --- |
| Date | 2026-10-23 |
| Taken by | Claude Code operating the bench at the Program Owner's direction |
| Instrument | `test/bench/fml-lora-gw.py` with `test/bench/unishox2_decode.py` |
| Upstream | OpenTAKServer 1.7.13, Meshtastic code unmodified, through the option 1 trial's relay; TAK Meshtastic Gateway 1.1.0 source and protobufs |
| Radios | the RAK4631 on pi-mule-1 (OpenTAKServer side), the T1000-E on pi-mule-2 (gateway side), private `MULE-TEST` channel |
| Hosts | pi-mule-1 reported under-voltage throttling during the runs, so timings are provisional |

## What upstream sends

- **OpenTAKServer** compresses every `TAKPacket` string with Unishox2 and sets
  `is_compressed`.
  - It sends a position as a compressed PLI from a node number it assigns to
    each EUD.
  - It sends an All Chat Rooms chat as bare Meshtastic text from that same
    node number, just after the PLI.
- **The TAK Meshtastic Gateway**, read from its source:
  - It honours `is_compressed` on receipt.
  - It sends PLIs plain and All Chat Rooms chat as bare text.
  - It compresses a direct message's strings except `chat.to`. As published,
    that path assigns a `str` to a field its own protobuf types as `bytes`, so
    it raises before sending.

## Before: the gateway on `main`, against OpenTAKServer

Phase 0 ran the unchanged gateway behind a probe that logs what its `decode()`
received and returned.

- **The compressed PLI was dropped.** It reached the gateway intact: 60 bytes,
  with the flag set and the firmware passing it through. meshtastic-python left
  it unparsed, and the gateway logged it as ignored.
- **The room text reached TAK named after a bare node id**, not after its
  sender.
- **The PLI-to-text gap was 4.5 s** through the relay, which spaces its
  downlinks 4 s apart.

## The change

1. **Strings are read in both forms.**
   - `unishox2_decode.py` is a pure-Python Unishox2 decoder.
   - It is ported from the reference implementation (siara-cc/Unishox2,
     Apache-2.0, at a recorded commit), default preset only.
   - It returns the whole string within a byte bound or raises. It never
     returns a partial result.
2. **A minimal wire reader** replaces meshtastic's protobuf parser for
   `ATAK_PLUGIN`, whose string fields reject compressed bytes.
   - It honours the flag per field: Unishox2 output always begins with a 1 bit,
     so a field whose first byte is below 0x80 is plain even in a flagged
     packet.
   - Each string is held to upstream's own limit (`atak.options`): callsign and
     uid 120 bytes, message 200, recipient 120.
   - A callsign must be printable, a carried uid must be well formed, and a
     position must be on the globe.
3. **Bare text is attributed only when unambiguous.**
   - It takes a TAK identity only from a node that sent a `TAKPacket` with
     exactly one identity in the last 15 s.
   - A node seen with two identities stays unattributed, which covers a MULE
     radio relaying for several EUDs, and a forgery.
   - A claim on a local client's uid is still refused.
4. **Loop guard.** A uid the gateway itself put on LoRa that comes back from
   LoRa is refused.
5. **Payload limit.** The 231-byte limit is now checked on the encoded payload
   of every kind, positions included.

**Send format: plain.**

- The TAK Meshtastic Gateway honours the flag, so it reads plain strings.
- OpenTAKServer's Meshtastic path decodes every string, so it cannot.
- The gateway therefore must not share a channel with that path.
- This is a bench-instrument choice. A `services/gateways/` component would
  need its own ADR.

## Verification

- **Reference vectors:** 440 of 440 decode exactly. They were generated with
  the reference C library through `unishox2-py3` 1.0.0, and the generator and
  provenance are in `test/unit/data/`.
- **Differential fuzz** against the reference library, on a bench Pi, with
  20,000 random inputs of up to 48 bytes:
  - **Agree:** 18,660, either identical output or both refused.
  - **This decoder refuses:** 1,340. Each contains a repeat that overlaps its
    own output, which the reference encoder never produces.
  - **Any other difference:** none.
- **Unit tests:**
  - Without meshtastic (as CI runs): 49 passed, 6 skipped.
  - With meshtastic: 55 passed.
  - 11 of the 17 new gateway tests fail on `main`. The other 6 guard behaviour
    `main` already has, such as refusing malformed input.
- **Bench, after the change.** The path was OpenTAKServer, the relay,
  LoRa, the new gateway, pi-mule-2's TAK Server, then a TLS listener client.
  - **2 of 2 PLIs** became that server's contact `FML-OTS-SIM` with uid
    `FML-OTS-SIM-UID`, each under its own proxy session.
  - **2 of 2 room chats** arrived in All Chat Rooms from `FML-OTS-SIM`, with
    `uid0` `FML-OTS-SIM-UID`.
- **Restore:**
  - The radio is back on its saved settings, verified field by field.
  - OpenTAKServer's config is byte-identical to its pre-trial copy, and the
    channel row is removed.
  - No garbage EUD rows were created.

## A bench observation on the way

During Phase 0, a full `tools/lint.sh` run on pi-mule-1 loaded the host, and
RabbitMQ's 5 s health check timed out. Under the unit's `HealthOnFailure=kill`,
podman killed the broker, and OpenTAKServer, bound to it, stopped. Both came
back once the broker was healthy. That is the recovery policy working as
written, but it means heavy work on a node can take its TAK stack down.

## Not established

- **A live TAK Meshtastic Gateway on RF.** It transmits only on the primary
  channel (option 2 trial), so its packets here are built offline with its own
  protobufs.
- **What an iTAK or WinTAK user sees.** The receiver here was a synthetic TLS
  client.
- **LoRa to OpenTAKServer.** That direction is limited by OpenTAKServer itself
  (option 1 trial, finding 6), and the plain send format does not change it.

## Scrubbing

Every identity is synthetic. Node ids, radio keys and positions are omitted.
