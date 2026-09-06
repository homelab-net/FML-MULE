# Map, tile and cache state is not TAK-server state

**Trade:** `TBR-TAK-01`.
**Date:** 2026-09-05.
**Taken by:** Cameron Zobrist, on the lab development machine.
**Status of this artifact:** classification, resolving closure item 6. It rests on
one empirical finding (OpenTAKServer serves no tiles) and the program's map
service architecture; it observes no ATAK client, and does not need to.

## What this supplies

The closure evidence lists "**local map, tile and cache state whose loss would be
operationally visible after failover**", and SAD section 30.2 adds a "map-cache"
test. `2026-08-31-datasync-and-package-workflows.md` deferred this as "**blocked
on a real ATAK client**". This artifact resolves it, because the gate asks for
**classification** -- "every item is classified into a CONOPS section 26 class
with a stated justification" -- not for an observation of a client's cache. The
classification does not need a client; it needs to establish *where the state
lives*, and that is now known.

## The finding it rests on

`2026-08-31-datasync-and-package-workflows.md` recorded that **OpenTAKServer
handles no map tiles at all** -- a grep of the package for tile, WMTS, XYZ,
MBTiles or map-cache handling returns only icon (symbology) code. The
`TBR-MAP-01` work confirmed the positive side: the tile source is the node's own
**S1 map service** (`services/map/`), a service distinct from the TAK server, and
a real EUD rendered a map from it with the TAK server irrelevant to the path
(`docs/evidence/TBR-MAP-01/2026-09-04-real-eud-offline-map-and-storage.md`).

## Classification

Map, tile and cache state resolves into three things, none of which is
TAK-server mission-critical state:

- **The TAK server's own map/tile/cache state: none.** OpenTAKServer stores no
  tiles, so there is nothing in the TAK server to classify here. For the TAK
  state boundary this item is **not present**.
- **The EUD client tile cache: CONOPS 26.3, reconstructable.** The tiles a client
  has rendered are cached **on the device**, keyed by position
  (`docs/evidence/TBR-MAP-01/`), and are re-fetched from the source on demand.
  Loss is recovered by re-fetching while a source is reachable. It is **client**
  state, not server state, and it is reconstructable by definition.
- **The node's tile repository: a separate S1 service, `TBR-MAP-01`.** The
  stored tiles are the S1 map service's own persistent state (CONOPS 9.2), with
  its own availability tier above the S2 TAK server. Its persistence and
  provisioning are `TBR-MAP-01` and `services/map/serving-across-the-mesh.md`,
  not this trade.

## The consequence for the boundary

**A TAK-server failover does not affect map, tile or cache state**, because maps
do not come from the TAK server. An EUD keeps its map across a TAK failover: the
tiles are cached on the device and sourced from the S1 map service, which is
designed to remain available when the S2 TAK server is gone. So:

- no map/tile/cache state enters the **mission-critical persistent** set that
  `TBR-HA-01` must carry across a TAK failover;
- the operational-visibility-after-failover concern the closure item raises is,
  for maps, answered by the tier split: map availability is the **S1 map
  service's** responsibility, not the TAK HA mechanism's.

This closes closure item 6 by classification. It is consistent with the whole
trade's result: the mission-critical TAK set is the relational state plus the
out-of-SQL durable set (`config.yml`, `ca/`, `uploads/`), and maps are not in it.

## What this does not establish

- **It classifies; it does not test a client's cache eviction.** Whether a
  specific ATAK/iTAK build evicts or retains tiles under memory pressure is a
  client-behaviour question outside the state boundary, and not what the gate
  asks.
- **It is not a statement about S1 map availability.** That maps survive TAK
  failover is a consequence of the tier split; the S1 map service's own
  availability under partition is `TBR-MAP-01` and `services/map/`, exercised in
  that trade's evidence, not here.

Nothing real: no deployment location, member identity, callsign, or credential.
See `SECURITY.md`.
