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

if have python3; then
  run "validate-mission" python3 tools/validate-mission.py
else
  skip "validate-mission" python3
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
