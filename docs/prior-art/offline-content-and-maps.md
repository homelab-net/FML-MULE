# Offline content and map inputs

**Evaluated:** 2026-09-11 against Kiwix tools `3.8.2` at
`f76e38bdc06b86b73ba8e84a5de234a0d6c3fa3d`, Kolibri `v0.19.5` at
`f7cafd40f5c339b0ffadc36aa8de10ea79a9175b`, a current ProtoMaps basemaps
snapshot at `4b5f6f806e4a5b2349632012e93fbf908f3a101e`, and a current PMTiles snapshot
at `182d5b3cfdc2f5a6adbc54630c612da2f6086bdd`. **Verdict:** make no new
runtime selection. Kiwix and Kolibri remain undecided service candidates;
retain ProtoMaps and PMTiles only as provisioning and format references.

## Boundary set by existing decisions

Project N.O.M.A.D. uses all four projects, but its intake retained only the
offline-content lifecycle pattern. FML evaluates each upstream separately so a
content service does not arrive through an unrelated management stack.

The map boundary is already narrower. `FML-ADR-073` selects one read-only
MBTiles file per mission, served as `z/x/y` behind ingress by Martin. It also
states that the program does not make maps. ProtoMaps basemaps and PMTiles can
inform an external provisioning toolchain, but this intake cannot replace the
selected on-node format or add a map-production workload to the MULE.

## Kiwix tools

Kiwix tools includes `kiwix-serve`, an HTTP server for one or more ZIM files.
It fits the offline-content pattern: the ZIM files and optional library XML are
provisioned artifacts, and the service can remain useful without WAN. It is not
an approved MULE service because GAP-02 has not selected a service-catalog
entry for general reference content.

The documented server default is TCP port 80 on all addresses. No application
authentication option appears in the documented command surface, so any MULE
profile would require a non-privileged port and the existing authenticated
ingress boundary. ZIM and library files can be mounted read-only; Kiwix owns no
separate durable application database in that narrow profile. External links
inside archived content still require the program's WAN and EMCON policy.

The source is GPL-3.0-or-later. `libkiwix` and `libzim` are separate required
dependencies, so the repository license alone is not a complete distribution
review. Release 3.8.2 was published on 2026-03-02, and the repository remained
active in September. GitHub listed no repository security advisory on the
evaluation date. No independent audit or complete SBOM was identified.

The exact artifact was not built or run. Upstream publishes multi-architecture
containers, but no image is adopted here; any later selection must resolve and
record an immutable digest, dependency licenses, ingress behavior and resource
use on the selected target.

## Kolibri

Kolibri is a complete offline learning platform, not a passive content server.
It manages facilities, users, roles, learning progress, content channels,
device-to-device synchronization and optional cloud synchronization. Those
features may be useful in another deployment, but adding them would expand the
MULE's service and durable-state scope and therefore belongs to GAP-02 and the
project owner.

The standard service listens on TCP 8080 unless configured otherwise and runs
as an ordinary service identity. Its `.kolibri` data tree is writable and
contains the main SQLite database, content databases, stored resources, logs,
configuration and backups. Upstream provides database backup and restore, but
warns that this mechanism restores one device rather than replicating state to
another device. A MULE deployment would need a complete state, identity,
retention and purge contract before selection.

The source is MIT licensed; bundled Python, JavaScript and content dependencies
still need their own review. Release 0.19.5 was published on 2026-07-13, and
the repository has a broad contributor base. CVE-2026-48053 describes an
unauthenticated server-side request forgery in versions through 0.19.3 and
declares 0.19.4 patched, so the evaluated 0.19.5 source is outside that range.
A separate 2024 GitHub Actions expression-injection advisory affected a
repository workflow rather than the shipped learning service. No deployment
SBOM or independent runtime audit was produced by this intake.

The exact release was not run. The remaining questions are whether a learning
platform is approved mission-service scope and, if so, which data and
authorization model governs it.

## ProtoMaps basemaps

ProtoMaps basemaps is a map-production and styling workspace. It combines an
OpenStreetMap-oriented build with browser styles and emits PMTiles content. It
is useful evidence for external provisioning, source attribution and style
packaging. It is not an on-node service and does not fit the selected MBTiles
runtime store without a separately approved conversion step.

No current GitHub release exists, so this intake pins the repository commit
observed on 2026-09-10 rather than presenting the old `2.1.0` tag as current.
The code is BSD-3-Clause and the map design is CC0. Produced OpenStreetMap
tilesets are ODbL and require visible attribution; other source datasets and
icons carry their own notices. That content-license chain is the material gate,
not the code license alone.

The repository is actively maintained but contributions are concentrated in
one principal account. GitHub listed no repository security advisory on the
evaluation date. No build, dependency scan, dataset audit or MULE resource
measurement was run. The retained reuse mode is pattern-only: an authorized
external provisioning process may use the documented attribution and build
patterns, while the MULE consumes only the approved mission artifact.

## PMTiles

PMTiles defines a single-file, range-readable tile archive and ships reference
implementations for several languages and serverless environments. Version 3
places a fixed header and root directory at the beginning of the file so a
client can locate tile ranges without a database server. That is useful format
prior art, but `FML-ADR-073` selected MBTiles for the MULE's provisioned store.

The repository has no tags or GitHub releases, so the evaluated artifact is the
immutable 2026-08-19 main-branch snapshot. The reference implementations are
BSD-3-Clause, the specification is CC0-1.0, the bundled Python conversion work
also contains MIT-licensed material, and sample archives carry ODbL or
CC-BY-4.0 terms. A content artifact therefore retains its own license and
attribution regardless of the format license.

PMTiles itself opens no port and owns no service identity. A chosen reader,
object store or serverless example supplies the network, privilege, cache and
update behavior. GitHub listed no repository security advisory on the
evaluation date, but each language implementation has a separate dependency
surface. No implementation, sample archive or conversion path was run.

The retained reuse mode is pattern-only. Replacing MBTiles would require a
superseding ADR, while using PMTiles solely in an external provisioning pipeline
would still require deterministic conversion and content-license evidence.

## Sources

- [Pinned Kiwix tools README](https://github.com/kiwix/kiwix-tools/blob/f76e38bdc06b86b73ba8e84a5de234a0d6c3fa3d/README.md)
- [Pinned Kiwix server documentation](https://github.com/kiwix/kiwix-tools/blob/f76e38bdc06b86b73ba8e84a5de234a0d6c3fa3d/docs/kiwix-serve.rst)
- [Kiwix release history](https://github.com/kiwix/kiwix-tools/releases)
- [Pinned Kolibri license](https://github.com/learningequality/kolibri/blob/f7cafd40f5c339b0ffadc36aa8de10ea79a9175b/LICENSE)
- [Kolibri data layout and provisioning](https://kolibri.readthedocs.io/en/latest/manage/provision.html)
- [Kolibri backup and restore](https://kolibri.readthedocs.io/en/latest/manage/command_line.html)
- [Kolibri SSRF advisory](https://github.com/learningequality/kolibri/security/advisories/GHSA-4mj9-pf4r-cqrc)
- [Pinned ProtoMaps basemaps README](https://github.com/protomaps/basemaps/blob/4b5f6f806e4a5b2349632012e93fbf908f3a101e/README.md)
- [Pinned ProtoMaps data licenses](https://github.com/protomaps/basemaps/blob/4b5f6f806e4a5b2349632012e93fbf908f3a101e/LICENSE_DATA.md)
- [Pinned PMTiles license](https://github.com/protomaps/PMTiles/blob/182d5b3cfdc2f5a6adbc54630c612da2f6086bdd/LICENSE)
- [Pinned PMTiles REUSE inventory](https://github.com/protomaps/PMTiles/blob/182d5b3cfdc2f5a6adbc54630c612da2f6086bdd/REUSE.toml)
- [Pinned PMTiles version 3 specification](https://github.com/protomaps/PMTiles/blob/182d5b3cfdc2f5a6adbc54630c612da2f6086bdd/spec/v3/spec.md)
- [Selected MULE map-store decision](../adr/FML-ADR-073-the-local-tile-store-is-per-mission-mbtiles-served-as-z-x-y-behind-ingress.md)
