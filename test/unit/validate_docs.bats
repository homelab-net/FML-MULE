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
  # Replace whatever status this ADR currently carries, rather than one
  # particular value. Naming SELECTED here meant the test silently stopped
  # planting anything the day FML-ADR-053 superseded this ADR: the sed matched
  # nothing, the tree stayed valid, and the check could not fire.
  sed -i 's/^status: .*$/status: PROBABLY FINE/' "$target"
  grep -q '^status: PROBABLY FINE$' "$target"

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

@test "validate-docs detects an open trade with no ITEP campaign" {
  make_sandbox
  # A trade with no plan to close it is a trade that will not close. The plan
  # must not be allowed to fall silently behind the register.
  sh -c "cd '$SANDBOX' && sh tools/new-trade.sh RF 'Planted uncovered question'"

  run sh "$SANDBOX/tools/validate-docs.sh" "$SANDBOX"
  [ "$status" -ne 0 ]
}

@test "validate-docs detects a blocked service that hides what mule/ already does" {
  make_sandbox
  # FML-ADR-052. The failure this catches is a reader arriving at a directory
  # whose README says it contains nothing else, and concluding that none of the
  # component has been written, when a decision function in mule/ already
  # implements part of it. Strip every mention of the module from the blocked
  # README and the pairing must be reported.
  sed -i 's|mule/status\.py|that module|g' \
    "$SANDBOX/services/status-aggregator/README.md"

  run sh "$SANDBOX/tools/validate-docs.sh" "$SANDBOX"
  [ "$status" -ne 0 ]
  [[ "$output" == *"does not name mule/status.py"* ]]
}

@test "validate-docs does not pair a blocked service with mule/ through FML-ADR-052 itself" {
  make_sandbox
  # The rule ADR is cited by every blocked README that carries a cross-reference
  # and by every mule/ module that declares which conditions it meets. Pairing
  # on it would demand a link between all of them, which is a false link: the
  # exact defect shape this repository has recorded twice. Cite it from a
  # blocked README that has no other reason to name a module, and the check must
  # stay quiet.
  printf '\nSee `FML-ADR-052` for the boundary rule.\n' \
    >> "$SANDBOX/services/gateways/README.md"

  run sh "$SANDBOX/tools/validate-docs.sh" "$SANDBOX"
  [ "$status" -eq 0 ]
}

@test "validate-docs detects the mesh interface bridged with loop avoidance off" {
  make_sandbox
  # FML-ADR-054. The program owner records that several nodes are likely to
  # share one LAN during configuration, during over-the-air update and in a
  # tactical operations centre, which is the exact topology bridge loop
  # avoidance exists for. Two nodes bridging bat0 onto that segment form a loop
  # with nothing left to break it.
  #
  # This spelling specifically: the interface comes BEFORE the keyword, and the
  # first version of the check required the keyword first and passed it in
  # silence. It is the most common way to put an interface in a bridge.
  printf '\n    ip link set bat0 master br0\n' \
    >> "$SANDBOX/os/config/batman-adv.conf.template"

  run sh "$SANDBOX/tools/validate-docs.sh" "$SANDBOX"
  [ "$status" -ne 0 ]
  [[ "$output" == *"FML-ADR-054"* ]]
}

@test "validate-docs detects the access point bridged with loop avoidance off" {
  make_sandbox
  # The likely route to a bridge that carries bat0, and the reason the question
  # is asked in hostapd.conf.template at all: bridge=br0 is the textbook way to
  # build an access point, and nothing here can see what br0 carries.
  sed -i 's/^bridge=TBD$/bridge=br0/' "$SANDBOX/os/config/hostapd.conf.template"

  run sh "$SANDBOX/tools/validate-docs.sh" "$SANDBOX"
  [ "$status" -ne 0 ]
  [[ "$output" == *"FML-ADR-054"* ]]
}

@test "validate-docs allows bridging when loop avoidance is on" {
  make_sandbox
  # The check fires on a PAIRING, not on the word bridge. Bridging with loop
  # avoidance enabled is what the feature is for, and a check that forbade it
  # outright would be wrong about the design rather than strict about it.
  sed -i 's/^bridge_loop_avoidance=0/bridge_loop_avoidance=1/' \
    "$SANDBOX/os/config/batman-adv.conf.template"
  printf '\n    ip link set bat0 master br0\n' \
    >> "$SANDBOX/os/config/batman-adv.conf.template"

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

@test "gen-status reports every unowned critical-path trade as a risk" {
  run sh "$REPO/tools/gen-status.sh" --check
  [ "$status" -eq 0 ]

  # Derived from the trade files rather than matched against a phrase this test
  # and the generator would both have to hardcode. An earlier version grepped
  # for one sentence, and went stale silently when the wording changed.
  unowned=0
  for f in "$REPO"/docs/trades/TBR-*.md; do
    [ -e "$f" ] || continue
    case "$(basename "$f")" in _*) continue ;; esac
    grep -q "^critical-path: true" "$f" || continue
    owner=$(sed -n 's/^owner: *//p' "$f" | head -1)
    case "$owner" in TBD | TBD-*) ;; *) continue ;; esac
    unowned=$((unowned + 1))
    id=$(sed -n 's/^id: *//p' "$f" | head -1)
    # Whatever the wording, the risk section must name the trade.
    grep -q "$id" "$REPO/STATUS.md"
  done

  # The assertion is worthless if no trade qualifies, so prove some did.
  [ "$unowned" -ge 1 ]
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
  # Derived, not hardcoded: the register grows, and a hardcoded number would
  # make this test fail for the wrong reason every time an ADR is added.
  highest=$(ls "$SANDBOX/docs/adr" | sed -n 's/^FML-ADR-\([0-9][0-9][0-9]\)-.*/\1/p' |
    sort -n | tail -1)
  expected=$(printf 'FML-ADR-%03d' "$((10#$highest + 1))")

  run sh -c "cd '$SANDBOX' && sh tools/new-adr.sh 'Planted test decision'"
  [ "$status" -eq 0 ]
  [ -f "$SANDBOX/docs/adr/$expected-planted-test-decision.md" ]
}

@test "new-trade allocates within its area and creates the evidence directory" {
  make_sandbox
  highest=$(ls "$SANDBOX/docs/trades" | sed -n 's/^TBR-RF-\([0-9][0-9]\)-.*/\1/p' |
    sort -n | tail -1)
  expected=$(printf 'TBR-RF-%02d' "$((10#$highest + 1))")

  run sh -c "cd '$SANDBOX' && sh tools/new-trade.sh RF 'Planted test question'"
  [ "$status" -eq 0 ]
  [ -f "$SANDBOX/docs/trades/$expected-planted-test-question.md" ]
  # The evidence directory exists before the work does, so that the closure
  # gate is written before the evidence is gathered.
  [ -d "$SANDBOX/docs/evidence/$expected" ]
  [ -f "$SANDBOX/docs/evidence/$expected/README.md" ]
}

@test "a generated ADR passes validation unmodified" {
  make_sandbox
  sh -c "cd '$SANDBOX' && sh tools/new-adr.sh 'Planted test decision'"

  run sh "$SANDBOX/tools/validate-docs.sh" "$SANDBOX"
  [ "$status" -eq 0 ]
}

@test "a generated trade is invalid until it has an ITEP campaign" {
  make_sandbox
  sh -c "cd '$SANDBOX' && sh tools/new-trade.sh RF 'Planted test question'"

  run sh "$SANDBOX/tools/validate-docs.sh" "$SANDBOX"

  # This is correct behaviour, not a generator defect: check 10 requires every
  # open trade to have a campaign, and a trade nobody has planned to close is
  # a trade that will not close. An earlier version of this test asserted the
  # generated trade passed, which check 10 had made impossible.
  [ "$status" -ne 0 ]

  # The campaign gap must be the ONLY thing wrong, otherwise the generator is
  # producing incomplete artifacts and this test would hide it.
  run sh -c "sh '$SANDBOX/tools/validate-docs.sh' '$SANDBOX' 2>&1 | grep -c '^FAIL'"
  [ "$output" -eq 1 ]
  run sh -c "sh '$SANDBOX/tools/validate-docs.sh' '$SANDBOX' 2>&1 | grep '^FAIL'"
  [[ "$output" == *"does not appear in"* ]]
}

@test "new-adr refuses to overwrite an existing file" {
  make_sandbox
  sh -c "cd '$SANDBOX' && sh tools/new-adr.sh 'Planted test decision'"
  # Confirm the second call does not clobber the first.
  run sh -c "cd '$SANDBOX' && sh tools/new-adr.sh 'Planted test decision'"
  [ "$status" -eq 0 ]
  # The second call allocates the NEXT identifier rather than overwriting the
  # first. Identifiers are permanent and never reused.
  count=$(ls "$SANDBOX/docs/adr" | grep -c -- '-planted-test-decision\.md$')
  [ "$count" -eq 2 ]
}
