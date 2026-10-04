# GAP-09H operator procedure: stand up the v0.0.1 node

**Finding:** GAP-09H (operator procedure, P1). **Prepared:** 2026-09-26.
**Reviewer:** independent. **State:** `DRAFT` -- this assembles the v0.0.1
build-and-bring-up steps a stranger follows, and names the gaps that still block a
clean end-to-end run. It is a procedure, not a completed drill: v0.0.1 is done only
when a person who did not write the docs runs the cold-start drill on real hardware
and reaches a working node (`ROADMAP.md`, `docs/verification/README.md`). Nothing
here is `HARDWARE-VERIFIED`. The config resolution, the partial hostapd render and
the Martin deployment contract are `SIMULATED` (Martin was instantiated on the x86
bench, `GAP-09G/2026-09-27-martin-instantiation.md`); none of them has run from the
image on the v0.0.1 article. The manual bring-up fallback (steps 4-8) leans on the
GAP-09E Pi bring-up card; the arm64 Pi article is in hand
(`GAP-09E/2026-10-03-arm64-development-article.md`).

## Target (and non-target)

v0.0.1 is **one node, one service, reachable from a phone, built by following this
repository** (`ROADMAP.md`): cold-boot a single node, bring up the EUD Wi-Fi access
point, run **Martin** serving one read-only per-mission MBTiles
(`FML-ADR-073`, GAP-09F), and have a phone on the AP reach the map **by name**.
Excluded, by milestone scope: mesh/HaLow/LoRa, the TAK service, identity/admission,
A/B rollback, hardware block qualification, the four placeholder services.

## The procedure

Each step names the record it rests on and, where the step is not yet runnable end
to end, the **gap** that blocks it (collected in the register below).

0. **Have a node.** A compute element and power (`ROADMAP.md`: *a* node, not a
   qualified block; `TBR-HW-01` need not be closed). The arm64 Raspberry Pi is the
   intended article. **Gap G1 (image not yet booted for the current closure; arm64
   needed for the Pi).**

1. **Build the image.** `os/image/` (mkosi, `FML-ADR-079`) produces the bootable
   root filesystem. **Gap G1 (image not yet booted for the current closure):**
   GAP-09C booted an earlier 97/440 foundation; `os/image/README.md` records the
   current 118/454 closure "has not yet earned the GAP-09C byte-identical image
   result; it requires a new image execution" -- so "an image that boots"
   (`ROADMAP.md`) is unproven for the current closure on **any** arch, and the Pi
   additionally needs an **arm64** image.

2. **Write the deployment inputs.** A region profile (`regions/us-915/`, AP RF set
   by `TBR-RF-03` AP-params, PR #177), a mission package (with `network.ap_ssid` and
   the `martin` service), and a node descriptor
   (a node descriptor under `nodes/`) whose `eud_ap` interface name is set to
   the node's real Wi-Fi interface. **Gap G2 (interface name, `TBR-LINUX-01`):**
   closed for the v0.0.1 article on 2026-10-03 -- `nodes/pi-mule-1/node.yml`
   names `wlan0`, verified on the board. It remains `TBD` in
   `nodes/mule-v001/`, correctly, because that prototype is unassembled. This
   gap previously required the interface to be named *in `mule-v001`*, which
   could only have been satisfied by asserting that the lab Pi is the field
   article.

3. **Boot; the runtime renders config.** `os/systemd/mule-runtime.service`
   (`FML-ADR-083`, PR #176) runs `python -m mule ... --out /run/fml`, resolving the
   region+mission+node and rendering the AP config. **Gap G3 (partial render):**
   the oneshot now writes `hostapd.partial.conf` (`mule/configuration.py`
   `_render_ap_config`, PR #187;
   `GAP-09E/2026-09-27-hostapd-render-wired-and-wpa-gate.md`), but the render is a
   `SIMULATED` partial that says of itself it is not bootable: no WPA block
   (`TBR-SEC-01`), and no DHCP/DNS, addressing, firewall or networkd output
   (`TBR-NET-05`).

4. **Bring up the EUD AP.** hostapd from the rendered config on `us-915` channel 149
   / 5 GHz (`FML-ADR-057` operational BSS not isolated). Until the render is
   complete (G3: the WPA block and the `TBR-NET-05` outputs), bring the AP up
   **by hand** per `docs/evidence/findings/GAP-09E/2026-09-27-pi-ap-bringup-execution-card.md`.
   **Gap G4 (AP credential, `TBR-SEC-01`):** the passphrase is supplied out of band,
   never from the repo.

5. **Serve the one service.** Martin as a rootless Podman **Quadlet** unit
   (`FML-ADR-029`, GAP-09G), referenced by immutable digest, with its catalog entry
   (`services/catalog/catalog.yml`). GAP-09G authored the unit
   (`GAP-09G/2026-09-24-implementation.md`) and instantiated it rootless on the x86
   bench at `SIMULATED` (`GAP-09G/2026-09-27-martin-instantiation.md`); running it
   here is its first run on the v0.0.1 article. It mounts one read-only per-mission MBTiles at
   `/var/lib/fml/maps/mission.mbtiles` and fails closed if that file is unreadable.
   **Gap G8 (runtime + unit not on the image):** the current `os/image` closure
   installs no Podman, and the build does not place `martin.container` or its
   catalog into the runtime-consumed paths, so on the fresh image this step cannot
   be followed as written. The image must ship Podman and install the Quadlet unit
   + catalog before the service can start. The same closure also carries no access
   point userspace (`hostapd`) and none of the Pi's Wi-Fi firmware or regulatory
   database, so step 4 cannot run from the image either; which packages, and the
   archive component the firmware needs, is for the Program Owner under
   `FML-ADR-081`.

6. **Provision the map tiles.** Place the mission MBTiles at
   `/var/lib/fml/maps/mission.mbtiles`, sourced per `FML-ADR-073` (one read-only
   per-mission file) / `FML-ADR-072`. Without it Martin fails closed and step 8
   cannot pass. **Gap G7 (tile provisioning, `FML-ADR-073`/`FML-ADR-072`,
   `TBR-SEC-01`):** how the operator obtains and places the file is upstream-sourced
   and not scripted here.

7. **Ingress: reach it by name.** Martin publishes on **loopback only**
   (`PublishPort=127.0.0.1:3000:3000`, a deliberate GAP-09G choice), so DNS alone
   reaches no socket: a phone reaches it by name only through a **reverse proxy on
   the AP interface**. **Gap G5a (reverse proxy / rootless port exposure):**
   `FML-ADR-031` selects local DNS + an HAProxy/TCP proxy, but `services/ingress/`
   records "there is no EUD-facing route" and "the mechanism is `TBD`." **Gap G5b
   (TLS):** undecided; `ROADMAP.md` makes this the step that confronts or
   consciously defers it. **Recommended conscious deferral for v0.0.1 (Owner +
   `services/ingress/` to confirm):** serve Martin over **HTTP by name via the
   reverse proxy on the AP subnet**, deferring TLS to post-v0.0.1. Frame this as an
   **accepted security deviation / residual risk, not threat-model compliance**:
   `THREAT_MODEL.md` names WPA2 for the AP **and, separately**, TLS for browser/API
   services (`services/ingress/`, which explicitly requires TLS), so WPA2 does
   **not** substitute for service TLS. The deferral accepts plain-HTTP tiles as a
   recorded residual risk for v0.0.1; it assumes at least a **WPA2** AP (itself
   gated -- G3/G4, no WPA block rendered, `TBR-SEC-01`), and an **open** AP plus
   HTTP would compound the deviation. **Gap G6 (AP subnet / DHCP -- owned,
   undecided):** `TBR-NET-05` owns AP addressing; the 2026-10-03 decision narrowed
   it (per-deployment subnet in the mission package, `address_prefix` governing on
   a meshed node) but left the lease and the per-node slice assignment open
   (`docs/evidence/TBR-NET-05/2026-10-03-ap-subnet-and-dhcp-decision.md`). Set the
   AP subnet by hand for the drill; `TBR-NET-05` closing is what makes it
   hands-free.

8. **The phone.** Join the AP (SSID from the mission; credential from step 4), open
   the map URL by name, confirm tiles load. Needs a phone on the AP (the bookmarked
   step; the arm64 Pi is the AP article).

## Acceptance -- the cold-start drill

v0.0.1 is accepted by the drill in `docs/verification/README.md`, scoped to this
milestone: a participant who did **not** write the documentation follows this
repository, may not ask questions, and files an **issue** for every command that did
not work or every point of confusion. The author does not defend the docs during
the drill; issues are read afterward. A skipped drill is recorded as skipped in
`CHANGELOG.md`.

## Gaps that block a clean drill today

| Gap | Blocks | Closes when |
| --- | --- | --- |
| G1 image not booted for current closure | boot on any arch, then the Pi | the current `os/image` closure is built and booted, and an arm64 artifact is produced |
| G2 interface name (`TBR-LINUX-01`) | rendered AP/networkd config | **met for the v0.0.1 article** 2026-10-03: `nodes/pi-mule-1/node.yml` names `wlan0`. Still `TBD` for the unassembled `mule-v001`. |
| G3 partial render (wired into the oneshot by PR #187) | hands-free bring-up | WPA path (`TBR-SEC-01`) and DHCP/DNS, addressing and firewall (`TBR-NET-05`) rendered |
| G4 AP credential (`TBR-SEC-01`) | AP security (and the WPA2 link the HTTP deferral rests on) | the credential-supply mechanism is decided |
| G5a reverse proxy / port exposure (`FML-ADR-031`, `services/ingress/`) | reach-by-name (Martin is loopback-only) | the ingress reverse-proxy mechanism is built |
| G5b ingress TLS (`services/ingress/`) | encrypted reach-by-name | the Owner confirms the WPA2-contingent HTTP deferral, or TLS is built |
| G6 AP subnet / DHCP -- owned by `TBR-NET-05`, undecided | phone gets an address | `TBR-NET-05` decides the lease and per-node slice assignment |
| G7 map-tile provisioning (`FML-ADR-073`/`FML-ADR-072`) | Martin serves tiles (step 8) | the mission MBTiles is sourced and placed |
| G8 runtime, unit and AP stack not on the image | starting Martin, and the AP, from the image | the image ships Podman, installs the Quadlet unit + catalog, and carries the AP userspace, firmware and regulatory database (`FML-ADR-081` package boundary) |

Until these close, the drill can be **rehearsed by hand** on the Pi (steps 4-7
manual, per the GAP-09E bring-up card) but not completed hands-free from the image
alone. This procedure is the assembly and the gap register; running the drill and
resolving its issues is what closes GAP-09H.

## Boundary

No invented RF, DHCP, or credential values; no representation or trade closed here.
GAP-09H stays `OPEN` until the cold-start drill runs on real hardware and its issues
are resolved. The conscious TLS deferral in step 7 is recommended, not decided, and
is flagged for the Owner and `services/ingress/`.
