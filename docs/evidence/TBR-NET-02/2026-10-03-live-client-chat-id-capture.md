# What a live client puts in `<__chat id>`, captured from a real iTAK client

**Tier:** real-client capture of upstream protocol behaviour. **Not**
`HARDWARE-VERIFIED` and not a claim about RF: this is what one client's software
composes, read from the server's stored CoT.
**Status:** closes the owed item named in `CCR-06` and in `mule/recipients.py`.
**Date:** 2026-10-03. **Trade:** `TBR-NET-02` (`CLOSED`) -- post-closure
verification of `FML-ADR-070`, closing nothing.

## 0. Provenance

| | |
| --- | --- |
| Node | the x86 bench article, hostname `FML-MULE`, descriptor `nodes/lab-bench/` |
| Image build | none -- hand-provisioned Debian GNU/Linux 13 (trixie), not the MULE image |
| Kernel | `6.12.105+deb13-amd64` |
| Server | OpenTAKServer in `fml-ots`, with `fml-cot_parser` and `fml-eud_handler` |
| Client | the Program Owner's iOS **iTAK**, connected over the Tailscale overlay to the mutual-TLS CoT port `8089` |
| Instrument | the server's own `cot` table, queried with `psql`; no packet capture involved |
| Taken by | Cameron Zobrist, with Claude Code, on the lab bench |
| Messages composed by that client | 5 carrying `<__chat>`, dated 2026-09-28 and 2026-10-02 |

**The Owner's EUD identity is deliberately absent from this artifact.**
`AGENTS.md` forbids committing a callsign or member identity, so the client's
UID and callsign appear only as `<OWNER-UID>` and `<OWNER-CALLSIGN>`. The
recipients named below are the program's own synthetic identities and are safe
to publish.

## 1. The question, and why it was still open

`FML-ADR-070` carries the recipient in upstream's own `GeoChat.to`. The
2026-09-28 record established what OpenTAKServer's encoder does with it: it
copies the client-supplied `<__chat id>` **verbatim** and substitutes no
callsign of its own. That left one half owed, and `CCR-06` (`ACCEPTED`
2026-09-29) lists it under "Still owed, unchanged by this decision":

> the **live-client `<__chat id>` capture** (a UID by convention, not yet
> confirmed for a live client), which the roster's `callsign -> key` binding
> assumes

`mule/recipients.py` says the same thing about its own roster key: the shape
"stays conditional until then". So the module that implements the decision was
keyed on an assumption about real client behaviour that nobody had checked.

## 2. What the live client actually composes

Two messages, composed by the Owner's iTAK client and stored by the server. The
sender fields identify the client; the recipients are synthetic:

```xml
<__chat chatroom="FML-ECHO"  groupOwner="false" id="FML-UID-RF-5F44AFBD"
        parent="RootContactGroup" senderCallsign="<OWNER-CALLSIGN>">
<remarks source="BAO.F.ATAK.<OWNER-UID>" time="2026-10-02T13:49:01Z"
         to="FML-UID-RF-5F44AFBD">

<__chat chatroom="FML-DELTA" groupOwner="false" id="FML-UID-RF-0DFB86A4"
        parent="RootContactGroup" senderCallsign="<OWNER-CALLSIGN>">
<remarks source="BAO.F.ATAK.<OWNER-UID>" time="2026-10-02T13:39:08Z"
         to="FML-UID-RF-0DFB86A4">
```

**`<__chat id>` is the recipient's UID.** Confirmed.

The discriminator is sound because each recipient's UID and callsign are
unrelated strings, which is the control the 2026-09-28 run could not apply --
its first attempt used `id == callsign` and so produced the same string either
way. From the server's `euds` table:

| Recipient UID | Recipient callsign | Share a substring? |
| --- | --- | --- |
| `FML-UID-RF-5F44AFBD` | `FML-ECHO` | no |
| `FML-UID-RF-0DFB86A4` | `FML-DELTA` | no |
| `FML-UID-ALPHA` | `FML-ALPHA` | partially |

The two `FML-UID-RF-*` cases carry no shared text at all, so the client cannot
have arrived at that `id` from the callsign.

## 3. The finding that was not asked for: the callsign rides too

`<__chat chatroom>` carries the recipient's **callsign** -- `FML-ECHO` beside
id `FML-UID-RF-5F44AFBD`, `FML-DELTA` beside `FML-UID-RF-0DFB86A4`. And
`senderCallsign` carries the sender's.

So for a direct message the client supplies **both halves of the
`callsign <-> UID` binding in the same element**. A node receiving such a
message does not need an external roster to learn that binding for that pair;
it can read it off the wire.

This does **not** remove the need for the roster `FML-ADR-087` selects, and must
not be read as doing so. The roster answers a different question: addressing a
person *by callsign before any message from them exists*. Learning a binding
from traffic is observation after the fact, it covers only pairs that have
already spoken, and it is unsigned -- whereas `FML-ADR-087` specifies **signed**
enrollment state precisely so the binding is authorised rather than inferred.
What this finding changes is narrower: the binding is observable, so a parser has
both values available, and the roster's job is authorisation and
addressing-before-contact rather than discovery.

## 4. Group messages branch, as the specification said

A third `<__chat id>` value from the same client is `All Chat Rooms` -- a room
name, not an identifier. This confirms the 2026-09-28 conclusion that
`GeoChat.to` "is not uniformly a callsign and the parser must branch". The
branch is UID-for-direct, room-name-for-group.

## 5. How this was obtained, and why that matters

**No new test produced this.** The data was already in the server's `cot` table
from 2026-10-02. A fake-EUD probe was written and run first
(`test/bench/eud-chat-id-capture.py`), and it registered successfully -- the
`euds` table carries `UID-FMLPROBE-DELTA-0001` / `FMLPROBE-DELTA-CS` -- but
received no CoT stream in 55 seconds and answered nothing.

`AGENTS.md` makes this a rule rather than an anecdote: "A number you cannot
explain has probably been explained here already ... The search costs seconds."
The same applies to a capture. The owed item had been satisfiable from stored
state for a day before anyone looked.

## 6. What this does not establish

- **One client, one platform.** iOS iTAK. ATAK on Android is a different
  implementation and is not covered; the convention is confirmed, not proven
  universal.
- **Nothing about RF.** No LoRa packet was sent. The Meshtastic bearer's
  handling of these fields is the separate `geochat-survival.sh` result, which
  is `SIMULATED` over a UDP bridge by its own header.
- **Nothing about the roster's delivery.** `services/mission-trust/` remains
  blocked, and `FML-ADR-087`'s signed enrollment state is unbuilt.
- **Nothing about the probe's stream.** Why a registered client on the plain
  `8088` port received no CoT is unexplained and recorded as open below.
- **No signal figure, no throughput, no timing.**

## 7. Open, from this work

The fake-EUD probe registered in `euds` and received nothing. The Owner's client
is connected to `8089` (mutual TLS) over the overlay, not to `8088`, and three
`eud_handler` processes hold its sessions. Whether `8088` requires group
membership, authentication, or a subscription the probe did not make is
unresolved. Separately, `eud_handler` logged
`AttributeError: 'NoneType' object has no attribute 'basic_publish'` in
`close_connection()` on 2026-10-01 and again on 2026-10-03; its RabbitMQ channel
was `None`. Neither is diagnosed here.
