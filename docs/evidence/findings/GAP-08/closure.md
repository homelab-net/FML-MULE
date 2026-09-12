---
schema_version: "1.0"
finding_id: GAP-08
scope: >-
  Eliminate documentation decision drift: correct docs that contradicted the
  authoritative machine-readable state, add a check so the trade-state category
  cannot silently return, and reconcile the last controlling-record reference.
governing_refs:
  - "CODEBASE-REPORT-2026-09-08.md section 8"
  - "AGENTS.md Done#6: a change that leaves a doc contradicting the state is not done"
pre_fix_reproduction: >-
  Before the fix, docs/trades/README.md marked four closed trades OPEN, ROADMAP.md
  and service/README docs described closed trades and an empty catalog, README
  hardcoded stale counts, and pyproject/test docs denied the mule/ package.
expected_failure: >-
  With the fix reverted, the bats test flips a closed trade's cell to OPEN and the
  new validate-trade-states check fires; before the check existed the drift passed
  silently.
implementation_commit: e996450f77c094ced5c17dd0fbcfbc77e6f9075b
files_changed:
  - docs/trades/README.md
  - docs/trades/TBR-TAK-01-mission-critical-state-boundary.md
  - ROADMAP.md
  - README.md
  - docs/README.md
  - services/catalog/README.md
  - services/gateways/README.md
  - services/quadlets/README.md
  - pyproject.toml
  - test/README.md
  - os/ansible/inventory/example.yml
  - tools/validate-trade-states.py
  - tools/validate-docs.sh
  - test/unit/validate_docs.bats
  - docs/adr/FML-ADR-061-the-mesh-is-keyed-and-mules-of-one-deployment-merge-automatically.md
tests:
  - name: documentation checks
    command: "bash tools/validate-docs.sh"
    exit_code: 0
  - name: shell unit tests (bats)
    command: "bats test/unit"
    exit_code: 0
  - name: generated files reproduce without diff
    command: "sh tools/gen-decision-index.sh --check && sh tools/gen-status.sh --check && sh tools/gen-traceability.sh --check"
    exit_code: 0
environment:
  os: "Debian GNU/Linux 13 (trixie)"
  python: "3.13.5"
  tools:
    - bats
    - shellcheck
    - shfmt
    - ruff
artifacts: []
date: "2026-09-11"
operator: Claude
reviewer: gap08_verifier
classification: SIMULATED
red_team_attempts:
  - attempt: "Independent reviewer sampling of controlling documents (the closure gate)"
    outcome: >-
      The first inventory was incomplete; sampling found further drift in
      ROADMAP.md, README.md, docs/README.md, pyproject.toml, test/README.md, the
      service READMEs, and closed-trade owner fields. All corrected from the
      CODEBASE-REPORT section 8 inventory.
  - attempt: "Injected-mismatch test of the new validator"
    outcome: >-
      Flipping a closed trade's status cell to OPEN in a sandbox makes
      validate-trade-states fire, naming the trade (bats test 38). It ignores
      non-status cells such as priority.
  - attempt: "Controlling-record reconciliation"
    outcome: >-
      The residual references were a SUPERSEDED ADR (FML-ADR-060, left as a
      historical record by owner decision) and FML-ADR-061's liaison condition.
      The Program Owner chose to annotate FML-ADR-061 that TBR-NET-01's precondition
      is now met (no design change); that annotation is included here.
residual_risks:
  - >-
    SIMULATED (documentation). The validator enforces only the trades-page status
    category; arbitrary stale prose in other docs is not machine-detectable, so
    new drift outside that category depends on review.
deferred_work:
  - >-
    Dated historical evidence and closed-trade decision-time reasoning that
    reference then-open trades are retained as-written by owner decision.
closure_approved_by: "Cameron Zobrist"
redaction_statement: >-
  This packet contains no credentials, keys, callsigns, or real identities.
owner_approval_refs:
  - >-
    Program Owner directions in the Claude Code session of 2026-09-11: leave
    historical records as-written; annotate FML-ADR-061 that the liaison
    precondition is met (Option 1); closure of GAP-08 in this change.
---

# GAP-08 closure packet

## Summary

Documentation that contradicted the authoritative machine-readable state is
corrected: the trades page's status tables and prose, ROADMAP and service and
package docs, and closed-trade owner fields. The trades-page status category is
now machine-enforced by `tools/validate-trade-states.py` (validate-docs check
24), and the last controlling-record reference -- FML-ADR-061's liaison
condition -- is reconciled with a dated annotation now that TBR-NET-01 has
closed.

## Closure rationale

An independent reviewer sampled the controlling documents (GAP-08's closure
gate) and found the first inventory incomplete; the full set from
CODEBASE-REPORT section 8 was then corrected, and a check added so the trade
category cannot silently rot again. The remaining references lived in a
SUPERSEDED ADR and dated evidence, which the Program Owner directed be left as
historical records, and in FML-ADR-061's condition, which the Owner directed be
annotated as met (Option 1) without a design change. With that annotation there
are no known contradictions in the current controlling records. All generated
files reproduce without diff and the injected-mismatch test fires. SIMULATED.
