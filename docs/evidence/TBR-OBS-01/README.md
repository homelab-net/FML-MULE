# Evidence for TBR-OBS-01

**Trade:** How is a mission observation recorded and presented so its age, source, and state stay visible

**Trade file:** `docs/trades/TBR-OBS-01-how-is-a-mission-observation-recorded-and-presented-so-its-age-source-and-state-stay-visible.md`

**Current contents:** two written readings. The comparison is
`2026-09-24-representation-comparison.md`. The consumer reading is
`2026-09-24-consumer-reading.md`. The upstream files they quote are
archived beside them. The CoT schema, the OpenTAKServer `CoT` model,
`scheduled_jobs.py`, and Meshtastic `mesh.proto` are archived beside the
comparison. The consumer reading archives excerpts of the OpenTAKServer
1.7.13 functions it cites and of Meshtastic firmware `v2.8.0.47db0e3`.
The OpenTAKServer `defaultconfig.py` is not archived whole, because it
contains upstream default credentials. The one default the comparison uses
is excerpted. The Python snapshots keep a `.py.txt` suffix so their text
stays verbatim. Their GPL-3.0 text is `docs/evidence/licenses/GPL-3.0.txt`.
No software digital twin was run. Nothing in either reading is `SIMULATED`
or `HARDWARE-VERIFIED`.

The comparison finds that none of the reviewed representations, using their
documented native semantics and without new FML semantics, satisfies the
complete CONOPS v1.2 section 28A contract. The consumer reading finds that
the functions it cites also do not satisfy that contract, and that a TAK
client was not read. Neither reading selects a representation. Accepting
either finding does not close the trade. The trade stays `OPEN`.

Read the **Closure evidence** and **Closure gate** sections of the trade file
named above. Those sections are authoritative; this file does not restate them,
so that the two cannot drift apart.

Naming and recording rules are in `docs/evidence/README.md`. Nothing real: no
deployment location, member identity, callsign, credential, or operational
capture. See `SECURITY.md`.
