# The mission-package and DataSync workflows

**Trade:** `TBR-TAK-01`.
**Date:** 2026-08-31.
**Taken by:** Cameron Zobrist, on the lab development machine.
**Status of this artifact:** `SIMULATED`. The containerised stack, a synthetic
PyTAK client, and the Marti API over `curl`.

## What this supplies

Two of the four workflow tests SAD section 30.2 names in this trade's closure
evidence: **mission package** and **DataSync**. The certificate and mission-API
tests are in earlier artifacts. The map-cache question is addressed at the end
and is blocked, not done.

SAD section 14.2 requires the actual MULE TAK workflows to be tested against the
selected backend, not asserted from an ORM. These run against PostgreSQL.

## Mission-package upload works end to end

`POST /Marti/sync/missionupload` with a file, authenticated with the default
`administrator` credential:

```text
upload            HTTP 200
data_packages row pkg.zip | dd33be1a... | size 527
on disk           /data/uploads/dd33be1a...zip
retrieve          GET /Marti/sync/content?hash=...  HTTP 200, 527 bytes
round-trip        valid Zip archive, original 42-byte payload inside
```

The package uploads, lands in `data_packages` and on disk under
`OTS_DATA_FOLDER/uploads/`, and is retrievable by hash. That confirms the
26.2/26.1 classification of `data_packages` and confirms `uploads/` as a durable
location outside the database, which `2026-08-31-durable-state-outside-the-database.md`
predicted and which any restore must carry.

**Two behaviours worth recording.** The server **re-wraps and re-hashes**: the
uploaded `pkg.txt` became `pkg.zip` and the stored hash is the server's zip hash,
not the hash of the bytes sent. So a client cannot assume the content hash it
computed is the hash the server stores. And `submission_user` was null on the
row even though the upload was authenticated, which is the same unbound-identity
pattern the certificate artifact records.

## DataSync mission content is a separate store, confirmed

A mission was created and a data package was attached to it:

```text
create mission FMLDS2 (creatorUid = a registered EUD)   HTTP 201
attach data-package hash to mission contents            HTTP 404
  "No such file with hash dd33be1a..."
```

The attach failed although `data_packages` holds that hash and the file is on
disk. Reading the endpoint shows why, and it is a state-study finding rather
than a bug:

```text
/Marti/api/missions/<name>/contents  resolves hashes against MissionContent
/Marti/sync/missionupload            writes DataPackage
```

**`data_packages` and `mission_content` are two different stores keyed by two
different hashes.** A data package uploaded through `/Marti/sync` is not mission
DataSync content and cannot be attached to a mission by its package hash; DataSync
content is its own table populated through the mission-content path.

The decomposition in `2026-08-31-relational-state-decomposed-into-conops-classes.md`
placed both in 26.2, which is correct, but treated them as near-equivalent. They
are not: a restore or a classification that conflates them will mis-handle one.
`mission_content` is DataSync's own content; `data_packages` is the file-share.
Both are 26.2, for different reasons.

**Mission creation and the change log work.** `FMLDS2` was created (`HTTP 201`),
`missions` gained a row and `mission_changes` gained one, so the DataSync mission
lifecycle and its ordered change record function. What was not exercised is a
content round-trip *through* the DataSync content path, which populates
`mission_content`; that is the remaining sliver of this test.

## The map-cache question is blocked on a real client

Outstanding item 6 asks what a client observes after failover when the tile
source is unreachable. **OpenTAKServer does not handle map tiles at all.** A grep
of the package for tile, WMTS, XYZ, MBTiles or map-cache handling returns only
icon code, which is symbology, not map tiles. Tiles are cached by the **ATAK
client**, not the server.

So this item cannot be answered with PyTAK or the API: it needs a tile-rendering
client observing its own cache across a server failover. It is **blocked on a
real ATAK client**, which is a device, and is recorded as such rather than
answered with a contrived substitute. That is the honest result: the question is
about client behaviour, and there is no client here that renders a map.

**Do not read this as "MULE cannot serve maps".** Two different things are being
distinguished. Device-side tile *caching* is an ATAK function, and that is what
this item asks about. Serving maps *locally* -- being the tile source -- is a
separate capability that OpenTAKServer does not provide and is not ATAK-only.
CONOPS section 9.2 makes "selected cached maps" a MULE **S1** local mission
service, a higher availability tier than the TAK server's S2. A local
map/tile service on the node is therefore a real and CONOPS-required capability;
it is roadmap item 4.4 and is not part of this trade.

## Where the trade now stands

Of the six empirical items the 2026-08-27 analysis listed, this closes the
package and DataSync workflow tests to the extent no hardware can take them
further, leaving:

- the DataSync content round-trip through `mission_content` (a sliver, no
  hardware, not done here);
- the map-cache question (blocked on an ATAK client).

Everything the gate's classification half requires exists. What remains is that
one sliver, the client-blocked cache question, and the named owner's acceptance.

## What this does not establish

**No ATAK client.** Every workflow was driven by `curl` and PyTAK. A real client
performs DataSync content sync, subscription and tile caching that these do not,
and the standing caveat on the queue findings applies here too.

**The re-hash and null-user behaviours were observed, not chased.** Whether a
real client's upload populates `submission_user`, and whether it relies on the
server's re-hash, are client-flow questions not answered here.

**One upload, one mission, one machine, empty database.** No volume, no
concurrent DataSync, no failover during a sync.
