# WAN and HaLow dependencies

**Evaluated:** 2026-09-11 against Tailscale `v1.102.4` at
`bbcd7d1fc2054b9189ebc1531acf74bd880ca0c8`, Morse Micro driver releases
`mm6108-2.1.1` at `d457021af4c5ba9556b3d059ccce3e15001adad7` and
`mm8108-2.1.0` at `4ce0a0272f8ac8e2fa58eea8ff08116e493399de`, and Morse
firmware branch `2.1` at `ce39cefb5fd01ad689a0c0b043557d9c2a3167d8`.
**Verdict:** retain all three as current candidates, not selected components.
Tailscale remains one implementation of the optional overlay; the driver and
firmware remain inseparable members of an unselected hardware compatibility
set.

## Boundary set by existing decisions

`FML-ADR-039` requires an optional WAN overlay to terminate on MULE
infrastructure and names Tailscale Grants as the preferred current policy
model, but permits Tailscale or an equivalent. It does not select a client or
coordination service.

`FML-ADR-040` requires the field kernel, radio driver, firmware and userspace
tooling to be promoted as one tested compatibility set. `FML-ADR-062` fixes the
required `mac80211`/`cfg80211` mesh-capable interface while explicitly selecting
no HaLow vendor. Evaluating the Morse artifacts cannot choose MM6108, MM8108,
their board configuration, or a kernel package while `TBR-RF-01`, `TBR-RF-03`,
`TBR-LINUX-01` and `TBR-HW-01` remain open.

## Tailscale client

The open-source Tailscale client supplies the Linux daemon, command-line client
and routed overlay data plane. In the normal Linux mode `tailscaled` requires
root, a tunnel interface, a service socket and writable state. The source also
offers userspace networking, but choosing that different routing model would
need its own fit and performance evidence.

The persistent state contains node and control-plane identity, configuration,
TLS material and other daemon state. It is a credential-bearing durable set,
not a cache. An authentication key may bootstrap a node, but it shall not be
committed to the repository or mission examples. Tailscale identity and grants
authorize infrastructure reachability only; `FML-ADR-039` keeps mission and
service authorization separate.

The client source is BSD-3-Clause. The hosted coordination service, account
terms and any selected package repository are separate dependencies. Release
1.102.4 was published on 2026-09-10 from the peeled commit recorded above, and
the repository has an active multi-maintainer contributor base.

The official bulletin list includes eleven 2026 entries through TS-2026-011.
The evaluated release is newer than the declared client fixes, including
1.98.0 for the web-interface route reset, 1.98.9 for the applicable SSH,
Serve, Funnel and Services defects, 1.102.1 for accepted-environment disclosure
and 1.102.3 for 4via6 host-scope filtering. TS-2026-003 affected the hosted
coordination service rather than this source artifact, and TS-2026-001 affected
the macOS sentinel rather than the Debian target. This version comparison is
not a deployment security review; the selected feature subset and tailnet
policy still require GAP-10 evidence.

No exact client package was installed or run. Selection still requires a
package pin, deny-by-default grants, route-overlap rejection, loss-of-control
plane behavior, durable-state backup/revocation, and proof that EUDs never join
the overlay. The exit strategy is the routed application boundary in
`FML-ADR-039`: an equivalent overlay can replace the client without changing
EUD membership or mission authorization.

## Morse Micro Linux driver

The repository contains out-of-tree Linux driver sources for the MM6108 and
MM8108 families. Current releases are split by chip family, so this intake pins
both rather than pretending one is universally current. The current MM8108
source registers mesh-point behavior and names matching firmware images; the
earlier FML source review established the required `nl80211` mesh and SAE path.
Neither source reading demonstrates a radio on Debian hardware.

The source carries GPL-2.0-or-later. It builds against a supplied kernel source tree and
therefore inherits the kernel-coupling risk that `FML-ADR-040` controls. The
repository provides a Makefile but no DKMS manifest, so the preferred DKMS path
is not established by this intake. Installation and module loading require
system privileges; ordinary radio configuration is expected through the
standard userspace interface selected by `FML-ADR-062`.

Both chip-family releases were published on 2026-09-11. GitHub listed eight
open issues and no repository security advisory. The contributor endpoint did
not expose a usable public contributor summary, and no independent audit or
SBOM was identified. Resource use, supported Debian kernel range, boot/load,
mesh formation, recovery and rollback remain unmeasured.

The exact releases were not built. Their reuse mode remains undecided until a
HaLow module and board are selected and the complete driver, firmware, BCF,
kernel and userspace set passes Stage 2.

## Morse Micro firmware

The firmware repository contains binary chip images and board configuration
files. Upstream instructs users to check out the branch matching the driver
version and installs the selected binaries under `/lib/firmware/morse`. The
current `2.1` branch covers the driver release family evaluated here, but the
repository publishes neither a `2.1` tag nor a GitHub release. This intake
therefore pins the exact branch commit and does not call it a release.

The chip firmware is not open source. Its binary distribution agreement limits
use to hardware containing Morse Micro chips, permits redistribution only
complete and unmodified for that hardware, requires the agreement to accompany
distribution, prohibits reverse engineering, and carries export restrictions.
BCFs can have vendor-specific licenses. Compatibility is therefore
`review-required`, and a selected module and distribution plan must be checked
against both the firmware and BCF terms.

The 2.1 branch commit landed on 2026-09-11. GitHub listed no open issue and no
repository security advisory; the small public history shows two contributor
accounts. Binary firmware cannot be source-audited through this repository, and
no SBOM or independent assessment was identified.

The binaries were not installed or loaded. Their reuse mode remains undecided,
and they cannot be promoted separately from a selected driver, kernel, module
and board configuration. The exit strategy is to preserve the standard
`mac80211` interface and replace the entire compatibility set if another
qualified HaLow implementation is selected.

## Sources

- [Pinned Tailscale license](https://github.com/tailscale/tailscale/blob/bbcd7d1fc2054b9189ebc1531acf74bd880ca0c8/LICENSE)
- [Pinned Tailscale daemon state and privilege handling](https://github.com/tailscale/tailscale/blob/bbcd7d1fc2054b9189ebc1531acf74bd880ca0c8/cmd/tailscaled/tailscaled.go)
- [Tailscale security bulletins](https://tailscale.com/security-bulletins)
- [Tailscale Linux installation](https://tailscale.com/docs/install/linux)
- [Pinned MM8108 mesh-point source](https://github.com/MorseMicro/morse_driver/blob/4ce0a0272f8ac8e2fa58eea8ff08116e493399de/mac.c)
- [Pinned MM6108 firmware references](https://github.com/MorseMicro/morse_driver/blob/d457021af4c5ba9556b3d059ccce3e15001adad7/mm6108.c)
- [Pinned MM8108 firmware references](https://github.com/MorseMicro/morse_driver/blob/4ce0a0272f8ac8e2fa58eea8ff08116e493399de/mm8108.c)
- [Pinned Morse driver license](https://github.com/MorseMicro/morse_driver/blob/4ce0a0272f8ac8e2fa58eea8ff08116e493399de/LICENSE)
- [Pinned Morse firmware README](https://github.com/MorseMicro/morse-firmware/blob/ce39cefb5fd01ad689a0c0b043557d9c2a3167d8/README.md)
- [Pinned Morse firmware license notice](https://github.com/MorseMicro/morse-firmware/blob/ce39cefb5fd01ad689a0c0b043557d9c2a3167d8/firmware/LICENSE)
- [Existing HaLow driver interface evidence](../evidence/TBR-LINUX-01/2026-08-31-halow-driver-mesh-and-sae-support.md)
