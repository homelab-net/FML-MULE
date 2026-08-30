# Does a Meshtastic payload carry a member tag, and how many bytes are left

**Trade:** `TBR-NET-02`.
**Date:** 2026-08-30.
**Taken by:** Cameron Zobrist, on the lab development machine.
**Status of this artifact:** `SIMULATED`. Two `meshtasticd` instances in
simulation on one Docker bridge. **No radio, no RF, no airtime.**

## What this answers

`docs/evidence/TBR-NET-02/2026-08-29-addressing-specification.md` lists three
things that would falsify it. The third:

> **If the gateway cannot carry an application tag** in the payload alongside
> the message, the encoding above is unimplementable and option D, one radio
> per EUD, becomes the serious alternative.

That had never been tested. This tests the transport half of it, and finds a
second thing that was not being looked for.

## Configuration

| Item | Value |
| --- | --- |
| Daemon | `meshtastic/meshtasticd@sha256:23e92b1331a3a471eaef0c63cbca4365ca40b3111a9781cfdbe5a5114e5773d4` |
| Client | `meshtastic` 2.7.11, from `tools/requirements-lora.txt` |
| Host | Debian 13, kernel 6.12.105+deb13-amd64, x86_64 |
| Radio module | `sim`. There is no radio. |
| Transport | `network.enabled_protocols=UDP_BROADCAST` over a user-defined Docker bridge |
| Node identities | `3437096449` and `3437096450`, from MACs `AA:BB:CC:DD:EE:01` and `:02` |
| Port | `PRIVATE_APP` (256) |
| Ambient | Not applicable. Nothing here is physical. |

Region profile, channel, transmit power, antenna, separation and orientation
are **not recorded because none exist.** A simulated module has no RF
configuration to state, and any value written here would look like a
measurement of something.

## Result 1: the tag survives

A payload of one tag byte followed by the message crossed from node 1 to node
2 and arrived byte-intact.

```text
DATA_PAYLOAD_LEN from the shipped protobuf: 233
PRIVATE_APP portnum: 256
sending 21 bytes: 1 tag byte + 20 message bytes
RECEIVED tag byte: 42
RECEIVED message : FML-TAG-PROBE-MARKER
tag intact       : True
message intact   : True
```

The one-byte index the specification selects is carriable alongside the
message, on the transport, at the size it selects.

## Result 2: the usable payload is 231 bytes, not 233

Looked for while confirming the byte costing. The specification costs the tag
against `DATA_PAYLOAD_LEN`, which the protobuf reports as 233 and which this
run confirms. **A 233-byte payload does not arrive.** Nor does 232.

```text
  requested  50 bytes -> received 50
  requested 100 bytes -> received 100
  requested 150 bytes -> received 150
  requested 200 bytes -> received 200
  requested 220 bytes -> received 220
  requested 232 bytes -> NOT RECEIVED
  requested 233 bytes -> NOT RECEIVED

  requested 221 bytes -> received 221
  requested 223 bytes -> received 223
  requested 225 bytes -> received 225
  requested 227 bytes -> received 227
  requested 229 bytes -> received 229
  requested 230 bytes -> received 230
  requested 231 bytes -> received 231
```

**231 bytes crosses. 232 does not.** The boundary is reproducible: the 232 and
233 cases were each sent twice, in separate runs, and never arrived.

There is no failure at the sender. `sendData` accepts the payload and returns
without error; the packet simply does not appear at the other node. **A
sender that does not complain is the part worth flagging**, because an
implementation that fills the documented 233 bytes would drop messages
silently, on the bearer CONOPS section 50.8 makes the lifeline.

Why two bytes are unavailable is **not established here.** Protobuf field
overhead is the obvious candidate and it is not measured, so it is not
claimed. What is established is the number that can be relied on.

## What this does and does not support

**Supports:** the encoding is implementable on the transport. Falsification 3
does not fire against Meshtastic itself, and the one-byte index costs
0.43% of the documented budget as stated.

**Does not support** any claim about the **gateway**, which is what
falsification 3 actually names. `FML-ADR-048` orders three of them,
OpenTAKServer first, and **none has been exercised.** A gateway that parses
CoT and re-emits a canned Meshtastic message would drop the tag whatever the
transport can carry. That remains untested and is the half that matters for
`services/gateways/`.

**Does not support** any claim about RF, airtime, duty cycle, collisions or
range. The transport here is UDP on a Docker bridge, which is a perfect wire.

## What should change because of this

1. The specification's costing table uses 233 as the denominator. The usable
   figure is 231. The percentages barely move; **the usable message length
   does**, and an implementer reading 233 would be wrong by two bytes.
2. Whatever writes the tag should refuse a payload over 231 bytes rather than
   hand it to a sender that accepts it and drops it.

Neither is made here. This is evidence; the specification is the owner's to
amend.
