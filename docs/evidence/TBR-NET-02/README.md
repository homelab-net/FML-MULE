# Evidence for TBR-NET-02

**Trade:** How does a node address the EUDs behind it

**Trade file:** `docs/trades/TBR-NET-02-how-does-a-node-address-the-euds-behind-it.md`

**Current contents:**

| Artifact | What it is |
| --- | --- |
| `2026-08-29-addressing-specification.md` | The analysis half: mapping table, a worked trace per plane, the operator-facing statement of what is lost at the plane boundary, the tag encoding costed against the 233-byte payload, and the unresolved-recipient rule. `UNVERIFIED`. |
| `2026-08-30-the-eud-code-must-be-unique-to-everyone-who-can-hear-it.md` | Analysis. The selected one-byte EUD index is allocated per deployment, and LoRa has no per-deployment boundary by default, so it collides with a real member of another deployment and the message is delivered to the wrong person. The fail-closed rule does not catch it. No measurement. |
| `2026-09-06-geochat-to-survives-the-meshtastic-bearer.md` | `SIMULATED`. Post-closure verification of the *selected* encoding: a `TAKPacket` with `Contact.callsign` and `GeoChat.to` crosses two `meshtasticd` nodes with both fields intact, on upstream's own ATAK plugin port. The custom-index falsifier was moot once `FML-ADR-070` chose upstream's fields; this shows those fields are carriable on the bearer. Reproduced by `test/bench/geochat-survival.sh`. |

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
