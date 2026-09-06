# Filling the store from WAN, when it is up

The map service's primary source is the node's own store (an S1 local service),
with a mesh-peer fallback for a storage-constrained node
(`serving-across-the-mesh.md`). This adds a third source, on the Program Owner's
direction (2026-09-06): when the node has a WAN route and the operating mode
permits, tiles the store lacks are fetched from a **permitted** upstream and
cached locally. It is a design, not a specification: it marks what is decided and
what is still an open decision, and it invents no mechanism.

## The source order, and where WAN sits

The node's map service resolves a `z/x/y` request in order:

1. the node's **own store**;
2. a **storage peer over the mesh**, if the node lacks the tile and a holder is
   reachable (`serving-across-the-mesh.md`);
3. a **permitted upstream over WAN**, if the tile is still missing, WAN is
   reachable, and the operating mode permits emission.

Every WAN-fetched tile is **written through to the local store**, so the area
fills in as operators use it and a repeat request is served locally. Across a
deployment with intermittent WAN, the store converges toward the S1-local ideal
rather than staying fixed at what was pre-loaded.

WAN is itself a mesh-shared resource: a node without its own uplink can reach one
through a peer gateway (`FML-ADR-068` forwards an EUD to the WAN uplink,
`FML-ADR-069` makes WAN a mesh-wide capability, `TBR-NET-04` pools it). So "over
WAN" means wherever the node has an internet route, its own or shared. A v1 may
restrict to the node's **own** uplink to keep the emission surface local; the
shared-uplink case is a natural extension and a `TBR-NET-04` concern.

## Three guardrails, none optional

### 1. Never a dependency (local-first, WAN-independent)

CONOPS sections 1, 4 and 5 make the program WAN-independent and local-first.
WAN-fetch is opportunistic **enrichment only**: a store miss with WAN down is a
miss the client sees, served from what the store holds -- never a hang, never a
hard dependency. The node is still provisioned before deployment and still works
with no internet, which is the invariant `README.md` states ("a node with no
internet cannot fetch what it was not given"). WAN-fetch does not move
provisioning into the field; it enriches a node already provisioned to work
offline.

**This does expand the service's v1 boundary.** `README.md` lists "no field tile
download" among what v1 deliberately does not do, with a strong rationale.
WAN-fetch is field tile download, guarded. The two reconcile through the
invariant above -- offline correctness is untouched -- but the expansion is a
**decision the Program Owner directed**, recorded as `FML-ADR-072` (`PROPOSED`);
accepting it (`SELECTED PRINCIPLE`) is the owner's act.

### 2. Permitted source only

The upstream **shall** be a permitted tile source -- USGS National Map (keyless,
US), Esri imagery/topo (keyless, attribution), or a licensed provider -- and
**shall not** be OpenStreetMap's public tiles. The 2026-09-04 evidence found OSM
bulk and proxy fetching IP-blocked and forbidden by policy
(`docs/evidence/TBR-MAP-01/2026-09-04-real-eud-offline-map-and-storage.md`); a
caching proxy hammering a public server is exactly what gets a deployment
blocked. Which source, and its licence and sensitivity, is `TBR-MAP-01` and
touches `TBR-SEC-01` -- the same call as store provisioning.

### 3. EMCON-gated

WAN-fetch emits: DNS and HTTPS to the upstream. Under EMCON or a radio-silent
mode it **shall** be suppressed, exactly as `FML-ADR-068` suppresses the WAN
passthrough under an EMCON profile that forbids emission on the WAN bearer. The
Status Aggregator already carries an `EMCON` state (`FML-ADR-046`); the map
service reads it and, in EMCON, serves only the local store. A map that reaches
out to the internet in radio silence is a compromise, so this is a gate, not a
preference.

## What it is, mechanically

A caching reverse proxy, over **two tiers**. On a `z/x/y` request the service
serves from the **provisioned store** (permanent, installed before deployment)
or the **fetch cache** (ephemeral) if a live copy is held. On a miss, with WAN
reachable and the mode permitting, it fetches from the permitted upstream,
returns the tile to the client, and writes it into the **fetch cache** -- not the
provisioned store -- with an expiration attached. The two tiers are kept distinct
so eviction never touches a provisioned tile. This is the same shape as the mesh
proxy in `serving-across-the-mesh.md`, with a WAN upstream and a time-bounded
local cache. `nginx` `proxy_cache` or a small tile cache provides it.

The distinction matters operationally: a tile an EUD happened to pull once is not
the same as a map installed to the node, and only the former ages out. An expired
tile requested again while WAN is up is re-fetched, so the cache also stays fresh
rather than serving stale imagery.

## Constraints it runs under

- **One compute element** (`FML-ADR-021`, `TBR-COMP-01`): a caching proxy is
  light but not free.
- **Storage** (`TBR-CARRIER-01`, `FML-ADR-050`): the fetch cache is bounded by
  time first -- each tile expires (the interval a deployment value, not a literal)
  -- and by a size cap as a backstop, so field maps do not become permanent and
  do not blow up the footprint. The exact rule (expiry from fetch versus last
  access, plus the cap) is `TBR-MAP-01`'s; `FML-ADR-050`'s write-amplification
  budget covers the churn. The provisioned store is separate and permanent.
- **At-rest security** (`TBR-SEC-01`): fetched tiles are stored; if the imagery
  is sensitive its at-rest posture applies, if it is public map data it does not.

## Decided, and open

**Decided (cited, not re-litigated here):**

- local-first and WAN-independence (CONOPS 1, 4, 5);
- EMCON gating (`FML-ADR-068` precedent, `FML-ADR-046` state);
- permitted-source-only (the 2026-09-04 finding, `TBR-MAP-01`, `TBR-SEC-01`);
- one compute element (`FML-ADR-021`);
- the source-order framing (`serving-across-the-mesh.md`).

**Open (this design surfaces, does not decide):**

- **The scope expansion itself** is recorded as `FML-ADR-072` (`PROPOSED`) --
  field tile download was a stated v1 non-goal of the service, and adopting
  WAN-fetch revises it; accepting the ADR is the Program Owner's act.
- The upstream source selection, and the fetch-cache policy -- the expiry
  interval and rule (from fetch versus from last access) and the size cap
  (`TBR-MAP-01`). The *principle* that fetched tiles expire and provisioned tiles
  do not is decided in `FML-ADR-072`; the numbers are the deployment's.
- Fetching over a **peer's** shared WAN, not only the node's own (`TBR-NET-04`).
- The exact EMCON/mode gate wiring, from the Status Aggregator's `EMCON` state
  into the map service.

See `serving-across-the-mesh.md` for the local and mesh sources this extends, and
`README.md` for the service outline.
