#!/bin/sh
# Generate the decision index: where each decision shows up in the repository.
#
# Usage: tools/gen-decision-index.sh [--check] [--out PATH]
#
#   (no argument)  write the index to docs/decision-index.md
#   --check        write nothing; exit non-zero if the committed index is stale
#
# WHY THIS IS GENERATED AND NOT WRITTEN
#
# Reading a decision and asking "what actually implements this?" had no answer
# before this script. Code cites decisions in its comments, so the link exists
# in one direction only: you can read a module and find its ADR, but you cannot
# read an ADR and find its modules without grepping and hoping the convention
# was followed.
#
# A hand-maintained `implemented-by:` field would answer it and then rot, which
# is the failure this program has already had at a smaller scale. So the
# back-link is derived from the citations themselves. It cannot drift, because
# nobody writes it.
#
# WHY *.template IS SCANNED
#
# os/config/*.template is where a decision stops being prose and becomes
# configuration, and those files cite decisions heavily: nine of the ten cite at
# least one, and FML-ADR-056 alone is cited eight times. Until 2026-08-31 the
# scan covered .md, .py, .sh and .yml only, so every one of those citations was
# invisible here and an ADR implemented purely as configuration read as
# implemented by nothing. That is the exact failure this file exists to prevent,
# in the half of the repository where most decisions currently land.
#
# WHAT AN EMPTY ENTRY MEANS
#
# A decision cited nowhere is NOT a defect here. This program is pre-PDR and
# most decisions are deliberately not implemented yet. It is reported because
# the distinction matters: "decided and built", "decided and not yet built",
# and "decided, built, and nobody wrote down which" look identical without it.

set -eu

ROOT=$(cd "$(dirname "$0")/.." && pwd)
cd "$ROOT"

OUT=docs/decision-index.md
CHECK=0

while [ $# -gt 0 ]; do
  case $1 in
    --check)
      CHECK=1
      shift
      ;;
    --out)
      OUT=${2:?--out needs a path}
      shift 2
      ;;
    *)
      printf 'Usage: %s [--check] [--out PATH]\n' "$0" >&2
      exit 2
      ;;
  esac
done

# Citations are counted from the working repository, not from the controlled
# documents that decisions were extracted FROM. The SAD naming an ADR it
# originated is circular; a module naming the ADR it implements is the fact
# this index exists to record. Generated files are excluded for the same
# reason: they would cite whatever this run just wrote.
searchable() {
  find . -type f \( -name '*.md' -o -name '*.py' -o -name '*.sh' -o -name '*.yml' \
    -o -name '*.template' \) \
    -not -path './.git/*' \
    -not -path './node_modules/*' \
    -not -path './.venv*' \
    -not -path './venv*' \
    -not -path '*__pycache__*' \
    -not -path './.pytest_cache/*' \
    -not -path './.ruff_cache/*' \
    -not -path './.mypy_cache/*' \
    -not -path './.ansible/*' \
    -not -path '*.egg-info/*' \
    -not -path './docs/adr/*' \
    -not -path './docs/trades/*' \
    -not -path './docs/conops/*' \
    -not -path './docs/architecture/*' \
    -not -path './docs/decision-index.md' \
    -not -path './docs/verification/traceability.md' \
    -not -path './CHANGELOG.md' \
    -not -path './STATUS.md' |
    LC_ALL=C sort
}

# The virtualenv and the other generated trees are pruned for the same reason
# tools/validate-docs.sh prunes them: a dependency's files are not this
# repository's, and their decision-shaped strings are not its citations. It is
# also the difference between this script taking a second and taking minutes,
# because it greps every file it does not prune.
#
# LC_ALL=C on the sort above, and on every sort feeding a generated file: sort
# order is locale-dependent, and this file is committed and checked for drift.
# Under en_US.UTF-8 punctuation and case are largely ignored, so `docs/g` sorts
# before `docs/N` and `.github/` moves; under C they do not. A contributor on
# an ordinary desktop would otherwise regenerate a file that differs from the
# committed one in a few hundred lines they did not touch, and CI would fail on
# drift they could not explain.
#
# Pinned at the call site rather than exported, so that it holds even where
# LC_ALL is already set in the environment, and so that nothing else in this
# script changes its interpretation of characters.

# Where a citation lives decides how much it means. Code citing a decision is
# evidence the decision was implemented; a README citing it is evidence someone
# explained it. They are not the same claim, so they are not merged.
fmt() {
  # $1 an accumulated "`a`, `b`, " list, $2 what to say when it is empty.
  if [ -z "$1" ]; then
    printf '*%s*' "$2"
  else
    printf '%s' "${1%, }"
  fi
}

area_of() {
  # Implementation is code, not prose about code. A Markdown file explains a
  # decision wherever it sits: test/stages/ holds stage definitions, which are
  # documents, and counting them as implementation would inflate the column
  # that is supposed to mean "something acts on this".
  case $1 in
    *.md) printf 'docs' ;;
    ./mule/* | ./tools/* | ./os/* | ./test/*) printf 'built' ;;
    *) printf 'docs' ;;
  esac
}

tmp=$(mktemp)
trap 'rm -f "$tmp" "$tmp.body"' EXIT
searchable >"$tmp"

emit() {
  printf '# Decision index\n\n'
  printf '**Generated by `tools/gen-decision-index.sh`. Do not edit.**\n\n'
  printf 'Where each decision shows up in the working repository. Read an ADR or\n'
  printf 'trade, then come here to find what acts on it.\n\n'
  printf '**Implemented in** counts citations from code and configuration under\n'
  printf '`mule/`, `tools/`, `os/` and `test/`: something that acts on the decision.\n'
  printf '**Explained in** counts Markdown, wherever it sits: someone describing it.\n'
  printf 'A stage definition is a document, not an implementation. They are\n'
  printf 'different claims, so they are different columns.\n\n'
  printf 'The CONOPS and SAD are excluded: they are what decisions were extracted\n'
  printf 'from, so citing them would be circular.\n\n'
  printf 'An empty **Implemented in** cell is **not** a defect. This program is\n'
  printf 'pre-PDR and most decisions are deliberately not built yet. It is shown so\n'
  printf 'that "decided and built" and "decided, not yet built" stay apart.\n\n'

  for kind in adr trades; do
    case $kind in
      adr)
        printf '## Architecture decisions\n\n'
        dir=docs/adr
        glob='FML-ADR-*.md'
        ;;
      trades)
        printf '## Trades\n\n'
        dir=docs/trades
        glob='TBR-*.md'
        ;;
    esac

    printf '| Decision | Status | Implemented in | Explained in |\n'
    printf '| --- | --- | --- | --- |\n'
    for f in "$dir"/$glob; do
      [ -e "$f" ] || continue
      case "$(basename "$f")" in _*) continue ;; esac
      id=$(sed -n 's/^id: *//p' "$f" | head -1)
      [ -n "$id" ] || continue
      status=$(sed -n 's/^status: *//p' "$f" | head -1)

      built='' explained=''
      while read -r candidate; do
        grep -q "$id" "$candidate" 2>/dev/null || continue
        path=${candidate#./}
        if [ "$(area_of "$candidate")" = docs ]; then
          explained="$explained\`$path\`, "
        else
          built="$built\`$path\`, "
        fi
      done <"$tmp"

      printf '| `%s` | %s | %s | %s |\n' \
        "$id" "$status" \
        "$(fmt "$built" 'not yet')" \
        "$(fmt "$explained" 'nowhere')"
    done
    printf '\n'
  done
}

# Strip the trailing blank the section loop leaves behind: markdownlint MD012
# rejects it, and a generated file that fails the repository's own linter is a
# generator defect, not a lint exception.
emit | awk 'BEGIN { blank = 0 }
  /^$/ { blank++; next }
  { while (blank-- > 0) print ""; blank = 0; print }
' >"$tmp.body"

if [ "$CHECK" -eq 1 ]; then
  if [ ! -f "$OUT" ]; then
    printf 'FAIL: %s does not exist. Run tools/gen-decision-index.sh.\n' "$OUT" >&2
    exit 1
  fi
  if ! diff -q "$OUT" "$tmp.body" >/dev/null 2>&1; then
    printf 'FAIL: %s is stale. Run tools/gen-decision-index.sh and commit.\n' "$OUT" >&2
    diff -u "$OUT" "$tmp.body" | head -30 >&2
    exit 1
  fi
  printf '%s is up to date.\n' "$OUT"
  exit 0
fi

cp "$tmp.body" "$OUT"
printf 'Wrote %s\n' "$OUT"
