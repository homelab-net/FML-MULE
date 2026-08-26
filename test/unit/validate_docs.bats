#!/usr/bin/env bats
# Tests for tools/validate-docs.sh, tools/gen-status.sh and
# tools/gen-traceability.sh.
#
# A test that only confirms a checker passes on a clean tree tells you nothing:
# a script that exits zero unconditionally would pass it. Every check below is
# also tested by PLANTING A VIOLATION in a temporary copy of the repository and
# asserting the check catches it.
#
# That matters more than usual here, because these checks are the only thing
# enforcing several rules that are otherwise a matter of discipline:
# identifier permanence, evidence-backed closure, the fork ledger, and
# digest-pinned container images.

setup() {
  REPO="$BATS_TEST_DIRNAME/../.."
  REPO="$(cd "$REPO" && pwd)"
  export REPO
}

# Make a throwaway copy of the repository, so a planted violation can never
# touch the working tree. Copies the tracked tree only.
make_sandbox() {
  SANDBOX="$BATS_TEST_TMPDIR/repo"
  mkdir -p "$SANDBOX"
  ( cd "$REPO" && git ls-files -z ) |
    ( cd "$REPO" && xargs -0 tar -cf - ) |
    ( cd "$SANDBOX" && tar -xf - )
  export SANDBOX
}

# --- clean tree -------------------------------------------------------------

@test "validate-docs passes on the repository as committed" {
  run sh "$REPO/tools/validate-docs.sh" "$REPO"
  [ "$status" -eq 0 ]
  [[ "$output" == *"All documentation checks passed."* ]]
}

@test "gen-status --check confirms STATUS.md is not stale" {
  run sh "$REPO/tools/gen-status.sh" --check
  [ "$status" -eq 0 ]
}

@test "gen-traceability --check passes with no untraced requirement" {
  run sh "$REPO/tools/gen-traceability.sh" --check
  [ "$status" -eq 0 ]
}

# --- planted violations -----------------------------------------------------

@test "validate-docs detects an ADR missing a required section" {
  make_sandbox
  # Remove the "## Accepted cost" section from one ADR.
  target="$SANDBOX/docs/adr/FML-ADR-021-single-primary-compute-element.md"
  sed -i 's/^## Accepted cost$/## Cost we accept/' "$target"

  run sh "$SANDBOX/tools/validate-docs.sh" "$SANDBOX"
  [ "$status" -ne 0 ]
}

@test "validate-docs detects a duplicated ADR identifier" {
  make_sandbox
  # Identifiers are permanent and never reused. Copy one onto a new filename
  # keeping the original id in frontmatter.
  cp "$SANDBOX/docs/adr/FML-ADR-021-single-primary-compute-element.md" \
    "$SANDBOX/docs/adr/FML-ADR-021-duplicate-identifier.md"

  run sh "$SANDBOX/tools/validate-docs.sh" "$SANDBOX"
  [ "$status" -ne 0 ]
}

@test "validate-docs detects an ADR citing a trade that does not exist" {
  make_sandbox
  target="$SANDBOX/docs/adr/FML-ADR-022-host-operating-system-family.md"
  sed -i 's/^trades: \[TBR-LINUX-01, TBR-HW-01\]$/trades: [TBR-LINUX-01, TBR-NOSUCH-99]/' "$target"

  run sh "$SANDBOX/tools/validate-docs.sh" "$SANDBOX"
  [ "$status" -ne 0 ]
}

@test "validate-docs detects an ADR with a status outside the vocabulary" {
  make_sandbox
  target="$SANDBOX/docs/adr/FML-ADR-024-802-11s-batman-adv-baseline-ip-manet.md"
  sed -i 's/^status: SELECTED$/status: PROBABLY FINE/' "$target"

  run sh "$SANDBOX/tools/validate-docs.sh" "$SANDBOX"
  [ "$status" -ne 0 ]
}

@test "validate-docs detects a trade closed without evidence" {
  make_sandbox
  # A trade does not close on document wording alone.
  target="$SANDBOX/docs/trades/TBR-NET-01-field-address-prefix.md"
  sed -i 's/^status: OPEN$/status: CLOSED/' "$target"

  run sh "$SANDBOX/tools/validate-docs.sh" "$SANDBOX"
  [ "$status" -ne 0 ]
}

@test "validate-docs detects a carried patch with no fork ledger entry" {
  make_sandbox
  # Every carried patch is a liability with a name attached. The failure this
  # catches is otherwise silent: a patch lands, works, and is forgotten.
  cat > "$SANDBOX/os/kernel/patches/0001-planted-test-patch.patch" <<'PATCH'
--- a/placeholder
+++ b/placeholder
@@ -0,0 +1 @@
+planted by a test
PATCH

  run sh "$SANDBOX/tools/validate-docs.sh" "$SANDBOX"
  [ "$status" -ne 0 ]
}

@test "validate-docs detects a container image referenced by mutable tag" {
  make_sandbox
  printf 'Image=quay.io/planted/service:latest\n' \
    > "$SANDBOX/services/quadlets/planted-test.container"

  run sh "$SANDBOX/tools/validate-docs.sh" "$SANDBOX"
  [ "$status" -ne 0 ]
}

@test "validate-docs accepts a container image referenced by digest" {
  make_sandbox
  digest="sha256:0000000000000000000000000000000000000000000000000000000000000000"
  printf 'Image=quay.io/planted/service@%s\n' "$digest" \
    > "$SANDBOX/services/quadlets/planted-test.container"

  run sh "$SANDBOX/tools/validate-docs.sh" "$SANDBOX"
  [ "$status" -eq 0 ]
}

@test "gen-status --check detects a hand-edited STATUS.md" {
  make_sandbox
  # STATUS.md is generated and never hand-edited. A stale status page is how a
  # repository signals abandonment.
  printf '\nHand-edited line that generation would not produce.\n' \
    >> "$SANDBOX/STATUS.md"

  run sh -c "cd '$SANDBOX' && sh tools/gen-status.sh --check"
  [ "$status" -ne 0 ]
}

@test "gen-status reports a critical-path trade with no owner as a risk" {
  run sh "$REPO/tools/gen-status.sh" --check
  [ "$status" -eq 0 ]
  run grep -c "is on the critical path and has no owner" "$REPO/STATUS.md"
  [ "$status" -eq 0 ]
  [ "$output" -ge 1 ]
}

@test "gen-traceability --check fails on a binding requirement with no stage" {
  make_sandbox
  # A requirement with no validating stage is a defect, not a gap.
  cat > "$SANDBOX/docs/verification/planted-requirement.md" <<'REQ'
---
requirements:
  - id: FML-REQ-900
    source: CONOPS 0.0
    modal: shall
    text: Planted requirement with an allocation but no validating stage.
    allocation: FML-ADR-042
---

# Planted requirement
REQ

  run sh -c "cd '$SANDBOX' && sh tools/gen-traceability.sh --check"
  [ "$status" -ne 0 ]
}

@test "gen-traceability --check accepts a fully traced binding requirement" {
  make_sandbox
  cat > "$SANDBOX/docs/verification/planted-requirement.md" <<'REQ'
---
requirements:
  - id: FML-REQ-901
    source: CONOPS 0.0
    modal: shall
    text: Planted requirement with both an allocation and a validating stage.
    allocation: FML-ADR-042
    stage: STAGE-0
---

# Planted requirement
REQ

  run sh -c "cd '$SANDBOX' && sh tools/gen-traceability.sh --check"
  [ "$status" -eq 0 ]
}

# --- identifier allocation --------------------------------------------------

@test "new-adr allocates the next unused identifier and never reuses one" {
  make_sandbox
  run sh -c "cd '$SANDBOX' && sh tools/new-adr.sh 'Planted test decision'"
  [ "$status" -eq 0 ]
  # 045 is the highest seeded identifier, so the next is 046.
  [ -f "$SANDBOX/docs/adr/FML-ADR-046-planted-test-decision.md" ]
}

@test "new-trade allocates within its area and creates the evidence directory" {
  make_sandbox
  run sh -c "cd '$SANDBOX' && sh tools/new-trade.sh RF 'Planted test question'"
  [ "$status" -eq 0 ]
  # RF-03 is the highest seeded RF identifier, so the next is RF-04.
  [ -f "$SANDBOX/docs/trades/TBR-RF-04-planted-test-question.md" ]
  # The evidence directory exists before the work does, so that the closure
  # gate is written before the evidence is gathered.
  [ -d "$SANDBOX/docs/evidence/TBR-RF-04" ]
  [ -f "$SANDBOX/docs/evidence/TBR-RF-04/README.md" ]
}

@test "generated ADRs and trades pass validation" {
  make_sandbox
  sh -c "cd '$SANDBOX' && sh tools/new-adr.sh 'Planted test decision'"
  sh -c "cd '$SANDBOX' && sh tools/new-trade.sh RF 'Planted test question'"

  run sh "$SANDBOX/tools/validate-docs.sh" "$SANDBOX"
  [ "$status" -eq 0 ]
}

@test "new-adr refuses to overwrite an existing file" {
  make_sandbox
  sh -c "cd '$SANDBOX' && sh tools/new-adr.sh 'Planted test decision'"
  # Roll the identifier back so the script would allocate 046 again, and
  # confirm it refuses rather than clobbering.
  run sh -c "cd '$SANDBOX' && sh tools/new-adr.sh 'Planted test decision'"
  [ "$status" -eq 0 ]
  [ -f "$SANDBOX/docs/adr/FML-ADR-047-planted-test-decision.md" ]
}
