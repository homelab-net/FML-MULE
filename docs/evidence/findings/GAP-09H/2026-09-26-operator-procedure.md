# GAP-09H operator procedure: stand up the v0.0.1 node

**Finding:** GAP-09H (operator procedure, P1). **Prepared:** 2026-09-26.
**Reviewer:** independent. **State:** `DRAFT` -- this assembles the v0.0.1
build-and-bring-up steps a stranger follows, and names the gaps that still block a
clean end-to-end run. It is a procedure, not a completed drill: v0.0.1 is done only
when a person who did not write the docs runs the cold-start drill on real hardware
and reaches a working node (`ROADMAP.md`, `docs/verification/README.md`). Nothing
here is `HARDWARE-VERIFIED`, and the tiers of the pieces vary: the config
resolution and rendering are `SIMULATED`, but the Martin service unit is
`UNVERIFIED` (authored, never instantiated -- GAP-09G), so the milestone is not a
uniform `SIMULATED` whole. The manual bring-up fallback (steps 4-8) additionally
depends on hardware not yet in hand: it leans on the GAP-09E Pi bring-up card, and
the arm64 Pi is acquired the weekend of 2026-09-27.

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
   (`nodes/mule-v001/node.yml`) whose `eud_ap` interface name is set to the node's
   real Wi-Fi interface. **Gap G2 (interface name, `TBR-LINUX-01`):** `eud_ap` is
   `TBD` until the node's interface is known.

3. **Boot; the runtime renders config.** `os/systemd/mule-runtime.service`
   (`FML-ADR-083`, PR #176) runs `python -m mule ... --out /run/fml`, resolving the
   region+mission+node and, once wired, rendering the AP config. **Gap G3
   (rendering wired into the oneshot):** `mule/rendering.py` (PR #178) renders the
   decided hostapd surface but is **not yet wired into the boot oneshot**, and is a
   partial (`SIMULATED`) render: no WPA block (`TBR-SEC-01`), no DHCP/addressing
   (`TBR-NET-01`).

4. **Bring up the EUD AP.** hostapd from the rendered config on `us-915` channel 149
   / 5 GHz (`FML-ADR-057` operational BSS not isolated). Until G2/G3 close, bring
   the AP up **by hand** per `docs/evidence/findings/GAP-09E/2026-09-27-pi-ap-bringup-execution-card.md`.
   **Gap G4 (AP credential, `TBR-SEC-01`):** the passphrase is supplied out of band,
   never from the repo.

5. **Serve the one service.** Martin as a rootless Podman **Quadlet** unit
   (`FML-ADR-029`, GAP-09G), referenced by immutable digest, with its catalog entry
   (`services/catalog/catalog.yml`). GAP-09G **authored and statically checked** this
   unit but its evidence tier is `UNVERIFIED`: no container has been instantiated,
   even on x86 (`GAP-09G/2026-09-24-implementation.md`). Running it here is its first
   instantiation. It mounts one read-only per-mission MBTiles at
   `/var/lib/fml/maps/mission.mbtiles` and fails closed if that file is unreadable.

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
   reverse proxy on the AP subnet**, deferring TLS to post-v0.0.1. This is only
   defensible if the AP link is **WPA2**: `THREAT_MODEL.md` (edge-of-node in the
   clear is a defect) is satisfied over the air by link encryption, not transport
   TLS -- and that link encryption is itself **G3/G4** (no WPA block rendered yet,
   credential mechanism undecided, `TBR-SEC-01`). An **open** AP plus HTTP would be
   a `THREAT_MODEL` defect; the deferral holds only for a WPA2 AP. **Gap G6 (DHCP
   range, `TBR-NET-01`):** the AP subnet/DHCP is not decided, so addressing is set by
   hand for the drill.

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
| G2 interface name (`TBR-LINUX-01`) | rendered AP/networkd config | the node's Wi-Fi interface is named in `nodes/mule-v001` |
| G3 render wired into oneshot + partial render | hands-free bring-up | rendering wired into `main`/the service; WPA path (`TBR-SEC-01`) + DHCP (`TBR-NET-01`) rendered |
| G4 AP credential (`TBR-SEC-01`) | AP security (and the WPA2 link the HTTP deferral rests on) | the credential-supply mechanism is decided |
| G5a reverse proxy / port exposure (`FML-ADR-031`, `services/ingress/`) | reach-by-name (Martin is loopback-only) | the ingress reverse-proxy mechanism is built |
| G5b ingress TLS (`services/ingress/`) | encrypted reach-by-name | the Owner confirms the WPA2-contingent HTTP deferral, or TLS is built |
| G6 DHCP/addressing (`TBR-NET-01`) | phone gets an address | the addressing trade closes |
| G7 map-tile provisioning (`FML-ADR-073`/`FML-ADR-072`) | Martin serves tiles (step 8) | the mission MBTiles is sourced and placed |

Until these close, the drill can be **rehearsed by hand** on the Pi (steps 4-7
manual, per the GAP-09E bring-up card) but not completed hands-free from the image
alone. This procedure is the assembly and the gap register; running the drill and
resolving its issues is what closes GAP-09H.

## Boundary

No invented RF, DHCP, or credential values; no representation or trade closed here.
GAP-09H stays `OPEN` until the cold-start drill runs on real hardware and its issues
are resolved. The conscious TLS deferral in step 7 is recommended, not decided, and
is flagged for the Owner and `services/ingress/`.
