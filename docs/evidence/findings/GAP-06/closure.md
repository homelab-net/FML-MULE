---
schema_version: "1.0"
finding_id: GAP-06
scope: >-
  Operator-status semantics on mule/status.py: a node that cannot serve users is
  reported FAULT and not operational (FML-ADR-074), and the operator WAN answer
  is the undetermined-capable mode value rather than a boolean (FML-ADR-076).
governing_refs:
  - FML-ADR-074
  - FML-ADR-076
  - "CONOPS section 67"
  - "SAD section 22"
pre_fix_reproduction: >-
  On the pre-fix tree, a booted node with wifi_ap enumerated but not associated
  reported operational=True and state=GREEN while admission.py admitted nobody;
  a booted node missing a required bearer reported operational=True with
  state=FAULT; and a node whose WAN reachability was unknown reported NO-WAN
  rather than an undetermined value.
expected_failure: >-
  With the fix reverted, test_a_node_with_no_access_point_is_faulted_not_green,
  test_a_required_bearer_present_but_not_serving_is_faulted_not_green and
  test_wan_answer_reports_unknown_distinctly_from_no_wan fail, and mutations
  M23/M97/M98/M99 survive.
implementation_commit: 96d79ee894e744c60b8b21a7056b97ef88ba7781
files_changed:
  - mule/status.py
  - test/flatsat/node.py
  - test/flatsat/scenarios/test_degraded_states.py
  - test/flatsat/scenarios/test_v001_flow.py
  - test/flatsat/mutations.yml
  - docs/adr/FML-ADR-074-a-node-that-cannot-serve-users-is-reported-fault-and-not-operational.md
  - docs/adr/FML-ADR-076-the-operator-wan-answer-is-the-undetermined-capable-mode-value-not-a-boolean.md
tests:
  - name: unit and flat-sat suite
    command: "python -m pytest test/flatsat test/unit -q"
    exit_code: 0
  - name: mule coverage held at 100 percent
    command: "python -m coverage run --source=mule -m pytest test/flatsat test/unit && python -m coverage report"
    exit_code: 0
  - name: mutation check catches every mutation
    command: "python tools/mutation-check.py"
    exit_code: 0
environment:
  os: "Debian GNU/Linux 13 (trixie)"
  python: "3.13.5"
  tools:
    - pytest
    - coverage
    - ruff
    - bats
artifacts: []
date: "2026-09-11"
operator: Claude
reviewer: gap0406_verifier
classification: SIMULATED
red_team_attempts:
  - attempt: "Independent red-team of the decision packet before implementation"
    outcome: >-
      Found the operational fix was mis-justified as aligning status with
      admission (the planes diverge on time-degraded by design) and that a WAN
      consumer was missed; both corrected and re-anchored to status.py's own
      rule 1 before any code was written.
  - attempt: "Independent verification of the implementation on PR #120"
    outcome: >-
      Confirmed the logic, failing-first tests, mutation coverage and 100
      percent mule/ coverage; the only defect was a stale generated
      decision-index.md, since regenerated.
  - attempt: "Mutation testing of the new behaviour (M23, M97, M98, M99)"
    outcome: "Each mutation killed; 101/101 mutations caught overall."
residual_risks:
  - >-
    SIMULATED only: the status logic is exercised against flat-sat fakes, not
    real radios. RADIO_NOT_SERVING behaviour on real hardware is unverified.
deferred_work:
  - >-
    The NON-AUTHORITATIVE operator state remains declared but unreachable,
    scoped to TBR-TAK-01 and TBR-HA-01.
  - "Renaming wan_available to wan_reachability is deferred (FML-ADR-076 accepted cost)."
closure_approved_by: "Cameron Zobrist"
redaction_statement: >-
  This packet contains no credentials, keys, callsigns, or real identities;
  all referenced fixtures use synthetic values.
owner_approval_refs:
  - >-
    Program Owner approval in the Claude Code session of 2026-09-11: status
    semantics and controlling ADRs approved, and closure directed in this PR.
---

# GAP-06 closure packet

## Summary

The operator status view no longer overstates a node's health or certainty. A
node that cannot serve users -- a required bearer absent, or present but not
serving -- is reported `FAULT` and therefore not `operational`, and an unknown
WAN reachability is reported as undetermined rather than as `NO-WAN`. The fix is
carried by FML-ADR-074 and FML-ADR-076, exercised end to end on the flat-sat.

## Closure rationale

The two defects were real and independently confirmed: `operational` was set to
`observed.booted` alone (contradicting `state=FAULT`), `_state`/`_fault` ignored
`required_not_serving` while `admission` failed closed on it, and the status WAN
answer collapsed an unknown value to `NO-WAN` despite `modes.wan` already
carrying the honest `WanReachability | None`.

The corrections restore `status.py`'s own precedence rule 1 and reuse the mode
plane's WAN value; both are covered by failing-first tests demonstrated to fail
against the old logic, and by mutations M23/M97/M98/M99 which the suite kills.
`mule/` coverage stays at 100 percent, the full mutation check reports 101/101,
and CI on PR #120 is green. An independent verifier separate from the
implementer reviewed the change; the Program Owner approved the semantics and
directed closure in this PR. The evidence tier is SIMULATED: correct against
fakes, not a claim about hardware.
