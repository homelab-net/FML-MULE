# Local map service

Deployment and design notes for the **local map/tile service** in the
mission-service plane: the node's own source of map tiles for EUDs, so operators
render a map with no internet and no reachable external tile server.

**Nothing is deployed, and no mechanism is selected.** This directory is the
service outline. Roadmap item 4.4 holds its place in the plan, and `TBR-MAP-01`
is the mechanism selection.

The **interface** below -- the `z/x/y` endpoint and the ATAK/iTAK map-source
definition -- has a `SIMULATED` bench demonstration under
`docs/evidence/TBR-MAP-01/` (2026-09-04): an `MBTiles` store served over `z/x/y`,
a valid PNG returned for an XYZ request, and a map-source definition for it. That
settles the interface works; it does not select the server, measure the CM4
footprint, or render on an EUD, so the trade stays `OPEN`.

## What this is, and what it is not

**It is a tile source, not a map cache.** Two things are commonly confused:

- **Device-side tile caching** is what the **ATAK client** does: it caches tiles
  it has already rendered, on the phone, in its own store. MULE cannot do that
  part, and `TBR-TAK-01`'s cache question is about it.
- **Serving tiles** is being the *source* the client fetches from. That is this
  service. It is **not** a TAK-server function -- OpenTAKServer serves no tiles
  at all -- and it is not ATAK-specific.

**It is an S1 service, above the TAK server.** CONOPS section 9.2 lists
"selected cached maps" as an **S1 Local Mission Service**, one that should remain
available even when all external hosts are absent. The TAK server is **S2**. So
the map source is meant to survive when TAK does not, and it must run **locally
on the node**, not on a shared host.

The program does not make maps, redraw them, or own a projection. It serves
tiles a mapping toolchain produced, over an interface EUD clients already speak.
See `docs/NON-GOALS.md`.

## How an EUD consumes it

An EUD renders a map from **tiles**: small images addressed by zoom, column and
row, `z/x/y`. A map source is a URL template the client fills in, for example
`http://<node>/tiles/{z}/{x}/{y}.png`. The client requests the tiles its current
view needs and caches them itself.

ATAK accepts a network tile source through a **map-source definition** -- a small
XML file naming the URL template, the tile scheme (XYZ or TMS, which differ only
in whether row 0 is top or bottom), and the zoom range. Delivering that
definition to the EUD is part of this service's job: it is a small file, and it
can ride the same path a data package or the EUD provisioning uses.

Browser-based EUD services consume the same `z/x/y` endpoint directly; a web map
library points at the URL template with no MULE-specific code.

**The interface this service commits to is the `z/x/y` tile endpoint and a
map-source definition for it.** Everything behind that is an implementation
choice `TBR-MAP-01` makes.

## What has to be decided, and why it is a trade

`TBR-MAP-01` selects the mechanism. The real choices:

- **Tile store format.** `MBTiles` (a SQLite file of tiles) is the common
  offline container and diffs and ships as one file. `GeoPackage` and a plain
  directory of `z/x/y` files are alternatives. The store is **pre-loaded**;
  nothing here downloads tiles in the field.
- **Tile server.** A small dedicated server that reads the store and exposes
  `z/x/y` -- a single-binary server, a library behind a thin wrapper, or a
  static file server for a pre-rendered tree. It must be rootless (`FML-ADR-029`),
  local-first, and reachable through the `ingress/` reverse proxy by name.
- **How the map-source definition reaches the EUD**, which touches EUD
  provisioning and `TBR-ID-01`.
- **What imagery, and its licence and sensitivity.** Provisioning tiles is a
  content and legal question, not a software one, and it is out of this service
  but named so it is not forgotten.

## The constraints this service runs under

- **One compute element** (`FML-ADR-021`). This competes with the routing daemon
  for memory, and `services/catalog/` warns that a starved router looks like a
  radio fault. A tile server is read-mostly and light, which helps, and
  `TBR-COMP-01` bounds it.
- **Storage.** A tile store is the largest static asset a node is likely to
  carry, and it is storage at rest. If the imagery is sensitive, it falls under
  `TBR-SEC-01`'s at-rest posture; if it is public map data, it does not, and the
  trade records which.
- **The catalog and Quadlet gates.** Like every service, it is a `catalog/`
  entry and a `quadlets/` unit with the image pinned by digest, not a file
  appearing in `quadlets/`.
- **Ingress.** It is reached by name through the reverse proxy (`services/ingress/`),
  which also owns whether the endpoint is authenticated and how.

## What it deliberately does not do in v1

- **No field tile download.** The store is provisioned before deployment. A node
  with no internet cannot fetch what it was not given, and pretending otherwise
  is the failure this whole program is built against.
- **No rendering or styling on the node.** Tiles are pre-rendered. Vector tiles
  and on-node styling are a later question, not a v1 baseline.
- **No projection or datum handling.** The service serves what the store holds
  in the scheme the store uses; reconciling projections is the mapping
  toolchain's job upstream of the store.

## Learned on a real EUD (2026-09-04)

A real iTAK EUD rendered a high-detail map streamed from a node with WAN cut
(`docs/evidence/TBR-MAP-01/2026-09-04-real-eud-offline-map-and-storage.md`). It
confirmed this interface and added constraints this outline now carries:

- **The store cannot be OpenStreetMap's public tiles.** Bulk provisioning is
  IP-blocked and forbidden by OSM's tile policy; it returns an "Access blocked"
  image the node would then serve. The store is populated from a **permitted
  source** -- USGS National Map (free, no key, US coverage), Esri
  imagery/topo (keyless, attribution), or a licensed provider. Which one, and
  its licence and sensitivity, is `TBR-MAP-01` and touches `TBR-SEC-01`.
- **A storage-equipped node is a map server for the mesh, not only its own
  EUDs.** Provisioning is area-scoped by storage (an AO is tens of MB; a region
  at street detail is hundreds of GB -- see the evidence), so a node carrying a
  large repository serves it to its own EUDs *and*, acting as a server, to other
  nodes over the mesh -- the same share-a-resource pattern as the WAN gateway
  (CONOPS section 42, `TBR-NET-04`). The M.2 slot this needs is `TBR-CARRIER-01`.
- **Clients cache tiles by position, not by source.** A tile-store update needs
  a cache-invalidation story (a changed source path forced a real EUD to refetch;
  a same-path swap did not), which the EUD-provisioning path must account for.

## Done when

`TBR-MAP-01` selects a store format and a tile server, a `catalog/` entry and a
`quadlets/` unit exist with the image pinned by digest, the endpoint is reachable
through `ingress/`, and **an EUD renders a map from the node with no external
network**. The last is the acceptance and needs a device; the selection does
not.
