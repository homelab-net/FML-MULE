# A LoRa gateway that is a TAK client: direct delivery, IP<->LoRa, and a DM across two MULEs

**Tier: real-hardware bench result; formal `HARDWARE-VERIFIED` held**, for the
same reason `2026-09-27-one-lora-hop-to-a-partner-node.md` gives: the
program-wide flip has not been made. Nothing here is `SIMULATED` -- every
transmission crossed real sub-GHz RF -- and nothing here is a product component.
The gateway is a bench instrument, `test/bench/fml-lora-gw.py`. `FML-ADR-048`
keeps `services/gateways/` README-only until `TBR-TAK-01` and `TBR-RF-02` close
(`FML-ADR-048` lines 94-95).

**What this adds to the 2026-09-27 and 2026-10-02 records.** Delivery across one
real LoRa hop was already shown there (`2026-09-27-one-lora-hop-to-a-partner-node.md`;
the October three-node record's addressed round trip). This run adds four things:

- a gateway that joins a TAK server as an ordinary TLS client, so it follows
  whichever server is authoritative;
- that gateway carried across authority swaps;
- the intended two-MULE path, EUD -> MULE -> LoRa -> MULE -> EUD, delivering a
  direct message to a live iTAK client;
- the defects and protocol facts that path exposed.

## Provenance

| Item | Value |
| --- | --- |
| Date | 2026-10-18, about 13:45 to 18:30 local (US Mountain) |
| Taken by | Cameron Zobrist (the Program Owner) at the bench and on the phone, with the bench operated remotely by Claude Code at his direction |
| Article | flat-sat bench hardware, not selected production hardware |
| Radio A | the RAK4631 of the 2026-09-27 record, USB serial on pi-mule-1 |
| Radio B | a Seeed T1000-E, USB serial on pi-mule-2, Meshtastic firmware 2.7.26 |
| Client library | Meshtastic Python 2.7.11, PyTAK 7.6.1 |
| Radio configuration | region US (902-928 MHz, Part 15.247), LongFast preset, private secondary channel `MULE-TEST` on the same RF channel as the public mesh (secondary channels are cryptographic, not frequency, separation), `lora.hop_limit` 0 except where stated |
| Channel key | bench-only, not recorded |
| Node ids | scrubbed |
| Antenna geometry | not recorded: both radios sat on one bench in one room |
| Hosts | both Pi 4B nodes read `vcgencmd get_throttled` = `0x50005` (under-voltage, throttled) during the session |

**Signal figures are withheld.** The antenna model, orientation, separation and
ambient conditions were not recorded, so the radio-reported RSSI and SNR are
withheld under the measurement-record contract in [`docs/evidence/README.md`](../README.md)
(check 25). **Every timing below is provisional** because of the throttle state.

## Results

### R1. Direct delivery between the two radios

The FML-ADR-070 encoding was used: `TAKPacket` on the ATAK plugin port, sender in
`Contact.callsign`, recipient in `GeoChat.to`.

| Run | Delivered | Acknowledged | One-way latency, median (min-max) | Ack round trip, median |
| --- | --- | --- | --- | --- |
| A -> B, direct to B's node, PKI-encrypted | 10/10 | 10/10 | 1.97 s (1.66-2.21) | 2.86 s |
| B -> A, direct to A's node, PKI-encrypted | 10/10 | 10/10 | 1.66 s (1.40-1.80) | 2.55 s |

Both clocks were NTP-synchronised. Sender and recipient fields arrived
byte-identical, and the received `hopStart` was 0.

**A disclosed deviation.** Before these runs, a 10-packet broadcast went out with
`hopStart` 7. The script passed `hopLimit=0` through the Python API, and the
firmware treats 0 from a client as "unset" and substitutes its configured
default. So zero-hop has to be set on the radio (`lora.hop_limit`), not per
packet. Those 10 packets were encrypted on the private channel. They may still
have been repeated by third-party routers on the shared RF channel.

### R2. IP <-> LoRa through a gateway that is a TAK client (first version)

The gateway ran on pi-mule-1 and connected to the bench mule's live OpenTAKServer
through a single `tak.field` front on that host. That front is retired; see the
`TBR-HA-01` record of the same date. A synthetic IP EUD and a synthetic LoRa EUD
on pi-mule-2 used one clock.

| Direction | Delivered | Latency, median (min-max) |
| --- | --- | --- |
| IP -> LoRa | 12/12 | 1.80 s (1.19-3.14) |
| LoRa -> IP | 11/11 | 1.44 s (1.15-1.69) |

**This first version relayed the live server's "All Chat Rooms",** so it put
traffic from a server with pilot users on the air and injected test traffic into
that room. That is a defect, and the reason the rewrite scopes rooms (R4).

### R3. Across authority swaps

| Run | IP -> LoRa | LoRa -> IP | Cause of the losses |
| --- | --- | --- | --- |
| First run, swaps live -> pi-mule-1 -> live | 22/23 | 21/22 | One per direction, about 13 s after a swap. **OpenTAKServer delivers nothing to a connection until that client has sent its own SA**, and the gateway and test EUD waited up to 30 s to send one. Fixed by announcing on every reconnect. |
| Second run, three swaps, live -> pi-mule-1 -> pi-mule-2 -> live | 31/31 | 29/30 | A LoRa message arrived during the gateway's 2 s reconnect and was dropped. Fixed with a bounded store-and-forward queue. |

Across the second run's swaps the gateway and the IP EUD reconnected in about
2.1 s, which is their retry delay. A targeted re-test of the reconnect window
delivered 16/17. The one loss was handed to the server 73 ms before the swap's
hard cut, so it was **in flight at the cut**. GeoChat has no end-to-end
acknowledgement. That loss is open and is `TBR-HA-01`'s to resolve.

### R4. The rewritten gateway

Changes from the first version:

- PyTAK transport (FML-ADR-033).
- A pure translator using `mule/recipients.py`.
- Configured rooms only.
- Fail-closed direct messages.
- The 231-byte budget, with a measured 12-byte framing bound.

A smoke test used a bench-only room and dedicated bench server accounts:

| Check | Result |
| --- | --- |
| IP -> LoRa | 6/7; the seventh was sent after the listener had stopped |
| LoRa -> IP | 6/6 |
| A LoRa direct message to an unknown callsign | **refused** ("unresolved and no default; not delivered") and never seen by the IP EUD |

The first rewrite received nothing from the radio. pypubsub holds listeners by
weak reference, so the receive callback was collected. Fixed, and a unit test
proves the failure without the fix.

### R5. The intended two-MULE path, with a live iTAK client

- **MULE B** (pi-mule-2): a synthetic EUD behind it, connected to pi-mule-2's own
  TAK Server (official 5.8), and a gateway on the T1000-E.
- **MULE A** (pi-mule-1): a gateway on the RAK4631, connected to the bench mule's
  live server, where the owner's iTAK client was connected over IP.
- No IP path joined the two servers, so LoRa was the only path between them.

| What | Result |
| --- | --- |
| Positions both ways | Crossed. The owner's iTAK showed the MULE B EUD as a new contact. |
| Room chat in a bench room | Not displayed by iTAK, although the contact appeared. **Hypothesis, not shown:** iTAK does not display chat for a room it has not joined. |
| DM, MULE B EUD -> owner's iTAK | **Delivered**, addressed end to end. Server-routed on MULE B's server, carried over LoRa as a PKI direct packet to MULE A's node with `GeoChat.to` = the recipient's callsign, resolved by MULE A's gateway, routed by the live server. Received and displayed by iTAK, repeatedly, under two different far-end identities. |
| iTAK's reply -> MULE B EUD | **Not delivered. The reply never reached the server.** A metadata-only tap on the server's firehose saw 8 position reports and 0 chats from the phone's connection in 75 s while replies were being sent. Resolved on TAK Server the same evening; see `2026-10-18-itak-reply-rule-and-two-way-dm-across-lora.md`. |

**Two protocol facts this exposed:**

1. **A TAK server routes a direct message to the one connection bound to the
   recipient.** An EUD that exists on the server only as events relayed over the
   gateway's single connection can't receive a routed DM. The gateway now opens
   one session per remote EUD, capped at 8 per remote MULE. That is the only
   change under which server-routed DMs reached it, shown on TAK Server 5.8.
2. **TAK Server 5.8 listed no client endpoint** for any of the bench clients until
   their SA carried both `<takv>` and `<contact endpoint="*:-1:stcp">`. Then the
   count went from 0 to 3. Both were added together, so **neither is shown
   necessary on its own**, and the effect on OpenTAKServer is not shown.

**Not shown, and stated as hypotheses:**

- iTAK replies were not fixed by changing the far-end uid prefix from `MESH-` to
  `FMLR-`.
- iTAK appeared to keep a callsign bound to the uid it first saw for it, which
  **confounds** that prefix test.
- The investigation starts from the 2026-10-02 positive control, where a phone
  reply did return.

### R6. A phone paired to a radio (not the intended architecture)

The owner's phone, running the stock Meshtastic app paired to the T1000-E,
displayed the gateway's IP -> LoRa messages on `MULE-TEST`. This is RF delivery
only. **EUDs are not meant to pair with a LoRa radio:** each EUD reaches its MULE
over IP, and LoRa joins MULEs.

## What this does not establish

- A product gateway: it is a bench instrument.
- Partition behaviour. In R5 two servers were up on purpose. When and how a MULE
  serves its EUDs once cut off from the authority is undecided (`TBR-HA-01`).
- Deduplication across two gateways attached to one server.
- Airtime, duty cycle, range or coexistence (`TBR-RF-02`).
- Any iTAK reply path.

## Procedures

- `test/bench/fml-lora-gw.py`, with its rules pinned by `test/unit/test_fml_lora_gw.py`.
  R1-R3 used earlier scratch versions; the committed file is the R4 rewrite plus
  the R5 changes and the 2026-10-18 clean-ups.
- R1 used a one-off sender and listener with the same encoding as
  `test/bench/lora-geochat-eud.py`, plus a direct, acknowledged mode.

## Scrubbing

Removed: node ids, the private channel key, the owner's callsign and device uid,
and every tailnet address. All raw logs stay off the repository.
