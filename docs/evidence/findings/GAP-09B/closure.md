---
schema_version: "1.0"
finding_id: GAP-09B
scope: >-
  Select and enforce Debian mkosi 25.3-7 as the reproducible Debian 13 x86-64
  development-image mechanism without selecting the package set, production
  hardware, network configuration, services, or rollback mechanism.
governing_refs:
  - ROADMAP.md
  - REMEDIATION-AND-CLOSURE-PLAN-2026-09-08.md
  - docs/evidence/findings/GAP-09B/decision-packet.md
  - docs/evidence/findings/GAP-09B/execution-card.md
  - FML-ADR-022
  - FML-ADR-040
  - FML-ADR-079
  - TBR-HW-01
  - TBR-LINUX-01
pre_fix_reproduction: >-
  The image directory contained an empty package manifest and prose explicitly
  stating that no build definition existed; the working lab system could not
  be reconstructed as a bootable artifact from the repository.
expected_failure: >-
  GAP-09B shall not close without an owner-approved builder, immutable builder
  and snapshot inputs, an enforced deterministic raw-disk contract, explicit
  cache-only behavior, prior-art intake, and independent exact-commit review.
implementation_commit: fbaff2484cf33a126f35413e2498b3e34d041f68
files_changed:
  - .gitignore
  - STATUS.md
  - docs/ROADMAP-DEV.md
  - docs/adr/FML-ADR-079-mkosi-builds-the-debian-development-image.md
  - docs/decision-index.md
  - docs/evidence/findings/GAP-09B/2026-09-13-implementation.md
  - docs/evidence/findings/GAP-09B/README.md
  - docs/evidence/findings/GAP-09B/decision-packet.md
  - docs/evidence/findings/GAP-09B/execution-card.md
  - docs/findings/register.yml
  - docs/prior-art/mkosi.md
  - docs/prior-art/registry.yml
  - os/image/README.md
  - os/image/build-inputs.yml
  - os/image/manifest/README.md
  - os/image/manifest/packages.list
  - os/image/mkosi.conf
  - test/unit/test_image_build.py
  - test/unit/test_prior_art.py
  - tools/build-image.sh
  - tools/gen-status.sh
  - tools/validate-docs.sh
  - tools/validate-image.py
  - tools/validate-prior-art.py
tests:
  - name: Independent complete repository gate
    command: >-
      env PATH=/home/cameron/.local/bin:/usr/local/bin:/usr/bin:/bin
      tools/lint.sh
    exit_code: 0
  - name: Independent targeted image and prior-art tests
    command: >-
      python3 -m pytest -q test/unit/test_image_build.py
      test/unit/test_prior_art.py
    exit_code: 0
  - name: Image-input validator
    command: python3 tools/validate-image.py
    exit_code: 0
  - name: Exact Debian mkosi 25.3 configuration parse
    command: mkosi --directory os/image summary
    exit_code: 0
  - name: Exact-commit patch secret scan
    command: >-
      git show --format= --binary
      fbaff2484cf33a126f35413e2498b3e34d041f68 |
      gitleaks stdin --no-banner --redact
    exit_code: 0
environment:
  os: Ubuntu 24.04.4 LTS under WSL2 on x86-64; development host, not target
  python: "3.12.3"
  tools:
    - mkosi 25.3 from extracted Debian package 25.3-7
    - pytest 9.1.1
    - coverage 7.16.0
    - ruff 0.16.5
    - yamllint 1.38.0
    - ansible-lint 26.8.0
    - Bats 1.10.0
    - ShellCheck 0.9.0
    - shfmt 3.10.0
    - gitleaks 8.30.1
artifacts: []
date: "2026-09-13"
operator: Codex
reviewer: /root/gap09b_final_verifier
classification: UNVERIFIED
red_team_attempts:
  - attempt: >-
      Reconstruct the new selected-builder and image-tool tests against the
      parent commit.
    outcome: >-
      All three selected failing-first tests failed before the implementation
      and passed at the reviewed commit.
  - attempt: >-
      Corrupt compression, image identity, manifest format, disk seed, and
      tools-tree activation in both representations.
    outcome: >-
      The independent reviewer observed exactly five rejection diagnostics;
      synchronized drift cannot bypass the selected-value controls.
  - attempt: >-
      Parse the configuration and wrapper options with the exact Debian mkosi
      package rather than the repository validator alone.
    outcome: >-
      This exposed and corrected the obsolete compression key, random disk
      seed, inactive tools tree, and doubled raw-image suffix. The final exact
      package parse accepted the configuration and wrapper arguments.
  - attempt: >-
      Inspect mkosi's target-side Debian source generation for live inputs.
    outcome: >-
      The generated target can retain live debug and security URLs. The docs no
      longer overclaim; GAP-09C owns their removal or replacement and validation.
  - attempt: >-
      Search the exact commit for credentials, device identifiers, mutable
      builder references, production-hardware claims, or built-image claims.
    outcome: >-
      Independent review and gitleaks found none. The package manifest remains
      empty and the wrapper refuses a build before privileged operations.
residual_risks:
  - >-
    No target or tools-tree package closure, SBOM, completed offline cache,
    two-build identity result, or VM boot evidence exists yet.
  - >-
    mkosi v25.3 can write live Debian debug and security URLs into target apt
    sources; GAP-09C shall remove or replace them and validate the final image.
  - >-
    This repository-enforced development mechanism supplies no production
    kernel, board-support, RF, power, thermal, or hardware evidence.
deferred_work:
  - >-
    GAP-09C selects and pins the target and tools-tree package closures,
    verifies signatures and licenses, generates the SBOM, cleans target apt
    sources, builds twice and offline, compares image identity, and boots in a
    virtual machine.
  - >-
    Production compute and compatibility-set decisions remain TBR-HW-01 and
    TBR-LINUX-01.
closure_approved_by: /root/gap09b_final_verifier
redaction_statement: >-
  The packet contains no credential, key, certificate, network identifier,
  serial number, real identity, deployment location, or captured traffic.
owner_approval_refs:
  - >-
    The Program Owner explicitly approved retaining Debian 13 and using Debian
    mkosi 25.3-7 for GAP-09B in the Codex thread on 2026-09-12.
---

# GAP-09B closure

## Summary

Debian mkosi `25.3-7` is the selected planning baseline for the Debian 13
x86-64 development image. The repository now governs the exact builder and
source identities, dated build mirror, deterministic disk and time inputs,
activated tools tree, raw output identity, and cache-only invocation.

## Closure rationale

The Program Owner approved the mechanism. Independent review authenticated
implementation commit `fbaff2484cf33a126f35413e2498b3e34d041f68`, reproduced
the complete no-skip repository gate, reconstructed the failing-first controls,
and found no remaining actionable defect. GAP-09B closes as `UNVERIFIED`
repository enforcement: it makes no claim that an image has been built, booted,
or run on hardware. Those demonstrations begin only after the separate GAP-09C
package-set owner gate.
