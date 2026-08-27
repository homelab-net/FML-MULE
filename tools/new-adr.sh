#!/bin/sh
# Create the next architecture decision record from the template.
#
# Usage: tools/new-adr.sh "Title in sentence case"
#
# Allocates the next unused FML-ADR identifier and writes the file from
# docs/adr/FML-ADR-000-template.md.
#
# IDENTIFIERS ARE PERMANENT AND NEVER REUSED, including identifiers used by
# files that have since been deleted. This script therefore takes the highest
# identifier ever recorded, from the working tree AND from the full git
# history, and adds one. It does not count files and it does not fill gaps: a
# gap in the numbering is information, and filling it destroys that
# information.

set -eu

usage() {
  printf 'Usage: %s "Title in sentence case"\n' "$0" >&2
  exit 2
}

[ $# -eq 1 ] || usage
TITLE=$1
[ -n "$TITLE" ] || usage

ROOT=$(cd "$(dirname "$0")/.." && pwd)
cd "$ROOT"

ADR_DIR=docs/adr
TEMPLATE="$ADR_DIR/FML-ADR-000-template.md"

[ -f "$TEMPLATE" ] || {
  printf 'Template not found: %s\n' "$TEMPLATE" >&2
  exit 1
}

# Highest identifier in the working tree.
highest=0
for f in "$ADR_DIR"/FML-ADR-*.md; do
  [ -e "$f" ] || continue
  n=$(basename "$f" | sed -n 's/^FML-ADR-\([0-9][0-9][0-9]\)-.*$/\1/p')
  [ -n "$n" ] || continue
  n=$(printf '%s' "$n" | sed 's/^0*//')
  [ -n "$n" ] || n=0
  [ "$n" -gt "$highest" ] && highest=$n
done

# Highest identifier ever recorded in git history, so that a deleted ADR's
# identifier is never reissued.
if [ -d .git ] && command -v git >/dev/null 2>&1; then
  hist=$(
    git log --all --pretty=format: --name-only --diff-filter=A 2>/dev/null |
      sed -n 's|^docs/adr/FML-ADR-\([0-9][0-9][0-9]\)-.*\.md$|\1|p' |
      sort -n | tail -1
  ) || hist=''
  if [ -n "$hist" ]; then
    hist=$(printf '%s' "$hist" | sed 's/^0*//')
    [ -n "$hist" ] || hist=0
    [ "$hist" -gt "$highest" ] && highest=$hist
  fi
fi

next=$((highest + 1))
id=$(printf 'FML-ADR-%03d' "$next")

# Slug: lower case, non-alphanumeric to hyphen, collapse and trim hyphens.
slug=$(
  printf '%s' "$TITLE" |
    tr '[:upper:]' '[:lower:]' |
    sed -e 's/[^a-z0-9]\{1,\}/-/g' -e 's/^-//' -e 's/-$//'
)
[ -n "$slug" ] || {
  printf 'Title produced an empty slug: %s\n' "$TITLE" >&2
  exit 1
}

out="$ADR_DIR/$id-$slug.md"
[ -e "$out" ] && {
  printf 'Refusing to overwrite existing file: %s\n' "$out" >&2
  exit 1
}

today=$(date -u +%Y-%m-%d)

{
  printf -- '---\n'
  printf 'id: %s\n' "$id"
  printf 'title: %s\n' "$TITLE"
  printf 'status: PROPOSED\n'
  printf 'date: %s\n' "$today"
  printf 'supersedes: none\n'
  printf 'superseded-by: none\n'
  printf 'trades: []\n'
  printf 'verification: TBD\n'
  printf -- '---\n'
  printf '\n'
  printf '# %s %s\n' "$id" "$TITLE"
  # Body of the template, from the first "## Context" onward.
  sed -n '/^## Context$/,$p' "$TEMPLATE"
} >"$out"

printf 'Created %s\n' "$out"
printf '\nNext:\n'
printf '  1. Fill in every section. Delete the template instructions.\n'
printf '  2. List the trades this decision depends on in frontmatter.\n'
printf '     Every trade you cite must exist in docs/trades/.\n'
printf '  3. Set the status from the vocabulary in %s/README.md.\n' "$ADR_DIR"
printf '  4. If this supersedes an earlier ADR, record it in BOTH directions.\n'
printf '  5. Run tools/validate-docs.sh and tools/gen-status.sh.\n'
