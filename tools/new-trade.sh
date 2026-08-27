#!/bin/sh
# Create the next trade from the template.
#
# Usage: tools/new-trade.sh AREA "Question in sentence case"
#
# Allocates the next unused number within the area and writes the file from
# docs/trades/_TEMPLATE.md.
#
# IDENTIFIERS ARE PERMANENT AND NEVER REUSED, including identifiers used by
# files that have since been deleted, and including trades that were closed,
# merged into another, or abandoned. This script takes the highest number ever
# recorded in the area, from the working tree AND from the full git history,
# and adds one. It does not fill gaps.

set -eu

usage() {
  printf 'Usage: %s AREA "Question in sentence case"\n' "$0" >&2
  printf '\nAreas in use: LINUX PWR COMP THERM HW RF TAK HA SEC TIME REC CARRIER NET\n' >&2
  printf 'A new area is fine. Add it to docs/trades/README.md in the same change.\n' >&2
  exit 2
}

[ $# -eq 2 ] || usage
AREA=$(printf '%s' "$1" | tr '[:lower:]' '[:upper:]')
TITLE=$2
[ -n "$AREA" ] || usage
[ -n "$TITLE" ] || usage

case "$AREA" in
  *[!A-Z0-9]*)
    printf 'Area must be alphanumeric and upper case: %s\n' "$AREA" >&2
    exit 2
    ;;
esac

ROOT=$(cd "$(dirname "$0")/.." && pwd)
cd "$ROOT"

TRADE_DIR=docs/trades
EVIDENCE_DIR=docs/evidence
TEMPLATE="$TRADE_DIR/_TEMPLATE.md"

[ -f "$TEMPLATE" ] || {
  printf 'Template not found: %s\n' "$TEMPLATE" >&2
  exit 1
}

highest=0
for f in "$TRADE_DIR"/TBR-"$AREA"-*.md; do
  [ -e "$f" ] || continue
  n=$(basename "$f" | sed -n "s/^TBR-$AREA-\([0-9][0-9]\)-.*\$/\1/p")
  [ -n "$n" ] || continue
  n=$(printf '%s' "$n" | sed 's/^0*//')
  [ -n "$n" ] || n=0
  [ "$n" -gt "$highest" ] && highest=$n
done

if [ -d .git ] && command -v git >/dev/null 2>&1; then
  hist=$(
    git log --all --pretty=format: --name-only --diff-filter=A 2>/dev/null |
      sed -n "s|^docs/trades/TBR-$AREA-\([0-9][0-9]\)-.*\.md\$|\1|p" |
      sort -n | tail -1
  ) || hist=''
  if [ -n "$hist" ]; then
    hist=$(printf '%s' "$hist" | sed 's/^0*//')
    [ -n "$hist" ] || hist=0
    [ "$hist" -gt "$highest" ] && highest=$hist
  fi
fi

next=$((highest + 1))
id=$(printf 'TBR-%s-%02d' "$AREA" "$next")

slug=$(
  printf '%s' "$TITLE" |
    tr '[:upper:]' '[:lower:]' |
    sed -e 's/[^a-z0-9]\{1,\}/-/g' -e 's/^-//' -e 's/-$//'
)
[ -n "$slug" ] || {
  printf 'Title produced an empty slug: %s\n' "$TITLE" >&2
  exit 1
}

out="$TRADE_DIR/$id-$slug.md"
[ -e "$out" ] && {
  printf 'Refusing to overwrite existing file: %s\n' "$out" >&2
  exit 1
}

evidence="$EVIDENCE_DIR/$id"

{
  printf -- '---\n'
  printf 'id: %s\n' "$id"
  printf 'title: %s\n' "$TITLE"
  printf 'status: OPEN\n'
  printf 'owner: TBD-SRR\n'
  printf 'area: %s\n' "$AREA"
  printf 'priority: 99\n'
  printf 'function-owner: TBD\n'
  printf 'critical-path: false\n'
  printf 'depends-on: []\n'
  printf 'feeds: []\n'
  printf 'requires-hardware: TBD\n'
  printf 'evidence: %s/\n' "$evidence"
  printf 'adr: []\n'
  printf 'target-date: TBD-SRR\n'
  printf -- '---\n'
  printf '\n'
  printf '# %s %s\n' "$id" "$TITLE"
  sed -n '/^## Question$/,$p' "$TEMPLATE"
} >"$out"

# The evidence directory exists before the work does, so that the closure gate
# is written before evidence is gathered and the result cannot be graded
# against a standard invented after seeing it.
mkdir -p "$evidence"
if [ ! -e "$evidence/README.md" ]; then
  {
    printf '# Evidence for %s\n\n' "$id"
    printf '**Trade:** %s\n\n' "$TITLE"
    printf '**Trade file:** `%s`\n\n' "$out"
    printf '**Current contents:** none. This trade is `OPEN` and no evidence has been\n'
    printf 'produced.\n\n'
    printf 'Read the **Closure evidence** and **Closure gate** sections of the trade file\n'
    printf 'named above. Those sections are authoritative; this file does not restate them,\n'
    printf 'so that the two cannot drift apart.\n\n'
    printf 'Naming and recording rules are in `docs/evidence/README.md`. Nothing real: no\n'
    printf 'deployment location, member identity, callsign, credential, or operational\n'
    printf 'capture. See `SECURITY.md`.\n'
  } >"$evidence/README.md"
fi

printf 'Created %s\n' "$out"
printf 'Created %s/\n' "$evidence"
printf '\nNext:\n'
printf '  1. Fill in every section. Delete the template instructions.\n'
printf '  2. Write the closure gate BEFORE the work starts.\n'
printf '  3. Record a NAMED owner and a target date. Assigning both to every\n'
printf '     open TBR is an SRR exit action; TBD-SRR marks the gap.\n'
printf '  4. Set priority and function-owner from the SAD section 30.2 register.\n'
printf '  5. Add a row to %s/README.md and, if the area is new, list it there.\n' "$TRADE_DIR"
printf '  6. Run tools/validate-docs.sh and tools/gen-status.sh.\n'
