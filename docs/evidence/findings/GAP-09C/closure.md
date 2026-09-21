---
schema_version: "1.0"
finding_id: GAP-09C
scope: >-
  Authenticate, build, reproduce, describe, and boot the Debian 13 x86-64
  development-image package closure selected by FML-ADR-081.
governing_refs:
  - REMEDIATION-AND-CLOSURE-PLAN-2026-09-08.md
  - docs/evidence/findings/GAP-09C/decision-packet.md
  - docs/evidence/findings/GAP-09C/execution-card.md
  - FML-ADR-079
  - FML-ADR-081
pre_fix_reproduction: >-
  The selected package locks and enforcement existed, but no complete image,
  isolated replay, repeated image identity, SBOM, licence report, or boot
  transcript had been produced.
expected_failure: >-
  Closure shall fail on package or source drift, an incomplete or altered
  cache, installed-root drift, raw-image inequality, a network-enabled VM, or
  failure to reach multi-user.target without operator input.
implementation_commit: 14ff2763452fb26aea3705ac146b4fbeae04e863
files_changed:
  - docs/evidence/findings/GAP-09C/2026-09-14-implementation.md
  - os/image/README.md
  - os/image/build-inputs.yml
  - os/image/manifest/README.md
  - os/image/manifest/tools-tree-direct-packages.list
  - os/image/manifest/tools-tree-lock.json
  - os/image/manifest/tools-tree-packages.list
  - os/image/mkosi.conf
  - os/image/mkosi.finalize
  - test/unit/test_image_build.py
  - tools/build-image.sh
  - tools/validate-image.py
  - tools/validate-package-cache.py
  - tools/verify-image-reproducibility.sh
tests:
  - name: Three-build reproducibility and isolated QEMU boot
    command: ./tools/verify-image-reproducibility.sh
    exit_code: 0
  - name: Image-input validator
    command: python3 tools/validate-image.py
    exit_code: 0
  - name: GitHub pull-request checks
    command: gh pr checks 154 --repo homelab-net/FML-MULE
    exit_code: 0
environment:
  os: Debian GNU/Linux 13 on x86_64 development article
  python: "3.13.5"
  tools:
    - mkosi 25.3 from Debian package 25.3-7
    - QEMU 10.0.13
artifacts:
  - path: docs/evidence/findings/GAP-09C/2026-09-20-verification.json
    sha256: 4570403996b0c627bf5bdaf73d3c098862fe3cda6110bba60b23dfc8cbf80bfe
date: "2026-09-20"
operator: Codex
reviewer: /root/gap09c_final_verifier
classification: SIMULATED
red_team_attempts:
  - attempt: Replay the authenticated networked-build cache with external networking unavailable.
    outcome: The isolated build completed and matched both clean networked raw images byte-for-byte.
  - attempt: Boot the image without an input channel or guest network.
    outcome: >-
      The initial run exposed the interactive Debian first-boot wizard. The
      corrected image bypassed that wizard without inventing deployment-local
      settings and reached multi-user.target.
  - attempt: Compare generated provenance outputs across all three builds.
    outcome: All three CycloneDX documents and all three licence reports were byte-identical.
residual_risks:
  - The result is a QEMU simulation on the development article, not production hardware qualification.
  - Production kernel, BSP, radio, RF, power, thermal, signing, update, and rollback evidence remain open.
  - Licence-exception records remain explicit review inputs rather than normalized SPDX conclusions.
deferred_work:
  - GAP-09D packages the MULE runtime and its bounded systemd entry point.
  - Later GAP-09 children render networking, select and deploy one service, and execute milestone acceptance.
closure_approved_by: /root/gap09c_final_verifier
redaction_statement: >-
  The source-controlled packet contains no credential, key, certificate,
  personal identity, deployment location, or captured traffic.
owner_approval_refs:
  - >-
    The Program Owner approved the minimum package set, same-time Debian
    snapshots, builder-only backports, and CycloneDX debsbom in the Codex thread
    on 2026-09-14 and directed continued gap closure on 2026-09-20.
---

# GAP-09C closure

## Summary

The Debian 13 x86-64 development image now has an authenticated, exact package
closure, an externally isolated replay path, CycloneDX provenance, and a
repeatable raw-image identity. Two clean networked builds and one cache-only
build produced raw-image SHA-256
`7bb1d923dfc0a6bfd2028f257124de320718ec87896668a48c59041b080dbccc`.

All three SBOMs and licence reports were also byte-identical. The isolated
artifact reached `multi-user.target` under QEMU/OVMF with the guest network
disabled and no operator input.

## Closure rationale

The execution-card runner returned zero for artifacts built at commit
`d31a686a89b09ea933f878fa4f6b17e07088db14`; the runtime-only policy correction
at `14ff2763452fb26aea3705ac146b4fbeae04e863` does not alter image bytes. The
compact verification record binds
the retained evidence hashes and environment. GitHub PR #154 passed all eight
checks. `/root/gap09c_final_verifier` independently authenticated the exact
implementation tip and reported no blocking defect.

The result is `SIMULATED`. It establishes development-image construction,
provenance, repeatability, and virtual boot behavior only.
