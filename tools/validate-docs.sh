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
#  13. Nothing claims HARDWARE-VERIFIED while nothing has met hardware.
#  14. Every decision ID cited anywhere resolves to a real ADR or trade.
#  15. Every hardware reading in mule/ is accounted for in docs/readings.md.
#  16. Every numeric reading carries its unit in its name.
#  17. Every reading declares a source kind; command sources name a package.
#  18. A blocked service README names the mule/ modules that act on its ADR.
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

# Third-party and generated trees, excluded from every check that walks the
# repository. A dependency's files are not this repository's to validate, and
# two of them actively produce false failures: tools/install-deps.sh puts a
# virtualenv at ./.venv whose site-packages holds several hundred directories
# with no README (check 12), and ansible-lint ships JSON schemas that reference
# container images by mutable tag (check 9). Both would be reported as defects
# in this repository.
#
# Held in one variable rather than repeated per check, because the set had
# already drifted: check 9 excluded nothing, and the filter in check 14 was
# applied to grep -h -o output, which is bare identifiers with no path in them
# to match against.
#
# This is the set .gitignore already declares.
GREP_EXCLUDES="--exclude-dir=.git --exclude-dir=node_modules \
--exclude-dir=.venv* --exclude-dir=venv --exclude-dir=__pycache__ \
--exclude-dir=.pytest_cache --exclude-dir=.ruff_cache \
--exclude-dir=.mypy_cache --exclude-dir=.ansible --exclude-dir=*.egg-info"

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
  # Word splitting on $GREP_EXCLUDES is intended: it is a list of flags.
  # shellcheck disable=SC2086
  grep -rInoE '[a-z0-9][a-z0-9.-]*\.[a-z]{2,}(:[0-9]+)?/[a-z0-9._/-]+:[A-Za-z0-9._-]+' \
    --include='*.container' --include='*.md' --include='*.yml' --include='*.yaml' \
    --include='*.json' --include='*.template' --include='*.sh' --include='*.disabled' \
    --include='Containerfile' --include='Dockerfile' \
    $GREP_EXCLUDES . 2>/dev/null |
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
# The list below is the set .gitignore already declares. A virtualenv is the
# case that bites, because tools/install-deps.sh puts one at ./.venv and its
# site-packages tree contributes several hundred READMEless directories: the
# check would then fail on a tree whose tracked files are all correct.

dir_count=0
find . -type d \
  -not -path './.git*' \
  -not -path './node_modules*' \
  -not -path '*__pycache__*' \
  -not -path './.pytest_cache*' \
  -not -path './.ruff_cache*' \
  -not -path './.mypy_cache*' \
  -not -path './.ansible*' \
  -not -path './.venv*' \
  -not -path './venv*' \
  -not -path '*.egg-info*' \
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

# --- 13: nothing claims HARDWARE-VERIFIED while nothing has met hardware -----
#
# AGENTS.md: nothing in this repository is HARDWARE-VERIFIED. That was an
# honour rule until a review found three places where something looked verified
# because nobody asked what would have to break for a check to notice.
#
# Trade closure is NOT re-checked here; check 7 already refuses a CLOSED trade
# with an empty evidence directory, and a second check saying the same thing is
# noise that makes both easier to ignore.
#
# The moment real evidence lands this check steps aside, because the claim it
# guards becomes one somebody can substantiate. It is a stage-appropriate
# tripwire, not a permanent law, and it says so rather than pretending.

VOCABULARY_FILES="AGENTS.md CHANGELOG.md CONTRIBUTING.md README.md \
docs/glossary.md docs/verification/README.md test/README.md \
docs/evidence/README.md"

evidence_files=$(find docs/evidence test/results -type f ! -name README.md 2>/dev/null | wc -l)

if [ "$evidence_files" -eq 0 ]; then
  # shellcheck disable=SC2086
  grep -rl "HARDWARE-VERIFIED" --include="*.md" --include="*.py" \
    $GREP_EXCLUDES . 2>/dev/null |
    sed 's|^\./||' >/tmp/fml-hv.$$ || true
  while read -r claimed; do
    [ -n "$claimed" ] || continue
    case " $VOCABULARY_FILES " in
      *" $claimed "*) continue ;;
    esac
    fail "$claimed uses HARDWARE-VERIFIED, but nothing has met hardware. See AGENTS.md."
  done </tmp/fml-hv.$$
  rm -f /tmp/fml-hv.$$
  info "nothing has met hardware, and nothing claims to have"
else
  info "$evidence_files evidence file(s) present; hardware claims now need review, not this check"
fi

# --- 14: every cited decision ID resolves ------------------------------------
#
# Code cites decisions in its comments, and that citation is the only link from
# a module back to the reasoning behind it. Nothing checked the link, so a typo
# or a reference to a deleted ADR read exactly like a correct citation and the
# reader had no way to tell.
#
# Check 4 already does this for trades named in ADR frontmatter. This covers
# every other citation: code, tooling, tests and prose.
#
# Placeholders are excluded by pattern: FML-ADR-### and TBR-XXX-## appear in
# this repository as literal examples of the format, not as references.

cited_count=0
# Templates are excluded: they carry example IDs to show the format, which is
# what a template is for. Everything else citing an ID means it.
# shellcheck disable=SC2086
grep -rhoE '(FML-ADR-[0-9]{3}|TBR-[A-Z]+-[0-9]{2})' \
  --include='*.md' --include='*.py' --include='*.sh' --include='*.yml' \
  $GREP_EXCLUDES . 2>/dev/null |
  sort -u >/tmp/fml-cited.$$ || true

while read -r id; do
  [ -n "$id" ] || continue
  cited_count=$((cited_count + 1))
  case $id in
    FML-ADR-*) [ -n "$(find "$ADR_DIR" -name "$id-*.md" 2>/dev/null | head -1)" ] && continue ;;
    TBR-*) [ -n "$(find "$TRADE_DIR" -name "$id-*.md" 2>/dev/null | head -1)" ] && continue ;;
  esac
  # shellcheck disable=SC2086
  where=$(grep -rlE "$id" --include='*.md' --include='*.py' --include='*.sh' \
    --include='*.yml' $GREP_EXCLUDES . 2>/dev/null |
    grep -vE '(/_|FML-ADR-000-template)' | head -3 | tr '\n' ' ')
  [ -n "$where" ] || continue
  fail "$id is cited but no such decision exists. Seen in: $where"
done </tmp/fml-cited.$$
rm -f /tmp/fml-cited.$$
info "$cited_count distinct decision IDs cited"

# --- 15: every reading is accounted for --------------------------------------
#
# mule/thermal.py was written with a complete decision and no way to obtain the
# readings it judged. Nobody noticed until someone asked how it would read on
# real hardware, and the question immediately found a defect: an interface that
# could not express "this platform cannot tell me".
#
# So the question is asked in advance, for every reading, in docs/readings.md.
# This requires a row to exist. It cannot check that the row is true; what it
# prevents is a reading being added without anyone having thought about where
# the value comes from.

READINGS_DOC=docs/readings.md

if [ -f "$READINGS_DOC" ] && [ -x tools/list-readings.py ]; then
  reading_count=0
  command_count=0
  pinned_count=0
  tools/list-readings.py >/tmp/fml-readings.$$
  while IFS="$(printf '\t')" read -r reading verdict; do
    [ -n "$reading" ] || continue
    reading_count=$((reading_count + 1))

    # 16: a numeric reading whose name does not state its unit. Linux reports
    # the same quantity in millidegrees, tenths and percents depending on the
    # subsystem, and every conversion is a place to be wrong by a factor of a
    # hundred while producing a plausible number.
    if [ "$verdict" = "needs-unit" ]; then
      fail "$reading returns a number but its name does not state the unit."
    fi

    row=$(grep "^| \`$reading\`" "$READINGS_DOC" || true)
    if [ -z "$row" ]; then
      fail "$reading is read by mule/ but has no row in $READINGS_DOC."
      continue
    fi

    # 17: a reading is served by a kernel interface, by a command that must be
    # in the image, or by nothing. A command row names the package that
    # provides it, so the image build has something to guarantee.
    case "$row" in
      *'| `kernel` |'*) ;;
      *'| `none` |'*) ;;
      *'| `command` |'*)
        command_count=$((command_count + 1))
        if ! printf '%s' "$row" | grep -q 'package `'; then
          fail "$reading is a command source but names no package in $READINGS_DOC."
        else
          for pkg in $(printf '%s' "$row" | sed -n 's/.*package `\([a-z0-9.+-]*\)`.*/\1/p'); do
            grep -q "^$pkg=" os/image/manifest/packages.list 2>/dev/null &&
              pinned_count=$((pinned_count + 1))
          done
        fi
        ;;
      *) fail "$reading has no source kind in $READINGS_DOC. Use kernel, command or none." ;;
    esac
  done </tmp/fml-readings.$$
  rm -f /tmp/fml-readings.$$
  info "$reading_count hardware readings checked against $READINGS_DOC"
  # Reported, not failed: nothing is pinned yet by decision. TBR-LINUX-01.
  info "$command_count reading(s) need a command; $pinned_count of those packages are pinned"
else
  info "no readings register found; hardware readings not checked"
fi

# --- 18: a blocked service names the mule/ modules that act on its decision ---
#
# FML-ADR-052 permits a pure decision function in mule/ to reason about subject
# matter a blocked services/ component describes, on four conditions. The fourth
# obligation falls on the blocked component: its README names what already
# exists, so a reader arriving at a directory that says "this contains nothing
# else" learns that part of the behaviour lives elsewhere.
#
# Fires on a pairing, not on prose: a blocked README citing an ADR that a mule/
# module also cites, without naming that module.

blocked_count=0
pairing_count=0

for readme in services/*/README.md; do
  [ -f "$readme" ] || continue
  grep -q 'NOT YET IMPLEMENTABLE' "$readme" || continue
  blocked_count=$((blocked_count + 1))

  # FML-ADR-052 is excluded from its own scan. It is the rule, not a subject: a
  # README cites it to explain this cross-reference, and a mule/ module cites it
  # to declare which conditions it meets. Pairing those two would demand a link
  # between every blocked component and every module in mule/, which is the
  # false-link failure this repository has had before.
  #
  # Split on whitespace deliberately. An identifier contains none, and an
  # intermediate variable keeps this a list of IDs rather than a pipeline whose
  # loop body would run in a subshell and lose the counters.
  adrs=$(grep -o 'FML-ADR-[0-9][0-9][0-9]' "$readme" | sort -u | grep -v '^FML-ADR-052$' || true)

  for adr in $adrs; do
    for module in mule/*.py; do
      [ -f "$module" ] || continue
      grep -q "$adr" "$module" || continue
      pairing_count=$((pairing_count + 1))
      grep -q "$module" "$readme" ||
        fail "$readme cites $adr, and $module acts on it, but $readme does not name $module. FML-ADR-052."
    done
  done
done

info "$blocked_count blocked service(s); $pairing_count mule/ module pairing(s) checked"

# --- 19: the mesh interface shares a bridge only with access points --------
#
# FML-ADR-056. The mesh interface IS bridged, by design: SAD section 4.3
# bridges local EUD access into the BATMAN domain so peer ATAK multicast
# traverses the mesh and clients need no MANET routing awareness.
#
# The first version of this check forbade any bridge containing the mesh
# interface. That was written from FML-ADR-054's premise that the interface was
# bridged to nothing, which was wrong, and the check therefore forbade the
# baselined architecture. It would have fired the first time anyone implemented
# section 4.3, and a check that fires on correct configuration teaches people to
# work around checks.
#
# The real rule is narrower. A loop needs the mesh interface in a bridge AND a
# second path between the same layer 2 domain outside the mesh. The first is the
# architecture; the second is what FML-ADR-056 forbids. So an access point may
# share the bridge, and anything reaching a segment shared with another node may
# not: a wired uplink, a management port, a venue LAN. A wired link that should
# carry field traffic joins the mesh as a batman-adv hard interface instead,
# where batman-adv does its own loop-free path selection.

bla_setting=$(sed -n 's/^bridge_loop_avoidance=\([^ 	]*\).*/\1/p' \
  os/config/batman-adv.conf.template)
mesh_if=$(sed -n 's/^mesh_interface=\([^ 	]*\).*/\1/p' \
  os/config/batman-adv.conf.template)

# While mesh_interface is TBD, bat0 is the name every template, workflow and
# ADR uses, and therefore the name a bridge would be written against.
if [ -z "$mesh_if" ] || [ "$mesh_if" = TBD ]; then
  mesh_if=bat0
fi

# Interfaces that reach a segment another node might also reach. Deliberately
# shaped rather than exhaustive: it catches the names a person actually types.
UPLINK_PATTERN='\<(eth[0-9]|en[a-z0-9]+|usb[0-9]|wan[0-9]?|uplink|mgmt|wired)\>'

if [ "$bla_setting" = 0 ]; then
  # Collected first, then acted on, for the reason check 18 records: a while
  # loop on the right of a pipe runs in a subshell, so fail() called inside one
  # would increment a counter that dies with it.
  looped=$(find os -type f \
    \( -name '*.template' -o -name '*.conf' -o -name '*.yml' \) |
    while IFS= read -r conf; do
      # A bridge statement naming BOTH the mesh interface and an uplink is the
      # loop condition, spelled on one line. Comments are stripped first, which
      # is what lets the ADRs and this file discuss what they forbid.
      # No bridge keyword in the filter, deliberately. A structured file puts
      # the keyword on one line and the members on another:
      #
      #   bridges:
      #     br-field:
      #       interfaces: [bat0, eth0]
      #
      # Requiring the keyword passed that silently, and the comment above this
      # check claimed it did not. Two names on one line is the signal instead.
      #
      # batctl lines are excluded because "batctl meshif bat0 interface add
      # eth0" names both and is the CORRECT way to attach a wired link: it
      # joins the mesh, where batman-adv does loop-free selection, rather than
      # the bridge. FML-ADR-056 requires exactly that, so flagging it would
      # fire on the fix.
      if grep -vE '^[ 	]*#' "$conf" |
        grep -vE '(batctl|interface add)' |
        grep -E "\<$mesh_if\>" |
        grep -qE "$UPLINK_PATTERN"; then
        printf '%s\n' "$conf"
      fi
    done)

  # Split on whitespace deliberately; a path here contains none.
  for conf in $looped; do
    fail "$conf puts $mesh_if in a bridge with an uplink interface while bridge_loop_avoidance=0. Two nodes bridging one segment form a loop with nothing left to break it. A wired link carrying field traffic joins the mesh with batctl interface add instead. FML-ADR-056."
  done

  # WHAT THIS DOES NOT CATCH: membership where the two interfaces never appear
  # on the same line, which systemd-networkd produces by design, one file per
  # member:
  #
  #   /etc/systemd/network/10-bat0.network    [Network] Bridge=br-field
  #   /etc/systemd/network/11-eth0.network     [Network] Bridge=br-field
  #
  # Nothing here joins those. Doing so needs a model of the network stack,
  # which is TBR-LINUX-01's territory and does not exist yet. The gap closes
  # when configuration generation exists and this check moves to the generated
  # output, where membership resolves to one place.
fi

info "mesh interface $mesh_if, bridge_loop_avoidance=${bla_setting:-unset}, bridge membership checked"

# --- 19: every roadmap item carries its own state -----------------------------
#
# docs/ROADMAP-DEV.md used to write each item's state twice: once in the item
# and once in the sequencing prose. Finishing anything then invalidated both,
# and the file was corrected three times in two days, every time for that
# reason. The rule now is that an item's `**State:**` line is the only place
# its state is written.
#
# This checks the half a machine can. An item with no State line means the
# single source has gone missing, and the reader falls back to prose that is
# not maintained.
#
# WHAT THIS DOES NOT CATCH, and it is the more likely failure: state creeping
# back into the sequencing section. That needs a judgement about what a
# sentence is claiming, and the only thing preventing it is whoever reads the
# diff.

printf 'Roadmap item state\n'

ROADMAP=docs/ROADMAP-DEV.md
roadmap_items=0
if [ -f "$ROADMAP" ]; then
  # Numbered Track 1 items, "### 1.4 ..." and the like.
  # The pending heading is resolved BEFORE a new one replaces it. An earlier
  # version set the new heading first and used `next`, so the unresolved one
  # was overwritten and never reported: the check could not fail, which is the
  # defect it exists to prevent, in the check itself.
  awk '
    /^### / {
      if (pending != "" && seen == 0) print pending
      pending = ""; seen = 0
      if ($0 ~ /^### [0-9]+\.[0-9]+ /) pending = $0
      next
    }
    /^\*\*State:\*\*/ { if (pending != "") seen = 1 }
    END { if (pending != "" && seen == 0) print pending }
  ' "$ROADMAP" >/tmp/fml-roadmap.$$

  while IFS= read -r heading; do
    [ -n "$heading" ] || continue
    fail "$ROADMAP: \"$heading\" has no **State:** line. That line is the only place an item's state is written; see the sequencing section."
  done </tmp/fml-roadmap.$$
  rm -f /tmp/fml-roadmap.$$

  roadmap_items=$(grep -c '^### [0-9]\+\.[0-9]\+ ' "$ROADMAP" || true)
fi

info "$roadmap_items roadmap item(s) checked for a state line"

# --- result -----------------------------------------------------------------
printf '\n'
if [ "$fail_count" -gt 0 ]; then
  printf '%s failure(s).\n' "$fail_count" >&2
  exit 1
fi
printf 'All documentation checks passed.\n'
