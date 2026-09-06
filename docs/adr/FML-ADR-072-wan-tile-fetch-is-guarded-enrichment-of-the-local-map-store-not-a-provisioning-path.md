---
id: FML-ADR-072
title: WAN tile-fetch is guarded enrichment of the local map store, not a provisioning path
status: SELECTED PRINCIPLE
date: 2026-09-06
supersedes: none
superseded-by: none
trades: [TBR-MAP-01, TBR-SEC-01]
verification: Stage 4
---

# FML-ADR-072 WAN tile-fetch is guarded enrichment of the local map store, not a provisioning path

**Source of rationale:** the Program Owner's direction (2026-09-06), the map
service design (`services/map/filling-the-store-from-wan.md`,
`serving-across-the-mesh.md`), CONOPS v1.01 sections 1, 4, 5, 9.2 and the
operating-mode sections, and `FML-ADR-068`, `FML-ADR-046` and `FML-ADR-050`.

## Context

The map service is an S1 local mission service (CONOPS 9.2): its primary source
is the node's own tile store, provisioned before deployment, and a **stated v1
non-goal** of the service is "no field tile download" -- a node with no internet
works from what it was given, and pretending otherwise is a failure the program
is built against.

The Program Owner has since directed a capability to fetch tiles the store lacks
from an upstream over WAN, when WAN is available, and cache them locally so the
store fills toward self-sufficiency. That is useful -- an operator with
intermittent WAN should not be stuck at exactly the tiles pre-loaded -- but it is
in tension with the local-first, WAN-independent principle (CONOPS 1, 4, 5), with
the reality that bulk or proxy fetching of public tiles is blocked and forbidden
(the 2026-09-04 OSM finding), and with emission control under EMCON. It also
revises a stated v1 boundary of the service, which is a decision that has to be
recorded rather than made in a config file. Doing nothing leaves the capability
either unbuilt or, worse, built without the guards.

## Decision

The map service **may** source a tile absent from its local store from a
**permitted** upstream over WAN, and **shall** cache it locally for reuse. A
WAN-fetched tile is **ephemeral cache**, held as a class distinct from the
**provisioned store**: it **shall** carry an expiration and be evicted when that
lapses, so opportunistically fetched field tiles do not accumulate as permanent
storage. The **provisioned store** -- tiles installed to the node before
deployment -- **shall not** expire, and the two classes **shall** be
distinguished so that expiry never touches a provisioned tile.

The fetch **shall** be gated: it happens only when the node has a WAN route and
the operating mode permits emission, and it is **enrichment, not provisioning**
-- the service **shall** function fully with WAN absent, and a store miss with no
WAN **shall** be served from what the store holds, never blocked. Provisioning
before deployment remains the baseline; this permits opportunistic,
self-expiring enrichment on top of it, and revises the map service's v1 non-goal
of no field tile download accordingly.

## Status

`SELECTED PRINCIPLE`. Accepted by the named owner (Cameron Zobrist) on
2026-09-06. The capability and its guards are decided: WAN-fetch is opportunistic
enrichment, never a dependency; the upstream is a permitted source, never OSM's
public tiles; the fetch is EMCON-gated; and a fetched tile is ephemeral, cached
distinctly from the provisioned store and evicted on expiry. The **mechanism** is
left to `TBR-MAP-01` and the map service's implementation: the upstream source,
the expiry interval and rule and the size cap, and the emission-gate wiring.

## Consequences

- **Permitted source only.** The upstream **shall** be a permitted tile source --
  USGS National Map, Esri imagery/topo, or a licensed provider -- and **shall
  not** be OpenStreetMap's public tiles, which the 2026-09-04 evidence found
  IP-blocked and policy-forbidden for proxy or bulk fetching. Which source, and
  its licence and sensitivity, is `TBR-MAP-01` and touches `TBR-SEC-01`.
- **EMCON-gated.** The fetch emits DNS and HTTPS, so it **shall** be suppressed
  under an EMCON or radio-silent mode, exactly as `FML-ADR-068` suppresses the
  WAN passthrough on an emission-forbidding profile, reading the `FML-ADR-046`
  EMCON state.
- **The fetch cache is bounded by time, then by size.** WAN-fetched tiles are the
  ephemeral class: each carries an expiration, so field maps do not become
  permanent and do not grow the footprint the way the provisioned store does. The
  **expiry interval is a deployment value** (region profile or mission package),
  not a literal in code, so a long operation can outlast a short one; the exact
  rule -- expiry from fetch versus from last access -- and a size cap as a
  backstop are `TBR-MAP-01`'s to set, and `FML-ADR-050`'s bounded-write policy and
  `TBR-CARRIER-01`'s capacity still apply. A lapsed tile requested again while WAN
  is up is re-fetched, so expiry doubles as imagery freshness. The provisioned
  store is untouched by any of this.
- **Compute.** A caching proxy is light but not free, and adds to the one-compute
  budget `TBR-COMP-01` sizes (`FML-ADR-021`).
- **It runs over shared WAN too.** A node without its own uplink may reach one
  through a peer gateway (`FML-ADR-068`, `FML-ADR-069`, `TBR-NET-04`); a v1 may
  restrict to the node's own uplink to keep the emission surface local.
- **It moves "field tile download" out of the map service's v1 non-goals.** The
  service README is updated to reflect the revised boundary. This is a service
  v1-scope note, not an entry in `docs/NON-GOALS.md`, so no non-goal removal is
  required; this ADR is the record of the change.

## Accepted cost

The program accepts a **controlled erosion of strict WAN-independence at the map
layer**. A node can now reach the internet for tiles, which is an emission and an
external-dependency surface that did not exist while the store was strictly
pre-provisioned. The never-a-dependency invariant and the EMCON gate bound it but
do not remove it, and someone will later argue that any field internet reach is
against the local-first ethos. The guards are the answer, and `TBR-SEC-01` and
the emission posture are where the residual risk is carried; the cost is accepted
because a store frozen at what was pre-loaded is a real operational limit an
operator with WAN should not have to live with.

## Fallback

The capability is opt-in per deployment and per mode, so if it proves to mask
under-provisioning, or if emission cannot be suppressed as reliably as EMCON
requires, it is disabled by configuration and the service reverts to store-only
-- the prior baseline, at no structural cost. The signal to take that fallback is
operators relying on WAN-fetch in place of provisioning, or an emission-control
failure found in the EMCON verification.

## Superseded by

None.

## Verification dependency

Stage 4 (the high-throughput IP path, where a WAN-reachable node is exercised)
and the map service stages. `TBR-MAP-01` selects the upstream source and the
cache policy; the EMCON gate is verified against the Status Aggregator's EMCON
state. The never-a-dependency invariant is verified by cutting WAN and confirming
the service still serves the store, which needs no hardware and can be exercised
on the bench.
