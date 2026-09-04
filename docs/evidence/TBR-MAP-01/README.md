# Evidence for TBR-MAP-01

**Trade:** Which local tile store and server serves maps to an EUD offline

**Trade file:** `docs/trades/TBR-MAP-01-which-local-tile-store-and-server-serves-maps-to-an-eud-offline.md`

**Current contents:** one `SIMULATED` interface demonstration. This trade is
still `OPEN`: the demonstration exercises the `z/x/y` contract but produces none
of the measured basis the closure gate demands.

- `2026-09-04-tile-interface-bench.py` -- reproducing script. Builds an MBTiles
  store of placeholder tiles and serves `z/x/y` from it; regenerates the store
  deterministically, so the binary is not committed.
- `2026-09-04-tile-interface-bench-x86.txt` -- the run and its reading, with an
  explicit list of what it is **not** (not CM4 footprint, not an EUD render, not
  a server selection, not map data).
- `2026-09-04-mule-local-tiles.xml` -- an ATAK/iTAK map-source definition for
  the endpoint, the client half of the interface.

What remains for closure is in the run record and in the trade's **Bench
progress** section: server selection, CM4 footprint (`TBR-COMP-01`), store size
with real imagery and the `TBR-SEC-01` call, and the EUD offline render.

Read the **Closure evidence** and **Closure gate** sections of the trade file
named above. Those sections are authoritative; this file does not restate them,
so that the two cannot drift apart.

Naming and recording rules are in `docs/evidence/README.md`. Nothing real: no
deployment location, member identity, callsign, credential, or operational
capture. See `SECURITY.md`.
