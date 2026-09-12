---
schema_version: "1.0"
finding_id: OSS-01
scope: Version 1 prior-art and reuse register covering all 28 candidates fixed by the OSS-01 execution card.
governing_refs:
  - REMEDIATION-AND-CLOSURE-PLAN-2026-09-08.md
  - docs/evidence/findings/OSS-01/execution-card.md
  - AGENTS.md
pre_fix_reproduction: The repository had no complete, machine-checked record of candidate provenance, licensing, immutable versions, architectural fit, reuse mode, exit strategy, risks, and approval gates.
expected_failure: Removing or weakening a required candidate, immutable reference, evidence document, license gate, owner approval, source, FML mapping, or narrative field shall make the focused checks return nonzero.
implementation_commit: 414d10543e4664206443e2b5626ae92012f0c598
files_changed:
  - REMEDIATION-AND-CLOSURE-PLAN-2026-09-08.md
  - docs/decision-index.md
  - docs/evidence/findings/OSS-01/README.md
  - docs/findings/register.yml
  - docs/prior-art/offline-content-and-maps.md
  - docs/prior-art/registry.yml
  - docs/prior-art/wan-and-halow-dependencies.md
  - test/unit/test_prior_art.py
tests:
  - name: Independent complete repository gate from a fresh checkout
    command: script -q -e -c "tools/lint.sh" /tmp/fml-oss01-414d105.lxE7jF/full-gate-noskip.typescript
    exit_code: 0
  - name: Independent prior-art validator
    command: .venv/bin/python tools/validate-prior-art.py
    exit_code: 0
  - name: Independent focused prior-art tests
    command: .venv/bin/python -m pytest -q test/unit/test_prior_art.py
    exit_code: 0
  - name: Independent immutable Git reference resolution
    command: Resolve each registry Git artifact with git ls-remote or an exact-SHA shallow fetch from its canonical upstream.
    exit_code: 0
environment:
  os: Ubuntu 24.04.4 LTS under WSL2 on x86_64; development host, not target
  python: 3.12.3
  tools:
    - pytest 9.1.1
    - coverage 7.16.0
    - PyYAML 6.0.3
    - jsonschema 4.26.0
    - ruff 0.16.5
    - yamllint 1.38.0
    - ansible-lint 26.8.0
    - ansible-core 2.21.3
    - Bats 1.10.0
    - Node.js 22.22.2
    - markdownlint-cli2 0.23.2
    - ShellCheck 0.9.0
    - shfmt 3.10.0
    - gitleaks 8.30.1
artifacts:
  - path: docs/evidence/findings/OSS-01/2026-09-12-verification.json
    sha256: 1ef2f27da8bd6faba9ead0139db7633ddee89720dfddb218be900231bf985b7b
date: "2026-09-12"
operator: Codex
reviewer: /root/oss_gap02_closure_verifier
classification: SIMULATED
red_team_attempts:
  - attempt: Run every configured repository gate from a fresh exact-commit checkout with the complete toolchain and en_US.UTF-8 present.
    outcome: The gate exited zero with no skipped tools or tests; 103/103 mutations were caught, 543/543 statements were covered, and all 38 Bats tests passed.
  - attempt: Exercise all 11 invalid prior-art fixture classes and mutations M80 through M96.
    outcome: Every missing-candidate, floating-reference, provenance, license, approval, evidence, mapping, and narrative fault failed closed.
  - attempt: Re-resolve every immutable Git artifact from its canonical upstream, using exact-SHA fetches when commits were no longer advertised.
    outcome: All 30 Git artifacts resolved; no pinned object was missing or retargeted.
residual_risks:
  - The final seven exact artifacts were not built or run and their resource behavior remains unmeasured.
  - Morse firmware remains proprietary, review-required and hardware-bound.
  - Kiwix, Kolibri, Tailscale and both Morse artifacts remain undecided; ProtoMaps and PMTiles remain references only.
  - hostapd 2.12 remains blocked from RADIUS promotion by upstream advisory 2026-5; dnsmasq and step-ca remain undecided.
  - SIMULATED verification establishes repository behavior only and says nothing about target hardware.
deferred_work: []
closure_approved_by: /root/oss_gap02_closure_verifier
redaction_statement: The packet and retained artifact contain no credentials, private keys, tokens, personal identities, deployment locations, or sensitive traffic.
owner_approval_refs:
  - The project owner approved the OSS-01 registry structure and continued execution of the remediation plan in the Codex thread on 2026-09-09 and 2026-09-12; no candidate adoption is approved by closing this finding.
---

# OSS-01 closure

## Summary

The version 1 prior-art corpus now contains current evaluations for all 28
candidates fixed by the execution card. Each record preserves provenance,
license, immutable artifact, architectural fit, reuse posture, exit strategy,
risks and unresolved owner gates. Closure records research completeness; it
does not adopt an undecided component or change the product architecture.

## Closure rationale

`/root/oss_gap02_closure_verifier` authenticated implementation commit
`414d10543e4664206443e2b5626ae92012f0c598` and tree
`f115fad1a931f4d31aecde74334ebf7858dd5a09` in a fresh clean checkout. The
reviewer reproduced the complete no-skip repository gate, all focused
prior-art checks, and the invalid-fixture and mutation controls. All 30 pinned
Git artifacts resolved from their canonical upstreams; exact-SHA fetches were
used where an object was no longer advertised by a ref.

The result is `SIMULATED`. It establishes the integrity and completeness of
the repository evidence only and makes no hardware claim.
