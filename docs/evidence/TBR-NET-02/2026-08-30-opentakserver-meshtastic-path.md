# What OpenTAKServer's Meshtastic path actually carries

**Trade:** `TBR-NET-02`, and it bears on `FML-ADR-048`.
**Date:** 2026-08-30.
**Taken by:** Cameron Zobrist, on the lab development machine.
**Status of this artifact:** source and protocol inspection of the upstream
package. **The server was not run**, no message was passed through it, and no
claim here is a runtime result.

## Why this was looked at

`docs/evidence/TBR-NET-02/2026-08-29-addressing-specification.md` lists three
things that would falsify it. The third:

> **If the gateway cannot carry an application tag** in the payload alongside
> the message, the encoding above is unimplementable [...] `FML-ADR-048` fixes
> the gateway order and none of the three has been exercised.

`2026-08-30-tag-payload-measurement.md` answered the transport half: a one-byte
tag crosses between two `meshtasticd` nodes intact. This is the gateway half,
for the **first** of `FML-ADR-048`'s three options.

## Configuration

| Item | Value |
| --- | --- |
| Package | `OpenTAKServer` 1.7.13, from PyPI, upstream's own channel |
| Host | Debian 13, Python 3.13 |
| Method | Reading `opentakserver/controllers/meshtastic_controller.py` and the compiled `opentakserver/proto/atak_pb2` descriptors |

## Finding 1: a payload on an unhandled port is discarded

`meshtastic_controller.py` dispatches on the Meshtastic port number:

```python
handler = protocols.get(mp.decoded.portnum)
if handler is None:
    try:
        if portnums_pb2.PortNum.Name(mp.decoded.portnum) == "ATAK_PLUGIN":
            tak_packet = atak_pb2.TAKPacket()
            tak_packet.ParseFromString(mp.decoded.payload)
            self.protobuf_to_cot(...)
    except:
        ...
    return
```

A port the `meshtastic` library has no handler for, and which is not
`ATAK_PLUGIN`, reaches `return` and nothing else. **The packet is dropped.**

`PRIVATE_APP` is such a port. It is the one
`2026-08-30-tag-payload-measurement.md` used, and the natural place to put a
custom encoding. So a member tag carried that way crosses the air, arrives at
the receiving node, and is then discarded by the gateway without appearing in
CoT. Falsification 3 fires **for that encoding**.

## Finding 2: the upstream wire format already carries identity and recipient

It does not fire for the design as a whole, because the ATAK plugin protobuf
`OpenTAKServer` does handle already carries what the tag was for.

`TAKPacket` fields: `is_compressed`, `contact`, `group`, `status`, `pli`,
`chat`. Their contents:

| Message | Fields |
| --- | --- |
| `Contact` | `callsign` (string), `device_callsign` (string) |
| `GeoChat` | `message` (string), `to` (string, optional) |
| `Group` | `role` (enum), `team` (enum) |
| `PLI` | `latitude_i`, `longitude_i`, `altitude`, `speed`, `course` |
| `Status` | `battery` |

**`Contact.callsign` travels with the packet**, so the sender is identified per
person rather than per MULE. **`GeoChat.to` names a recipient.** Both are
strings and both are upstream's, not this program's.

## What this means for the specification

The specification's own mapping table says: "Callsign is already the
deployment-scoped human name." Its costing table considered a short callsign
string at roughly 8 bytes, 3.4% of the payload, and selected a one-byte index
instead at 0.43%, on airtime grounds. That reasoning is sound in isolation.

**It is not available in combination with `FML-ADR-048`.** That ADR fixes the
gateway order as OpenTAKServer first, and OpenTAKServer's Meshtastic path emits
and parses the ATAK plugin protobuf. A one-byte index cannot be added to it:
there is no spare field, and putting it on a private port has it discarded per
finding 1. Using the index means **replacing** upstream's encoding with a
custom one, which is the thing `FML-ADR-048` orders the program not to do
first.

So the choice is not "one byte or eight". It is:

1. **Use what upstream carries.** Callsign in `Contact`, recipient in
   `GeoChat.to`. Costs more airtime than the index and requires no custom
   protocol work, no schema change to the mission package, and nothing of this
   program's on the wire.
2. **Keep the index and stop being upstream-first**, which needs an ADR against
   `FML-ADR-048` rather than an implementation.

**This artifact does not choose.** `TBR-NET-02` has a named owner now and this
is evidence for that decision, not the decision.

## What this does not establish

The server was not run. Nothing was sent through it. `GeoChat.to`'s contents
are not established: whether it holds a callsign, a UID or something else needs
a message passed through a running instance, and that is the obvious next test.

Two of `FML-ADR-048`'s three options remain unexamined: the TAK Meshtastic
Gateway, and PyTAK with the Meshtastic Python API. A finding about
OpenTAKServer is not a finding about them, and the second may well accept an
arbitrary payload since it is a library rather than a server.

`PLI`, `Status` and `Group` carry no recipient field at all. Anything about
addressing position reports to a person, rather than chat, is untouched by
this.
