#!/bin/sh
# Check that the pinned toolchain is installable on arm64, without an arm64
# machine.
#
# Usage: tools/check-toolchain-arm64.sh
#
# WHY. FML-ADR-022 selects Debian, and the compute element is unselected but
# expected to be an arm64 board: the program is a portable field appliance, not
# a rack. Every version in this repository was nonetheless resolved on x86_64,
# because that is what continuous integration and the contributors have. A
# Python package with compiled extensions can have wheels for one architecture
# and not the other, and a refreshed lock file can lose arm64 support silently,
# on a machine where nothing tries it.
#
# So this asks the question that can be asked from here, on every run, rather
# than leaving it to the first person to unpack a board.
#
# WHAT IT PROVES, AND WHAT IT DOES NOT. It proves that a wheel exists for
# aarch64 for every pinned Python package, and that the arm64 binaries this
# repository pins are published and hash to what tools/toolchain-versions.sh
# records. That is resolvability, not function.
#
# IT DOES NOT RUN ANYTHING ON ARM64. Nothing here executes an arm64 binary, so
# it says nothing about whether the toolchain works there, and nothing at all
# about the node: no radio, no kernel module, no thermal behaviour. A green run
# means the install would find its files. See test/README.md.
#
# Needs network. Deliberately NOT part of tools/lint.sh, which is offline and
# should stay that way.

set -eu

ROOT=$(cd "$(dirname "$0")/.." && pwd)
cd "$ROOT"

# shellcheck source=tools/toolchain-versions.sh
. "$ROOT/tools/toolchain-versions.sh"

PY_LOCK="$ROOT/tools/requirements-dev.txt"
failures=0

fail() {
  printf 'FAIL: %s\n' "$1" >&2
  failures=$((failures + 1))
}

info() {
  printf '  %s\n' "$1"
}

need() {
  command -v "$1" >/dev/null 2>&1 || {
    printf 'ERROR: %s is required and not installed.\n' "$1" >&2
    printf 'Run tools/install-deps.sh first.\n' >&2
    exit 2
  }
}

need curl

# --- 1: every pinned Python package has an aarch64 wheel --------------------

printf 'Python lock, resolved for aarch64\n'

PIP="$ROOT/.venv/bin/pip"
if [ ! -x "$PIP" ]; then
  printf 'ERROR: %s is missing. Run tools/install-deps.sh --only python.\n' "$PIP" >&2
  exit 2
fi

# --only-binary=:all: is the point: it refuses to fall back to building from
# source, so a package with no aarch64 wheel fails here rather than turning
# into a compiler and a Rust toolchain on somebody's board.
wheels=$(mktemp -d)
if "$PIP" download --quiet --requirement "$PY_LOCK" --dest "$wheels" \
  --platform manylinux2014_aarch64 --only-binary=:all: \
  --python-version 3.13 >/dev/null 2>"$wheels/err"; then
  count=$(find "$wheels" -name '*.whl' | wc -l | tr -d ' ')
  native=$(find "$wheels" -name '*aarch64*.whl' | wc -l | tr -d ' ')
  info "$count wheel(s) resolve for aarch64; $native carry compiled aarch64 code"
else
  sed -n '1,20p' "$wheels/err" >&2
  fail 'one or more pinned Python packages have no aarch64 wheel.'
fi
rm -rf "$wheels"

# --- 2: the pinned arm64 binaries are published and match their digests -----

printf 'Pinned arm64 binaries\n'

check_digest() {
  # $1 label, $2 url, $3 expected sha256
  tmp=$(mktemp)
  if ! curl -fsSL -o "$tmp" "$2"; then
    rm -f "$tmp"
    fail "$1: arm64 artifact could not be downloaded from $2"
    return
  fi
  actual=$(sha256sum "$tmp" | cut -d' ' -f1)
  rm -f "$tmp"
  if [ "$actual" != "$3" ]; then
    fail "$1: arm64 digest mismatch. expected $3, got $actual"
    return
  fi
  info "$1: published and digest matches"
}

check_digest "shfmt v$SHFMT_VERSION" \
  "https://github.com/mvdan/sh/releases/download/v$SHFMT_VERSION/shfmt_v${SHFMT_VERSION}_linux_arm64" \
  "$SHFMT_SHA256_arm64"

check_digest "gitleaks v$GITLEAKS_VERSION" \
  "https://github.com/gitleaks/gitleaks/releases/download/v$GITLEAKS_VERSION/gitleaks_${GITLEAKS_VERSION}_linux_arm64.tar.gz" \
  "$GITLEAKS_SHA256_arm64"

# --- result -----------------------------------------------------------------

printf '\n'
if [ "$failures" -gt 0 ]; then
  printf '%s check(s) failed. The toolchain would not install on arm64.\n' "$failures" >&2
  exit 1
fi
printf 'The pinned toolchain resolves for arm64. Nothing here ran on arm64.\n'
