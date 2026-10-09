# GAP-09H: the pi4b-arm64 profile cross-built three times, in CI and in a cloud session

**Tier:** `SIMULATED`. Nothing here booted on a Pi, and `FML-ADR-088` does not
accept a QEMU boot in place of one. **Date:** 2026-10-09. **Who:** Claude agent,
through `.github/workflows/image.yml` on PR #223 and in its cloud session.
**Finding:** GAP-09H gap G1, the arm64 condition "an arm64 artifact is
produced".

## What this is

The `FML-ADR-081` build sequence run on the `FML-ADR-088` profile:

- two clean networked builds;
- one build with external network access unavailable, from the first build's
  cache;
- a comparison of the three raw images.

There is no boot. Acceptance for the profile is bench card BC-1 on a physical
Pi 4B, and that has not been run.

## Result

Both hosts ran `tools/verify-image-reproducibility.sh --profile pi4b-arm64` to
exit 0. On each host the three raw images were identical.

| Item | CI | Cloud session |
| --- | --- | --- |
| Source | PR #223 head `175454c`, as GitHub's merge with `main` | the same tree, copied from the working copy |
| Run | Actions run `37959824179`, job `113919517347`, 16:32:15Z to 16:54:24Z | one container run, 1950 s |
| Raw image SHA-256, all three builds | `468f2008ba676e526b11c7d43129a12361c16c57e3b91ab532c74cd4fb75bb05` | `14974840fbdbeec110e89edc60deb25e70a927867c7406d79cd1183b8baf2f07` |
| `mule-development-pi4b.sbom.cdx.json` SHA-256 | `756ec673c997f805ea8fc9330e6082bd42ed420ce23ad5b83a954293d12aaeb7` | same |
| `mule-development-pi4b.license-exceptions.json` SHA-256 | `41cb0e1adea8fe593251e08db35caee394c8c6022a2fa5e5197d780552702e8b` | same |
| Host emulator (`host-emulator.txt`, the `FML-ADR-088` record) | `qemu-user` and `qemu-user-binfmt` `1:10.0.13+ds-0+deb13u1` | same |
| binfmt handler | `qemu-aarch64`, flags `POF` | same |
| Build environment | Debian 13 container `mirror.gcr.io/library/debian@sha256:9cc080028c43b27d2074d63a5f9caf7166d731494965616c1a6d2827a004585c`, mkosi `25.3-7` | same |

In the session run, the isolated build's log shows "Building tools image". So
the amd64 tools tree was rebuilt from the cache with the network unavailable,
as it is in the x86-64 sequence.

## What the image contains

An earlier session build produced an image with the same raw hash
(`14974840...`). It was built before the two fixes below, neither of which
changes the image. Its partitions were read by offset from the GPT, without
booting.

- Partition 1 is the ESP type, 512 MiB, vfat. It holds the Pi 4 firmware
  (`start4.elf`, `fixup4.dat` and the other `start*`/`fixup*` files,
  `bootcode.bin`) and `bcm2711-rpi-4-b.dtb` among other device trees. It also
  holds `overlays/`, `vmlinuz-6.12.107+deb13-arm64` and
  `initrd.img-6.12.107+deb13-arm64`.
- `config.txt` sets `arm_64bit=1`, `enable_uart=1` and `upstream_kernel=1`,
  plus `kernel=` and `initramfs` lines naming that kernel and initrd.
- `cmdline.txt` reads: `console=tty0 console=ttyS1,115200 root=LABEL=mule-root rw
  fsck.repair=yes net.ifnames=0  rootwait systemd.unit=multi-user.target
  systemd.show_status=yes systemd.firstboot=no`. There is no `cma=`.
- Partition 2 has the arm64 root partition type `b921b045-...`, GPT name
  `mule-root`, and ext4 with `LABEL=mule-root`.
- `/etc/default/raspi-firmware` carries the profile's `ROOTPART`, `CONSOLES`
  and `CMA=0`.

## Defects the first arm64 builds found, fixed in PR #223

- **The tools-tree lock was incomplete (`FML-ADR-081`).** mkosi 25.3 installs
  `systemd-boot` in every Debian tools tree after bullseye. The source is
  `mkosi.conf.d/10-debian-kali-ubuntu/mkosi.conf.d/systemd-boot.conf`, and
  `systemd-boot` pulls in `systemd-boot-tools`. Neither was in the lock.
  - The x86-64 cache validator could not notice, because both are also x86-64
    target packages.
  - The arm64 cache failed on them.
  - The lock now carries 456 packages.
- **The isolated build could not rebuild the tools tree.**
  - mkosi gives the tools tree the image's package cache (`__init__.py`,
    `finalize_default_tools`), and APT keeps one lists directory there
    (`installer/apt.py`, `subdir()`).
  - The arm64 sync runs second, and apt-get's default list cleanup erased the
    amd64 lists.
  - CI failed with `E: Unable to locate package base-files`.
  - A separate agent confirmed the mechanism with apt alone and found the
    route. The profile's sandbox now sets `APT::Get::List-Cleanup "false";`,
    and `tools/validate-image.py` requires it.

## What it does not show

- **That a Pi boots it.** The firmware stage, the `LABEL=` root lookup, and
  Wi-Fi, AP mode and the RTC on this kernel are BC-1's questions.
- **Reproducibility across hosts.** The two hosts produced different raw images
  from the same inputs, while the SBOM and licence report are byte-equal. The
  cause is not established. `FML-ADR-081` claims identity between builds on
  one host only. BC-1's rebuild-identity step compares a build against the
  flashed image, so it should be run on the host that built that image, or
  this difference must be explained first.

## Retained privately

Nothing. The job's `image-evidence-pi4b-arm64` artifact is kept by GitHub for
its retention period only. The raw images were not retained.
