# A real EUD renders a MULE-served map offline; and what it costs to store

**Trade:** `TBR-MAP-01`.
**Date:** 2026-09-04.
**Taken by:** Cameron Zobrist, with Claude Code, on the lab bench.
**Status of this artifact:** the render is a **real-device** result (an iOS iTAK
client drawing tiles served by the node); the CM4 footprint is **not** measured,
so this does not close the trade. Storage figures are calculated, not measured.

Nothing real: no deployment location, member identity, or callsign is recorded;
areas below are given as sizes and public region names for the storage
arithmetic, not as an operating location.

## What was demonstrated

A node ran the committed `services/map/` interface -- a `z/x/y` tile endpoint
behind the node's reverse proxy -- and a **real iTAK EUD** on the node's access
point selected it as its map source and **rendered a continuous, high-detail
map**, tiles streamed from the node and cached by the client. The client held no
pre-loaded map file; it fetched every tile from the node. With the node's WAN
uplink cut, tiles kept flowing from the node's local store (verified in the
node's access log: hundreds of `200`s to the EUD across zooms z12-19 with no
internet path present).

So the model `services/map/README.md` commits to is real on a device: **the node
is the tile source; the EUD streams and caches; no map data is loaded onto the
EUD by hand.**

## Three findings that cost real time and are worth keeping

1. **You cannot provision the store from OpenStreetMap's public tiles.** A bulk
   pull was IP-blocked; OSM returned an identical "Access blocked" image for
   every tile (2350 byte-identical files), which the node then served faithfully
   -- a working pipeline serving garbage. OSM's tile policy forbids this. The
   store must come from a **permitted source**: USGS National Map (free, no key,
   US coverage), Esri World Imagery/Topo (keyless, attribution), or a licensed
   provider. This is the imagery-licence question `TBR-MAP-01` and
   `services/map/README.md` name, now concrete, and it touches `TBR-SEC-01` only
   if the imagery is sensitive.
2. **The client caches tiles by position, not by source.** Swapping the node's
   map source did not refresh the EUD -- it showed stale cached tiles until the
   source URL path changed (a fresh path the client had never cached). Real
   EUD-provisioning consequence: a tile update needs a cache-invalidation story,
   not just a new source.
3. **The serve pipeline was never the fault.** Every failure was store content
   (OSM block, a provider watermark) or client cache. The node served exactly
   what it held.

## What it costs to store (calculated, ~16 KB/tile satellite JPEG)

Measured on the bench: a ~13x15 km AO at z10-19 (full detail) = **62 MB /
3,504 tiles**. Scaling that tile density:

| Coverage | Zoom | Store |
| --- | --- | --- |
| One AO (~13x15 km) | z10-19 | 62 MB |
| ~200x200 mi region, building detail | z18 | ~150 GB |
| ~200x200 mi region, full detail | z19 | ~600 GB |
| Colorado + 7 adjacent states, navigation | z8-13 | ~3.8 GB |
| Colorado + 7 adjacent states, street | z16 | ~240 GB |
| CONUS, street level | z16 | ~1.1 TB |
| CONUS, full detail | z19 | ~73 TB |

**The map service is area-scoped by physics, not by choice.** The CM4's 32 GB
eMMC (`FML-ADR-021`, BOM `NODE-CORE/Compute`) holds an AO at full detail with
room to spare, or a multi-state region only at a navigation zoom (~z13). Useful
street/building detail across a region is hundreds of GB to TB -- it requires
**added storage**, which is the `TBR-COMP-01` budget and a `TBR-CARRIER-01` slot
decision. This is exactly why CONOPS section 9.2 says "selected cached maps," not
"the country": you provision an operating area, and a **storage-equipped node
serves that repository to its EUDs and, acting as a server, to other nodes over
the mesh** -- the same share-a-resource-across-the-mesh pattern as the WAN
gateway (CONOPS section 42, `TBR-NET-04`).

## What remains for closure

Unchanged and still required: a selected tile server (single-binary vs static
tree vs library), rootless and digest-pinned (`FML-ADR-029`); the **CM4
footprint** while serving alongside the router (`TBR-COMP-01`); the imagery
source, licence, and sensitivity call (`TBR-SEC-01`); and the store-size figure
for a representative provisioned area from a permitted source. The real-device
render settles the interface and the client model; it does not settle the
mechanism or the CM4 cost.
