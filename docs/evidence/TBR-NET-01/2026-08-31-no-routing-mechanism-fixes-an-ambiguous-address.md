# The four candidate mechanisms, measured

**Trade:** `TBR-NET-01`.
**Date:** 2026-08-31.
**Taken by:** Cameron Zobrist, on the lab development machine.
**Status of this artifact:** `SIMULATED`. `batman-adv` over `veth` in network
namespaces. **No radio was involved.**
**Reproduced by:** `test/bench/route-isolation.sh`.

## Why this exists

`2026-08-31-external-network-collision-analysis.md` named four candidate
mechanisms and said plainly that none was measured. This trade's decision was
next, and `FML-ADR-060` had been superseded one day after it was written for
deciding a consequence of something untested. Measuring first was the guard
against doing that twice, and it was needed: **the mechanism that looked
obvious does not work.**

## The results

Baseline is a node with `10.41.0.0/16` on `bat0`, two mesh peers -- one at
`10.41.5.7` inside the venue's range and one at `10.41.9.9` outside it -- and an
uplink holding a lease from a venue LAN using `10.41.5.0/24`.

| Configuration | mesh node inside the range | mesh node outside | venue gateway |
| --- | --- | --- | --- |
| **Baseline** | **LOST** | ok | ok |
| Policy routing, mesh prefix in its own table | ok | ok | **LOST** |
| No overlapping lease on the uplink | ok | ok | **LOST** on the old range, ok on a new one |
| VRF, from an **ordinary** application | **LOST** | **unreachable** | ok |
| VRF, from a **VRF-aware** application | ok | ok | **LOST** |

## What each one actually does

**Policy routing does not fix the failure. It moves it.** An `ip rule` sending
`10.41.0.0/16` to a table holding the mesh route recovers both mesh peers and
loses the venue gateway, which is itself inside `10.41.0.0/16`. Exempting the
venue's `/24` with a higher-priority rule restores the gateway and loses the
mesh node again, because `10.41.5.7` is inside that `/24`. The two rules cannot
both be satisfied.

**No overlapping lease works and is not a mechanism.** With the uplink addressed
outside the mesh prefix nothing overlaps and nothing is lost. But the venue
chooses the range it hands you, and this program does not control it. It is a
description of a lucky case.

**A VRF separates them, per application, and no application gets both.** With
`bat0` enslaved to a VRF, an ordinary application loses the mesh entirely -- not
just the overlapping part: `10.41.9.9` becomes `Network is unreachable`, because
the mesh route now lives only in the VRF's table. An application bound into the
VRF reaches both mesh peers and loses the venue. **That is the honest
description: the VRF gives a mesh-using application the mesh and a venue-using
application the venue, and nothing sees both.**

## The finding

**`10.41.5.7` is claimed by two networks at once.** No routing mechanism can
disambiguate a destination that is genuinely ambiguous. It can only choose which
claimant to serve, and every row above is that choice being made somewhere
different: per destination, per prefix, or per application.

So the trade's remaining question is not "which routing mechanism". It is
whether the mesh can hold address space an uplink will not also claim, which is
an addressing decision, and what a node does when it cannot.

**This connects to `FML-ADR-061`.** That ADR already forces per-deployment
prefixes for any interoperation. Per-deployment prefixes do not eliminate
overlap with an arbitrary venue, but they make a fixed program-wide prefix --
the thing that guarantees every deployment collides with the same venues --
strictly worse than the alternative.

## What this does not establish

**No mechanism is selected, and this artifact must not be read as selecting
one.** The VRF row is the only one that separates the two networks, and the cost
is that **every mesh-using application must bind into the VRF**: ATAK on an EUD,
the TAK server, `meshtasticd`, `dnsmasq`. Whether they can is untested and is a
large question.

**Nothing about a Tailscale subnet router**, which is the other route source the
collision analysis identified and which needs a tailnet to test. The `/17` case
recorded there is unaddressed by any candidate here.

**`veth`, not radios. One venue, one overlapping `/24`, two mesh peers.** A real
incident has more of everything, and nothing here was measured under load or
during a partition.

**No IPv6.** The link-local result in
`docs/evidence/TBR-NET-03/2026-08-30-what-happens-with-no-configuration.md` is
relevant, because a link-local address cannot be claimed by an uplink route at
all, and it is not tested here.
