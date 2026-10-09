# GAP-09H: the FML-ADR-081 sequence on the current x86 closure, in CI

**Tier:** `SIMULATED`. A virtual machine says nothing about the Pi, the access
point or any radio. **Date:** 2026-10-09. **Who:** Claude agent, through
`.github/workflows/image.yml` on PR #222. **Finding:** GAP-09H gap G1, the x86
("any arch") half.

## What this is

The result record bench card BC-0 asks for
(`2026-10-04-bc0-x86-image-execution-card.md`, "What to record"), produced by
CI instead of on the N150. The Program Owner decided on 2026-10-05 that a
passing CI run of the unchanged `FML-ADR-081` sequence with a committed record
satisfies G1's x86 half, so BC-0 need not be run for G1. The record is
committed because Actions logs and artifacts expire.

## Result

`tools/verify-image-reproducibility.sh` exited 0: two clean networked builds
and one network-isolated cache-only build produced identical raw images, and
the isolated build's image reached `multi-user.target` under QEMU with no guest
network and no console input.

| Item | Value |
| --- | --- |
| Source | PR #222 head `df32f97`, checked out as GitHub's merge with `main` at `987f645` (merge commit `419129b`) |
| Run | Actions run `37944983134`, job `113868816164`, 2026-10-09 14:32:53Z to 14:47:28Z |
| Step 2, `tools/lint.sh` | Not run in this job. The Lint workflow ran on the same head and passed, including its "Fresh Debian install" job, which runs `tools/lint.sh` and fails on any `Skipped` line. |
| Step 3, `tools/build-image.sh --check` | exit 0 ("Image build inputs: 0 defects.") |
| Step 5, `tools/verify-image-reproducibility.sh` | exit 0 ("Three identical raw images and offline QEMU boot: SIMULATED.") |
| Raw image SHA-256, networked 1 | `ae7608b6ddffef076bcf3a74a2f7b06e8706cce4cfbdb792afbd5b9e0ec10095` |
| Raw image SHA-256, networked 2 | `ae7608b6ddffef076bcf3a74a2f7b06e8706cce4cfbdb792afbd5b9e0ec10095` |
| Raw image SHA-256, isolated cache | `ae7608b6ddffef076bcf3a74a2f7b06e8706cce4cfbdb792afbd5b9e0ec10095` |
| Identical | yes |
| `mule-development.sbom.cdx.json` SHA-256 | `d764eb1133c755be08293e4f2632cc41a523a709b04def03e9a64150e18208b3` |
| `mule-development.license-exceptions.json` SHA-256 | `d28d2581b649731106b80b784c86febfa59448b130da35a900e337256d348a81` |
| SBOM components | 260 |
| Retained cache | "Retained package cache: 0 defects." before the isolated build |
| Boot | `[  OK  ] Reached target multi-user.target - Multi-User System.`; bound 300 s because `/dev/kvm` was present |
| Units that failed during boot | `systemd-pcrlock-firmware-code.service`, `systemd-pcrlock-firmware-config.service`, `systemd-pcrlock-make-policy.service`; they did not prevent `multi-user.target` |
| Build environment | Debian 13.7 container, `mirror.gcr.io/library/debian@sha256:9cc080028c43b27d2074d63a5f9caf7166d731494965616c1a6d2827a004585c`, privileged |
| Host | GitHub-hosted `ubuntu-24.04` runner, image `20261004.327.1`, kernel `6.17.0-1022-azure`, 4 CPUs, 15 GiB RAM, `/dev/kvm` present |
| mkosi | Debian `25.3-7`, retained package verified by `tools/resolve-mkosi-builder.sh` |
| QEMU | `qemu-system` `1:10.0.11+ds-0+deb13u1`, from the locked tools tree (`os/image/manifest/tools-tree-packages.list`) |

The first run of the same sequence on this PR (run `37941908306`, head
`2902064`) produced the same three hashes and the same boot result. Its job
failed afterwards, in the upload step, because the runner user could not enter
the root-owned evidence directory. `df32f97` fixed that and is the run
recorded here.

## What it does not show

- Reproducibility across hosts. The three builds ran on one runner. The
  2026-10-05 cloud-session build of a different source tree had a different raw
  hash (`b07b3dca...`), and its SBOM hash matches this one; that pair is not a
  reproducibility result in either direction.
- Anything about the Pi 4B. G1's arm64 half needs the `FML-ADR-088` profile
  and, for acceptance, bench card BC-1 on the board.
- The cause of the three `systemd-pcrlock` failures, which is still not
  established (`2026-10-05-first-build-cloud-session.md`).

## Retained privately

Nothing. The job's `image-evidence` artifact (logs, hash files, SBOM) is kept
by GitHub for its retention period only; the raw images were not retained.
