# GeoChat.to survives the Meshtastic bearer

**Tier:** `SIMULATED`. Two `meshtasticd` nodes exchanging over UDP on a docker
bridge -- no LoRa RF, no modulation, no airtime, no range.

**Date:** 2026-09-06. **Node:** development machine (`docs/dev-machine.md`).
**Daemon:** `meshtasticd` at the digest pinned in `tools/toolchain-versions.sh`,
`Lora.Module: sim`, `network.enabled_protocols: UDP_BROADCAST`. **Client:** the
`meshtastic` Python client in `.venv-lora`. **Procedure:**
`test/bench/geochat-survival.sh`. **Taken by:** Cameron Zobrist.

## What this verifies, and why it is not the old falsifier

`TBR-NET-02` closed on `FML-ADR-070`, which carries the sender in an ATAK
`Contact.callsign` and the recipient in an ATAK `GeoChat.to` -- upstream's own
TAK fields on the ATAK plugin port -- and **not** a custom member index. The
specification's original falsifier ("if the gateway cannot carry a custom
application tag") is therefore moot:
`2026-08-30-opentakserver-meshtastic-path.md` found a custom tag on a private
port is discarded by the `FML-ADR-048` gateway, which is exactly why the program
chose the upstream fields the ATAK plugin protobuf already handles.

That gateway evidence inspected the fields the gateway *handles*. It did not
carry a live GeoChat two nodes apart. This does: it confirms the **selected
encoding is carriable on the bearer**, which is the assumption `FML-ADR-070` rests
on and which nothing had exercised.

## Run

```text
=== single-step: a plain text message crosses ===
  text crossed: True ['fml-geochat-probe-marker']
=== multi-step: FML-ADR-070's TAKPacket (Contact.callsign + GeoChat.to) survives ===
  sent      contact.callsign='FMLPROBE-ALPHA'  chat.to='FMLPROBE-BRAVO'
  received  contact.callsign='FMLPROBE-ALPHA'  chat.to='FMLPROBE-BRAVO'  message='fml-geochat-probe-marker'
  Contact.callsign survived: True
  GeoChat.to survived:       True
PASS.
```

A `TAKPacket` (`meshtastic.protobuf.atak_pb2`) with `contact.callsign` and
`chat.to` set was sent from node 1 on the ATAK plugin port (portnum 72), received
on node 2, and decoded with **both fields byte-identical** to what was sent. The
single-step plain-text check passes first, so the multi-step result is
interpretable (`AGENTS.md`).

## The reading

`FML-ADR-070`'s encoding works on the bearer: the recipient (`GeoChat.to`) and the
sender (`Contact.callsign`) cross two Meshtastic nodes intact, on upstream's own
ATAK path rather than a channel invented beside it (`AGENTS.md` rule 6). The
follow-up the addressing specification named -- confirming what `GeoChat.to`
carries before recipient resolution is built -- can proceed on a field this probe
has shown survives.

## Why docker, not podman

`meshtasticd` exchanges over IP multicast `224.0.0.69`. With docker installed its
FORWARD chain policy is drop, and `br_netfilter` pushes even same-bridge frames
on a podman network through that chain, so podman-bridged nodes never hear each
other; docker's own bridges carry it (assessed 2026-09-06). This is the transport
`.github/workflows/lora-probe.yml` uses in CI. It is a bench-environment detail,
not a property of the encoding.

## What it does not establish

`SIMULATED`. UDP on a docker bridge is a perfect wire: nothing here is a LoRa RF
result -- no spreading factor, no duty cycle, no airtime, no range. Whether the
231-byte usable payload actually holds a callsign plus a useful message under
real modulation is `FML-ADR-070`'s composition-limit consequence and `TBR-RF-02`,
not this. And the clients are the raw `meshtastic` client, not ATAK/iTAK.

Nothing real: `FMLPROBE-ALPHA` and `FMLPROBE-BRAVO` are synthetic callsigns, the
message is a marker. No member identity, deployment location, or credential. See
`SECURITY.md`.
