---
id: TBR-MAP-01
title: Which local tile store and server serves maps to an EUD offline
status: OPEN
owner: Cameron Zobrist
area: MAP
priority: 99
function-owner: Platform + TAK
critical-path: false
depends-on: []
feeds: []
requires-hardware: partly
evidence: docs/evidence/TBR-MAP-01/
adr: []
target-date: TBD-SRR
---

# TBR-MAP-01 Which local tile store and server serves maps to an EUD offline

**Source:** CONOPS section 9.2 (S1 "selected cached maps"), roadmap item 4.4,
`services/map/README.md`.

## Question

What tile store format and tile server does the node use to serve `z/x/y` map
tiles to an EUD with no external network?

## Why it matters

CONOPS section 9.2 makes a local map source an **S1** service, above the TAK
server's S2, so an operator has a map when everything external is gone. Nothing
in `services/` provides it. The service outline in `services/map/README.md`
commits to one interface -- a `z/x/y` tile endpoint and an ATAK map-source
definition for it -- and leaves the mechanism behind that interface to this
trade.

The choice sets what the node carries (the store is the largest static asset it
is likely to hold), what competes with the routing daemon for the one compute
element, and whether the imagery falls under `TBR-SEC-01`'s at-rest posture.

## Options

- **`MBTiles` plus a single-binary tile server.** One SQLite file of tiles and a
  small server that exposes `z/x/y`. Ships and diffs as one file, rootless,
  light. Right if a maintained single-binary server runs on Debian ARM64.
- **A pre-rendered `z/x/y` directory served statically.** No tile server at all,
  just the reverse proxy serving files. Simplest and most robust; costs disk
  and inodes for a large tile tree, and is awkward to update.
- **`GeoPackage` plus a server that reads it.** Right only if the mapping
  toolchain already produces GeoPackage and MBTiles is a worse fit.
- **A heavier map server** (vector tiles, on-node styling). Right only if
  pre-rendered raster tiles prove inadequate, which v1 does not assume.

## Closure evidence

For the selected mechanism: resident memory and CPU while serving a
representative view, on the CM4, alongside the service-host load
(`TBR-COMP-01`); the store size for a representative area and zoom range; a
demonstrated `z/x/y` fetch and an ATAK map-source definition that renders it;
and a statement of whether the imagery provisioned is public or sensitive,
which decides the `TBR-SEC-01` interaction. Committed under
`docs/evidence/TBR-MAP-01/`.

## Closure gate

A selection with the measured basis above, accepted by the named owner, and an
ADR entered for the chosen mechanism. The gate is a comparison against store
size, footprint and update burden, not a single threshold.

The acceptance demonstration -- an EUD rendering a map from the node offline --
needs a device and is Stage 4/8; the selection and footprint work do not.

## Dependencies

- **Depends on:** none. The selection can start today.
- **Feeds:** the `services/map/` catalog entry and Quadlet, and EUD
  provisioning where the map-source definition is delivered.
- **Related decisions:** `FML-ADR-029` (rootless containers, digest-pinned),
  `FML-ADR-031` (ingress), `TBR-COMP-01` (budget), `TBR-SEC-01` (at-rest if
  sensitive), `TBR-ID-01` (how the map-source definition reaches the EUD).
- **Validating stage:** Stage 4, field demo Stage 8.
- **Requires hardware:** `partly`. The store and server comparison runs on any
  Debian ARM64; the offline-render acceptance needs an EUD.

## Frontmatter notes

`priority` is 99 because this trade postdates the SAD section 30.2 register;
`critical-path` is `false` on the same grounds, not a judgement of importance --
it is a CONOPS S1 capability with no coverage. `owner` is a named individual
because the trade was raised inside the repository.
