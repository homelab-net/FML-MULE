# Evidence for TBR-MAP-01

**Trade:** Which local tile store and server serves maps to an EUD offline

**Trade file:** `docs/trades/TBR-MAP-01-which-local-tile-store-and-server-serves-maps-to-an-eud-offline.md`

**Current contents:** `SIMULATED` interface and mesh demonstrations, plus the
server selection and its software-half footprint. This trade is still `OPEN`:
the server is selected and sized on x86, but the closure gate's CM4 footprint
(`TBR-COMP-01`) and the real-imagery USB2 read-latency check remain.

- `2026-09-04-tile-interface-bench.py` -- reproducing script. Builds an MBTiles
  store of placeholder tiles and serves `z/x/y` from it; regenerates the store
  deterministically, so the binary is not committed.
- `2026-09-04-tile-interface-bench-x86.txt` -- the run and its reading, with an
  explicit list of what it is **not** (not CM4 footprint, not an EUD render, not
  a server selection, not map data).
- `2026-09-04-mule-local-tiles.xml` -- an ATAK/iTAK map-source definition for
  the endpoint, the client half of the interface.

- `2026-09-04-real-eud-offline-map-and-storage.md` -- a **real iTAK EUD**
  rendering a high-detail map streamed from the node with WAN cut, plus the
  storage arithmetic (AO vs region vs CONUS) and the findings that cost the most
  time: the store cannot come from OSM's public tiles (permitted source
  required), and the client caches tiles by position not by source.

- `2026-09-05-map-server-over-mesh-hwsim.md` -- a `SIMULATED` demonstration of
  the **map-server-for-the-mesh role** the real-EUD session identified: a
  storage node serves its `z/x/y` store over `batman-adv`, and a storage-less
  node fetches a tile that is byte-identical to the store's copy. The
  routing-and-interface half of the role; it selects no store or server and
  measures no serve rate (`hwsim` has no medium). Reproduced by
  `test/bench/map-server-mesh.sh`.

- `2026-09-05-real-eud-map-fetch-over-mesh-fallback.md` -- the same fallback with
  a **real iTAK EUD**: a storage-less serving node renders the EUD's map by
  sourcing every tile from a peer over the mesh (395 tiles served `200`), and a
  kill test proves the sourcing -- with the peer stopped, fresh tiles fail `502`
  and the peer's log is frozen; restoring it resumes serving. Still the transport
  half only (a hardcoded upstream, no discovery or failover), and the inter-node
  hop is `hwsim`, so `SIMULATED`. See `services/map/serving-across-the-mesh.md`.

- `2026-09-06-martin-mbtiles-server-footprint.md` -- the **server selection and
  its software-half footprint**. Martin (MapLibre) is selected over `mbtileserver`
  (no arm64 image) and `tileserver-gl-light` (a GL renderer, a v1 non-goal): it is
  a rootless, digest-pinned, single Rust binary that reads MBTiles and serves
  `z/x/y`. Measured idle RSS ~8.5 MB, peak ~28 MB under sustained loopback load
  (75 k requests, 0 errors, p95 3.4 ms), image ~650 MB at rest. x86 only -- the
  software half; the CM4 footprint is `TBR-COMP-01`. Reproduced by
  `test/bench/map-server-footprint.sh`.

What remains for closure is in the run records and in the trade's **Bench
progress** section: the CM4 footprint (`TBR-COMP-01`), and store size with real
imagery from a permitted source plus the USB2 read-latency check and the
`TBR-SEC-01` call. The server is now selected; the real-device render settled the
interface and client model, and this settles the server, but not the CM4 cost.

Read the **Closure evidence** and **Closure gate** sections of the trade file
named above. Those sections are authoritative; this file does not restate them,
so that the two cannot drift apart.

Naming and recording rules are in `docs/evidence/README.md`. Nothing real: no
deployment location, member identity, callsign, credential, or operational
capture. See `SECURITY.md`.
