# What iTAK needs before it replies, and a two-way DM across LoRa between two MULEs

**Tier: real-hardware bench result; formal `HARDWARE-VERIFIED` held** (see
`2026-09-27-one-lora-hop-to-a-partner-node.md` for why). It follows
`2026-10-18-lora-gateway-as-a-tak-client.md` from the same day, which left an
open question: a live iTAK client received direct messages that had crossed LoRa
but never sent its replies to the server.

| Item | Value |
| --- | --- |
| Date | 2026-10-18, about 20:00 to 20:40 local |
| Taken by | Cameron Zobrist (the Program Owner) on the phone and at the bench, with Claude Code operating the bench at his direction |
| Clients | the owner's iTAK on iOS (version not recorded) and WinTAK 5.8 on the bench desktop, both real clients, plus synthetic TLS clients |
| Servers | official TAK Server 5.8 on each Pi, joined to each other **only** by LoRa; the bench mule's live server was not used |
| Radios | as in the earlier same-day record: private `MULE-TEST`, radio `hop_limit` 0 |
| Hosts | both Pi nodes under-voltage and throttled (`0x50005`), so timings are provisional |

## R1. A positive control: three senders that differ only in their SA

Three synthetic clients on pi-mule-1's TAK Server each sent the iTAK client one
direct message. They used the same DM builder and differed only in the
situational-awareness event each had announced:

| Sender | SA | iTAK made it a contact | iTAK's reply |
| --- | --- | --- | --- |
| V1 | the gateway's proxy shape: `contact` with `endpoint="*:-1:stcp"`, `takv`, position 0,0 | yes | **delivered** |
| V2 | an ATAK-style SA: UUID uid, `takv`, `contact endpoint`, `precisionlocation`, `status`, `track`, a non-zero position | yes | **delivered** |
| V3 | minimal: `contact callsign` and `__group` only | **no** | **not sent**: it vanished from the phone's screen and never reached the server |

**Finding.** iTAK sends a reply only to a contact whose SA carries `takv` and a
`contact endpoint`. The gateway's proxy SA meets that, and full ATAK fidelity is
not needed.

**This retires the earlier hypotheses.** The `MESH-` uid prefix was not the
cause, nor the room. The live-server attempts earlier in the day mixed SAs from
before this fix with contacts iTAK had cached from older SAs, so they could not
separate the variables. Whether OpenTAKServer behaves differently from TAK
Server here has **not** been tested.

## R2. Two-way DM, iTAK <-> an EUD behind the other MULE, across LoRa

- **MULE A** (pi-mule-1): the iTAK client on its TAK Server, and a gateway on the
  RAK4631.
- **MULE B** (pi-mule-2): a synthetic EUD on its TAK Server, and a gateway on the
  T1000-E.
- Each gateway connected to its own server; gateway A verified the server
  certificate by hostname.

| Direction | Delivered | Path latency |
| --- | --- | --- |
| EUD behind B -> iTAK | 4/4 | about 2.3 s, B's gateway hand-off to A's gateway delivery |
| iTAK reply -> EUD behind B | 3/3 | about 1.9 s, A's gateway hand-off to the EUD |

Every message was **routed by each server** to the recipient's connection.
Remote EUDs exist on a server as proxy sessions the gateway opens, one per remote
EUD. Each crossed RF as a PKI direct packet to the far node, with `GeoChat.to`
carrying the recipient's callsign.

## R3. WinTAK as the EUD behind MULE B

WinTAK's truststore held only the bench CA, while the Pi TAK Servers now present
leaves from the bench mule's CA. So it had not connected since the servers'
certificates changed. Adding that root to its truststore connected it.

| Direction | Result |
| --- | --- |
| WinTAK -> iTAK, across LoRa | 2/2 delivered, about 1.7 s |
| A synthetic DM -> WinTAK, across LoRa | delivered (WinTAK showed it unread) |
| **iTAK -> WinTAK, across LoRa** | **0/3** with the gateway minting a uid; **resolved by R4** |

**On the open case.** pi-mule-1's server listed the WinTAK proxy session as a
connected client bound to that callsign, but the gateway received none of
iTAK's three sends. A fresh conversation did not change that, so this is not a
stale conversation. The same iTAK -> WinTAK reply **was** delivered over IP when
WinTAK was a direct client (see the `TBR-RF-01` record of the same date). So the
fault is specific to this proxied contact. R4 found the cause.

## R4. One identity across bearers

**The cause.** WinTAK had reached the iTAK client directly earlier in the
session, under its own uid. The gateway then gave the same callsign a minted
uid on the far side. iTAK addressed its replies to the uid it already held for
that callsign, and no session held that uid, so nothing was delivered.

**The change.** The gateway now carries the sender's own uid in
`Contact.device_callsign`, the field OpenTAKServer's encoder fills
(`2026-09-28-real-geochat-encoding-through-ots.md`). The far gateway reuses it.
It mints a uid only when none was carried, when the carried one is malformed, or
when it already belongs to a client of the far server. That last case is
refused, because otherwise anyone holding the channel key could impersonate that
client.

**The result.**

- WinTAK -> iTAK across LoRa was delivered under WinTAK's own uid.
- **iTAK's reply was delivered to WinTAK**: about 2.0 s from gateway hand-off to
  gateway delivery.
- On both clients the IP exchange and the LoRa exchange with the other became
  **one conversation**: the same contact, whichever bearer carried it.
- The carried uid costs its length plus 2 bytes of the 231-byte payload, so a
  long uid shortens the longest chat that fits. A message that no longer fits is
  refused, never truncated.

## What this does not establish

- That OpenTAKServer needs the same SA fields as TAK Server.
- Anything about range, airtime or duty cycle (`TBR-RF-02`).
- Partition behaviour: the two servers were joined only by LoRa on purpose.

## Procedures

- The gateway is `test/bench/fml-lora-gw.py`.
- R1's three senders and the synthetic EUDs were scratch clients built on that
  file's CoT builders.
- Remote-EUD proxy sessions and the `takv`/`endpoint` SA are in the committed
  gateway.

## Scrubbing

Removed: the owner's callsign, device uid and position, node ids and the channel
key. Client callsigns appear only as bench names. Raw logs and screenshots stay
off the repository.
