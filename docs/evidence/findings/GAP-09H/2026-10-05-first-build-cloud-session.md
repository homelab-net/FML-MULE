# GAP-09H: first build and QEMU boot of the current x86 closure, in a cloud session

**Tier:** `SIMULATED`. A virtual machine says nothing about the Pi, the access
point or any radio. **Date:** 2026-10-05. **Who:** Claude agent, cloud session,
with a separate agent qualifying the environment first (`CLAUDE.md`, Done rule
7). **Finding:** GAP-09H gap G1, the x86 half.

## What this is and is not

One `tools/build-image.sh --populate-cache` build and one bounded QEMU boot of
its output. It is **not** the `FML-ADR-081` acceptance sequence: that needs two
clean networked builds, one network-isolated cache-only build, and identical
raw images. `tools/verify-image-reproducibility.sh` runs that sequence, and it
remains to be run (step S2 of the cloud plan moves it into CI).

## What it found

- **A repository defect, fixed in the same change.** The first in-session build
  failed in `os/image/mkosi.postinst`: "The target shall contain exactly one MULE
  runtime entry point." Debian's `sysconfig` sends `pip install --prefix /usr` to
  `/usr/local` unless `DEB_PYTHON_INSTALL_LAYOUT` is `deb`, so the runtime, its
  unit and the mission schema landed where the postinst does not look. The pip
  step landed in #176 (`FML-ADR-083`, 2026-09-25), after GAP-09C's last build
  on 2026-09-20. The image could not have built on any host since, the N150
  included.
- **With the fix, the build succeeds and the image boots to
  `multi-user.target`** with no guest network, with a login prompt on the
  console.
- **Three units failed during boot:** `systemd-pcrlock-firmware-code.service`,
  `systemd-pcrlock-firmware-config.service` and
  `systemd-pcrlock-make-policy.service`. They did not prevent
  `multi-user.target`. Their cause was not established: the console was
  non-interactive, so `systemctl status` could not be read. "pcrlock" appears
  nowhere else in this repository, and GAP-09C retained no boot log to compare
  against. The probe boot planned for CI is the place to capture their journal.

## Configuration

| Item | Value |
| --- | --- |
| Source | `main` at `f1365d7`, plus the `os/image/mkosi.postinst` fix in this change |
| Host | Claude Code cloud container: 4 CPUs, 15 GiB RAM, 29 GiB free, root, **no `/dev/kvm`** |
| Build environment | Privileged `debian:13` container, `mirror.gcr.io/library/debian@sha256:9cc080028c43b27d2074d63a5f9caf7166d731494965616c1a6d2827a004585c` (Docker Hub returned HTTP 429), `--network host` through the session proxy |
| Builder | Debian `mkosi` `25.3-7`, retained package verified by `tools/resolve-mkosi-builder.sh` against `os/image/build-inputs.yml` |
| Package inputs | snapshot `20260912T000000Z` via the image's own sandbox trees |
| Build | `tools/build-image.sh --populate-cache`: exit 0, 214 s |
| Raw image SHA-256 | `b07b3dca37c05acffd5dca879001e65e5e38065696a53b0ff8be036ced88d0af` (1.0 GiB, 666.5 MiB allocated) |
| SBOM | 260 components; SHA-256 `d764eb1133c755be08293e4f2632cc41a523a709b04def03e9a64150e18208b3` |
| Package cache | "Retained package cache: 0 defects." |
| Boot | The VM step of `tools/verify-image-reproducibility.sh` verbatim (`--runtime-network=none --console=native vm </dev/null`), bound raised from 180 s to 1500 s because QEMU ran under TCG without KVM |
| Boot result | `[  OK  ] Reached target multi-user.target - Multi-User System.` then `localhost login:`; ended by the bound (exit 124, which the script accepts) |
| Boot log | `2026-10-05-first-build-cloud-session-qemu-boot.log`, carriage returns stripped, SHA-256 `0186b7bf75356541dfbf18e6a2b6094ba03166417e79f4e3b45c961460c5272e` |

The package resolver was also run in this environment by the qualifying agent:
`tools/resolve-image-packages.py --keyring /usr/share/keyrings/debian-archive-keyring.gpg`
without `--write`, exit 0 after 737 s, output identical to the committed
`target-lock.json` and `tools-tree-lock.json`.

## What this changes

- Cloud sessions can build the image and boot it under QEMU (TCG). The BC-0
  card's statement that they cannot is corrected in the same change.
- The image builds again on any host.
