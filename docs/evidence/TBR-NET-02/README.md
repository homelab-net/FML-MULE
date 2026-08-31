# Evidence for TBR-NET-02

**Trade:** How does a node address the EUDs behind it

**Trade file:** `docs/trades/TBR-NET-02-how-does-a-node-address-the-euds-behind-it.md`

**Current contents:**

| Artifact | What it is |
| --- | --- |
| `2026-08-29-addressing-specification.md` | The analysis half: mapping table, a worked trace per plane, the operator-facing statement of what is lost at the plane boundary, the tag encoding costed against the 233-byte payload, and the unresolved-recipient rule. `UNVERIFIED`. |
| `2026-08-30-the-eud-code-must-be-unique-to-everyone-who-can-hear-it.md` | Analysis. The selected one-byte EUD index is allocated per deployment, and LoRa has no per-deployment boundary by default, so it collides with a real member of another deployment and the message is delivered to the wrong person. The fail-closed rule does not catch it. No measurement. |

**This trade is still `OPEN`, and the artifact says so in its own first
section.** Two things are missing. Every trade owner in this repository is
`TBD-SRR`, and a trade closes when a **named** owner accepts the evidence. And
the empirical half does not exist: nothing exercises an EUD behind one MULE
reaching an EUD behind another, because `test/flatsat/` builds exactly one
node.

Read the **Closure evidence** and **Closure gate** sections of the trade file
named above. Those sections are authoritative; this file does not restate them,
so that the two cannot drift apart.

Naming and recording rules are in `docs/evidence/README.md`. Nothing real: no
deployment location, member identity, callsign, credential, or operational
capture. See `SECURITY.md`.
