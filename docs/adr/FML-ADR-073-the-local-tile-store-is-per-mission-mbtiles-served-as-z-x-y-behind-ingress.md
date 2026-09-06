---
id: FML-ADR-073
title: The local tile store is per-mission MBTiles served as z/x/y behind ingress
status: PROPOSED
date: 2026-09-06
supersedes: none
superseded-by: none
trades: [TBR-MAP-01]
verification: Stage 4
---

# FML-ADR-073 The local tile store is per-mission MBTiles served as z/x/y behind ingress

**Source of rationale:** `TBR-MAP-01`, `services/map/` (the service outline,
`serving-across-the-mesh.md`, `filling-the-store-from-wan.md`,
`hot-swappable-mission-stores.md`), the `docs/evidence/TBR-MAP-01/` evidence,
`FML-ADR-031` (ingress), `FML-ADR-029` (rootless), `FML-ADR-072` (WAN cache).

## Context

`TBR-MAP-01` selects the local tile store and its server. The **interface** --
a `z/x/y` endpoint and an ATAK/iTAK map-source definition -- is committed and
demonstrated: a real iTAK EUD rendered a high-detail map from the node with WAN
cut, tiles crossed the mesh from a storage node, and the WAN and hot-swap tiers
are designed. What is unselected is the **on-disk store format** and the
**server**. The CM4 footprint (`TBR-COMP-01`) and the store size from real
imagery are hardware-and-content questions, not this one; this ADR settles the
format and server, which are software.

Whatever is chosen has to satisfy the serving model already decided: served as
`z/x/y` behind ingress by name (`FML-ADR-031`); sitting behind a mount point so a
mission store can be hot-swapped (`hot-swappable-mission-stores.md`); with the
WAN-fetched tiles held in a **distinct, ephemeral** tier (`FML-ADR-072`). Two
store forms are credible, and the Program Owner asked for both to be laid out.

- **A `z/x/y` directory tree** of pre-rendered tiles, served directly by `nginx`
  as static files. It is the simplest option and exactly what every bench ran
  (the real-EUD render, the mesh serve, the WAN cache). Its cost is the shape of
  the artifact: a mission's tree is on the order of millions of small files, slow
  to copy onto a drive, heavy on inodes, awkward to verify for integrity, and
  slow to provision.
- **MBTiles, one SQLite file per mission.** It is the standard offline tile
  container the mapping toolchain (`gdal`, `mbutil`, and the tile pipelines)
  already produces, so provisioning is one file. That one file is atomic to ship,
  diff and swap, and it carries its own metadata -- name, bounds, min and max
  zoom -- which is exactly the per-mission manifest the hot-swap design asked for.
  Its cost is the server: reading MBTiles and exposing `z/x/y` is not plain
  `nginx`, it is a tile server that reads SQLite.

## Decision

The provisioned map store **shall** be **MBTiles, one file per mission**, served
as `z/x/y` behind ingress by a rootless tile server that reads it **read-only**.
The WAN ephemeral cache (`FML-ADR-072`) **shall** be a separate `z/x/y` directory
tree, write-through and expiring, kept distinct from the provisioned MBTiles. A
mission store's manifest **is** its MBTiles metadata table; no separate manifest
file is introduced.

The runner-up -- a `z/x/y` directory served by `nginx` -- is recorded in Fallback
below, because the served `z/x/y` interface is identical either way and nothing
downstream depends on the choice.

## Status

`PROPOSED`. It recommends MBTiles over the directory tree and states why; the
named owner decides on this PR -- accept, or switch the Decision to the directory
form. Even on acceptance, `TBR-MAP-01` stays `OPEN`: this settles the format and
the server class, while the CM4 footprint (`TBR-COMP-01`) and a USB2
random-read-latency check on real imagery remain, and the trade closes only when
those exist and the named owner accepts them.

## Consequences

- **The server is a small MBTiles-to-`z/x/y` tile server** -- a single rootless
  binary pinned by digest (`FML-ADR-029`), reached by name through ingress
  (`FML-ADR-031`). It should be an existing tool rather than a new one
  (`AGENTS.md` rule 6); a single-binary MBTiles server of the `mbtileserver`
  class is the shape. Which exact binary, and whether the mesh-peer and WAN
  source order wrap it as a proxy or are folded into one map-service process, is
  implementation left to the catalog work, not fixed here.
- **The node holds two tiers, by construction.** A read-only MBTiles file per
  mission (provisioned, hot-swappable) and a `z/x/y` cache directory (ephemeral,
  written through from WAN fetches, expiring). Writing into MBTiles would be
  SQLite writes under a lock; keeping the mutable tier as files is why the WAN
  cache is a directory, not the MBTiles.
- **Hot-swap is one file.** A mission USB carries one `.mbtiles`; the manifest is
  its metadata; a swap is mounting the new file at the store path
  (`hot-swappable-mission-stores.md`).
- **Provisioning stays upstream.** The program does not make maps
  (`docs/NON-GOALS.md`); the toolchain produces the MBTiles, from a permitted
  source (`FML-ADR-072`, `TBR-SEC-01`).
- **A catalog entry and a Quadlet** with the server image pinned by digest are
  now the buildable next step, gated on a `services/catalog/` decision.

## Accepted cost

MBTiles needs a SQLite-reading tile server, not the plain `nginx` static path the
benches already proved rootless and pinned. That is one more moving part than a
directory of files, and someone will later argue the directory form was simpler.
The cost is accepted for the one-file-per-mission provisioning, the atomic
hot-swap, and the built-in manifest -- which the directory form cannot match --
and it is bounded by the Fallback, which reverts to the proven static path with
no downstream change.

## Fallback

The runner-up: a `z/x/y` directory tree served by `nginx` static, exactly as the
bench evidence ran it. Take it if the MBTiles server cannot be sourced rootless
and digest-pinned, or if its random-read latency from a USB2 SSD proves
inadequate for tile serving. Because the served interface is `z/x/y` in both
cases, the switch is a superseding ADR that changes the store and server and
**nothing else** -- not ATAK's map source, not the mesh proxy, not ingress.

## Superseded by

None.

## Verification dependency

Stage 4 and the map service stages. The `z/x/y` interface and a real-EUD render
are already evidenced (`docs/evidence/TBR-MAP-01/2026-09-04-real-eud-offline-map-and-storage.md`).
What this decision still needs before `TBR-MAP-01` closes: the tile server as a
rootless, digest-pinned `catalog/` entry and `quadlets/` unit; the CM4 footprint
of that server under load (`TBR-COMP-01`); and a read-latency check of MBTiles on
a USB2 SSD against a real-imagery store.
