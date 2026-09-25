# GAP-09G Martin deployment implementation

**Date:** 2026-09-24. **Owner:** Codex. **Evidence tier:** `UNVERIFIED`. Static
and unit checks pass, but the selected deployment profile has not been exercised
end to end and has not met target hardware.

## Owner-selected contract

The Program Owner selected Martin serving one read-only per-mission MBTiles
file. This implementation serves `FML-ADR-029`, `FML-ADR-073`, and
`FML-ADR-078`:

- `services/catalog/catalog.yml` enables `martin` and names
  `martin.container`;
- the unit is intended for a rootless user Quadlet;
- the host handoff is the stable file
  `/var/lib/fml/maps/mission.mbtiles`;
- the file is mounted read-only and Martin's container root filesystem is
  read-only;
- the backend publishes only on `127.0.0.1:3000`, leaving the EUD-facing path
  to GAP-09E;
- no restart policy or target-hardware resource budget is invented while
  `TBR-HA-01` and `TBR-COMP-01` remain open.

## Immutable image resolution

The official source tag is `martin-v1.16.1`, source commit
`434782d95c08933bf2558135d2a7bac5bfb39274`. The pinned source documentation
names the official image `ghcr.io/maplibre/martin` and release tag `1.16.1`.

Inspecting the official `1.16.1` image with Docker Buildx resolved the
multi-architecture index to:

```text
sha256:59902019bf9038926ff0c71174237d6852e64c457830a6349abe7090be8818ca
linux/amd64: sha256:3b32a074916064a5cfed394725796c9b7869276596ee7a695d2efb709f450d6c
linux/arm64: sha256:62e47a4924d11f7e8983d0df0e253b70a0b4c857b6821593c0be571f2a657f00
```

The catalog, Quadlet, unit test, and manual footprint bench all carry the index
digest rather than the mutable release tag.

## Failing-first proof and verification

Before the implementation, the new test failed twice: the Martin catalog entry
was disabled and `services/quadlets/martin.container` did not exist. After the
change:

```text
59 passed in 1.79s
```

The focused run covered `test_martin_quadlet.py`, `test_service_catalog.py`, and
`test_gen_config.py`. It proves the selected service resolves through mission
configuration, owns exactly one loadable unit, pins the expected digest, keeps
the store and root filesystem read-only, binds only loopback, checks store
readability before startup, and does not set restart or automatic-update policy.

The Podman Quadlet generator was not present on the development machine. The
topology workflow runs `test/topology/quadlet-dry-run.sh`; that check now
requires the generated `martin.service` in addition to the TAK units. Runtime
container and target-hardware evidence are not claimed here.
