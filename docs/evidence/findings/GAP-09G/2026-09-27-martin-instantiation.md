# Martin Quadlet instantiated on x86 (first run)

**Finding:** GAP-09G (service deployment). **Date:** 2026-09-27. **Tier:**
`SIMULATED` (exercised end to end on the x86 bench with synthetic data; says nothing
about target hardware, RF, or a real client). No real identity, location, or
capture; the tile store is a one-tile synthetic MBTiles, deleted afterward
(`SECURITY.md`).

## Why

The 2026-09-24 implementation recorded the Martin Quadlet as `UNVERIFIED`: the unit
was authored and statically checked, but "no container has been instantiated, even
on x86." This reading closes that specific gap by starting the pinned image with the
unit's deployment contract and observing it serve tiles and fail closed. It does not
close GAP-09G (independent review and the GAP-09I phone-over-AP acceptance remain).

## Method

`podman 5.4.2` on the x86 bench host. The pinned image
`ghcr.io/maplibre/martin@sha256:59902019bf9038926ff0c71174237d6852e64c457830a6349abe7090be8818ca`
(the digest in `services/quadlets/martin.container` and `services/catalog/catalog.yml`)
was pulled and run with the unit's contract: `PublishPort=127.0.0.1:3000:3000`, a
read-only `Volume` of a synthetic one-tile MBTiles at
`/var/lib/fml/maps/mission.mbtiles:/data/mission.mbtiles:ro`, `--read-only` root
filesystem, and `Exec=/data/mission.mbtiles`. The unit was also run through the
`podman-systemd` (Quadlet) generator.

## Observations

1. **It serves tiles.** `GET /catalog` returned the `mission` source
   (`content_type image/png`, name `fml-synthetic`); `GET /mission/0/0/0` returned
   **HTTP 200** with a PNG tile. The `z/x/y` contract of `FML-ADR-073` holds on the
   pinned image with a read-only root filesystem and a read-only mount.
2. **It fails closed on a missing store.** With the mission MBTiles absent, the
   container refused to start (`podman` exit 125, `statfs ... no such file or
   directory`). The unit's `ExecStartPre=/usr/bin/test -r ...` gate likewise fails
   on an absent file. **Caveat:** the gate's *unreadable-but-present* case
   (`chmod 000`) could not be exercised here because the run was as **root**, which
   bypasses the DAC read check; the gate is a control for the **rootless** user the
   unit is meant to run as, and should be re-checked rootless.
3. **The Quadlet unit generates.** `podman-systemd -dryrun` loaded
   `martin.container` and produced a valid `martin.service` (with
   `RequiresMountsFor=/var/lib/fml/maps/mission.mbtiles`,
   `network-online.target`), so the unit file itself is well-formed.

## What this does and does not establish

- **Establishes (`SIMULATED`):** the selected image + the unit's deployment contract
  work end to end on x86 -- Martin serves `z/x/y` from a read-only mission store on
  loopback and fails closed when the store is absent. GAP-09G moves from
  `UNVERIFIED` to `SIMULATED` for the deployment contract.
- **Does not establish:** rootless operation of the readability gate (root bypass,
  above); the EUD-facing route (loopback only -- ingress, G5a); target-hardware
  footprint (`TBR-COMP-01`); or the phone-over-AP acceptance (GAP-09I). It also does
  **not** install Martin into the image: `os/image/manifest/packages.list` ships no
  `podman`, and the build installs `mule-runtime.service` but not `martin.container`
  or the catalog. That image install (register gap **G8**) requires adding podman to
  the locked package closure and a **new image execution**, coupling it to the
  image-boot gap (G1); it is a follow-on, not done here.

The synthetic MBTiles and test containers were removed; the pinned image is retained
locally. GAP-09G stays open pending independent review and the hardware acceptance.
