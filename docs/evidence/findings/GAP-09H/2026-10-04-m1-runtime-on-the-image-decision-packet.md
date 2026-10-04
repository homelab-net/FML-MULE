# GAP-09H decision packet: what the image carries so M1 can run from it

**State:** `AWAITING_USER_DECISION`. Nothing here is implemented. The Program
Owner decides; the decision lands in a new ADR (the arm64 profile ADR, not yet
written), as `FML-ADR-083` did for `python3`, because a packet cannot override
a `shall`.

**Finding:** GAP-09H, gap G8 (operator procedure,
`2026-09-26-operator-procedure.md`). **Prepared:** 2026-10-04. **Author:**
Claude agent, cloud session. **Independent verifier:** a separate agent at
execution time; a separate agent reviewed this draft before submission and its
corrections are applied. **Tier:** analysis only; nothing exercised.

## 1. Decision requested

M1 (`v0.0.1`) is a node that "cold-boots, creates its EUD AP, reports health,
and serves one real local service to a phone" (`docs/ROADMAP-DEV.md`, gate M1).
The phone reaches it "by name" (`ROADMAP.md`, ingress), and the service is
Martin (`services/catalog/catalog.yml`). Today the image cannot create the AP or
serve Martin from its own contents, and cold boot of the current closure is
itself unproven (G1). Two questions:

1. **Which packages join the direct-package list** so the access point, the
   one service and its ingress can start from the image?
2. **How Martin runs on the image**: which account, which Quadlet directory,
   which state path, and what starts it.

## 2. Governing constraints

- `FML-ADR-081`: the image "shall begin with these direct target packages and
  no application or network-service packages", and
  `os/image/manifest/direct-packages.list` requires Program Owner approval to
  add one. The ADR's list is exhaustive, so every package below needs the Owner
  and an ADR, not only this packet.
- `FML-ADR-029`: rootless Podman and Quadlet is the default execution model.
  Rootful is not offered here.
- `FML-ADR-031`: stable local DNS plus HAProxy/TCP ingress for service
  identities.
- `FML-ADR-083`: the `mule-runtime` oneshot renders configuration and exits.
  Per `os/systemd/README.md` it has no `[Install]` section and is started
  explicitly after provisioning. `TBR-HA-01` is open, so no `Restart=` is
  proposed.
- `FML-ADR-078`: only catalogued services run; `martin` is catalogued with a
  digest-pinned image.
- Open trades this packet leaves open: `TBR-NET-05` (AP subnet, lease, DHCP
  scope), `TBR-SEC-01` (AP credential), `TBR-HA-01` (recovery),
  `TBR-LINUX-01` (kernel and driver viability).

## 3. Question 1: packages

The image installs eleven direct packages today
(`os/image/manifest/direct-packages.list`): boot userspace, the amd64 kernel,
and the Python runtime. None of the following is present.

| Role | Proposed Debian package | Needed by | Profile | Notes |
| --- | --- | --- | --- | --- |
| Container runtime | `podman` | step 5, Martin (G8) | both | Rootless helpers (`passt`, `uidmap`, `dbus-user-session`) may be Recommends, which this image does not install (`os/image/mkosi.conf`, `WithRecommends=no`). The resolver run records which; any that are needed join this list by name. The lab's hand-provisioned Debian 13 hosts ran `podman version 5.4.2` (`docs/evidence/TBR-LINUX-01/2026-10-01-infrastructure-wifi-prototype.txt`). |
| Access point userspace | `hostapd` | step 4, the EUD AP | both | Consumes the rendered `hostapd.partial.conf`; the WPA block stays gated on `TBR-SEC-01`. |
| Wi-Fi firmware | `firmware-brcm80211` | step 4 on the Pi 4B (CYW43455) | arm64 only | Expected to carry the CYW43455 firmware and the Pi 4B NVRAM file, and expected in the `non-free-firmware` component, which the image does not enable today; the arm64 profile ADR decides that component. The lab Pis run a Raspberry Pi kernel, so they are not evidence for the Debian package. |
| Regulatory database | `wireless-regdb` | step 4 | both | Expected to provide the kernel's regulatory database, so a `country_code` request is applied rather than leaving the world domain. On the Pi 4B's FullMAC `brcmfmac` the firmware's own country tables also apply (`TBR-LINUX-01`). |
| DHCP and local DNS | `dnsmasq` | steps 7-8, a phone gets an address and resolves the name | both | Package only. Its configuration is `TBR-NET-05`'s and stays unrendered until that trade decides lease and scope. |
| Ingress proxy | `haproxy` | step 7, reach Martin by name (G5a) | both | `FML-ADR-031` selects it. `os/config/haproxy.conf.template` has its bind address `TBD` on `TBR-NET-05`. |

**How the names get confirmed.** The image's package resolver
(`tools/resolve-image-packages.py`) authenticates the pinned
`snapshot.debian.org` index and fails if a named package, or the component it
lives in, is absent. That run is where each name, component and dependency above
becomes a recorded fact; this packet does not claim them in advance. The cloud
session that wrote this packet could not reach any Debian archive host
(connections to `snapshot.debian.org`, `deb.debian.org`, `packages.debian.org`,
`salsa.debian.org` and `sources.debian.org` were refused by the session's network
policy on 2026-10-04), so the resolver run happens once that access is allowed,
or on the N150 as a bench card.

**Recommendation.** Approve all six as the M1 package set. Each is required by
a numbered step of the operator procedure, and adding them one at a time costs
one ADR each against the same `FML-ADR-081` sentence. Shipping `dnsmasq` and
`haproxy` decides nothing about their values, provided the image disables
`dnsmasq.service` and `haproxy.service` until their configuration is rendered;
Debian maintainer scripts may enable packaged services with a stock
configuration. The build run records each package's default enablement.

**Alternative.** Approve `podman`, `hostapd`, `firmware-brcm80211` and
`wireless-regdb` only, and leave `dnsmasq` and `haproxy` for when `TBR-NET-05`
closes. M1's drill then sets the phone's address by hand and reaches Martin by
address, not by name, which falls short of the `v0.0.1` ingress text, "enough
that the phone reaches the service by name" (`ROADMAP.md`).

## 4. Question 2: how Martin runs on the image

### What exists, and what the lab does instead

- `services/quadlets/martin.container` mounts
  `/var/lib/fml/maps/mission.mbtiles` read-only, refuses to start if it is
  unreadable, publishes on loopback only, and has no `[Install]` section.
- `os/systemd/mule-runtime.service` checks that the catalogued Quadlets exist
  under `--quadlets /etc/containers/systemd/users`
  (`mule/configuration.py` tests each with `is_file`). It installs and starts
  nothing.
- The lab Pis instead run the unit with a home-directory tile path, an added
  `[Install] WantedBy=default.target`, and lingering enabled for their ordinary
  login account
  (`docs/evidence/TBR-HA-01/2026-10-02-deployed-recovery-policy-and-repo-divergence.md`).
  That record notes `/var/lib/fml` does not exist on either Pi, so the
  repository's unit would fail there.

### A defect in the current path

Podman 5.4.2's own documentation, for the directory the runtime checks:

> For rootless containers, when administrators place Quadlet files in the
> /etc/containers/systemd/users directory, all users' sessions execute the
> Quadlet when the login session begins. If the administrator places a Quadlet
> file in the /etc/containers/systemd/users/${UID}/ directory, then only the
> user with the matching UID execute the Quadlet when the login session gets
> started.

(`containers/podman` `v5.4.2`, `docs/source/markdown/podman-systemd.unit.5.md`;
the generator's `getRootlessDirs` in `cmd/quadlet/main.go` reads `users/` for
every UID and `users/<UID>` only for the matching one.)

With the `[Install]` line recommended below, Martin would be generated and
started in every user's manager. A second session, such as an operator console
login, would start a second Martin that either fails to bind `127.0.0.1:3000`
or, if it starts first, holds the port, so the service then lives only as long
as that login. The directory should be the per-UID one.

### Recommendation

1. **Account.** A dedicated system account for mission services, created at
   image build with a fixed UID (systemd `sysusers.d`), so the per-UID Quadlet
   directory has a stable name. Its `sysusers.d` entry names a home directory
   the image creates for it (`tmpfiles.d`, owned by the account), because
   rootless Podman stores images under `$HOME`. The image also writes
   `/etc/subuid` and `/etc/subgid` ranges for it, because `sysusers.d` creates
   none and the lab's ordinary account had them. The range size is `TBD` and is
   recorded by the first rootless instantiation.
2. **Quadlet directory.** `/etc/containers/systemd/users/<that UID>/`, for the
   reason quoted above. `mule-runtime.service`'s `--quadlets` argument moves to
   the same directory.
3. **State path.** Keep the repository's `/var/lib/fml/maps/mission.mbtiles`.
   The image creates `/var/lib/fml/maps` (systemd `tmpfiles.d`), root-owned,
   mode `0755`, with the tile file `0644`; Martin only reads it. Rootless
   reading of that mount is unexercised: GAP-09G's instantiation ran as root.
   This removes the failure the divergence record names: `/var/lib/fml` does
   not exist, and a rootless user cannot create it.
4. **Boot start.** Add `[Install] WantedBy=default.target` to the Quadlet, and
   enable lingering for the service account at image build. Podman's
   documentation, same file:

   > The services created by Podman are considered transient by systemd ...
   > it is not possible to "systemctl enable" them ... To compensate for this,
   > the generator manually applies the `[Install]` section of the container
   > definition unit files during generation ... For example, to start a
   > container on boot, add something like this to the file: `[Install]`
   > `WantedBy=default.target`

   and systemd's, for what lingering does
   (`systemd` `v257`, `man/loginctl.xml`):

   > If enabled for a specific user, a user manager is spawned for the user at
   > boot and kept around after logouts. This allows users who are not logged
   > in to run long-running services.

   `systemd-logind` reads lingering from the presence of
   `/var/lib/systemd/linger/<user>` at start
   (`src/login/logind.c`, `manager_enumerate_linger_users`), so the image can
   create that file at build time, once the account exists in `/etc/passwd`.

   On first boot the tile file is absent, so Martin fails closed and stays
   failed (no `Restart=`). After step 6 the operator starts it with
   `systemctl --user -M <account>@ start martin.service`; that command is added
   to the operator procedure.
5. **Recovery is not decided here.** No `Restart=` is added. The lab's
   thirteen recovery drop-ins stay a recorded deployment fact, not a selection,
   until `TBR-HA-01` decides.

### Alternative

Start Martin from the `mule-runtime` oneshot after it renders, instead of
`[Install]` plus lingering. Not recommended: the oneshot runs as a
`DynamicUser` and would need authority over another account's user manager, and
`FML-ADR-083` says the entry point "shall not become a second service
controller or a long-running supervisor"; starting another account's service is
that controller's job.

## 5. What implementation changes, after the decision

`os/image/manifest/direct-packages.list` and the regenerated locks for each
profile; `os/image/mkosi.postinst` installs `martin.container`, the catalog,
the `sysusers.d`, `tmpfiles.d` and subordinate-range entries, the linger file,
and disables `dnsmasq.service` and `haproxy.service`;
`services/quadlets/martin.container` gains `[Install]` and its install-path
comment changes; `os/systemd/mule-runtime.service` moves `--quadlets`, and
`test/unit/test_runtime_entrypoint.py`'s pinned `--quadlets` path follows;
`test/unit/test_martin_quadlet.py` asserts the `[Install]` line; a rootless
Martin case in `.github/workflows/topology.yml` runs the decided unit with a
fixture MBTiles and a negative control with the file absent. Each with a test
that fails without it.

One question stays open for the Owner and is not decided here: how the
digest-pinned Martin image reaches the account's storage on a node with no
WAN, pulled at first start or pre-seeded at build.

## 6. What this does not do

It decides no `TBR-NET-05`, `TBR-SEC-01`, `TBR-HA-01` or `TBR-LINUX-01` value.
It does not reconcile the lab articles, which is deferred by the Program Owner.
It does not make the image boot on the Pi; that is the arm64 profile ADR (not
yet written).

## 7. Owner disposition

Pending.
