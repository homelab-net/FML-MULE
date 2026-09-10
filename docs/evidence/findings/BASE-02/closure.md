---
schema_version: "1.0"
finding_id: BASE-02
scope: Normal-user verification baseline from a clean checkout with empty caches and fault-injection evidence.
governing_refs:
  - REMEDIATION-AND-CLOSURE-PLAN-2026-09-08.md
  - docs/dev-machine.md
  - docs/findings/README.md
pre_fix_reproduction: No retained artifact identified a clean normal-user run, its complete toolchain, or proof that a temporary fault produced a nonzero result.
expected_failure: Removing the findings validator in a disposable checkout shall make its focused tests return nonzero.
implementation_commit: ae71308f189cdc48d71b4dc2e69cef0a5dc0f09a
files_changed:
  - REMEDIATION-AND-CLOSURE-PLAN-2026-09-08.md
  - docs/evidence/findings/BASE-02/2026-09-09-verification.json
  - docs/evidence/findings/BASE-02/README.md
  - docs/findings/register.yml
  - test/unit/test_findings.py
tests:
  - name: Implementer complete repository gate
    command: sh tools/lint.sh
    exit_code: 0
  - name: Independent toolchain preflight
    command: sh tools/install-deps.sh --check
    exit_code: 0
  - name: Independent Python test collection
    command: python -m pytest --collect-only -q
    exit_code: 0
  - name: Independent complete repository gate from a new checkout and empty caches
    command: /usr/bin/time -p sh tools/lint.sh
    exit_code: 0
  - name: Independent generated-output recovery
    command: rm STATUS.md docs/verification/traceability.md docs/decision-index.md; sh tools/gen-status.sh; sh tools/gen-traceability.sh; sh tools/gen-decision-index.sh; git diff --exit-code
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
  - path: docs/evidence/findings/BASE-02/2026-09-09-verification.json
    sha256: cdbcbf29f0636904d0fe2bc295f2d8c9e156c217e7d280d6f1f2ce273a4683a4
date: "2026-09-09"
operator: Codex
reviewer: /root/gap01_verifier
classification: SIMULATED
red_team_attempts:
  - attempt: Run from a new checkout with four newly created empty cache directories as uid 1001.
    outcome: The complete gate exited zero in 325.67 seconds with no permission warning, missing-tool skip, ignored failure, or incorrectly owned path.
  - attempt: Delete the three committed generated outputs and regenerate each one.
    outcome: All generators exited zero; git diff --exit-code and the final status were clean.
  - attempt: Remove tools/validate-findings.py temporarily and run test/unit/test_findings.py.
    outcome: All 21 cases errored on the missing validator and pytest exited 1; restoration checks then exited zero with a clean checkout.
residual_risks:
  - The WSL host lacks en_US.UTF-8, so two locale-specific Bats cases reported conditional skips; GitHub run 34413744271 executed both without skips and passed at the evidence source commit.
  - The measured duration is a host-specific baseline, not a product performance requirement.
  - SIMULATED verification establishes repository behavior only and says nothing about target hardware.
deferred_work: []
closure_approved_by: /root/gap01_verifier
redaction_statement: The packet and retained artifact contain no credentials, private keys, tokens, personal identities, deployment locations, or sensitive packet contents.
owner_approval_refs:
  - The project owner confirmed continued execution of the approved remediation plan in the Codex thread on 2026-09-09; BASE-02 made no product, trade, or architecture decision.
---

# BASE-02 closure

## Summary

The baseline was reproduced from new local clones as an ordinary uid-1001
user with empty dependency and test caches. The accepted source-commit run
collected 282 Python tests, caught all 79 mutations, covered all 535 `mule/`
statements, and completed all configured lint and validation stages. Its 36
Bats cases comprised 34 passes and two explicit locale-dependent skips on the
WSL host; the green GitHub source-commit run exercised both locale cases.

The result is `SIMULATED`. It demonstrates repository behavior and does not
claim target-system or hardware behavior.

## Closure rationale

The implementer regenerated all committed outputs from deletion, demonstrated
that removing the findings validator makes the focused suite return nonzero,
restored the disposable checkout, and recorded the exact environment and
results in the hashed JSON artifact. The work also removed a BASE-01 test
fixture's dependency on the lifecycle state of later findings; the live
repository remains unnormalized and is still validated directly.

`/root/gap01_verifier` independently reviewed implementation commit
`ae71308f189cdc48d71b4dc2e69cef0a5dc0f09a`, repeated the empty-cache full
gate in 325.67 seconds, reproduced the generated-output and temporary-fault
checks, confirmed clean restoration and ownership, and approved closure.
