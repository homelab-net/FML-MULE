# Map server over the mesh (hwsim)

**Tier:** `SIMULATED`. `mac80211_hwsim` models the 802.11 MAC and nothing
physical.

**Date:** 2026-09-05. **Node:** development machine (see `docs/dev-machine.md`),
`6.12.105+deb13-amd64 x86_64`, `batman-adv 2024.2` (`batctl debian-2025.0-2`).
**Configuration:** two `mac80211_hwsim` radios, two network namespaces, 802.11s
mesh at 2412 MHz, `batman-adv` `BATMAN_IV`, `bridge_loop_avoidance 0`
(`FML-ADR-056`). **Procedure:** `test/bench/map-server-mesh.sh`. **Taken by:**
Cameron Zobrist.

## What this demonstrates

`services/map/README.md` records, from the 2026-09-04 real-EUD session, that a
storage-equipped node is **a map server for the mesh, not only its own EUDs**:
provisioning is area-scoped by storage, so a node carrying a large repository
serves it to other nodes over the mesh -- named there as the same
share-a-resource pattern as the WAN gateway (`TBR-NET-04`, CONOPS section 42).
That was a claim with no bench behind it. This is the bench.

`MULE-A` joins the mesh and serves its `z/x/y` tile store over HTTP on its
`bat0` address -- the endpoint `services/map/README.md` commits to. `MULE-B`
joins the same mesh with **no store** and fetches a tile across `batman-adv`.
The tile `MULE-B` receives is compared byte-for-byte against `MULE-A`'s on-disk
copy, so a pass proves the **repository tile itself** crossed the mesh, not that
some `200` with some bytes came back. It is the direct analog of
`wan-gateway-sharing.sh`: one node holds a resource, a node that does not have it
reaches it across the mesh.

## Run

```text
  MULE-A store built at /tmp/fml-mapstore.U6kEN3 (2 tiles)
  MULE-A radio=phy39 (store server), MULE-B radio=phy40 (storage-less)
  radios chosen from the hwsim device tree; no real phy can be named here
  802.11s + batman-adv mesh formed (MULE-A 10.43.0.1, MULE-B 10.43.0.2)
  mesh carries traffic (MULE-B reaches MULE-A)
  MULE-A serving z/x/y on the mesh at 10.43.0.1:8080

PASS. Storage-less MULE-B fetched a map tile from MULE-A over the mesh.
  tile:  15/6852/12530.png
  bytes: 1372, PNG image data
  md5:   304e64e2f51a56ce28cdb727a47a1768 -- byte-identical to MULE-A store; the repository tile
         itself crossed 802.11s + batman-adv to the storage-less node.

This is the map-server-for-the-mesh role (services/map/README.md): one
node holds the repository and serves it to the rest of the mesh -- the
TBR-NET-04 share-a-resource pattern applied to TBR-MAP-01.
Tier: SIMULATED. hwsim models the 802.11 MAC and nothing physical; no
serve rate here is a real-radio rate, and this selects no store or server.
```

The `md5` is per-run reproducible because the store is generated deterministically
(a raw-PNG encoder, seeded per tile); it is not a fixed constant to memorise.

## The reading

The map-server-for-the-mesh role composes on the stack this program has already
decided: a storage node's `z/x/y` service is reachable across `batman-adv`, and
a storage-less node retrieves a repository tile from it intact. The single-step
check (the storage-less node pings the storage node) passes before the fetch is
trusted, per CLAUDE.md -- the multi-step result is uninterpretable until the
boring one holds.

This is the routing-and-interface half of the role, and it is the half that does
not need hardware. It says the pattern works; it does not size it.

## What it is not

- **Not a store or server selection for `TBR-MAP-01`.** It exercises the `z/x/y`
  contract with a static file server, the same interface commitment the
  2026-09-04 bench exercised; the store format and tile server remain the trade's
  to pick.
- **Not a serve rate.** `hwsim` has no medium -- no path loss, no rate
  adaptation. The byte count and any timing are MAC-layer, not a real-radio
  serve rate. Throughput of a map server over a real mesh is a hardware item.
- **Not a CM4 footprint.** Serving a repository to the mesh while running the
  full catalog is load `TBR-COMP-01` measures on the target; nothing here runs on
  a CM4.
- **Not real imagery.** The tiles are deterministic generated PNGs, not map data.
  Real imagery on a real EUD is the 2026-09-04 evidence; committing tiles here
  would be map data this program does not own.
- **Not a `TBR-NET-04` closure.** `TBR-NET-04` is the WAN-gateway election and
  pooling trade; this borrows its share-a-resource pattern for maps and does not
  bear on gateway selection.

## Cross-references

- `test/bench/map-server-mesh.sh` -- the procedure.
- `services/map/README.md` -- the map-server-for-the-mesh role this exercises.
- `docs/evidence/TBR-MAP-01/2026-09-04-real-eud-offline-map-and-storage.md` --
  the real-EUD render and the storage arithmetic that motivated the role.
- `test/bench/wan-gateway-sharing.sh`, `docs/evidence/TBR-NET-04/` -- the
  WAN-gateway share pattern this is the map analog of.

Nothing real: no deployment location, member identity, callsign, credential, or
operational capture. The store, addresses, and mesh id are bench values. See
`SECURITY.md`.
