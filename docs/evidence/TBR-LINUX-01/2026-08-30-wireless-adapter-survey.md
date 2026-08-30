# Can the wireless hardware on hand join an 802.11s mesh

**Trade:** `TBR-LINUX-01`.
**Date:** 2026-08-30.
**Taken by:** Cameron Zobrist, on the lab development machine.
**Status of this artifact:** `UNVERIFIED` as a statement about the MULE. It is a
measurement of two adapters that are **not** the selected hardware, because
none is selected. It is a real result about real silicon and it says nothing
about what a MULE will ship with.

## Why this exists

`FML-ADR-053` baselines BATMAN-IV and `FML-ADR-024` before it selected IEEE
802.11s for mesh association. Nothing in this repository had ever asked a real
adapter whether it can do 802.11s at all. Two were to hand, so they were asked.

## Configuration

| Item | Value |
| --- | --- |
| Host | Debian 13, kernel `6.12.105+deb13-amd64`, x86_64 |
| Adapter A | Internal, `rtw89_8852be`, PCIe |
| Adapter B | USB `0bda:8812`, "RTL8812AU 802.11a/b/g/n/ac 2T2R DB WLAN Adapter" |
| Tooling | `iw` 6.9-1, `modinfo` from `kmod` |

Antenna, separation, orientation and ambient are not recorded: nothing here
transmitted. These are capability and driver-binding results.

## Adapter A: the internal card cannot do mesh point

`iw phy phy0 info` reports the supported interface modes as:

```text
managed, AP, AP/VLAN, monitor, P2P-client, P2P-GO
```

`mesh point` is absent. Asked directly:

```text
# iw dev wlp2s0 interface add mesh0 type mp
command failed: Operation not supported (-95)
```

**A trap worth recording, because it would have produced a false positive.**
Grepping `iw phy phy0 info` for "mesh" returns four hits: `set_mesh_config` and
`join_mesh` under supported commands, and `mesh point` twice under frame-type
capabilities. None of them means the adapter can be a mesh point. The
authoritative facts are the interface mode list and the `-95` above. A check
that looked for the word would have concluded the opposite of the truth.

## Adapter B: no driver binds to it at all

The device enumerates and stops there. No driver on the USB interface, no
netdev, no `phy`.

Four in-tree Realtek drivers were checked for an alias claiming `0bda:8812`:

| Module | Aliases matching `v0BDAp8812` |
| --- | ---: |
| `rtl8xxxu` | 0 |
| `rtw88_usb` | 0 |
| `rtw88` | 0 |
| `rtlwifi` | 0 |

`modules.alias` for the running kernel carries no entry for the device either.
**Debian 13 ships nothing that drives this adapter.**

### The out-of-tree drivers do not build on this kernel

Two were tried against `6.12.105+deb13-amd64`, both from source, both failing
to compile:

| Source | Result |
| --- | --- |
| `aircrack-ng/rtl8812au` | `error: initialization of 'int (*)(struct wiphy *, struct net_device *, struct cfg80211_chan_def *)' from incompatible pointer type` on `.set_monitor_channel` |
| `lwfinger/rtl8812au` | fails in the wireless-extensions path, `union iwreq_data *wdata` |

Both are `cfg80211` and wireless-extensions API drift: the kernel moved and the
vendor trees did not follow.

**Worth noting for whoever picks this up:** the `aircrack-ng` tree does contain
802.11s support. Its Makefile builds `core/mesh/rtw_mesh.o`,
`rtw_mesh_pathtbl.o` and `rtw_mesh_hwmp.o`. So the chip plus a working driver
might well do mesh point. **That is not established**, because the driver does
not build, and a capability nobody has run is not a capability.

## What this means for the trade

`TBR-LINUX-01` asks whether a stock distribution kernel can drive the selected
radio or whether a patched or out-of-tree tree is required, and records that a
local fork is a program liability with a named owner and a rebase cadence.

This is that liability, demonstrated rather than argued, on the first two
adapters anyone tried:

- One adapter is fully supported in-tree and **cannot do the thing the
  architecture needs.**
- The other might do it and **has no working driver on the baseline OS.**

It is the same shape as the finding behind `FML-ADR-053`, which chose BATMAN-IV
partly to avoid "a custom kernel or the out-of-tree `batman-adv` module,
permanently, in the compatibility set `FML-ADR-040` governs, maintained by
volunteers." An out-of-tree Wi-Fi driver that already fails to compile against
the current stable kernel is that cost with a worked example attached.

## What this does not say

Neither adapter is a candidate for a MULE. No sub-GHz HaLow radio was tested,
and HaLow is what `FML-ADR-053` actually baselines the mesh on; its driver
situation is untouched by this and remains the substance of the trade.

Nothing here transmitted, so there is no result about range, throughput,
coexistence or power.

## What would close the gap

Ask any candidate adapter, before purchase, in this order:

1. Does `iw phy <phy> info` list **`mesh point`** under supported interface
   modes? Not "does it mention mesh".
2. Does `iw dev <dev> interface add mesh0 type mp` succeed?
3. Is the driver in-tree on Debian stable, and does `modinfo` show an alias for
   the USB or PCI id?

The first two take a minute on a board somebody already owns, and would have
saved this program from selecting hardware that cannot form the mesh its
architecture is built on.
