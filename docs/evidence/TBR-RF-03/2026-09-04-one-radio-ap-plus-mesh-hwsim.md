# One radio serving an access point and an 802.11s mesh at once

**Trade:** `TBR-RF-03` (option 1: one radio, multiple VIFs, same channel).
**Date:** 2026-09-04.
**Taken by:** Cameron Zobrist, with Claude Code, on the lab bench.
**Status of this artifact:** `SIMULATED` (`mac80211_hwsim`). It substantiates the
interface-combination and bridge model for consolidation; it says nothing about
RF, airtime contention, or any specific chip's real behaviour.

## Why it was run

`TBR-RF-03`'s option 1 is "one radio, multiple virtual interfaces, same
channel." It is also the lever that frees the carrier's single M.2 M-key slot:
on the current BOM that slot holds the high-rate mesh radio (SparkLAN QCA6174A),
so consolidating the AP and mesh onto one radio is what lets the M.2 carry a
storage SSD instead. See `TBR-CARRIER-01` and `docs/evidence/TBR-MAP-01/`.

## What the hardware advertises

A mesh-capable `mac80211` radio advertises a valid interface combination of
`#{ managed, AP, mesh point, P2P-client, P2P-GO } <= N, #channels <= 1`. That is
the silicon-level answer to option 1's question: **AP and 802.11s mesh point can
be instantiated on one radio at once, on one channel.**

A finding that narrows the hardware choice: the **RTL8812AU** (the USB adapter
used as the bench access point) advertises `IBSS, managed, AP, P2P` and **no
mesh point mode at all** -- Realtek's out-of-tree driver does not do 802.11s. So
the consolidated radio cannot be an RTL8812AU; it must be a mesh-capable chipset
(`ath9k`, `mt76`, or the `ath10k` QCA6174 itself), which also bears on
`TBR-LINUX-01`.

## What was brought up

On one `hwsim` radio, concurrently:

```text
Interface wlan0   type mesh point     (joined mesh, freq 2412)
Interface ap0     type AP             (hostapd, WPA2, channel 1)
```

Both live at the same time on the same phy and channel: the mesh point joined
and the AP beaconing. `batman-adv` (`BATMAN_IV`, `bridge_loop_avoidance 0` per
`FML-ADR-056`) ran over the mesh interface, and a bridge joined the AP interface
to `bat0` -- the `FML-ADR-056`/`057` bridge model. A **real EUD (a station on a
second radio) associated to `ap0` while the mesh was joined**, confirming the AP
serves clients concurrently with the mesh.

## What this does NOT establish

The end-to-end traffic path (EUD -> AP+mesh radio -> mesh -> peer node) was
**not** captured here: the run was aborted to protect the host after an unrelated
scripting error, and it is left for a repeat under a hwsim-driver-filtered
harness. What stands is: the interface combination is advertised, and the AP and
mesh VIFs plus an associated EUD were shown live on one radio. And nothing about
RF is shown -- `hwsim` models the 802.11 MAC only; airtime contention between the
AP and the mesh (the concrete risk `TBR-RF-03` names) needs real radios.

## Bearing on the trade

Option 1 is feasible at the interface-combination and bridge level, on a
mesh-capable chip (not the RTL8812AU). Whether it is acceptable depends on the
airtime-contention and stream/antenna-count evidence the closure gate demands,
which is hardware. The consolidation's value here is the **M.2 slot it frees for
storage**, which is the decision `TBR-CARRIER-01` must record.
