---
schema_version: "1.0"
finding_id: GAP-04
scope: >-
  Target-aware configuration resolution: a node's active bearer set is declared
  node data under nodes/ and scopes which configuration targets gen-config
  resolves, validates and emits (FML-ADR-075), so the ROADMAP v0.0.1
  access-point-only node is not blocked by TBD values for bearers it does not
  field. RF configuration only; ingress/DNS/service config is out of scope.
governing_refs:
  - FML-ADR-075
  - TBR-RF-01
  - TBR-RF-02
  - TBR-RF-03
  - "ROADMAP.md v0.0.1"
pre_fix_reproduction: >-
  On the pre-fix tree, tools/gen-config.py checked and emitted every bearer
  target unconditionally, so an access-point-only node refused generation on the
  TBD HaLow, LoRa and mesh values it does not field, and could not resolve the
  one target the v0.0.1 milestone needs.
expected_failure: >-
  With the scoping defeated (resolve forced to all targets),
  test_an_ap_only_node_emits_only_its_bearer_blocks finds a HaLow block that
  should not be present and
  test_an_ap_only_node_refuses_only_on_the_trade_for_its_own_bearer sees the
  HaLow/LoRa trade named in a refusal that should mention only TBR-RF-03.
implementation_commit: 96d79ee894e744c60b8b21a7056b97ef88ba7781
files_changed:
  - tools/gen-config.py
  - nodes/README.md
  - nodes/_template/node.yml
  - nodes/mule-v001/node.yml
  - test/fixtures/nodes/README.md
  - test/fixtures/nodes/ap-only/node.yml
  - test/unit/test_gen_config.py
  - test/flatsat/mutations.yml
  - docs/adr/FML-ADR-075-a-node-s-active-bearer-set-is-declared-node-data-and-scopes-which-configuration-targets-must-resolve.md
tests:
  - name: unit and flat-sat suite
    command: "python -m pytest test/flatsat test/unit -q"
    exit_code: 0
  - name: gen-config target-aware unit tests
    command: "python -m pytest test/unit/test_gen_config.py -q"
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
      Corrected the framing that two fitment vocabularies existed (fitment was
      declared in neither), kept required and fielded distinct, scoped RF vs
      config targets, and grounded the tools-to-mule import in existing
      precedent rather than an overstated ADR claim.
  - attempt: "Independent verification of the implementation on PR #120"
    outcome: >-
      Confirmed backward compatibility (no --node resolves all targets), the
      scoped path, the unknown-active-bearer hard error, and required not being
      derived from fielded; only a stale decision-index.md was found, since
      regenerated.
  - attempt: "Mutation testing of the new behaviour (M11, M100, M101)"
    outcome: "Each mutation killed; 101/101 mutations caught overall."
residual_risks:
  - >-
    SIMULATED only: the TBR-RF-01/02/03 trades still owe the real channel and
    power values, so a real region profile still refuses until they close.
deferred_work:
  - >-
    Ingress, DNS and service configuration for v0.0.1 are not modelled by
    gen-config and remain a separate finding.
  - >-
    Auto-detecting fitment from radio enumeration rather than a declared
    descriptor is deferred to when a node can enumerate its own radios.
closure_approved_by: "Cameron Zobrist"
redaction_statement: >-
  This packet contains no credentials, keys, callsigns, or real identities;
  all referenced fixtures use synthetic values.
owner_approval_refs:
  - >-
    Program Owner approval in the Claude Code session of 2026-09-11: the
    capability/target model (declared node data, v0.0.1 = {wifi_ap}) approved,
    and closure directed in this PR.
---

# GAP-04 closure packet

## Summary

Configuration generation is now target-aware. A node declares its active bearer
set as node data under `nodes/`, and `gen-config` resolves, validates and emits
only those targets. The ROADMAP v0.0.1 access-point-only node therefore
generates its configuration without being blocked by the `TBD` HaLow, LoRa and
mesh values it does not field, while still refusing on its own AP channel until
`TBR-RF-03` closes. FML-ADR-075 carries the decision.

## Closure rationale

The defect was real: resolution was whole-catalogue, so the first-milestone node
could not configure itself. The fix scopes resolution to a declared active
bearer set, keeps `active` and `required` distinct, treats an unknown active
bearer as a hard error, and preserves the whole-catalogue behaviour when no node
is given. It is covered by failing-first tests demonstrated to fail against
defeated scoping, and by mutations M11/M100/M101 which the suite kills. The full
mutation check reports 101/101, `mule/` coverage stays at 100 percent, and CI on
PR #120 is green. An independent verifier separate from the implementer reviewed
the change; the Program Owner approved the model and directed closure in this
PR. The evidence tier is SIMULATED, and the RF trades remain open by design.
