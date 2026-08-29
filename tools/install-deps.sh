#!/bin/sh
# Install the development toolchain that tools/lint.sh runs.
#
# Usage: tools/install-deps.sh [--check]
#
#   (no argument)  install what is missing
#   --check        install nothing; report what is missing and exit non-zero
#                  if anything is
#
# WHY THIS EXISTS. tools/lint.sh skips every tool that is not installed and
# still exits zero, so a fresh checkout produces a green run that has checked
# almost nothing. docs/dev-machine.md names that as the first thing that will
# fool you. Closing it previously meant reading .github/workflows/lint.yml and
# transcribing its install steps by hand.
#
# .github/workflows/lint.yml REMAINS THE AUTHORITATIVE LIST. This script
# mirrors it as a convenience, and the two are kept in step by review rather
# than by machinery. Where they disagree the workflow is right and this script
# is the defect.
#
# WHAT THIS DOES NOT DO. It installs the tools that check the repository. It
# does not install batctl, iw, tcpdump or iputils-arping, which the network
# plane work needs on a real machine; docs/dev-machine.md lists those. It
# builds no image and it verifies no hardware. A clean tools/lint.sh run after
# this still means only that the files parse and the documents agree with each
# other.
#
# SCOPE. Debian and its derivatives, because FML-ADR-022 selects the current
# Debian stable release as the host operating system family. On anything else
# this script reports what is needed and stops, rather than guessing at a
# package manager it has never been run against.

set -eu

ROOT=$(cd "$(dirname "$0")/.." && pwd)
cd "$ROOT"

# shfmt ships no apt package at the version CI uses, so it is fetched from its
# release page. The version is pinned and the download is checksummed: an
# unverified binary from the network is exactly the supply-chain problem
# SECURITY.md declines to accept. Both digests were recorded by downloading
# the published artifacts; update them together with the version.
SHFMT_VERSION=3.10.0
SHFMT_SHA256_amd64=1f57a384d59542f8fac5f503da1f3ea44242f46dff969569e80b524d64b71dbc
SHFMT_SHA256_arm64=9d23013d56640e228732fd2a04a9ede0ab46bc2d764bf22a4a35fb1b14d707a8

# Python tooling, installed into a repository-local virtualenv rather than
# system-wide. Debian marks its system Python externally managed, and a
# contributor's other projects have no business sharing this one's linters.
#
# Versions come from the lock file and from nowhere else (FML-ADR-058). The
# file records the fully resolved set that was exercised, so that "lint.sh
# passed" identifies which linters passed. Do not add package names here: a
# version installed from this script rather than the lock is exactly the drift
# the lock exists to prevent.
VENV="$ROOT/.venv"
PY_LOCK="$ROOT/tools/requirements-dev.txt"

# Debian packages. gitleaks is included because tools/lint.sh looks for the
# binary on PATH; CI runs the gitleaks action instead, so the versions there
# and here are not the same one.
APT_PACKAGES='shellcheck bats python3-venv nodejs npm gitleaks curl ca-certificates'

CHECK=0
if [ $# -gt 0 ]; then
  case "$1" in
    --check) CHECK=1 ;;
    -h | --help)
      sed -n '2,8p' "$0" | sed 's/^# \{0,1\}//'
      exit 0
      ;;
    *)
      printf 'ERROR: unknown argument: %s\n' "$1" >&2
      exit 2
      ;;
  esac
fi

have() {
  command -v "$1" >/dev/null 2>&1
}

as_root() {
  if [ "$(id -u)" -eq 0 ]; then
    "$@"
  else
    sudo "$@"
  fi
}

note() {
  printf '   %s\n' "$1"
}

step() {
  printf '\n== %s ==\n' "$1"
}

missing=''
record_missing() {
  missing="$missing $1"
}

# --- what is already here ---------------------------------------------------

step 'Current state'
for tool in shellcheck shfmt bats gitleaks markdownlint-cli2; do
  if have "$tool"; then
    note "$tool: present"
  else
    note "$tool: MISSING"
    record_missing "$tool"
  fi
done
for tool in ruff pytest yamllint ansible-lint coverage; do
  if have "$tool" || [ -x "$VENV/bin/$tool" ]; then
    note "$tool: present"
  else
    note "$tool: MISSING"
    record_missing "$tool"
  fi
done

if [ "$CHECK" -eq 1 ]; then
  step 'Result'
  if [ -z "$missing" ]; then
    note 'Nothing missing.'
    exit 0
  fi
  note "Missing:$missing"
  note 'Run tools/install-deps.sh to install them.'
  exit 1
fi

if [ -z "$missing" ]; then
  step 'Result'
  note 'Nothing to do; the toolchain is already installed.'
  exit 0
fi

# --- distribution gate ------------------------------------------------------

if ! have apt-get; then
  step 'Unsupported distribution'
  note 'This script installs through apt-get, which is not present here.'
  note 'FML-ADR-022 selects Debian stable, and this script has been run'
  note 'against nothing else. Install the equivalents by hand; the'
  note 'authoritative list is .github/workflows/lint.yml.'
  note ''
  note "Debian packages:  $APT_PACKAGES"
  note "Python packages:  from tools/requirements-dev.txt"
  note "shfmt:            v$SHFMT_VERSION from https://github.com/mvdan/sh"
  note 'Node:             markdownlint-cli2, installed globally with npm'
  exit 1
fi

# --- Debian packages --------------------------------------------------------

step 'Debian packages'
note "$APT_PACKAGES"
as_root apt-get update -qq
# env, not a prefix assignment: sudo does not carry the caller's environment
# through, so DEBIAN_FRONTEND would be lost and the install could stop on a
# prompt nobody is there to answer.
#
# Word splitting is intended: APT_PACKAGES is a list, not one argument.
# shellcheck disable=SC2086
as_root env DEBIAN_FRONTEND=noninteractive apt-get install -y -qq $APT_PACKAGES

# --- Python virtualenv ------------------------------------------------------

step 'Python virtualenv'
note "$VENV"
if [ ! -f "$PY_LOCK" ]; then
  printf 'ERROR: %s is missing.\n' "$PY_LOCK" >&2
  printf 'It carries the pinned toolchain (FML-ADR-058) and is not optional.\n' >&2
  exit 1
fi
if [ ! -x "$VENV/bin/python" ]; then
  python3 -m venv "$VENV"
fi
"$VENV/bin/pip" install --quiet --upgrade pip
"$VENV/bin/pip" install --quiet --requirement "$PY_LOCK"
note "Installed from tools/requirements-dev.txt."

# --- shfmt ------------------------------------------------------------------

step "shfmt v$SHFMT_VERSION"
if have shfmt && [ "$(shfmt --version 2>/dev/null)" = "v$SHFMT_VERSION" ]; then
  note 'Already at the pinned version.'
else
  arch=$(uname -m)
  case "$arch" in
    x86_64 | amd64)
      shfmt_arch=amd64
      shfmt_sha=$SHFMT_SHA256_amd64
      ;;
    aarch64 | arm64)
      shfmt_arch=arm64
      shfmt_sha=$SHFMT_SHA256_arm64
      ;;
    *)
      printf 'ERROR: no pinned shfmt digest for architecture %s.\n' "$arch" >&2
      printf 'Add one to this script rather than skipping verification.\n' >&2
      exit 1
      ;;
  esac

  url="https://github.com/mvdan/sh/releases/download/v$SHFMT_VERSION/shfmt_v${SHFMT_VERSION}_linux_$shfmt_arch"
  tmp=$(mktemp)
  curl -fsSL -o "$tmp" "$url"
  actual=$(sha256sum "$tmp" | cut -d' ' -f1)
  if [ "$actual" != "$shfmt_sha" ]; then
    rm -f "$tmp"
    printf 'ERROR: shfmt checksum mismatch.\n' >&2
    printf '  expected %s\n' "$shfmt_sha" >&2
    printf '  actual   %s\n' "$actual" >&2
    exit 1
  fi
  as_root install -m 0755 "$tmp" /usr/local/bin/shfmt
  rm -f "$tmp"
  note 'Installed and checksum verified.'
fi

# --- markdownlint-cli2 ------------------------------------------------------

step 'markdownlint-cli2'
if have markdownlint-cli2; then
  note 'Already installed.'
else
  as_root npm install -g --silent markdownlint-cli2
  note 'Installed.'
fi

# --- done -------------------------------------------------------------------

step 'Done'
note 'The Python tools live in .venv and tools/lint.sh finds them there'
note 'without activation. To run them directly, activate it first:'
note ''
note '  . .venv/bin/activate'
note ''
note 'Now run tools/lint.sh. It should report nothing skipped. A green run'
note 'means the files parse and the documents agree; it says nothing about'
note 'radios, battery life or thermal behaviour. See test/README.md.'
