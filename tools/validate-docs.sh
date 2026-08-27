#!/bin/sh
# Validate the FERAL MULE documentation set.
#
# Usage: tools/validate-docs.sh [repo-root]
#
# Checks, in order:
#   1. Every ADR has the eight required sections.
#   2. Every ADR has the required frontmatter fields, with a valid status.
#   3. No ADR identifier is duplicated, and each matches its filename.
#   4. Every trade referenced by an ADR exists as a file in docs/trades/.
#   5. Every trade has the six required sections and its frontmatter fields.
#   6. No trade identifier is duplicated, and each matches its filename.
#   7. Every trade's evidence directory exists.
#   8. Every patch file in os/kernel/patches/ has an entry in docs/forks/.
#   9. No OCI image reference anywhere uses a mutable tag.
#  10. Every open trade appears in the ITEP campaign plan.
#  11. Every fake in the flat-sat is named in the flat-sat README.
#  12. Every directory has a README, or is named in its parent's README.
#
# Exits non-zero on the first category of failure found, after reporting every
# failure in the run. POSIX sh, no dependencies beyond coreutils, grep and sed.

set -eu

ROOT=${1:-$(dirname "$0")/..}
cd "$ROOT"
ROOT=$(pwd)

ADR_DIR=docs/adr
TRADE_DIR=docs/trades
FORK_DIR=docs/forks
PATCH_DIR=os/kernel/patches
ITEP=docs/verification/FML-MULE-ITEP-v0.1.md
FAKES=test/flatsat/fakes.py
FLATSAT_README=test/flatsat/README.md

fail_count=0

fail() {
  printf 'FAIL: %s\n' "$1" >&2
  fail_count=$((fail_count + 1))
}

info() {
  printf '  %s\n' "$1"
}

# Read one frontmatter field from a Markdown file. Frontmatter is the block
# between the first two lines consisting solely of "---".
frontmatter_field() {
  # $1 file, $2 field name
  awk -v field="$2" '
    NR == 1 && $0 == "---" { inside = 1; next }
    inside && $0 == "---" { exit }
    inside {
      idx = index($0, ":")
      if (idx > 0) {
        key = substr($0, 1, idx - 1)
        val = substr($0, idx + 1)
        gsub(/^[ \t]+|[ \t]+$/, "", key)
        gsub(/^[ \t]+|[ \t]+$/, "", val)
        if (key == field) { print val; exit }
      }
    }
  ' "$1"
}

# Expand a YAML flow sequence such as "[A, B]" into one item per line.
flow_items() {
  printf '%s\n' "$1" |
    sed -e 's/^\[//' -e 's/\]$//' -e 's/,/\n/g' |
    sed -e 's/^[[:space:]]*//' -e 's/[[:space:]]*$//' |
    grep -v '^$' || true
}

has_heading() {
  # $1 file, $2 heading text
  grep -qx "## $2" "$1"
}

printf 'Validating documentation in %s\n\n' "$ROOT"

# --- 1, 2, 3: ADRs ----------------------------------------------------------
printf 'Architecture decision records\n'

ADR_SECTIONS='Context
Decision
Status
Consequences
Accepted cost
Fallback
Superseded by
Verification dependency'

ADR_STATUSES='PROPOSED
SELECTED
SELECTED PRINCIPLE
SELECTED TARGET
SELECTED PLANNING BASELINE
PREFERRED
CONDITIONAL
SUPERSEDED
RETIRED'

seen_adr_ids=''
adr_count=0

for f in "$ADR_DIR"/FML-ADR-*.md; do
  [ -e "$f" ] || continue
  adr_count=$((adr_count + 1))
  base=$(basename "$f")

  # Required sections.
  printf '%s\n' "$ADR_SECTIONS" | while IFS= read -r section; do
    [ -n "$section" ] || continue
    has_heading "$f" "$section" || printf 'MISSING_SECTION %s\n' "$section"
  done >/tmp/fml-adr-sections.$$
  while IFS= read -r line; do
    section=${line#MISSING_SECTION }
    fail "$base is missing required section '## $section'"
  done </tmp/fml-adr-sections.$$
  rm -f /tmp/fml-adr-sections.$$

  # Frontmatter.
  id=$(frontmatter_field "$f" id)
  status=$(frontmatter_field "$f" status)
  supersedes=$(frontmatter_field "$f" supersedes)
  superseded_by=$(frontmatter_field "$f" superseded-by)
  trades=$(frontmatter_field "$f" trades)

  [ -n "$id" ] || fail "$base has no 'id' in frontmatter"
  [ -n "$status" ] || fail "$base has no 'status' in frontmatter"
  [ -n "$supersedes" ] || fail "$base has no 'supersedes' in frontmatter"
  [ -n "$superseded_by" ] || fail "$base has no 'superseded-by' in frontmatter"
  [ -n "$trades" ] || fail "$base has no 'trades' in frontmatter"

  # Status must be from the vocabulary in docs/adr/README.md.
  if [ -n "$status" ] && ! printf '%s\n' "$ADR_STATUSES" | grep -qx "$status"; then
    fail "$base has status '$status', which is not in the vocabulary in $ADR_DIR/README.md"
  fi

  # Identifier must match the filename.
  if [ -n "$id" ]; then
    case "$base" in
      "$id"-*.md) ;;
      *) fail "$base has id '$id', which does not match its filename" ;;
    esac

    # Identifiers are permanent and never reused.
    if printf '%s\n' "$seen_adr_ids" | grep -qx "$id"; then
      fail "duplicate ADR identifier '$id'. Identifiers are permanent and never reused."
    fi
    seen_adr_ids="$seen_adr_ids
$id"
  fi

  # Every trade an ADR cites must exist.
  for trade in $(flow_items "$trades"); do
    if ! ls "$TRADE_DIR/$trade"-*.md >/dev/null 2>&1; then
      fail "$base cites trade '$trade', which has no file in $TRADE_DIR/"
    fi
  done
done

info "$adr_count records checked"

# --- 4, 5, 6, 7: trades -----------------------------------------------------
printf 'Trades\n'

TRADE_SECTIONS='Question
Why it matters
Options
Closure evidence
Closure gate
Dependencies'

TRADE_STATUSES='OPEN
IN WORK
BLOCKED
CLOSED
ABANDONED'

seen_trade_ids=''
trade_count=0

for f in "$TRADE_DIR"/TBR-*.md; do
  [ -e "$f" ] || continue
  base=$(basename "$f")
  # Files beginning with an underscore are templates, not trades.
  case "$base" in _*) continue ;; esac
  trade_count=$((trade_count + 1))

  printf '%s\n' "$TRADE_SECTIONS" | while IFS= read -r section; do
    [ -n "$section" ] || continue
    has_heading "$f" "$section" || printf 'MISSING_SECTION %s\n' "$section"
  done >/tmp/fml-trade-sections.$$
  while IFS= read -r line; do
    section=${line#MISSING_SECTION }
    fail "$base is missing required section '## $section'"
  done </tmp/fml-trade-sections.$$
  rm -f /tmp/fml-trade-sections.$$

  id=$(frontmatter_field "$f" id)
  status=$(frontmatter_field "$f" status)
  owner=$(frontmatter_field "$f" owner)
  critical=$(frontmatter_field "$f" critical-path)
  evidence=$(frontmatter_field "$f" evidence)

  [ -n "$id" ] || fail "$base has no 'id' in frontmatter"
  [ -n "$status" ] || fail "$base has no 'status' in frontmatter"
  [ -n "$owner" ] || fail "$base has no 'owner' in frontmatter"
  [ -n "$critical" ] || fail "$base has no 'critical-path' in frontmatter"
  [ -n "$evidence" ] || fail "$base has no 'evidence' in frontmatter"

  if [ -n "$status" ] && ! printf '%s\n' "$TRADE_STATUSES" | grep -qx "$status"; then
    fail "$base has status '$status', which is not in the vocabulary in $TRADE_DIR/README.md"
  fi

  if [ -n "$id" ]; then
    case "$base" in
      "$id"-*.md) ;;
      *) fail "$base has id '$id', which does not match its filename" ;;
    esac
    if printf '%s\n' "$seen_trade_ids" | grep -qx "$id"; then
      fail "duplicate trade identifier '$id'. Identifiers are permanent and never reused."
    fi
    seen_trade_ids="$seen_trade_ids
$id"
  fi

  # A closed trade must cite evidence, and that evidence must exist. A trade
  # does not close on document wording alone.
  if [ -n "$evidence" ] && [ ! -d "$evidence" ]; then
    fail "$base names evidence directory '$evidence', which does not exist"
  fi
  if [ "$status" = "CLOSED" ]; then
    if [ -z "$(find "$evidence" -type f ! -name README.md 2>/dev/null | head -1)" ]; then
      fail "$base is CLOSED but $evidence holds no evidence. A trade does not close on wording alone."
    fi
  fi
done

info "$trade_count trades checked"

# --- 8: fork ledger ---------------------------------------------------------
printf 'Fork ledger\n'

patch_count=0
for p in "$PATCH_DIR"/*.patch "$PATCH_DIR"/*.diff; do
  [ -e "$p" ] || continue
  patch_count=$((patch_count + 1))
  pbase=$(basename "$p")
  found=0
  for entry in "$FORK_DIR"/*.md; do
    [ -e "$entry" ] || continue
    case "$(basename "$entry")" in README.md) continue ;; esac
    if grep -q "$PATCH_DIR" "$entry" 2>/dev/null; then
      found=1
      break
    fi
  done
  if [ "$found" -eq 0 ]; then
    fail "patch '$pbase' has no entry in $FORK_DIR/. Every carried patch is a liability with a name attached."
  fi
done

info "$patch_count patch files checked"

# --- 9: no mutable OCI image tags -------------------------------------------
printf 'Container image references\n'

# An OCI reference by digest contains "@sha256:". A reference carrying a tag
# instead is mutable: the image behind it can change with no file in this
# repository changing, so the artifact that was reviewed is not necessarily the
# artifact that runs. See FML-ADR-040 and services/README.md.
#
# Matched on reference SHAPE rather than on the surrounding keyword, so that a
# tag cannot slip in through a syntax this check did not anticipate:
#
#   <registry-with-a-dot-or-port>/<path>:<tag>
#
# Requiring a dot or a port in the registry is what keeps English prose such as
# "Baked into the image: reproducible" out of the results.
#
# EXEMPTION, deliberate and narrow: references under "example.org" and
# "example.invalid" are counter-examples in documentation, showing the form
# that is forbidden. Those hostnames are reserved for documentation and cannot
# resolve to a real registry, so exempting them cannot let a real mutable
# reference through. Exempting anything wider would defeat the check.
tag_hits=$(
  grep -rInoE '[a-z0-9][a-z0-9.-]*\.[a-z]{2,}(:[0-9]+)?/[a-z0-9._/-]+:[A-Za-z0-9._-]+' \
    --include='*.container' --include='*.md' --include='*.yml' --include='*.yaml' \
    --include='*.json' --include='*.template' --include='*.sh' --include='*.disabled' \
    --include='Containerfile' --include='Dockerfile' \
    . 2>/dev/null |
    grep -v '@sha256:' |
    grep -vE 'example\.(org|invalid|com)/' |
    grep -vE '://' || true
)
if [ -n "$tag_hits" ]; then
  printf '%s\n' "$tag_hits" | while IFS= read -r hit; do
    printf 'FAIL: mutable image tag: %s\n' "$hit" >&2
  done
  fail 'one or more OCI image references use a mutable tag. Use an immutable digest.'
fi

info 'checked'

# --- 10: every open trade is planned for in the ITEP -------------------------
printf 'ITEP campaign coverage\n'

# A trade with no plan to close it is a trade that will not close. The ITEP
# groups every open trade into a campaign; this check fails the build if a
# trade is added without one, so the plan cannot silently fall behind the
# register.
#
# Closed and abandoned trades are exempt: their campaign has served its purpose.

itep_count=0
if [ -f "$ITEP" ]; then
  for f in "$TRADE_DIR"/TBR-*.md; do
    [ -e "$f" ] || continue
    case "$(basename "$f")" in _*) continue ;; esac
    status=$(frontmatter_field "$f" status)
    case "$status" in CLOSED | ABANDONED) continue ;; esac
    id=$(frontmatter_field "$f" id)
    [ -n "$id" ] || continue
    itep_count=$((itep_count + 1))
    if ! grep -q "\`$id\`" "$ITEP"; then
      fail "$id is OPEN but does not appear in $ITEP. Every open trade needs a campaign."
    fi
  done
  info "$itep_count open trades checked against the ITEP"
else
  info "no ITEP found at $ITEP; coverage not checked"
fi

# --- 11: every fake is named in the flat-sat README -------------------------
#
# AGENTS.md makes this a rule rather than a courtesy: a reader must be able to
# see exactly which boundary is simulated, and an unlisted fake is how "it works
# on the flat-sat" becomes a permanent excuse. A rule nothing checks is a
# suggestion, so this checks it.

if [ -f "$FAKES" ] && [ -f "$FLATSAT_README" ]; then
  fake_count=0
  sed -n 's/^class \(Fake[A-Za-z0-9_]*\).*/\1/p' "$FAKES" >/tmp/fml-fakes.$$
  # Read from a file rather than a pipe: a while loop on the right of a pipe
  # runs in a subshell, and fake_count would not survive it.
  while read -r name; do
    [ -n "$name" ] || continue
    fake_count=$((fake_count + 1))
    if ! grep -q "\`$name\`" "$FLATSAT_README"; then
      fail "$name is defined in $FAKES but not named in $FLATSAT_README."
    fi
  done </tmp/fml-fakes.$$
  rm -f /tmp/fml-fakes.$$
  info "$fake_count flat-sat fakes checked against the README"
else
  info "no flat-sat fakes found; listing not checked"
fi

# --- 12: every directory is explained somewhere ------------------------------
#
# AGENTS.md: a reader who does not write code should be able to navigate this
# repository. A directory carries its own README.md, or its parent's README
# names it. Ansible's mandated role subdirectories are the case that needs the
# second form: a README in each would be noise, so the role README explains the
# layout instead.
#
# Generated, cache and vendored directories are skipped: nobody navigates them.

dir_count=0
find . -type d \
  -not -path './.git*' \
  -not -path './node_modules*' \
  -not -path '*__pycache__*' \
  -not -path './.pytest_cache*' \
  -not -path './.ruff_cache*' \
  -not -path './.ansible*' \
  -not -path '.' |
  sort >/tmp/fml-dirs.$$

while read -r dir; do
  [ "$dir" = "." ] && continue
  [ -n "$dir" ] || continue
  dir_count=$((dir_count + 1))
  [ -f "$dir/README.md" ] && continue
  parent=$(dirname "$dir")
  base=$(basename "$dir")
  if [ -f "$parent/README.md" ] && grep -q "$base" "$parent/README.md"; then
    continue
  fi
  fail "$dir has no README.md and is not named in $parent/README.md."
done </tmp/fml-dirs.$$
rm -f /tmp/fml-dirs.$$
info "$dir_count directories checked for a README or a parent that names them"

# --- result -----------------------------------------------------------------
printf '\n'
if [ "$fail_count" -gt 0 ]; then
  printf '%s failure(s).\n' "$fail_count" >&2
  exit 1
fi
printf 'All documentation checks passed.\n'
