#!/bin/sh
# Run every configured linter over the repository.
#
# Usage: tools/lint.sh
#
# Runs whatever is installed and SKIPS what is not, reporting which. That is
# deliberate: a contributor should be able to run this and get useful results
# without first installing six tools. CI installs all of them, so nothing is
# skipped there.
#
# Exits non-zero if any linter that ran reported a problem.

set -eu

ROOT=$(cd "$(dirname "$0")/.." && pwd)
cd "$ROOT"

failures=0
skipped=''

have() {
  command -v "$1" >/dev/null 2>&1
}

run() {
  # $1 label, rest command
  label=$1
  shift
  printf '\n== %s ==\n' "$label"
  if "$@"; then
    printf '   ok\n'
  else
    printf '   FAILED\n' >&2
    failures=$((failures + 1))
  fi
}

skip() {
  printf '\n== %s ==\n' "$1"
  printf '   skipped, %s not installed\n' "$2"
  skipped="$skipped $2"
}

# --- shell ------------------------------------------------------------------
# POSIX sh where possible, bash where not. Every script opens with `set -eu`
# and a usage comment. See CONTRIBUTING.md.
shell_files=$(find tools -name '*.sh' -type f | sort)

if have shellcheck; then
  # Word splitting on $shell_files is intended: the linter takes a file list.
  # shellcheck disable=SC2086
  run shellcheck shellcheck $shell_files
else
  skip shellcheck shellcheck
fi

if have shfmt; then
  # shellcheck disable=SC2086
  run "shfmt (formatting)" shfmt -d -i 2 -ci $shell_files
else
  skip "shfmt (formatting)" shfmt
fi

# --- python -----------------------------------------------------------------
if have ruff; then
  run "ruff (lint)" ruff check .
  run "ruff (format)" ruff format --check .
else
  skip ruff ruff
fi

# --- yaml -------------------------------------------------------------------
if have yamllint; then
  run yamllint yamllint .
else
  skip yamllint yamllint
fi

# --- ansible ----------------------------------------------------------------
if have ansible-lint; then
  run ansible-lint ansible-lint os/ansible
else
  skip ansible-lint ansible-lint
fi

if have ansible-playbook; then
  run "ansible-playbook --syntax-check" \
    ansible-playbook -i os/ansible/inventory/example.yml \
    os/ansible/site.yml --syntax-check
else
  skip "ansible-playbook --syntax-check" ansible-playbook
fi

# --- markdown ---------------------------------------------------------------
if have markdownlint-cli2; then
  run markdownlint markdownlint-cli2 '**/*.md'
else
  skip markdownlint markdownlint-cli2
fi

# --- secrets ----------------------------------------------------------------
# No private key, certificate, credential, real callsign, real member identity,
# real deployment location, or captured operational data ever enters this
# repository. See SECURITY.md.
if have gitleaks; then
  run gitleaks gitleaks detect --no-banner --redact --source .
else
  skip gitleaks gitleaks
fi

# --- repository checks ------------------------------------------------------
run "validate-docs" sh tools/validate-docs.sh
run "gen-status --check" sh tools/gen-status.sh --check
run "gen-traceability --check" sh tools/gen-traceability.sh --check
run "gen-decision-index --check" sh tools/gen-decision-index.sh --check

# Reports, never gates: the Refs: rule is [review] in AGENTS.md and this is what
# keeps that honest. It exits 0 whatever it finds; read the number.
run "refs-report" sh tools/refs-report.sh

if have python3; then
  run "validate-mission" python3 tools/validate-mission.py
else
  skip "validate-mission" python3
fi

# Mutation check: does the test suite actually notice a broken node? Runs the
# suite once per mutation, so it is the slowest check here and still seconds.
if have python3 && python3 -c "import pytest, yaml" 2>/dev/null; then
  run "mutation-check" python3 tools/mutation-check.py
else
  skip "mutation-check" python3
fi

# --- coverage of the production package -------------------------------------
# An uncovered line in mule/ is a decision nobody tested or code nobody can
# reach, and this repository has shipped the second kind twice. See the
# reasoning at the top of the script.

if have python3 && python3 -c "import coverage, pytest" 2>/dev/null; then
  run "coverage-check" sh tools/coverage-check.sh
else
  skip "coverage-check" coverage
fi

# --- shell unit tests -------------------------------------------------------
# These plant violations in a throwaway copy of the tree and assert each check
# catches them. They belong here rather than only in CI: AGENTS.md says a change
# is done when tools/lint.sh passes, and a command that omits the shell tests
# makes that sentence untrue. Two failures survived unnoticed that way.

if have bats; then
  run "bats" bats test/unit
else
  skip "bats" bats
fi

# --- result -----------------------------------------------------------------
printf '\n'
if [ -n "$skipped" ]; then
  printf 'Skipped (not installed):%s\n' "$skipped"
  printf 'CI installs all of these, so nothing is skipped there.\n\n'
fi

if [ "$failures" -gt 0 ]; then
  printf '%s linter(s) reported problems.\n' "$failures" >&2
  exit 1
fi
printf 'All linters that ran are clean.\n'
