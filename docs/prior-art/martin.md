# Martin

**Evaluated:** 2026-09-10 at release `martin-v1.16.1`, commit
`434782d95c08933bf2558135d2a7bac5bfb39274`. **Verdict:** adopt the already
selected Martin tile server within the narrow `FML-ADR-073` profile; this intake
does not widen its role.

## Fit

Martin is a Rust tile server supporting PostgreSQL/PostGIS and local tile files,
including MBTiles. FML's existing `TBR-MAP-01` evidence selected Martin as the
single-binary server for one read-only, per-mission MBTiles store behind ingress.
That selection satisfies `FML-REQ-018`, `FML-ADR-029` and `FML-ADR-073`; this
evaluation records the upstream dependency and current release against OSS-01.

The approved profile is deliberately smaller than Martin's full feature set:
rootless OCI execution, an immutable image digest, a read-only MBTiles mount,
the web UI disabled, and exposure only through the FML ingress. PostgreSQL,
remote object stores, dynamic processing and filesystem write access are not
adopted by this record.

## Existing prototype and resource evidence

The 2026-09-06 FML bench ran a digest-pinned Martin image on Debian x86-64 under
rootless Podman, served deterministic synthetic MBTiles through the `z/x/y`
contract, and completed two 20-second loopback load runs with zero errors. It
measured approximately 8.5 MB idle RSS and 27-30 MB peak RSS; the image occupied
approximately 650 MB at rest. These are `SIMULATED` software-half measurements,
not target-hardware, RF, CPU or real-imagery results.

That bench pinned an OCI digest resolved before release 1.16.1 rather than this
Git commit, so the registry keeps the exact 1.16.1 source intake `EVALUATED` and
does not claim that this release was prototyped. Promotion still requires a new
digest-pinned build/profile and the remaining trade gates.

## Runtime and data

Pinned runtime source defaults to `0.0.0.0:3000`; Martin does not supply the FML
authentication boundary. The selected deployment shall bind and expose it only
through the authenticated ingress. The built-in web UI is disabled by default.
Directory sources are watched and hot-reloaded, while explicitly named MBTiles
sources are snapshotted at startup. The FML profile mounts a named mission file
read-only to avoid adopting directory hot reload.

The adopted data format is MBTiles, a local SQLite file. Martin's workspace also
ships MBTiles copy, validation, metadata, diff and apply tooling, but this intake
does not make those operational tools part of the node. Backup is replacement or
copy of the provisioned mission file outside the serving process; schema and
source-content migration remain a provisioning responsibility.

## Intake result

- License: dual MIT OR Apache-2.0, compatible for the selected use. The Cargo
  lockfile records dependencies, but a complete redistribution/license review
  remains pending.
- Maintenance: releases are active, with `martin-v1.16.1` published on
  2026-09-09 and a broad contributor base.
- Platform: published Linux images and binaries include amd64 and arm64; source
  also supports macOS and Windows.
- Security: the evaluated version is outside the affected range of both
  GHSA-5x5g-6p4c-jqfh and GHSA-6774-6cqw-f586. The latter has no declared patched
  version, so this record does not claim an upstream fix. Upstream runs an
  automated Rust dependency audit; no independent audit or repository SBOM was
  identified.
- Prototype: the exact 1.16.1 source intake was not run. Existing FML Martin
  evidence remains `SIMULATED` and is retained separately.

## Exit strategy and questions

Keep the service behind the stable `z/x/y` ingress contract so another compliant
MBTiles server can replace it. Before promotion, resolve and record the 1.16.1
multi-architecture image digest, reproduce the narrow rootless profile, complete
the dependency/license scan, and run the remaining CM4 and permitted-real-imagery
checks owned by `TBR-COMP-01`, `TBR-MAP-01` and `TBR-SEC-01`.

## Sources

- [Pinned workspace metadata](https://github.com/maplibre/martin/blob/434782d95c08933bf2558135d2a7bac5bfb39274/Cargo.toml)
- [Pinned MBTiles guide](https://github.com/maplibre/martin/blob/434782d95c08933bf2558135d2a7bac5bfb39274/docs/content/sources-mbtiles.md)
- [Pinned container guide](https://github.com/maplibre/martin/blob/434782d95c08933bf2558135d2a7bac5bfb39274/docs/content/run-with-docker.md)
- [Pinned server defaults](https://github.com/maplibre/martin/blob/434782d95c08933bf2558135d2a7bac5bfb39274/martin/src/config/file/srv.rs)
- [Pinned security workflow](https://github.com/maplibre/martin/blob/434782d95c08933bf2558135d2a7bac5bfb39274/.github/workflows/security.yml)
- [FML selection and footprint evidence](../evidence/TBR-MAP-01/2026-09-06-martin-mbtiles-server-footprint.md)
- [Release history](https://github.com/maplibre/martin/releases)
- [Contributor summary](https://api.github.com/repos/maplibre/martin/contributors)
- [Repository security advisories](https://github.com/maplibre/martin/security/advisories)
