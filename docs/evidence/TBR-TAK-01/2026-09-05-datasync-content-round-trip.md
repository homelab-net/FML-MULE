# The DataSync content round-trip through `mission_content`

**Trade:** `TBR-TAK-01`.
**Date:** 2026-09-05.
**Taken by:** Cameron Zobrist, on the lab development machine.
**Status of this artifact:** `SIMULATED`. The containerised OTS stack
(`fml-ots` + PostgreSQL), the Marti API over `curl`, a synthetic client cert, and
a synthetic EUD. No hardware.

## What this supplies

The one empirical item `2026-08-31-datasync-and-package-workflows.md` left open:
**a content round-trip through `mission_content`**, the DataSync content store,
as distinct from `data_packages`, the file-share store. That artifact showed the
two are different tables keyed by different hashes and that a `data_packages`
hash cannot be attached to a mission; this runs the DataSync content path end to
end and attaches its result to a mission. SAD section 14.2 requires the actual
workflow against the backend, not an ORM claim; this runs against PostgreSQL.

## The DataSync content path is `/Marti/sync/upload`, and it needs a certificate

`upload_content()` (`blueprints/marti_api/mission_marti_api.py`) writes a
**`MissionContent`** row, where `/Marti/sync/missionupload` writes a
`DataPackage`. It calls `verify_client_cert()`, which reads the `X-Ssl-Cert`
header (`OTS_SSL_CERT_HEADER`) and validates the PEM against `ca.pem`. As
`2026-08-31-mission-api-and-the-header-that-authenticates.md` recorded, that
header authenticates on the certificate alone with no proof of possession, so the
test supplies a URL-encoded client cert **signed by the on-disk CA** (whose key
opened with the default password `atakatak`, per
`2026-08-31-certificate-enrollment.md`). The submitter is taken from the cert
common name; the identity used here is the synthetic `CN=fml-datasync-test`.

## The round-trip

```text
upload   POST /Marti/sync/upload?name=fml-ds-test.txt&creatorUid=<synthetic>
         X-Ssl-Cert: <CA-signed test cert>, 57-byte text/plain body
         HTTP 200  Hash=42265917...  PrimaryKey=1  SubmissionUser=fml-datasync-test

db       SELECT ... FROM mission_content WHERE hash=42265917...
         -> 1 row: fml-ds-test.txt | fml-datasync-test | text/plain
         SELECT count(*) FROM data_packages WHERE hash=42265917...
         -> 0   (it is DataSync content, NOT the file-share store)

retrieve GET /Marti/sync/content?hash=42265917...
         HTTP 200, 57 bytes, md5 matches the uploaded bytes exactly
```

The content uploaded through the DataSync content path lands in `mission_content`
and nowhere in `data_packages`, and it retrieves byte-identical. This confirms
the `2026-08-31` decomposition's placement of `mission_content` in CONOPS class
26.2, and confirms it is a store *distinct* from `data_packages` -- the finding
that decomposition flagged and this test was written to settle.

## Attaching content to a mission works, once the hash is DataSync content

With the hash now present in `MissionContent`, the attach that failed in the
prior artifact (with a `data_packages` hash) succeeds:

```text
attach   PUT /Marti/api/missions/FMLDS3/contents  {"hashes":["42265917..."]}
         HTTP 200
db       mission_content_mission -> row (mission FMLDS3 -> content id 1)
         mission change log       -> ADD_CONTENT change recorded
```

So the DataSync mission-content lifecycle is complete: content into
`mission_content`, linked to a mission through `mission_content_mission`, and the
change recorded in the ordered mission change log.

## A finding, reproduced and pinned

Creating the mission returned **HTTP 500** -- `'NoneType' object has no attribute
'id'` -- **while still creating a usable mission** (the subsequent attach found
it and returned the full mission). This reproduces
`2026-08-31-mission-api-and-the-header-that-authenticates.md`'s "the API reported
failure after creating the mission", and pins the cause: `put_mission()` looks
up a **user** by the certificate common name and dereferences it, so a cert whose
CN is not a registered user 500s after the row is written. It is upstream default
behaviour, recorded for `services/ingress/` alongside the other header findings.

## Where the trade now stands

Every empirical item in the closure evidence is now performed:
durable-queue inspection, the different-node restore, and all four workflow tests
(mission API, certificate enrollment, mission-package upload, and -- here --
DataSync content). What remains for closure is not another workflow:

- **The map/tile/cache item** (closure item 6) is answerable by classification
  rather than an ATAK client: OpenTAKServer holds no map/tile state (it serves no
  tiles), so that state is the EUD's own client cache (26.3, reconstructable by
  re-fetch) and the separate **S1 map service** store (`TBR-MAP-01`,
  `services/map/`), not TAK-server state. It is written up separately.
- **The durable set's partition and rejoin behaviour** is to be exercised on the
  bench before acceptance (Program Owner's call, 2026-09-05), beyond the gate's
  "described".
- **The named owner's acceptance** and the resulting ADR.

## What this does not establish

- **No ATAK client.** Driven by `curl` with a synthetic cert; a real client's
  DataSync sync behaviour (subscription, change feed consumption) is not
  exercised.
- **One upload, one mission, empty of prior test state.** No volume, no
  concurrent DataSync, no failover during a sync.
- **The cert authenticates on public data.** The test relies on the recorded
  `X-Ssl-Cert` weakness; it is a state-study convenience here and a defect for
  `services/ingress/` to close, not a property to build on.

Nothing real: the client cert CN, the EUD used as `creatorUid`, the mission and
the payload are all synthetic bench values. No member identity, callsign, or
credential is recorded. See `SECURITY.md`.
