#!/bin/sh
# Report how often a change that alters a decision citation records which
# decision it served.
#
# Usage: tools/refs-report.sh [--all] [--range REV_RANGE]
#
#   (no argument)  report on commits not yet on origin/main, or all history
#                  when that ref is absent
#   --all          report on all history
#   --range R      report on an explicit range, e.g. HEAD~20..HEAD
#
# THIS REPORTS. IT DOES NOT GATE.
#
# AGENTS.md marks the `Refs:` trailer `[review]`, and this script is why that
# is a defensible position rather than a hopeful one. The rule decays silently:
# nobody notices a missing trailer until the day they need to ask why a line
# changed and `git log --grep` cannot answer. A number that drifts is a
# reminder; a build that fails is a different decision, deliberately not taken
# here.
#
# WHAT COUNTS AS A COMMIT THAT NEEDED ONE
#
# Not "touched code". A change that adds or removes a decision citation in
# code, because that is the change which alters the relationship between the
# code and the reasoning behind it.
#
# The distinction is not pedantic. Adding a repository check that enforces an
# AGENTS.md rule touches `tools/` and serves no ADR, and a rule demanding a
# trailer there would produce a fabricated reference. A false link is worse
# than a missing one: it survives review because it looks deliberate.

set -eu

ROOT=$(cd "$(dirname "$0")/.." && pwd)
cd "$ROOT"

# FML-ADR-000 is the template. It is an example of the format, not a decision,
# so a diff touching it is not a decision link changing.
TEMPLATE_ID='FML-ADR-000'

RANGE=''
while [ $# -gt 0 ]; do
  case $1 in
    --all)
      RANGE='ALL'
      shift
      ;;
    --range)
      RANGE=${2:?--range needs a revision range}
      shift 2
      ;;
    *)
      printf 'Usage: %s [--all] [--range REV_RANGE]\n' "$0" >&2
      exit 2
      ;;
  esac
done

if [ -z "$RANGE" ]; then
  if git rev-parse --verify --quiet origin/main >/dev/null 2>&1 &&
    [ "$(git rev-list --count origin/main..HEAD 2>/dev/null || echo 0)" -gt 0 ]; then
    RANGE='origin/main..HEAD'
  else
    RANGE='ALL'
  fi
fi

if [ "$RANGE" = 'ALL' ]; then
  revs=$(git log --reverse --format=%H)
  scope='all history'
else
  revs=$(git log --reverse --format=%H "$RANGE")
  scope=$RANGE
fi

tmp=$(mktemp)
trap 'rm -f "$tmp"' EXIT
printf '%s\n' "$revs" >"$tmp"

needed=0
recorded=0
missing=''
mismatched=''

while read -r rev; do
  [ -n "$rev" ] || continue

  # Decision identifiers added or removed by this commit, in code rather than
  # prose. A README explaining a decision is not the code acting on one.
  raw=$(git show "$rev" -- 'mule/*' 'tools/*' 'os/*' 'test/*' 2>/dev/null |
    grep -E '^[+-]' | grep -vE '^(\+\+\+|---)' |
    grep -ohE '(FML-ADR-[0-9]{3}|TBR-[A-Z]+-[0-9]{2})' |
    grep -v "$TEMPLATE_ID" | sort -u || true)

  # Only identifiers that resolve to a real decision count. A test that plants
  # a deliberately bogus id to prove a check fires is doing its job, and
  # counting it here would report the test suite as a decision change forever.
  ids=''
  for id in $raw; do
    case $id in
      FML-ADR-*) dir=docs/adr ;;
      *) dir=docs/trades ;;
    esac
    [ -n "$(find "$dir" -name "$id-*.md" 2>/dev/null | head -1)" ] || continue
    ids="$ids$id "
  done
  ids=${ids% }
  [ -n "$ids" ] || continue

  needed=$((needed + 1))
  trailer=$(git log -1 --format=%B "$rev" | sed -n 's/^Refs: *//p' | head -1)
  short=$(git log -1 --format='%h %s' "$rev" | cut -c1-64)

  count=$(printf '%s' "$ids" | wc -w | tr -d ' ')
  if [ "$count" -gt 4 ]; then
    shown="$(printf '%s' "$ids" | cut -d' ' -f1-4) and $((count - 4)) more"
  else
    shown=$ids
  fi

  if [ -z "$trailer" ]; then
    missing="$missing    $short
        changed: $shown
"
    continue
  fi
  recorded=$((recorded + 1))

  # A trailer that names none of the changed decisions is not a fault: a change
  # can legitimately serve one decision while touching another's citation. It
  # is worth seeing, so it is shown separately rather than counted against.
  overlap=0
  for id in $ids; do
    case " $trailer " in
      *"$id"*)
        overlap=1
        break
        ;;
    esac
  done
  [ "$overlap" -eq 1 ] || mismatched="$mismatched    $short
        changed: $shown
        recorded: $trailer
"
done <"$tmp"

printf 'Refs: trailer coverage over %s\n\n' "$scope"

if [ "$needed" -eq 0 ]; then
  printf '  No commit in this range changed a decision citation in code.\n'
  exit 0
fi

percent=$((recorded * 100 / needed))
printf '  %s of %s commits that changed a decision citation recorded which (%s%%).\n' \
  "$recorded" "$needed" "$percent"

if [ -n "$missing" ]; then
  printf '\n  No Refs: trailer:\n'
  printf '%s' "$missing"
fi

if [ -n "$mismatched" ]; then
  printf '\n  Recorded a decision other than the one whose citation changed.\n'
  printf '  Often correct; shown so it is a choice rather than an oversight:\n'
  printf '%s' "$mismatched"
fi

printf '\n  This is a report, not a gate. AGENTS.md marks the rule [review].\n'
