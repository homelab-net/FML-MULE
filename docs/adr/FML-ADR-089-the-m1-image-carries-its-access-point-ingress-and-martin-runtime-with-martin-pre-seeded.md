---
id: FML-ADR-089
title: The M1 image carries its access point, ingress and Martin runtime, with Martin pre-seeded
status: SELECTED
date: 2026-10-04
supersedes: none
superseded-by: none
trades: [TBR-NET-05, TBR-HA-01, TBR-LINUX-01, TBR-CARRIER-01]
verification: GAP-09H
---

# FML-ADR-089 The M1 image carries its access point, ingress and Martin runtime, with Martin pre-seeded

## Context

M1 (`v0.0.1`) is a node that "cold-boots, creates its EUD AP, reports health,
and serves one real local service to a phone" (`docs/ROADMAP-DEV.md`, gate M1).
The phone reaches the service "by name" (`ROADMAP.md`), and the service is
Martin (`services/catalog/catalog.yml`). Gap G8 of the operator procedure
(`docs/evidence/findings/GAP-09H/2026-09-26-operator-procedure.md`) records that
the image can do neither from its own contents: it carries no Podman, no access
point userspace, no Pi Wi-Fi firmware and no regulatory database, and the build
installs neither `martin.container` nor its catalog.

`FML-ADR-081` says the image "shall begin with these direct target packages and
no application or network-service packages", and that "a package required only
by a later capability remains in that capability's owner gate".
`FML-ADR-083` added `python3` through that gate without superseding it, and this
record does the same for M1.

The options, the package facts and the Martin runtime defect were prepared in
the G8 decision packet
(`docs/evidence/findings/GAP-09H/2026-10-04-m1-runtime-on-the-image-decision-packet.md`),
which a separate agent reviewed before submission. The packet left open how the
digest-pinned Martin image reaches a node with no WAN. A recommendation for that
was written and reviewed by a separate agent in the same session; its
corrections are applied below. The Program Owner approved all three on
2026-10-04, in the Claude Code cloud session that prepared this record.

## Decision

### Packages

The direct-package list shall add `podman`, `uidmap`, `passt`,
`dbus-user-session`, `hostapd`, `wireless-regdb`, `dnsmasq` and `haproxy` to
every profile, and `firmware-brcm80211` to the arm64 profile only. The three
rootless helpers are named because at the pinned snapshot `podman` only
recommends them, and the image installs no recommended packages
(`os/image/mkosi.conf`, `WithRecommends=no`). `firmware-brcm80211` is in
`non-free-firmware`, which `FML-ADR-088` enables for the arm64 profile.

The image shall disable `dnsmasq.service`, `haproxy.service` and
`hostapd.service` at build time. At the pinned snapshot each package's
`postinst` runs `deb-systemd-helper enable` on first installation, so each would
otherwise start at boot with its stock configuration. Each stays disabled until
its configuration is rendered: `dnsmasq` and the HAProxy bind on `TBR-NET-05`,
the `hostapd` WPA block on the AP credential decision.

### How Martin runs

- **Account.** A dedicated system account for mission services, created at build
  with a fixed UID through `sysusers.d`, with a home directory the image creates
  for it, and `/etc/subuid` and `/etc/subgid` ranges. Rootless Podman stores
  images under `$HOME`, and `sysusers.d` creates no subordinate ranges. The range
  size is `TBD`, recorded by the first rootless instantiation.
- **Quadlet directory.** `/etc/containers/systemd/users/<that UID>/`, and
  `mule-runtime.service`'s `--quadlets` argument moves to it. Podman 5.4.2's
  `podman-systemd.unit(5)`: "when administrators place Quadlet files in the
  /etc/containers/systemd/users directory, all users' sessions execute the
  Quadlet when the login session begins. If the administrator places a Quadlet
  file in the /etc/containers/systemd/users/${UID}/ directory, then only the user
  with the matching UID execute the Quadlet". The shared directory would start a
  second Martin in any other login.
- **State path.** `/var/lib/fml/maps/mission.mbtiles` is unchanged. The image
  creates `/var/lib/fml/maps` through `tmpfiles.d`, root-owned, mode `0755`;
  Martin only reads the file.
- **Boot start.** `martin.container` gains `[Install] WantedBy=default.target`,
  and the image enables lingering for the account by creating
  `/var/lib/systemd/linger/<account>`. No `Restart=` is added, because
  `TBR-HA-01` is open. On first boot the tile file is absent, so Martin fails
  closed and stays failed. After placing the tiles the operator starts it with
  `systemctl --user -M <account>@ start martin.service`.

### How the Martin image reaches the node

The Martin OCI image shall be pre-seeded in the OS image, not pulled at first
start:

1. In the build's cache-populating run only, a `skopeo` from the tools tree runs
   `skopeo copy --all` from the catalog's digest reference into an OCI layout
   directory in a dedicated retained image cache, separate from the package
   cache. `skopeo` joins the tools-tree direct-package list and its lock. The
   offline build reads only that cache.
2. A validator fails the build unless the layout's `index.json` names the
   catalog digest and every blob hashes to its own name.
3. The layout is the whole multi-architecture index, so the one catalog digest
   serves every profile. It installs under `/usr/share/fml/images/martin/`, and
   the SBOM gains one component carrying the index digest.
4. A Quadlet `martin.image` in the account's directory loads the layout into the
   account's storage. `martin.container` keeps its digest `Image=`, depends on
   that load, and sets `Pull=never`, so a missing image fails instead of
   fetching from the network whenever a WAN happens to be present.
5. The catalog digest does not change.

The on-node disk cost is `TBD`, measured on the first build and recorded against
`TBR-CARRIER-01`. It is the layout plus the unpacked copy in rootless storage.

## Status

`SELECTED`. The Program Owner approved the package set, the Martin runtime and
pre-seeding on 2026-10-04. Nothing in it is implemented yet. It decides no
`TBR-NET-05`, `TBR-HA-01`, `TBR-LINUX-01` or `TBR-CARRIER-01` value, and no AP
credential mechanism.

## Consequences

- The operator procedure's steps 4, 5 and 7 can run from the image once this is
  implemented, subject to the configuration the open trades still own.
- The image gains a container runtime, three network-service packages and, on
  arm64, non-free firmware. Each enters the lock, the SBOM and, where its
  licence does not normalize, the licence-exception report.
- The build gains a second retained cache and its validator, and the tools tree
  gains `skopeo`. The Martin version now promotes with the OS image, consistent
  with `FML-ADR-040`.
- A node with no WAN can start Martin. A node with a WAN still never fetches it.
- The lab Pis, which run Martin from an ordinary login account's home directory,
  diverge further from the repository until reconciliation, which the Program
  Owner has deferred.

## Accepted cost

The OS image carries both architectures of the Martin image, because the catalog
pins one multi-architecture index and copying a single platform would change
that digest. Every node pays the disk for an architecture it cannot run. Two
copies also sit on each node, the layout and the unpacked storage. A
removable-media load at provisioning would have cost no build change, at the
price of an image outside the SBOM.

## Fallback

If `--all` layouts prove impractical in the build, pin a per-architecture digest
in the catalog for each profile, a catalog change under `FML-ADR-078`. If M1
cannot wait for the build work, load the image from removable media during
provisioning, as the tile file arrives, with `Pull=never`; that copy is recorded
as outside the SBOM. If rootless storage cannot read the layout or the mounted
tile file, the failure is recorded as evidence and the account design returns to
the Program Owner; rootful execution is not substituted here, because
`FML-ADR-029` is `SELECTED`.

## Superseded by

None.

## Verification dependency

GAP-09H: the operator procedure run on the article from a repository-built
image. Before that, a CI topology case shall start the decided unit, rootless,
from the pre-seeded layout with the network removed, with a negative control
that fails with the layout absent and one that fails with the tile file absent.
The pre-seed mechanics were exercised by the reviewing agent on Podman 4.9.3,
not the 5.4.2 the image ships, so that case is the first check on 5.4.2. The
result is `SIMULATED` until repeated on the article.
