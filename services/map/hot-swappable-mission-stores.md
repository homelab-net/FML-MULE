# Hot-swappable mission map stores

Two questions this answers: does an EUD end up pointed at a USB drive that may
not be there, and how does a node serve a different mission's maps from a
swappable drive. It is design, not code -- the tile server itself is `TBR-MAP-01`
and gated on a `services/catalog/` decision -- but the shape below is what that
implementation has to satisfy.

## The EUD never sees the USB

An EUD's map source is a **stable URL naming its own MULE**, resolved by the
node's local DNS and reverse proxy (`FML-ADR-031`) -- for example
`http://<node>/tiles/{z}/{x}/{y}.jpg`. The MULE's map **service** is what reads
the store on disk; the EUD only ever speaks to the service.

So a drive that is present, absent, or swapped is **entirely behind the
service**, invisible to the EUD -- the same "invisible to the EUD" property
`serving-across-the-mesh.md` relies on for the mesh and WAN tiers. The EUD does
not have a living path to a USB that may vanish; it has a living path to its
MULE, which is always there. A store the node cannot read becomes a served
**miss** (a gray tile), never a broken client path.

## The store is a mount point, not a device

The tile server roots at a **stable mount point** -- a path, not a device or a
partition. `FML-ADR-073` makes the provisioned store per-mission **MBTiles**, so
the mount point holds one `.mbtiles` file, and the server reads it; a mission map
drive **auto-mounts there by filesystem label**: any drive carrying the agreed
label mounts at the same path, driven by a udev rule or a systemd mount unit in
the OS image (`os/`). Then:

- **drive present** -> the mount point holds that mission's store -> the server
  serves from it;
- **drive absent** -> the mount point holds the node's baseline store (an eMMC
  MBTiles) or nothing -> the server serves the baseline, or a miss -- never an
  error to the EUD.

Because the map store is separate from the node's operational storage (the eMMC
and whatever `TBR-COMP-01` puts PostgreSQL on), pulling the map drive touches
neither the TAK service nor the node's own state.

## Hot-swap

Pull mission A's drive, insert mission B's: the mount point now holds B's
`.mbtiles`, and the tile server serves B on the next request. **No EUD change, no
source-URL change, no service restart** for a server that reads the store at the
mount point.

It is safe because the map store is **read-only**: a drive pulled mid-serve
yields `ENOENT` for the tiles it held, which the service turns into a gray tile,
never a corrupt write or a crash. An explicit unmount-before-pull is still
cleaner, and the operator I/O the BOM carries -- the sealed button and the OLED --
is the natural place to drive and confirm it.

## The wrinkle: the EUD's own cache

The EUD caches tiles **by position, not by source** (the 2026-09-04 finding,
`docs/evidence/TBR-MAP-01/2026-09-04-real-eud-offline-map-and-storage.md`). After
a swap, an area the EUD already viewed under mission A may still render A's cached
tiles until the EUD re-fetches. Two handles, and choosing between them is a
`TBR-MAP-01` policy call:

- **Accept it.** The EUD re-fetches as the operator pans or zooms into fresh
  ground, and two missions rarely occupy the same ground at the same zoom.
- **Force it.** Bump a version segment in the served path on swap
  (`/v<n>/{z}/{x}/{y}`) so the EUD treats it as a new source and re-fetches -- the
  same lever that forced a refetch in the 2026-09-04 evidence, where a changed
  path refetched and a same-path swap did not.

## Mission-scoped drives

A mission map drive is one mission's map cache, and it can carry a small
**manifest** naming the mission, the area, and the zoom range it holds. That lets
the node -- and the operator OLED -- state *which* mission's maps are loaded, so a
wrong or blank drive is visible rather than silently serving the wrong ground.
This aligns the map drive with the **mission package** (`FML-ADR-063` already
carries a deployment's configuration in the mission package): changing the
mission changes both, and the manifest is where the drive says which mission it
belongs to.

## Decided, and open

**Decided (cited):** the EUD reaches the map by name through ingress
(`FML-ADR-031`); the store sits behind the service at a mount point, not on the
EUD's path; the map store is read-only, so a swap is safe and a missing store is
a miss.

**Open (this design surfaces, does not decide):** the mount mechanism and label
(udev versus a systemd mount unit, in `os/`); the version-on-swap policy for the
EUD cache; the manifest format and its tie to the mission package; and, as ever,
the tile-store format and server, which are `TBR-MAP-01`. Nothing is built here;
implementation waits on `TBR-MAP-01` and a `services/catalog/` decision.

See `README.md` for the service outline, `serving-across-the-mesh.md` for the
local-mesh source order, and `filling-the-store-from-wan.md` for the WAN tier and
the full EUD-cache-to-WAN escalation this store sits inside.
