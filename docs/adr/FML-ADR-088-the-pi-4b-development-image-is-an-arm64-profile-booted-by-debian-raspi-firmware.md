---
id: FML-ADR-088
title: The Pi 4B development image is an arm64 profile booted by Debian raspi-firmware
status: PROPOSED
date: 2026-10-04
supersedes: none
superseded-by: none
trades: [TBR-HW-01, TBR-LINUX-01]
verification: TBD
---

# FML-ADR-088 The Pi 4B development image is an arm64 profile booted by Debian raspi-firmware

## Context

The `v0.0.1` article is a Raspberry Pi 4B (GAP-09E,
`docs/evidence/findings/GAP-09E/2026-10-03-arm64-development-article.md`), but
the development image is x86-64 only: `FML-ADR-079` decides "The Debian 13
x86-64 development image", and `FML-ADR-081` fixes an amd64 kernel and the
`systemd-boot` UEFI chain. Gap G1 of the operator procedure stays open until
"an arm64 artifact is produced"
(`docs/evidence/findings/GAP-09H/2026-09-26-operator-procedure.md`). Meanwhile
the lab Pis run hand-provisioned Debian with a Raspberry Pi vendor kernel
(`6.18.50+rpt-rpi-v8`), so no repository-built image has met the article.

Both earlier ADRs leave room for an architecture profile. `FML-ADR-079`'s
status says "`TBR-HW-01` may select a non-x86 production compute article.
Either trade can trigger a replacement image mechanism or architecture profile
without invalidating this development result." This one follows GAP-09E's
choice of development article, not an outcome of either trade.

The Pi 4B does not run the existing chain natively. Its EEPROM bootloader loads
GPU firmware and `config.txt` from a FAT partition, and a UEFI loader needs
u-boot or third-party firmware in between. The Program Owner chose the
direction on 2026-10-04, in the Claude Code cloud session that prepared this
record: Debian's `raspi-firmware` with the stock Debian arm64 kernel and no
UEFI loader. The alternatives were Debian's `u-boot-rpi` chainloading
`systemd-boot`, and the Raspberry Pi vendor kernel and archive. The vendor
archive would add a non-Debian source against `FML-ADR-081` and `FML-ADR-022`,
and would decide part of `TBR-LINUX-01`.

What `raspi-firmware` does was read from its own package at the pinned snapshot
(`snapshot.debian.org` `20260912T000000Z`, `raspi-firmware`
`1.20240424+ds-6`, `non-free-firmware/misc`, `Depends: dosfstools`). It has not
yet been observed in a build:

- Its `postinst` copies the GPU firmware to `/boot/firmware` and then runs its
  kernel hook. Both skip the mount-point check under `ischroot`. That should
  report a chroot, because dpkg runs maintainer scripts chrooted into the image
  root (mkosi passes `--root=/buildroot`). mkosi also writes
  `/run/host/container-manager`, which `systemd-detect-virt` reads.
- The kernel hook, `/etc/kernel/postinst.d/z50-raspi-firmware`, copies the
  newest `/boot/vmlinuz-*`, `/boot/initrd.img-*` and `bcm*.dtb` files to
  `/boot/firmware`, and generates `config.txt` and `cmdline.txt` there. If no
  initrd exists, it prints "no initrd found in /boot/initrd.img-*, cannot
  populate /boot/firmware" and exits 0.
- Unless `ROOTPART` is set in `/etc/default/raspi-firmware`, the hook derives
  the root device from `findmnt` on `/`. Inside a build that names the build
  host's mount, not the Pi's root partition.
- With `CONSOLES="auto"` the hook probes `/dev` for consoles. Its own comment
  reads: "ttyS1 is used in arm64 (RPi families 3, 4)".
- The hook identifies a Pi 4 by reading `/sys/firmware/devicetree/base/model`.
  mkosi's package sandbox mounts `run`, `tmp`, `proc` and `dev` but not `sys`
  (`mkosi/run.py`, `apivfs_options`), so that check is false in any build. With
  the default `CMA=64M` the hook then writes `cma=64M`, where its own comment
  says "specifying CMA as with earlier models renders it unbootable".
- The generated command line carries `net.ifnames=0`, so the image keeps the
  kernel names `eth0` and `wlan0` that `nodes/pi-mule-1/node.yml` uses. It
  writes `cmdline.txt` itself, so nothing reads mkosi's `KernelCommandLine=`.

Of mkosi `25.3`, at the pinned upstream commit `54c625c`. On `Bootable=`: "If
disabled, no bootloader will be installed even if found inside the image, no
unified kernel images will be generated and no ESP partition will be added to
the image if the disk output format is used." Its Debian installer exports
`INITRD=No` to the package manager unless `Bootable` is disabled
(`mkosi/installer/apt.py`), and initramfs-tools' kernel hook then generates no
initrd. When `mkosi.repart/` exists, or `RepartDirectories=` is used, "we will
not use any of the default partition definitions". And on `Architecture=`:
"When building for a foreign architecture, you'll also need to install and
register a user mode emulator for that architecture".

Of the Pi 4 EEPROM bootloader: the release promoted on 2020-09-14 lists "Add
support GPT and Hybrid MBR partition tables", and an earlier one resolves "USB
boot fails if the GPT contains no basic data or EFI partitions"
(`raspberrypi/rpi-eeprom`, `firmware-2711/release-notes.md`). The image is GPT
(`Format=disk`).

## Decision

The development image shall gain an arm64 profile for the Raspberry Pi 4B,
built by the same mkosi mechanism, snapshot and provenance rules as the x86-64
profile. The x86-64 profile is unchanged.

In the arm64 profile:

- The kernel shall be Debian's `linux-image-arm64`. The Pi boot files shall come
  from Debian's `raspi-firmware`. No UEFI bootloader shall be installed:
  `Bootable=no`. This is load-bearing: it is what lets initramfs-tools generate
  `/boot/initrd.img-*`, without which the hook copies no kernel and the build
  still succeeds.
- The image validation shall fail if `/boot/firmware` lacks `vmlinuz-*`,
  `initrd.img-*`, `bcm2711-rpi-4-b.dtb`, `start4.elf`, `config.txt` or
  `cmdline.txt`.
- The target repositories shall enable the `non-free-firmware` component,
  because `raspi-firmware` lives there. Its packages go through the same
  licence-exception report. Its DEP-5 copyright file declares `Proprietary_1`
  and `Proprietary_2`, so it is expected to be listed.
- The disk layout shall be an explicit repart definition, selected by
  `RepartDirectories=` in the arm64 profile only, so the x86-64 profile keeps
  mkosi's defaults. The FAT partition shall be `Type=esp` or Microsoft basic
  data, formatted `vfat`, populated with `CopyFiles=/boot/firmware:/`, which
  resolves against the image root. systemd-repart formats `vfat` as FAT32,
  which the 2020-09-14 EEPROM floor reads on GPT.
- `/etc/default/raspi-firmware` shall set `ROOTPART` to an identifier the
  repart definition assigns, `CONSOLES` explicitly (`ttyS1` is the arm64 Pi 4
  serial console according to the package itself), and `CMA=0`, so none of the
  three is derived from the build host. `GPU_FREQ` cannot take effect from any
  build, and is not set.
- `/etc/default/raspi-extra-cmdline` shall carry the x86-64 profile's
  non-console kernel parameters (`systemd.unit=multi-user.target
  systemd.show_status=yes systemd.firstboot=no`), because the hook writes
  `cmdline.txt` and mkosi's `KernelCommandLine=` does not reach it.
- The profile shall have its own `ImageId` and `Seed`, its own target lock and
  direct-package list, and its own SBOM and licence report.
- The build host should be the N150 development article, cross-building with
  Debian's `qemu-user-binfmt` registered on the host. The existing amd64
  tools-tree lock then serves both profiles. The host's `qemu-user` version
  shall be recorded with each build's provenance, since it is outside the
  tools-tree lock. A native build on a Pi may replace this if emulation breaks
  reproducibility, at the cost of an arm64 tools-tree lock.
- Acceptance shall be on a physical Pi 4B whose EEPROM bootloader is from the
  2020-09-14 release or later, and the acceptance record shall include that
  version. A QEMU boot shall not stand in for acceptance: QEMU's `raspi4b`
  machine does not execute the VideoCore firmware or read `config.txt`. A
  `raspi4b` boot of the generated kernel, DTB, initrd and `cmdline.txt` should
  be used as a pre-flight check of the root and initramfs stage.

This ADR does not decide which packages the image carries for M1. That is the
GAP-09H G8 decision packet, prepared on branch `claude/c2-m1-runtime-packet`,
and a separate decision.

## Status

`PROPOSED`. It is written for the Program Owner's acceptance and carries no
weight until then. Accepted, it is meant as a `SELECTED PLANNING BASELINE` for
a development-article profile, revisited by `TBR-HW-01` and `TBR-LINUX-01`, not
a `TBR-HW-01` selection: the field article named in the prototype BOM is a CM4,
and `TBR-LINUX-01` still owns the production kernel and driver set.

## Consequences

- G1's arm64 condition, "an arm64 artifact is produced", becomes reachable.
  This ADR adds a physical boot before the profile is accepted.
- The image's archive policy widens from `main` to `main` plus
  `non-free-firmware` for one profile. The licence-exception report gains
  non-free firmware entries, which an auditor sees.
- `tools/resolve-image-packages.py`, `tools/validate-image.py` and
  `os/image/build-inputs.yml` become per-target; each hardcodes amd64 or
  x86-64 today. `tools/build-image.sh` and
  `tools/verify-image-reproducibility.sh` become per-target too; they assume
  one image directory, the `mule-development` output and a QEMU boot. Their
  tests gain arm64 fixtures.
- Building under user-mode emulation is slower than a native build, and its
  byte-for-byte reproducibility is unproven. The first repeated build
  establishes it.
- A contributor without a Pi can build the arm64 image, inspect
  `/boot/firmware`, and run the `raspi4b` pre-flight, but cannot verify the
  firmware stage. CI cannot either.
- The Debian kernel is not the vendor kernel the lab Pis run. Wi-Fi, AP mode
  and the RTC on this kernel are questions the acceptance run answers. That is
  the point: it is the Linux/radio boundary this program has not yet confronted
  with a repository-built image.

## Accepted cost

The vendor kernel's Pi-specific drivers and tuning are given up for this
profile. If the Debian kernel cannot field the CYW43455 as an access point, or
lacks something the bench depends on, that is discovered on the Pi, not
avoided. The vendor-kernel option would have avoided it at the price of a
second archive.

## Fallback

If `raspi-firmware`'s kernel hook cannot produce a booting image from a build
tree, keep its GPU firmware and set `KERNEL=u-boot.bin` and `INITRAMFS=no` so it
loads Debian's `u-boot-rpi`, chainloading the existing `systemd-boot` chain.
If mkosi cannot build the profile, `FML-ADR-079` already names `debos` as its
fallback. If the Debian kernel cannot run the AP on the CYW43455, the vendor
kernel returns as a question for `TBR-LINUX-01`, not as a quiet substitution
here. The signal for each is a failed step of the acceptance run, recorded as
evidence.

## Superseded by

None.

## Verification dependency

A bench card, not yet written. On a physical Pi 4B it builds the arm64 profile,
flashes it, cold-boots it, and records the boot log, raw-image SHA-256, SBOM
hash, a byte-identical rebuild and the EEPROM bootloader version. On the stock
Debian kernel it also records whether `wlan0` appears, whether `iw list` shows
AP mode, and whether `hostapd` starts. Those checks presuppose
`firmware-brcm80211` in the image, which `raspi-firmware` does not supply; if
the G8 decision has not added it, the run records that it is absent instead of
a driver result. `TBR-LINUX-01` defines what those checks are required to show
before they count toward it.
