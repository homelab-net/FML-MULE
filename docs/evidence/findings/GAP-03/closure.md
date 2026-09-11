---
schema_version: "1.0"
finding_id: GAP-03
scope: >-
  The per-deployment IPv4 address_prefix (FML-ADR-063) is carried from the
  mission package into generated configuration, where it was previously dropped.
governing_refs:
  - FML-ADR-063
pre_fix_reproduction: >-
  On the pre-fix tree, tools/gen-config.py built the resolved network block
  without address_prefix, so a mission package's valid IPv4 prefix never reached
  generated configuration.
expected_failure: >-
  With the fix reverted, test_the_mission_package_supplies_the_address_prefix
  raises KeyError because the generated network block has no address_prefix key.
implementation_commit: 9e014e031736410f92afcf8aa2056876c5a5f3bd
files_changed:
  - tools/gen-config.py
  - test/unit/test_gen_config.py
tests:
  - name: gen-config unit tests
    command: "python -m pytest test/unit/test_gen_config.py -q"
    exit_code: 0
  - name: unit and flat-sat suite
    command: "python -m pytest test/flatsat test/unit -q"
    exit_code: 0
environment:
  os: "Debian GNU/Linux 13 (trixie)"
  python: "3.13.5"
  tools:
    - pytest
    - coverage
    - ruff
artifacts: []
date: "2026-09-11"
operator: Claude
reviewer: gap030507_verifier
classification: SIMULATED
red_team_attempts:
  - attempt: "Independent verification of the implementation on PR #121"
    outcome: >-
      Confirmed the prefix is carried only when present (None otherwise), the
      schema validates its CIDR form on load, and the test binds to the
      fixture's own value rather than a literal. No defect.
residual_risks:
  - >-
    SIMULATED only: the value is carried through configuration resolution; the
    FML-ADR-063 overlap-reporting behaviour on a real uplink is a separate runtime
    concern, not exercised here.
deferred_work: []
closure_approved_by: "Cameron Zobrist"
redaction_statement: >-
  This packet contains no credentials, keys, callsigns, or real identities; the
  referenced prefix is an illustrative fixture value.
owner_approval_refs:
  - >-
    Program Owner direction in the Claude Code session of 2026-09-11 to wrap up
    the ready findings in this PR; the change introduces no unspecified address
    semantics (the field and its CIDR form are already governed by FML-ADR-063).
---

# GAP-03 closure packet

## Summary

`tools/gen-config.py` now carries the mission package's per-deployment IPv4
`address_prefix` into the resolved `network` block; it was previously dropped, so
a valid prefix never reached generated configuration.

## Closure rationale

The defect was a missing field in one dict, with no downstream semantics: the
schema already validates the prefix's CIDR form on load, so resolution only had to
preserve it. The failing-first test binds to the fixture package's own value and
raises `KeyError` against the old code. An independent verifier confirmed the fix
and the test; the `user_gate` ("approve any unspecified address semantics") is
satisfied because none are introduced. SIMULATED.
