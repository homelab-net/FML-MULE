---
id: FML-ADR-053
title: BATMAN-IV is the baseline routing algorithm, not BATMAN-V
status: SELECTED PLANNING BASELINE
date: 2026-08-28
supersedes: FML-ADR-024
superseded-by: none
trades: [TBR-RF-01, TBR-RF-03, TBR-NET-01, TBR-LINUX-01]
verification: Stage 2
---

# FML-ADR-053 BATMAN-IV is the baseline routing algorithm, not BATMAN-V

## Context

`FML-ADR-024` selected IEEE 802.11s for mesh association together with
`batman-adv` in **BATMAN-V** mode, carrying forward the `AD-004` decision from
the v0.1 point-of-departure design. Everything in it was reasoned from
documentation. Nothing had been run.

The first time the program actually loaded the module, in a three-node mesh on a
continuous integration runner, it said this:

```text
batman_adv: B.A.T.M.A.N. advanced 2025.3 (compatibility version 15) loaded
batman_adv: Routing algorithm 'BATMAN_V' is not supported
```

The module loads. The algorithm the architecture is built on is a **kernel build
option**, `CONFIG_BATMAN_ADV_BATMAN_V`, that the stock distribution build leaves
off. Selecting it means a custom kernel or the out-of-tree `batman-adv` module,
permanently, in the compatibility set `FML-ADR-040` governs, maintained by
volunteers.

That cost would be worth paying if BATMAN-V's advantage were assured. It is not,
and `FML-ADR-024` said so itself before any of this was measured:

> BATMAN-V's throughput-based metric needs a usable throughput estimate from the
> driver. Whether the HaLow driver provides one is **UNVERIFIED**... If it does
> not, path selection may be effectively arbitrary, which would undermine this
> decision.

So the program was carrying a permanent kernel obligation to buy a metric whose
benefit depends on an out-of-tree driver reporting a figure that out-of-tree
drivers frequently do not report. `TBR-LINUX-01` was going to answer that
eventually. The module answered half of it immediately and for free.

The alternatives were three.

**Keep BATMAN-V and take the kernel work.** Rejected for now. It commits the
compatibility set to a custom build before `TBR-RF-01` has shown the metric
would even function, which is paying a certain cost for an uncertain benefit.

**Keep BATMAN-V and defer.** Rejected. It is the current state, and the current
state is a decision nothing can implement, which reads as a plan while
functioning as a gap.

**Baseline on BATMAN-IV, revisit on evidence.** Selected.

## Decision

The primary IP MANET **shall** use IEEE 802.11s for mesh association together
with `batman-adv` in **BATMAN-IV** mode.

Everything else in `FML-ADR-024` is carried forward unchanged: 802.11s as the
association layer, layer 2 routing, the flat field broadcast domain, EUD access
bridged into it, and `10.41.0.0/16` as the preferred initial field prefix
subject to `TBR-NET-01`.

BATMAN-V **may** be reconsidered, and doing so requires both:

1. `TBR-RF-01` evidence that the selected sub-GHz driver reports a usable
   throughput estimate; and
2. measurement showing BATMAN-IV selecting materially worse paths than
   BATMAN-V would on the same links.

Absent both, the program stays on the algorithm the stock module provides.

## Status

`SELECTED PLANNING BASELINE`.

Adopted so the network plane can be built, configured and exercised now.
Expected to be revisited when `TBR-RF-01` closes, and nobody should be surprised
if it changes. It is deliberately not `SELECTED`: the evidence supporting
BATMAN-IV is availability and the absence of a demonstrated need for BATMAN-V,
which is a weaker claim than a measurement.

## Consequences

The baseline runs on a stock distribution kernel. No custom build, no
out-of-tree module, no DKMS, and nothing extra for a volunteer to maintain or
for `FML-ADR-040` to track.

Path selection uses BATMAN-IV's transmit quality metric, which is derived from
packet loss rather than throughput. On links of unequal rate but similar loss,
it may prefer a lossless slow path over a lossy fast one. On a node with one
high-rate and one range-oriented bearer that is a real effect, and it is the
specific thing the revisit criteria above exist to detect.

Anything measured on BATMAN-IV says nothing about BATMAN-V path selection, and
the reverse. Evidence gathered under this baseline does not transfer if the
program later moves.

What becomes easier: the mesh can be exercised on any ordinary Linux machine, by
a contributor with no hardware and no custom kernel. That is the property
`AGENTS.md` asks for throughout and the network plane has never had.

## Accepted cost

The program gives up a throughput-aware metric on a system whose whole purpose
is degrading gracefully across bearers of very different rates. That is not a
small thing to give up, and it is the specific decision someone will later argue
was wrong.

The argument for taking it anyway is that the alternative was not "have a
throughput-aware metric". It was "have a decision that no stock kernel can
execute, whose benefit is contingent on an unverified driver property". Between
a working loss metric and a non-working throughput metric, the working one wins
until measurement says otherwise.

Second cost, smaller and real: `batman-adv` is not in a stock cloud kernel's
base module set. It came from `linux-modules-extra`. Whatever the image is, it
has to guarantee the module, and `os/image/manifest/packages.list` now records
that.

## Fallback

Reconsider BATMAN-V under the two criteria in the decision, which would
supersede this ADR and reinstate the substance of `FML-ADR-024`. The cost is the
kernel work that was avoided here, and the signal to take it is `TBR-RF-01`
evidence of both a usable driver throughput estimate and demonstrably poor
BATMAN-IV path selection.

The broader fallback in `FML-ADR-024` is unchanged and still applies: a layer 3
routing protocol over the same radio links, at the cost of link-local service
discovery and the configuration-free property.

## Superseded by

None.

## Verification dependency

Stage 2, unchanged from `FML-ADR-024`: mesh formation and multi-hop traffic with
node count, spacing and offered load recorded, plus the EUD broadcast
measurement that decision requires.

Partial evidence exists and its limits matter. `.github/workflows/mesh-probe.yml`
forms a three-node BATMAN-IV mesh in network namespaces and confirms originator
exchange, translation-table learning and correct multi-hop next-hop selection.
The link layer there is a veth pair: a perfect wire with no propagation, loss,
contention or rate adaptation. It is `SIMULATED` and says nothing about RF.
