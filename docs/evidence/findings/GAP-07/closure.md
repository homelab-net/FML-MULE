---
schema_version: "1.0"
finding_id: GAP-07
scope: >-
  The mesh and LoRa probe workflows trigger on the configuration and toolchain
  pins they exercise, not only on their own workflow file; a new validate-docs
  check enforces the toolchain-pin trigger so it cannot regress.
governing_refs:
  - "AGENTS.md: any rule you add is enforced by a check"
pre_fix_reproduction: >-
  On the pre-fix tree, lora-probe.yml and mesh-probe.yml triggered only on their
  own workflow file. lora-probe.yml sources tools/toolchain-versions.sh for the
  pinned meshtasticd image, so a pin bump shipped without the probe re-running.
expected_failure: >-
  With the pin path removed from lora-probe.yml (as the bats test does in a
  sandbox), validate-docs.sh exits non-zero naming the workflow.
implementation_commit: 9e014e031736410f92afcf8aa2056876c5a5f3bd
files_changed:
  - .github/workflows/lora-probe.yml
  - .github/workflows/mesh-probe.yml
  - tools/validate-docs.sh
  - test/unit/validate_docs.bats
tests:
  - name: shell unit tests (bats)
    command: "bats test/unit"
    exit_code: 0
  - name: documentation checks
    command: "bash tools/validate-docs.sh"
    exit_code: 0
environment:
  os: "Debian GNU/Linux 13 (trixie)"
  python: "3.13.5"
  tools:
    - bats
    - shellcheck
    - shfmt
artifacts: []
date: "2026-09-11"
operator: Claude
reviewer: gap030507_verifier
classification: SIMULATED
red_team_attempts:
  - attempt: "Independent verification of the implementation on PR #121"
    outcome: >-
      Confirmed lora-probe.yml genuinely sources the pin file and now lists it in
      trigger paths, the new check is POSIX-sh clean and the bats test proves it
      fires. Noted the config-template paths over-trigger (safe, forward-looking);
      the wording was softened in response.
residual_risks:
  - >-
    The config-template trigger paths point at still-TBD templates the probes do
    not yet read; they over-trigger safely and become load-bearing when the
    templates gain real values.
deferred_work: []
closure_approved_by: "Cameron Zobrist"
redaction_statement: >-
  This packet contains no credentials, keys, callsigns, or real identities.
owner_approval_refs:
  - >-
    Program Owner direction in the Claude Code session of 2026-09-11 to wrap up
    the ready findings in this PR. The finding's user_gate is null (no required
    approval); no required-check policy changed beyond adding the enforcing check.
---

# GAP-07 closure packet

## Summary

The mesh and LoRa integration probes now re-run when the configuration and
toolchain pins they exercise change. The load-bearing fix is that `lora-probe.yml`
triggers on `tools/toolchain-versions.sh`, the meshtasticd image pin it sources,
and a new `validate-docs` check fails any workflow that sources the pins without
triggering on them.

## Closure rationale

The defect was concrete: a pinned-image bump did not re-run the probe that
validates the new daemon build. The fix adds the dependency to the trigger paths
and locks it with a machine check that was watched firing (bats test 37). An
independent verifier confirmed the check and the bats coverage, and flagged that
the config-template paths over-state their current coupling; the wording was
softened accordingly. The finding's `user_gate` is null. SIMULATED (CI
configuration).
