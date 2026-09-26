# Evidence for TBR-OBS-01

**Trade:** How is a mission observation recorded and presented so its age, source, and state stay visible

**Trade file:** `docs/trades/TBR-OBS-01-how-is-a-mission-observation-recorded-and-presented-so-its-age-source-and-state-stay-visible.md`

**Current contents:** two written readings and a decision packet. The comparison
is `2026-09-24-representation-comparison.md`. The consumer reading is
`2026-09-24-consumer-reading.md`. The decision packet is
`2026-09-27-representation-decision-packet.md`: it builds on the two readings to
recommend a representation direction (CoT as carrier plus an FML metadata layer for
the behaviors no read consumer performs) and records the TAK-client reading as a
limitation. After an independent red-team the Owner accepted its **frame** on
2026-09-26, recorded in `FML-ADR-085` (`SELECTED PRINCIPLE`); the metadata carrier,
the state-model thresholds, and the assignment of the section 28A behaviors to local
policy are deferred to a later implementation ADR gated on the owed CoT-`detail` and
TAK-client readings. The trade stays `OPEN`. The packet adds no upstream excerpts of
its own. `2026-09-26-cot-detail-roundtrip-on-ots.md` is a `SIMULATED` runtime
reading: it injected one synthetic CoT event into the live OTS bench and observed
that OpenTAKServer preserves an unknown CoT `detail` child verbatim through store
and re-serve, that the time trio maps to the record, and that a past-`stale` row is
retained (not deleted) -- answering the OpenTAKServer half of `FML-ADR-085`'s owed
carrier reading. The TAK-client half stays owed. The upstream files the readings quote are
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
