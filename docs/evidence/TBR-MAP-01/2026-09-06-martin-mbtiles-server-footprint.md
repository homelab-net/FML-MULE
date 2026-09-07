# Martin MBTiles server: selection and software-half footprint

**Tier:** `SIMULATED`. An x86 bench, a synthetic store, and loopback load; it
measures no CM4 figure and no radio-limited serve rate.

**Date:** 2026-09-06. **Node:** development machine (see `docs/dev-machine.md`),
`6.12.105+deb13-amd64 x86_64`, rootless `podman`. **Image:**
`ghcr.io/maplibre/martin@sha256:84f406ac96839aad3ea06ddaa68ef7617ed55305c21038c182d59f100e48dd6d`
(resolved from the project's `latest` tag at `ghcr.io/maplibre/martin` on
2026-09-06). **Procedure:**
`test/bench/map-server-footprint.sh`. **Taken by:** Cameron Zobrist.

## What this settles

`FML-ADR-073` selects the store as per-mission MBTiles served as `z/x/y` and
leaves *which exact binary* to the catalog work. `services/catalog/` will not
accept an entry whose resource envelope is estimated -- "an entry with an
estimated envelope has not been evaluated." Both the 2026-09-04 interface bench
and the mesh bench served tiles from an ad-hoc `python3` process, which selects
no server and sizes nothing. This selects the server and measures it.

## The selection: Martin, and why not the alternatives

The criteria are `FML-ADR-029` (rootless, digest-pinned), `AGENTS.md` rule 6 (an
existing maintained tool, not a new one), and the CM4 target: **arm64**.

| Candidate | arm64 image | Fit | Verdict |
| --- | --- | --- | --- |
| **`martin`** (MapLibre) | **yes** (official amd64+arm64) | single Rust binary; reads MBTiles read-only; serves `z/x/y`; base-path prefix for ingress; actively maintained | **selected** |
| `mbtileserver` (the class `FML-ADR-073` named) | **no multi-arch manifest** | purpose-built for MBTiles→`z/x/y`, but cannot be pinned for the CM4 without building a new artifact | rejected: no arm64 pin, against rule 6 |
| `tileserver-gl-light` (MapTiler) | yes | Node.js GL **renderer**; on-node rendering is a stated v1 non-goal; heavier | rejected: renderer, not a tile server; footprint |

`mbtileserver` was the name in the ADR's "`mbtileserver` class"; it turns out its
published image is single-arch, so on the arm64 CM4 it is disqualified. Martin is
the same class (single binary, reads MBTiles, serves `z/x/y`) with an arm64 image,
which is why the ADR left the exact binary to this step.

## What it demonstrates

Martin, run rootless and pinned by digest with the `.mbtiles` mounted read-only,
auto-discovered the store as a source and served the `z/x/y` contract:

```text
GET /mission/0/0/0   -> 200 image/png 270 pngsig=True
GET /mission/3/4/5   -> 200 image/png 761 pngsig=True
GET /mission/6/10/20 -> 200 image/png 761 pngsig=True
GET /mission/6/63/63 -> 200 image/png 762 pngsig=True
```

Under 8 concurrent workers fetching random `z/x/y` across the zoom range for 20 s
(loopback):

```text
run 1: requests=75236  errors=0  rate=3762/s  lat p50=2.0ms p95=3.4ms  peak 27.6 MB
run 2: requests=74792  errors=0  rate=3740/s  lat p50=2.0ms p95=3.5ms  peak 29.8 MB
idle mem: ~8.5 MB
```

**The measured software-half envelope: idle RSS ~8.5 MB, peak RSS ~28 MB (27-30 MB
across runs) under sustained load**, zero errors, tile latency p50 2.0 ms / p95
3.5 ms. This is the
"read-mostly and light" property `services/map/README.md` predicted, now a
measurement rather than a hope, and it is the figure a catalog entry's
resource-envelope field records for the software half.

One footprint fact cuts the other way: the **image is ~650 MB at rest** (Rust with
PostGIS/PMTiles support compiled in). That is disk, not RAM, and it is the largest
single cost of the choice; it is recorded so the catalog and `TBR-CARRIER-01`
capacity accounting carry it.

## What this is not

- **Not the CM4 footprint.** x86 only -- the software half. The arm64/CM4 memory
  and CPU under load are `TBR-COMP-01`'s hardware item and stay open. This
  selects no host.
- **Not CPU-sized.** `podman stats` CPU% on this host reads as cumulative, not a
  per-interval figure, so no CPU envelope is claimed; the definitive CPU-under-load
  number is the CM4 item above. RSS is the reported figure.
- **Not real imagery, and not a USB2 read-latency check.** The store is a small
  synthetic MBTiles (deterministic PNG per `z/x/y`, one colour, no imagery, no
  third-party tiles). Martin queries SQLite per tile rather than loading the file,
  so RSS is expected to stay bounded as the store grows, but a real-imagery store
  on a USB2 SSD is a separate `FML-ADR-073` open item, not this.
- **Not a serve rate.** Load is loopback HTTP; the request rate is server-side
  capacity, not the EUD access point or a radio-limited mesh serve.
- **No imagery or third-party data is committed.** The store is generated per run
  and deleted on exit. See `SECURITY.md`.

## What this unblocks

The catalog gate's hard requirement -- a *measured* resource envelope -- is met
for the software half. With the server selected and pinned, a `services/catalog/`
entry and a `services/quadlets/` unit are now buildable rather than blocked. What
still stands between here and `TBR-MAP-01` closure is in the trade's **Closure
gate**: the CM4 footprint (`TBR-COMP-01`), and the USB2 read-latency check on a
real-imagery store from a permitted source with the `TBR-SEC-01` call.
