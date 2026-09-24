---
schema_version: "1.0"
finding_id: GAP-02
scope: Fail-closed service-catalog schema, unique reference resolution, enabled-state enforcement, and catalog-to-Quadlet integrity before boot.
governing_refs:
  - FML-ADR-078
  - REMEDIATION-AND-CLOSURE-PLAN-2026-09-08.md
  - services/catalog/README.md
pre_fix_reproduction: The initial catalog implementation accepted duplicate same-name records, had no enabled or alias model, did not require a real deployment unit, and let gen-config --check bypass catalog enforcement.
expected_failure: Unknown, disabled, duplicate, ambiguous, malformed, unit-less, absent-unit and unowned-unit inputs shall return nonzero before configuration generation or boot; removing any principal enforcement path shall fail a mutation check.
implementation_commit: b8b69cc8e94b4ea611eaae3153c521573bc5e6f5
files_changed:
  - docs/decision-index.md
  - docs/evidence/findings/GAP-02/implementation.md
  - mission/examples/valid-full.json
  - services/catalog/README.md
  - services/catalog/catalog.schema.json
  - services/catalog/catalog.yml
  - services/quadlets/README.md
  - test/flatsat/README.md
  - test/flatsat/catalog/README.md
  - test/flatsat/catalog/catalog.yml
  - test/flatsat/conftest.py
  - test/flatsat/mission-with-services.json
  - test/flatsat/mutations.yml
  - test/flatsat/node.py
  - test/flatsat/quadlets/README.md
  - test/flatsat/quadlets/stand-in-alpha.container
  - test/flatsat/quadlets/stand-in-beta.container
  - test/flatsat/scenarios/test_degraded_states.py
  - test/flatsat/scenarios/test_time_fail_closed.py
  - test/flatsat/scenarios/test_v001_flow.py
  - test/unit/test_gen_config.py
  - test/unit/test_mission.py
  - test/unit/test_service_catalog.py
  - test/unit/validate_docs.bats
  - tools/gen-config.py
  - tools/validate-catalog.py
tests:
  - name: Independent focused GAP-02 and flat-sat suite
    command: .venv/bin/python -m pytest -q test/unit/test_gen_config.py test/unit/test_service_catalog.py test/flatsat
    exit_code: 0
  - name: Independent service-catalog validator
    command: .venv/bin/python tools/validate-catalog.py
    exit_code: 0
  - name: Independent focused mutation checks
    command: .venv/bin/python tools/mutation-check.py --only M103,M104,M105,M106,M107
    exit_code: 0
  - name: Independent complete repository gate
    command: env PATH=/home/cameron/.local/bin:/usr/local/bin:/usr/bin:/bin tools/lint.sh
    exit_code: 0
environment:
  os: Ubuntu 24.04.4 LTS under WSL2 on x86_64; development host, not target
  python: 3.12.3
  tools:
    - pytest 9.1.1
    - coverage 7.16.0
    - ruff 0.16.5
    - yamllint 1.38.0
    - ansible-lint 26.8.0
    - Bats 1.10.0
    - Node.js 22.22.2
    - ShellCheck 0.9.0
    - shfmt 3.10.0
    - gitleaks 8.30.1
artifacts:
  - path: docs/evidence/findings/GAP-02/2026-09-12-verification.json
    sha256: 0a8c8359a6ddf7fb05d5a93e57f8059fdbb310b436467cdfd1306a105b6d30fe
date: "2026-09-12"
operator: Codex
reviewer: /root/oss_gap02_closure_verifier
classification: SIMULATED
red_team_attempts:
  - attempt: Add a second martin record with different content and run both the repository validator and gen-config --check.
    outcome: Both paths returned nonzero; the operator preflight named the duplicate service reference.
  - attempt: Select the disabled martin contract in a schema-valid mission and run gen-config --check.
    outcome: Preflight returned exit 2 and named the disabled service before reporting unresolved region values.
  - attempt: Defeat unknown-service, disabled-service, missing-unit, duplicate-reference, and operator-preflight enforcement one control at a time.
    outcome: Mutations M103 through M107 were all killed by the suite.
residual_risks:
  - No production service or Quadlet is enabled or deployed.
  - Image, resource-envelope and recovery decisions remain open.
  - Future catalog enablement requires GAP-09F/G decisions and real deployment units.
  - SIMULATED verification establishes repository behavior only and says nothing about target hardware.
deferred_work:
  - Select and package a production milestone service under GAP-09F and GAP-09G before enabling its catalog contract.
closure_approved_by: /root/oss_gap02_closure_verifier
redaction_statement: The packet and retained artifact contain no credentials, private keys, tokens, personal identities, deployment locations, or sensitive traffic.
owner_approval_refs:
  - The project owner explicitly directed Codex to recover, create the OSS-01 and GAP-02 closures, and open the pull request in the Codex thread on 2026-09-12; this closure enables no production service.
---

# GAP-02 closure

## Summary

Every accepted mission service now resolves to exactly one enabled catalog
record before configuration generation or boot. Names and aliases are unique,
the runtime validates malformed records, an enabled record names its exact
existing `<name>.container`, and a loadable production Quadlet has exactly one
enabled catalog owner. Operator `--check` uses the same service gates.

OpenTAKServer and Martin remain disabled contracts with `TBD` units. The
flat-sat exercises the production resolver through clearly synthetic test-only
services and existence markers, so this closure does not imply that a product
service has been selected or deployed.

## Closure rationale

`/root/oss_gap02_closure_verifier` authenticated implementation commit
`b8b69cc8e94b4ea611eaae3153c521573bc5e6f5` and tree
`d9338943a6898181649c6edc1e6839d17fbbb6e8` in a fresh clean checkout. The
reviewer reproduced 251 focused tests, all five focused mutations, and the
complete gate with 107/107 mutations, 543/543 covered statements and 38 Bats
tests with no failures or skips. Independent duplicate and disabled-service
CLI attacks both returned exit 2.

The result is `SIMULATED`. It proves repository enforcement and no physical or
deployed-service behavior.
