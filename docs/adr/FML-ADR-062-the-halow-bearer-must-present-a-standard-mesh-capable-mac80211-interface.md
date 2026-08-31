---
id: FML-ADR-062
title: The HaLow bearer must present a standard mesh-capable mac80211 interface
status: SELECTED PRINCIPLE
date: 2026-08-31
supersedes: none
superseded-by: none
trades: [TBR-LINUX-01, TBR-RF-01, TBR-RF-03, TBR-HW-01]
verification: Stage 2
---

# FML-ADR-062 The HaLow bearer must present a standard mesh-capable mac80211 interface

**Source of rationale:**
`docs/evidence/TBR-LINUX-01/2026-08-31-halow-driver-mesh-and-sae-support.md`.

## Context

`FML-ADR-061` requires a keyed 802.11s mesh. Whether the HaLow bearer can
provide one was researched in both candidate vendors' published driver source.
Both offer `NL80211_IFTYPE_MESH_POINT` on the sub-GHz path, both gate it on
`CONFIG_MAC80211_MESH` which the Debian baseline already sets, and one contains
explicit mesh-SAE frame handling.

**The obvious next step is to baseline one of the two vendors. This ADR
deliberately does not**, for reasons below, and baselines what they have in
common instead.

**A drift worth naming.** The program is already leaning on Morse Micro without
having decided to:

- SAD source register `SR-011` cites `MorseMicro/morse_driver` and **MM8108** by
  name, as the "kernel/driver lifecycle risk basis".
- `FML-ADR-021` lists "the Morse Micro Linux driver stack" among the ordinary
  Linux components MULE relies on.
- `FML-ADR-046` has the status aggregator consuming "Morse Micro driver
  interfaces".
- `FML-ADR-040` is the only one that hedges: "the Morse Micro **or other**
  out-of-tree radio driver set".

No ADR selects a HaLow module, `TBR-RF-01`, `TBR-RF-03` and `TBR-HW-01` are all
open, and `regions/us-915/profile.yml` records `halow.permitted: TBD`. A reader
of `FML-ADR-021` or `FML-ADR-046` could reasonably conclude the vendor is
settled. **It is not**, and this ADR says so where a reader will find it.

## Decision

**The Wi-Fi HaLow bearer shall present as a `mac80211`/`cfg80211` driver that
offers `NL80211_IFTYPE_MESH_POINT` and carries authentication frames for
userspace SAE.**

A candidate module whose vendor supplies only a proprietary SDK, a
`netdev`-only shim, or a stack that does not expose mesh point through
`nl80211` **shall not be selected**, whatever its RF performance.

**This ADR selects no vendor.** Which module provides the interface is
`TBR-RF-01`, `TBR-RF-03` and `TBR-HW-01`.

## Status

`SELECTED PRINCIPLE`. The property is decided; the module that provides it is
not, and the ADR naming the module will **not** supersede this one.

## Consequences

`FML-ADR-061`'s keyed mesh becomes a stated requirement on the radio rather than
a hope about it, so a module that cannot support it is disqualified at selection
rather than discovered later.

Configuration work in `os/config/` can proceed against `iw`, `wpa_supplicant`
and `nl80211` without waiting for a module, because the interface is now fixed
even though the hardware is not.

It **narrows the candidate field**, and that is the point. Some HaLow modules
ship SDK-only stacks. This rules them out before RF numbers make them tempting.

Both currently known candidates satisfy it, so nothing available is excluded
today.

## Accepted cost

**A module may be excluded that has better RF performance.** If a
non-`mac80211` stack turns out to be materially better on range or power, this
decision costs that, and revisiting it means a superseding ADR rather than a
quiet exception.

**This is decided on source reading, not measurement.** No HaLow radio exists
in this program. The interface requirement is safe to state early precisely
because it constrains selection rather than asserting performance, but it is
not evidence about what the radios do.

## Fallback

If no available module satisfies the requirement, the fallback is
`FML-ADR-061`'s: the field mesh runs on a bearer that does, and HaLow is used
for something else or not at all. That is a large change and would need a
superseding ADR, which is the intended friction.

## Superseded by

None.

## Verification dependency

Stage 2, with `FML-ADR-040`'s promotion gate. Both known candidate drivers are
**out-of-tree and ship binary firmware**, so every kernel update is a
rebuild-and-retest event, which is the risk `TBR-LINUX-01` exists to assess and
which this ADR does not reduce.

**Untested and material:** mesh at 1 MHz S1G channel width, which is the
configuration HaLow's range argument depends on.
