# What the HaLow drivers honour: mesh point, and SAE

**Trade:** `TBR-LINUX-01`.
**Date:** 2026-08-31.
**Taken by:** Cameron Zobrist.
**Status of this artifact:** `UNVERIFIED`. **Read from published driver source
and from the local kernel configuration. No HaLow hardware exists in this
program and nothing here was executed on a radio.**

## Why this exists

`FML-ADR-061` decides that the field mesh is keyed with `key_mgmt=SAE` and that
MULEs merge automatically. It names one assumption as its largest:

> **`TBR-LINUX-01` owns whether the HaLow bearer supports SAE at all**, and that
> is the single largest unverified assumption in this ADR.

`os/config/wpa_supplicant.conf.template` had already flagged it: "Whether the
HaLow driver honours standard `wpa_supplicant` mesh options at all" is
unverified. Both HaLow vendors publish their drivers, so this is answerable by
reading rather than by buying.

**No HaLow module is selected.** `regions/us-915/profile.yml` has
`halow.permitted: TBD` and every parameter under it is `TBD`. This is research
into what is available, not a selection.

## The kernel side is already satisfied

An 802.11s mesh point in `mac80211` requires `CONFIG_MAC80211_MESH`. On the
Debian baseline this program targets, checked locally on the development
machine:

```text
CONFIG_MAC80211=m
CONFIG_MAC80211_MESH=y
```

Both HaLow drivers below gate their mesh support on exactly that symbol, so the
gate is closed on our OS baseline rather than open.

## Newracom NRC7292: mesh point, gated on the kernel symbol

From `package/src/nrc/nrc-mac80211.c` in `newracom/nrc7292_sw_pkg`, retrieved
2026-08-31:

```c
hw->wiphy->interface_modes =
    BIT(NL80211_IFTYPE_STATION) | BIT(NL80211_IFTYPE_AP) |
#ifdef CONFIG_MAC80211_MESH
    BIT(NL80211_IFTYPE_MESH_POINT) |
#endif
#if !defined(CONFIG_S1G_CHANNEL)
#ifdef CONFIG_SUPPORT_P2P
    BIT(NL80211_IFTYPE_P2P_CLIENT) | ...
```

**Mesh point sits outside the `CONFIG_S1G_CHANNEL` guard**, which is the guard
that removes P2P when the driver is built for sub-GHz. So mesh is offered in the
HaLow configuration, not only in a 2.4 GHz build.

It is not a bare declaration. The driver carries mesh through its S1G beacon
path:

```text
BSS_CHANGED_BEACON_ENABLED flag is used only for AP and MESH.
AP/MESH : When 'enable_short_bi' is true (AP will send S1G beacons ...
```

**No SAE handling was found**, in `nrc-mac80211.c`, `nrc-init.c` or `wim.c`. See
the caveat below before reading anything into that.

## Morse Micro: mesh point, a dedicated mesh implementation, and SAE by name

From `MorseMicro/morse_driver`, retrieved 2026-08-31. Same interface-mode
pattern:

```c
hw->wiphy->interface_modes =
    BIT(NL80211_IFTYPE_AP) |
    BIT(NL80211_IFTYPE_STATION) |
#if MESH_CONFIG_ENABLED(MAC80211_MESH)
    BIT(NL80211_IFTYPE_MESH_POINT) |
#endif
    BIT(NL80211_IFTYPE_ADHOC);
```

The repository ships **`mesh.c` at 27 kB and `mesh.h` at 11.9 kB**, a purpose-
built mesh implementation rather than a declaration.

**And it names SAE explicitly, in mesh:**

```c
is_mesh_auth_frame = ieee80211_is_auth(fctl) && (auth_alg == WLAN_AUTH_SAE);
...
case IEEE80211_STYPE_AUTH:
    if (!sta && is_mesh_auth_frame) {
        /* Peer will retry the auth frame and by then supplicant will have peer info */
```

It also handles `PLINK_OPEN` and `PLINK_CONFIRM`, which are 802.11s Mesh Peering
Management frames.

That comment is the useful part: the driver expects **the supplicant** to hold
peer state and expects SAE auth frames to arrive in mesh mode. That is precisely
the arrangement `FML-ADR-061` depends on, and this vendor has written code for
it.

Morse Micro additionally maintains a `hostap` tree of their own, last pushed
2026-07-18, and an `rpi-linux` tree carrying their patches for Raspberry Pi LTS
kernels.

## A drift this research exposed

The program already leans on Morse Micro without having decided to. SAD source
register `SR-011` cites `MorseMicro/morse_driver` and **MM8108** by name as the
"kernel/driver lifecycle risk basis"; `FML-ADR-021` lists "the Morse Micro Linux
driver stack"; `FML-ADR-046` has the status aggregator consuming "Morse Micro
driver interfaces". Only `FML-ADR-040` hedges, with "the Morse Micro **or
other** out-of-tree radio driver set".

**No ADR selects a HaLow module.** `TBR-RF-01`, `TBR-RF-03` and `TBR-HW-01` are
open and `regions/us-915/profile.yml` records `halow.permitted: TBD`. A reader
of `FML-ADR-021` or `FML-ADR-046` could reasonably conclude otherwise, which is
how a vendor gets selected by repetition rather than by decision.
`FML-ADR-062` records that it is not settled.

## What this changes

`FML-ADR-061`'s largest assumption is **substantially reduced, not removed.**
Mesh point is offered by both candidate vendors on the sub-GHz path, the kernel
symbol they depend on is already set on the Debian baseline, and one vendor has
written explicit mesh-SAE frame handling.

## What this does not establish, and some of it matters a great deal

**Nothing was executed.** This is source reading. No HaLow radio exists in this
program, `TBR-RF-01` and `TBR-HW-01` have selected no module, and
`regions/us-915/profile.yml` records `halow.permitted: TBD`, so whether HaLow
may be operated here at all is itself undecided.

**The absence of SAE in the Newracom source is not evidence of absence.** SAE
for a `mac80211` softmac driver is performed by `wpa_supplicant` in userspace;
the driver only has to carry authentication frames, and most drivers therefore
contain no SAE code at all. Three files were searched, not the whole package of
41. Morse Micro's explicit handling shows a vendor who tested the path; the
Newracom silence shows nothing either way, and **it would be wrong to select
between vendors on this artifact.**

**Mesh at S1G channel widths is untested.** HaLow channels are 1, 2, 4, 8 and 16
MHz. Nothing here shows that peering, beaconing and AMPE behave at 1 MHz, which
is the configuration the range argument for HaLow depends on.

**Firmware is a separate dependency.** Both vendors ship binary firmware, Morse
Micro from a `firmware_binaries` repository. An out-of-tree driver plus a
firmware blob is exactly the lifecycle risk `TBR-LINUX-01` exists to assess, and
`FML-ADR-040`'s kernel promotion gate applies to both.

**Neither driver is in the mainline kernel.** Both are out-of-tree, so every
kernel update is a rebuild-and-retest event under the promotion gate.

**Nothing about throughput, range, latency or coexistence with LoRa in the same
band**, which is `TBR-RF-01`, `TBR-RF-02` and `FML-ADR-027`.
