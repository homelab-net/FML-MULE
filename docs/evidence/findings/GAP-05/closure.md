---
schema_version: "1.0"
finding_id: GAP-05
scope: >-
  Unknown radio enumeration (None) is a distinct fault (RADIO_ENUMERATION_FAILED)
  and the node fails closed to FAULT, rather than crashing on list(None) or being
  read as RADIO_ABSENT. FML-ADR-077.
governing_refs:
  - FML-ADR-077
pre_fix_reproduction: >-
  On the pre-fix tree, FlatSatNode._enumerated() evaluated
  list(self._radio.enumerated()), raising TypeError when the reader returned None
  (the platform could not enumerate).
expected_failure: >-
  With the fix reverted, test_a_node_that_cannot_enumerate_its_radios_fails_closed
  raises TypeError at list(None); mutations M23/M97/M98/M102 on the state logic
  survive.
implementation_commit: 9e014e031736410f92afcf8aa2056876c5a5f3bd
files_changed:
  - mule/status.py
  - test/flatsat/node.py
  - test/flatsat/fakes.py
  - test/flatsat/scenarios/test_degraded_states.py
  - test/flatsat/mutations.yml
  - docs/adr/FML-ADR-077-an-unknown-radio-enumeration-is-a-distinct-fault-and-the-node-fails-closed.md
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
artifacts: []
date: "2026-09-11"
operator: Claude
reviewer: gap030507_verifier
classification: SIMULATED
red_team_attempts:
  - attempt: "Independent verification of the implementation on PR #121"
    outcome: >-
      Swept every consumer of observed.enumerated and confirmed each handles None
      without crashing and without collapsing unknown into absent or present;
      confirmed the distinct RADIO_ENUMERATION_FAILED precedence and the
      failing-first TypeError against the old code. No defect.
  - attempt: "Mutation testing of the state logic (M23, M97, M98, M102)"
    outcome: "Each killed; the enumeration-None fault term is covered."
residual_risks:
  - >-
    SIMULATED only: exercised against flat-sat fakes. The real reader
    (CommandRadio) already returns None when iw dev cannot run, but the
    fail-closed behaviour on real hardware is unverified.
deferred_work:
  - >-
    RADIO_ENUMERATION_FAILED does not distinguish why enumeration failed; a cause
    taxonomy waits for a reader that can report it (FML-ADR-077 accepted cost).
closure_approved_by: "Cameron Zobrist"
redaction_statement: >-
  This packet contains no credentials, keys, callsigns, or real identities; all
  referenced fixtures use synthetic values.
owner_approval_refs:
  - >-
    Program Owner approval in the Claude Code session of 2026-09-11: unknown and
    failure enumeration semantics approved (distinct states, fail closed on
    unknown), and closure directed in this PR.
---

# GAP-05 closure packet

## Summary

An unknown radio enumeration is now honoured as its own state. When the platform
cannot enumerate (`None`), the node reports the distinct fault
`RADIO_ENUMERATION_FAILED` and fails closed to `FAULT`, instead of crashing on
`list(None)` or claiming the required bearer is absent. Unknown, empty and
populated are three distinct states, never collapsed. FML-ADR-077.

## Closure rationale

The named defect (a `TypeError` on `None`) is fixed, and the deeper decision --
never present "cannot tell" as a definite answer -- is implemented across every
consumer of `observed.enumerated` and covered by a failing-first test and
mutations M23/M97/M98/M102. `mule/` coverage stays 100 percent and the full
mutation check is green. An independent verifier separate from the implementer
swept the consumers and confirmed no crash and no collapse; the Program Owner
approved the unknown/failure semantics and directed closure. SIMULATED.
