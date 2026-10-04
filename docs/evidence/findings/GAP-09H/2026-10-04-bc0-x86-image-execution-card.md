# GAP-09H execution card BC-0: build and boot the current x86 closure

## Finding and authority

- **Finding:** GAP-09H, gap G1, the "any arch" half: "the current `os/image`
  closure is built and booted" (`2026-09-26-operator-procedure.md`).
- **Governing records:** `FML-ADR-079` (mkosi builds the development image),
  `FML-ADR-081` (closure, provenance, and the three-build plus QEMU acceptance
  sequence), `FML-ADR-083` (the runtime the 118/454 closure added).
- **Why now:** `os/image/README.md` records that the 118/454 closure "has not
  yet earned the GAP-09C byte-identical image result; it requires a new image
  execution". GAP-09C proved the earlier 97/440 closure. Running this before the
  arm64 profile refactors `tools/verify-image-reproducibility.sh` gives that
  refactor a known-good x86 baseline to preserve.

## Status

A procedure to run, not a result. A QEMU boot exercises the image in a virtual
machine, so its result is `SIMULATED` and says nothing about the Pi, the access
point, or any radio. It closes no finding by itself; GAP-09H needs independent
review and the cold-start drill.

## Where and as whom

The N150 development article (GAP-09A), Debian 13, as root, with network access
to `snapshot.debian.org`. Not a Claude Code cloud session: those have no KVM or
QEMU, and on 2026-10-04 their network policy refused every Debian archive host.

## Steps

1. Check out `main` and record the commit: `git rev-parse HEAD`.
2. Confirm the tree is the one CI checked: `tools/lint.sh; echo $?` prints `0`
   and no `Skipped` line (`tools/install-deps.sh` first if it does).
3. `tools/build-image.sh --check` and record its exit code. Safe without root.
4. If the pinned builder package is not in APT's archive cache, set
   `FML_MKOSI_PACKAGE_DEB` to the retained `mkosi_25.3-7_all.deb`
   (`os/image/README.md`, Commands).
5. `sudo tools/verify-image-reproducibility.sh; echo $?` and record the exit
   code. It runs two clean networked builds, one network-isolated cache-only
   build, compares outputs, and boots the result under QEMU with no network.
   It writes its evidence to a new `out/gap09c.*` directory.

## What to record

Commit a short record beside this card, named
`<date>-bc0-x86-image-result.md`, carrying:

- the commit from step 1 and every exit code from steps 2, 3 and 5;
- the three raw-image SHA-256 values and whether they are identical;
- the SHA-256 of `mule-development.sbom.cdx.json` and
  `mule-development.license-exceptions.json`, and the SBOM component count;
- the QEMU transcript line showing `Reached target multi-user.target`, or the
  last twenty lines if it is absent;
- the host's Debian version, kernel, QEMU and mkosi versions.

Do not commit the raw image, the package cache, full logs, hostnames, hardware
addresses or serial numbers (`SECURITY.md`; the evidence checks refuse
equipment identifiers). Hash anything kept privately and record the hash.

## Stop conditions

Stop and record, rather than relaxing the contract, if: the builder cannot
authenticate the snapshot, the cache-only build needs the network, the raw
hashes differ, the image does not reach `multi-user.target`, or the SBOM does
not cover the installed root (the GAP-09C stop conditions). A failure is a
result worth committing; a claim that the step is blocked needs separate-agent
qualification first (`AGENTS.md`, Done 7).
