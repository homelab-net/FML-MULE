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
  #
  # The trade is chosen at run time rather than named. This test used to close
  # TBR-NET-01, which had no evidence when it was written and acquired some
  # later, at which point closing it stopped being a violation and the test
  # failed for a reason that had nothing to do with the check.
  target=""
  for candidate in "$SANDBOX"/docs/trades/TBR-*.md; do
    id=$(basename "$candidate" | cut -d- -f1-3)
    files=$(find "$SANDBOX/docs/evidence/$id" -type f ! -name README.md 2>/dev/null | wc -l)
    if [ "$files" -eq 0 ] && grep -q '^status: OPEN$' "$candidate"; then
      target="$candidate"
      break
    fi
  done
  [ -n "$target" ] || skip "every open trade now has evidence"
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

# --- vendored directories ---------------------------------------------------
#
# tools/install-deps.sh creates a virtualenv at .venv, which .gitignore has
# always declared. Its site-packages tree trips the two checks that walk the
# filesystem rather than the tracked file list: every directory needs a README
# (check 12), and nothing may reference a container image by mutable tag
# (check 9). ansible-lint really does ship JSON schemas that do the latter.
#
# Planted rather than trusted to be absent, because the failure it guards
# against is a contributor installing the documented toolchain and being told
# their untouched tree has four hundred defects. Both halves are planted in one
# test: they are one rule, and a second test saying the same thing would make
# both easier to ignore.

@test "validate-docs ignores a virtualenv in the working tree" {
  make_sandbox
  vendored="$SANDBOX/.venv/lib/python3.13/site-packages/planted"
  mkdir -p "$vendored/schemas"
  # A registry hostname outside the example.* exemption, so this line would
  # fail check 9 if the virtualenv were scanned.
  printf 'image: registry.planted.net/planted/tool:latest\n' \
    > "$vendored/schemas/planted.json"
  # A directory with no README, so this would fail check 12 the same way.
  printf 'planted\n' > "$vendored/notes.md"

  run sh "$SANDBOX/tools/validate-docs.sh" "$SANDBOX"
  [ "$status" -eq 0 ]
  [[ "$output" == *"All documentation checks passed."* ]]
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

@test "validate-docs detects the mesh interface bridged with an uplink" {
  make_sandbox
  # FML-ADR-056. A loop needs the mesh interface in a bridge AND a second path
  # outside the mesh. Both halves on one line is the loop condition.
  printf '\n  bridge_ports: bat0 eth0\n' >> "$SANDBOX/os/ansible/site.yml"

  run sh "$SANDBOX/tools/validate-docs.sh" "$SANDBOX"
  [ "$status" -ne 0 ]
  [[ "$output" == *"FML-ADR-056"* ]]
}

@test "validate-docs detects a bridge written as a structured list" {
  make_sandbox
  # netplan and friends put the keyword on one line and the members on
  # another. Requiring a bridge keyword in the filter passed this silently,
  # while the check's own comment claimed it did not. Caught by watching it.
  printf '\n      interfaces: [bat0, eth0]\n' >> "$SANDBOX/os/ansible/site.yml"

  run sh "$SANDBOX/tools/validate-docs.sh" "$SANDBOX"
  [ "$status" -ne 0 ]
}

@test "validate-docs detects the forbidden bridge built by a shell script" {
  make_sandbox
  # Configuration is not only declarative. A script that bridges the mesh
  # interface with an uplink builds the loop FML-ADR-056 forbids just as
  # surely as a .conf that declares it, and the check used to read only os/
  # and only declarative files, so nothing looked.
  cat > "$SANDBOX/test/bench/planted-loop.sh" <<'SH'
#!/bin/sh
ip link add name br-field type bridge
ip link set bat0 master br-field
ip link set eth0 master br-field
SH

  run sh "$SANDBOX/tools/validate-docs.sh" "$SANDBOX"
  [ "$status" -ne 0 ]
  [[ "$output" == *"across separate lines"* ]]
}

@test "validate-docs allows the access point bridged to the mesh interface" {
  make_sandbox
  # THE ARCHITECTURE, not a violation. SAD section 4.3 bridges local EUD access
  # into the BATMAN domain so peer ATAK multicast traverses the mesh. The first
  # version of this check forbade it, which would have fired the first time
  # anyone implemented the design. A check that fires on correct configuration
  # teaches people to work around checks.
  printf '\n  bridge_ports: bat0 wlan_ap0\n' >> "$SANDBOX/os/ansible/site.yml"
  sed -i 's/^bridge=TBD$/bridge=br-field/' "$SANDBOX/os/config/hostapd.conf.template"

  run sh "$SANDBOX/tools/validate-docs.sh" "$SANDBOX"
  [ "$status" -eq 0 ]
}

@test "validate-docs allows a wired link joined to the mesh with batctl" {
  make_sandbox
  # FML-ADR-056 requires a wired link carrying field traffic to join the mesh
  # rather than the bridge, because batman-adv does its own loop-free path
  # selection. That line names the mesh interface and an uplink together, so a
  # naive check fires on the very fix the ADR mandates.
  printf '\n  batctl meshif bat0 interface add eth0\n' >> "$SANDBOX/os/ansible/site.yml"

  run sh "$SANDBOX/tools/validate-docs.sh" "$SANDBOX"
  [ "$status" -eq 0 ]
}

# --- generated files do not depend on the contributor's locale ----------------
#
# sort order is locale-dependent. Under en_US.UTF-8 punctuation and case are
# largely ignored, so `docs/glossary.md` sorts before `docs/NON-GOALS.md` and
# `.github/` moves; under C they do not. The generators feed files that are
# committed and checked for drift, so an unpinned sort means a contributor on
# an ordinary desktop regenerates a few hundred lines they never touched and
# CI fails on drift they cannot explain. It is the same shape as a green run
# that checked nothing: the tool, not the tree, was wrong.

# --- roadmap state lives in one place ----------------------------------------
#
# docs/ROADMAP-DEV.md wrote each item's state twice, in the item and in the
# sequencing prose, and was corrected three times in two days because finishing
# anything invalidated both. The State line is now the single source and check
# 19 fails when one goes missing.
#
# The first version of that check could not fail: its awk replaced a pending
# heading before anything tested it, so a missing State line was overwritten
# and never reported. This test is why that was found.

@test "validate-docs detects a roadmap item with no state line" {
  make_sandbox
  # Delete the first State marker. The check looks for the marker, so removing
  # that one line is the whole violation.
  sed -i "0,/^\*\*State:\*\*/{/^\*\*State:\*\*/d}" "$SANDBOX/docs/ROADMAP-DEV.md"

  run sh "$SANDBOX/tools/validate-docs.sh" "$SANDBOX"
  [ "$status" -ne 0 ]
  [[ "$output" == *"has no **State:** line"* ]]
}

@test "gen-decision-index is stable across locales" {
  if ! locale -a 2>/dev/null | grep -qi '^en_US\.utf8$'; then
    skip "en_US.UTF-8 not available on this machine"
  fi
  LC_ALL=en_US.UTF-8 run sh "$REPO/tools/gen-decision-index.sh" --check
  [ "$status" -eq 0 ]
}

@test "gen-traceability is stable across locales" {
  if ! locale -a 2>/dev/null | grep -qi '^en_US\.utf8$'; then
    skip "en_US.UTF-8 not available on this machine"
  fi
  LC_ALL=en_US.UTF-8 run sh "$REPO/tools/gen-traceability.sh" --check
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
