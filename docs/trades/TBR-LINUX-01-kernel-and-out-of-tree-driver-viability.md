---
id: TBR-LINUX-01
title: Kernel and out-of-tree driver viability
status: OPEN
owner: TBD
area: LINUX
critical-path: true
depends-on: []
feeds: [TBR-HW-01, TBR-RF-01, TBR-RF-03, TBR-CARRIER-01]
evidence: docs/evidence/TBR-LINUX-01/
adr: [FML-ADR-022, FML-ADR-023, FML-ADR-024, FML-ADR-040]
---

# TBR-LINUX-01 Kernel and out-of-tree driver viability

## Question

Can the Wi-Fi HaLow driver, `batman-adv` in BATMAN-V mode, and the required
userspace be brought up together on a stock Debian-family kernel, or is a
patched vendor kernel tree required?

## Why it matters

This is on the critical path. Almost everything in `os/` waits behind it.

If a patched vendor tree is required, the program acquires a **maintained
kernel fork**: an owner, a rebase cadence, an upstream submission posture, and
an entry under `docs/forks/`. That is a permanent liability attached to a
specific person, and a volunteer program that acquires one without noticing
tends to discover it when that person becomes unavailable.

It also constrains hardware selection, because a vendor tree exists only for
the boards its vendor supports. A compute module with no viable kernel path is
disqualified regardless of how well it scores on every other axis.

`FML-ADR-024` further assumes BATMAN-V can obtain a usable throughput estimate
from the HaLow driver. Whether it does is `UNVERIFIED` and is part of this
trade.

## Options

1. **Stock distribution kernel plus DKMS out-of-tree driver.** The best
   outcome: no fork, ordinary security updates within the compatibility-set
   rule, widest hardware choice. Right answer if the driver builds and the
   radio behaves against an unmodified kernel.
2. **Stock upstream kernel with a small carried patch set.** Acceptable if the
   delta is small, well understood, and plausibly acceptable upstream. Requires
   a fork entry and an owner from day one.
3. **Vendor kernel tree.** Right answer only if the radio cannot be made to
   work otherwise. Largest liability: vendor trees lag, and rebasing onto a
   newer base is often not a rebase but a port.
4. **Defer, and select hardware first.** Rejected as an option to recommend,
   recorded because it is what happens by default if nobody picks this trade
   up. It inverts the dependency and risks buying hardware with no kernel path.

## Closure evidence

Committed under `docs/evidence/TBR-LINUX-01/`:

- A build log showing the out-of-tree driver compiling against each candidate
  kernel, with kernel version, driver version and toolchain recorded.
- `dmesg` and `iw` output from a booted node showing the radio enumerating and
  the interface entering mesh mode, with the image build identifier recorded.
- A recorded demonstration of two nodes forming an 802.11s mesh and
  `batman-adv` establishing originator entries between them.
- `batctl` output showing whether BATMAN-V obtains a throughput estimate from
  the driver, or evidence that it falls back to a default.
- Where a patch set is required: the patch files, the upstream base commit they
  apply to, and a written assessment of upstream acceptability.
- Archived copies of any vendor documentation relied on.

## Closure gate

Two nodes form a mesh, exchange bidirectional IP traffic over at least one hop,
and survive a reboot of both, on a kernel and driver combination whose exact
provenance is recorded. The closure states explicitly whether a carried patch
set is required, and if so, a `docs/forks/` entry exists with a **named owner**
before the trade is marked `CLOSED`.

Closing this trade with the fork owner recorded as `TBD` is not permitted.

## Dependencies

- **Depends on:** none. Blocked only by the availability of candidate hardware.
- **Feeds:** `TBR-HW-01`, `TBR-RF-01`, `TBR-RF-03`, `TBR-CARRIER-01`, and the
  whole of `os/`.
- **Requires hardware:** **yes.** A candidate compute module and a HaLow radio
  must be in hand. This is why the trade has not started.
