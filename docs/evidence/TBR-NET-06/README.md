# Evidence for TBR-NET-06

**Trade:** How does a remote EUD resolve the one service name to its assigned MULE across multiple MULEs

**Trade file:** `docs/trades/TBR-NET-06-how-does-a-remote-eud-resolve-the-one-service-name-to-its-assigned-mule-across-multiple-mules.md`

**Current contents:**

| Artifact | What it is |
| --- | --- |
| `2026-09-29-remote-name-resolution-analysis.md` | Analysis **by reasoning, no bench**. Shows tailnet-global split-DNS cannot fan out one name to different assigned MULEs, scores the options against the four locked constraints, and recommends a **contingent** direction (per-EUD/per-device resolver set at enrollment). Selects nothing; the trade closes on a real two-MULE tailnet observation, not on this note. |

This trade is `OPEN`. The analysis advances it; it does not close it.

Read the **Closure evidence** and **Closure gate** sections of the trade file
named above. Those sections are authoritative; this file does not restate them,
so that the two cannot drift apart.

Naming and recording rules are in `docs/evidence/README.md`. Nothing real: no
deployment location, member identity, callsign, credential, or operational
capture. See `SECURITY.md`.
