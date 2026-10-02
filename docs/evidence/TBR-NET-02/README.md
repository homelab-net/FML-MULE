# Evidence for TBR-NET-02

**Trade:** How does a node address the EUDs behind it

**Trade file:** `docs/trades/TBR-NET-02-how-does-a-node-address-the-euds-behind-it.md`

**Current contents:**

| Artifact | What it is |
| --- | --- |
| `2026-08-29-addressing-specification.md` | The analysis half: mapping table, a worked trace per plane, the operator-facing statement of what is lost at the plane boundary, the tag encoding costed against the 233-byte payload, and the unresolved-recipient rule. `UNVERIFIED`. |
| `2026-08-30-the-eud-code-must-be-unique-to-everyone-who-can-hear-it.md` | Analysis. The selected one-byte EUD index is allocated per deployment, and LoRa has no per-deployment boundary by default, so it collides with a real member of another deployment and the message is delivered to the wrong person. The fail-closed rule does not catch it. No measurement. |
| `2026-09-06-geochat-to-survives-the-meshtastic-bearer.md` | `SIMULATED`. Post-closure verification of the *selected* encoding: a `TAKPacket` with `Contact.callsign` and `GeoChat.to` crosses two `meshtasticd` nodes with both fields intact, on upstream's own ATAK plugin port. The custom-index falsifier was moot once `FML-ADR-070` chose upstream's fields; this shows those fields are carriable on the bearer. Reproduced by `test/bench/geochat-survival.sh`. |
| `2026-09-27-one-lora-hop-to-a-partner-node.md` | Real-hardware bench result; formal `HARDWARE-VERIFIED` tier **held** pending a program-wide posture flip (see the note). A Meshtastic message crosses one **real** sub-GHz LoRa RF hop between two physical nodes (RAK4631 + a partner node, ~1 room, SNR 6-7 dB), both ways with a delivery ACK. Also finds a PKI direct message NAKs `NO_CHANNEL` until a NodeInfo key exchange completes. Says nothing about range/duty/coexistence (`TBR-RF-02`) or real `GeoChat.to` contents (still `SIMULATED`). |
| `2026-09-28-real-geochat-encoding-through-ots.md` | `SIMULATED` / real-OTS-encoder. Drives a GeoChat through OpenTAKServer's own encoder: it copies the client's `<__chat id>` into `GeoChat.to` verbatim, substituting no callsign of its own (in-run a DM carried the injected **id**/UID, a room the **room name**; what a live client places there -- a UID by convention -- is owed a capture), `Contact.callsign` = sender callsign, `device_callsign` = sender UID (unishox2, `ATAK_PLUGIN`). **Advances** `FML-ADR-070`'s "GeoChat.to contents" item (encoder behavior); the *resolution* roster source is now decided (the Mission Trust Service; `CCR-06`, recorded in `FML-ADR-087`), while the live-client DM (what the client places in `<__chat id>`) remains owed. |

The [October three-node record][three-node] adds a real addressed LoRa/IP
phone round trip, with native UID correlation and a continuously connected
synthetic sender. It also records every assisted step and the fresh-checkout
limits. It does not establish persistent gateway or RF fail-closed behavior.

[three-node]: 2026-10-02-three-node-lab-boundaries.md

**This trade is `CLOSED` (2026-09-04) on `FML-ADR-070`,** accepted by the named
owner (Cameron Zobrist). The selected encoding is upstream's `Contact.callsign`
and `GeoChat.to`, not the one-byte index the analysis first costed; the
`2026-08-30-opentakserver-meshtastic-path.md` evidence found a custom tag is
discarded by the `FML-ADR-048` gateway. The empirical half exists: the mesh probe
exercises an EUD behind one MULE reaching an EUD behind another, and the
2026-09-06 artifact confirms the selected fields survive the bearer.

Read the **Closure evidence** and **Closure gate** sections of the trade file
named above. Those sections are authoritative; this file does not restate them,
so that the two cannot drift apart.

Naming and recording rules are in `docs/evidence/README.md`. Nothing real: no
deployment location, member identity, callsign, credential, or operational
capture. See `SECURITY.md`.
