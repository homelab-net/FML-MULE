#!/bin/sh
# Install the development toolchain that tools/lint.sh runs.
#
# Usage: tools/install-deps.sh [--check] [--only GROUP[,GROUP...]]
#
#   (no argument)  install what is missing
#   --check        install nothing; report what is missing and exit non-zero
#                  if anything is
#   --only         act on the named groups only. One or more of:
#                    apt       shellcheck, bats, Node, curl
#                    python    the pinned toolchain, into .venv
#                    shfmt     the pinned shfmt binary
#                    gitleaks  the pinned gitleaks binary
#                    node      markdownlint-cli2, pinned, globally
#                    lora      the LoRa plane bench: docker, the pinned
#                              meshtasticd image, and the pinned Meshtastic
#                              client in .venv-lora
#
# --only exists for continuous integration, whose jobs are split by language
# and would otherwise each install the whole toolchain to use a quarter of it.
# It is also why the workflow can call this script rather than restating the
# package list: one source of versions, used by both.
#
# WHY THIS EXISTS. tools/lint.sh skips every tool that is not installed and
# still exits zero, so a fresh checkout produces a green run that has checked
# almost nothing. docs/dev-machine.md names that as the first thing that will
# fool you. Closing it previously meant reading .github/workflows/lint.yml and
# transcribing its install steps by hand.
#
# THIS SCRIPT IS THE AUTHORITATIVE LIST. .github/workflows/lint.yml calls it
# rather than restating the packages, so continuous integration installs what a
# contributor installs and the two cannot drift. That was not always so: the
# workflow used to carry its own copy, and this script mirrored it by review.
# If you add a tool, add it here, and CI picks it up with no second edit.
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

# Pinned tool versions and their digests, shared with
# tools/check-toolchain-arm64.sh so that neither can drift from the other.
# shellcheck source=tools/toolchain-versions.sh
. "$ROOT/tools/toolchain-versions.sh"

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

# The LoRa bench, kept out of the lint virtualenv. See the header of the file.
LORA_VENV="$ROOT/.venv-lora"
LORA_LOCK="$ROOT/tools/requirements-lora.txt"

# Debian packages: the ones whose distribution build is the thing we want, and
# whose version does not decide what passes. shellcheck and bats are pinned by
# the distribution; shfmt, gitleaks and markdownlint-cli2 are pinned above
# because their versions do decide what passes.
APT_PACKAGES='shellcheck bats python3-venv nodejs npm curl ca-certificates'

CHECK=0

# Every group --only will accept.
ALL_GROUPS='apt python shfmt gitleaks node lora'

# What a bare run installs, which is NOT all of them. lora is opt-in: it pulls
# a container runtime and an image, and most work in this repository does not
# touch that plane. An earlier version defaulted to ALL_GROUPS while
# tools/README.md said lora was not installed by default, so a fresh Debian
# ended up with docker.io and criu to run a linter, and the documentation was
# describing something the code did not do.
DEFAULT_GROUPS='apt python shfmt gitleaks node'

WANTED=$DEFAULT_GROUPS

while [ $# -gt 0 ]; do
  case "$1" in
    --check) CHECK=1 ;;
    --only)
      shift
      [ $# -gt 0 ] || {
        printf 'ERROR: --only needs a group list.\n' >&2
        exit 2
      }
      WANTED=$(printf '%s' "$1" | tr ',' ' ')
      ;;
    --only=*)
      WANTED=$(printf '%s' "${1#--only=}" | tr ',' ' ')
      ;;
    -h | --help)
      sed -n '2,17p' "$0" | sed 's/^# \{0,1\}//'
      exit 0
      ;;
    *)
      printf 'ERROR: unknown argument: %s\n' "$1" >&2
      exit 2
      ;;
  esac
  shift
done

for g in $WANTED; do
  case " $ALL_GROUPS " in
    *" $g "*) ;;
    *)
      printf 'ERROR: unknown group: %s\n' "$g" >&2
      printf 'Known groups: %s\n' "$ALL_GROUPS" >&2
      exit 2
      ;;
  esac
done

# Is a group selected?
want() {
  case " $WANTED " in
    *" $1 "*) return 0 ;;
  esac
  return 1
}

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

report() {
  # $1 tool, $2 non-empty to also look inside the virtualenv
  if have "$1" || { [ -n "$2" ] && [ -x "$VENV/bin/$1" ]; }; then
    note "$1: present"
  else
    note "$1: MISSING"
    record_missing "$1"
  fi
}

want apt && for tool in shellcheck bats; do report "$tool" ''; done
want shfmt && report shfmt ''
want gitleaks && report gitleaks ''
want node && report markdownlint-cli2 ''
want python && for tool in ruff pytest yamllint ansible-lint coverage; do
  report "$tool" venv
done
if want lora; then
  report docker ''
  if [ -x "$LORA_VENV/bin/meshtastic" ]; then
    note 'meshtastic: present'
  else
    note 'meshtastic: MISSING'
    record_missing meshtastic
  fi
fi

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
  note 'against nothing else. Install the equivalents by hand; what is'
  note 'needed is listed below.'
  note ''
  note "Debian packages:  $APT_PACKAGES"
  note "Python packages:  from tools/requirements-dev.txt"
  note "shfmt:            v$SHFMT_VERSION from https://github.com/mvdan/sh"
  note "gitleaks:         v$GITLEAKS_VERSION from https://github.com/gitleaks/gitleaks"
  note "Node:             markdownlint-cli2@$MDLINT_VERSION, globally with npm"
  exit 1
fi

# --- Debian packages --------------------------------------------------------

if want apt; then
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
fi

# --- Python virtualenv ------------------------------------------------------

if want python; then
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
fi

# --- shfmt ------------------------------------------------------------------

if want shfmt; then
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
fi

# --- gitleaks ---------------------------------------------------------------

if want gitleaks; then
  step "gitleaks v$GITLEAKS_VERSION"
  if have gitleaks && [ "$(gitleaks version 2>/dev/null)" = "$GITLEAKS_VERSION" ]; then
    note 'Already at the pinned version.'
  else
    arch=$(uname -m)
    case "$arch" in
      x86_64 | amd64)
        gl_arch=x64
        gl_sha=$GITLEAKS_SHA256_amd64
        ;;
      aarch64 | arm64)
        gl_arch=arm64
        gl_sha=$GITLEAKS_SHA256_arm64
        ;;
      *)
        printf 'ERROR: no pinned gitleaks digest for architecture %s.\n' "$arch" >&2
        printf 'Add one to this script rather than skipping verification.\n' >&2
        exit 1
        ;;
    esac

    gl_url="https://github.com/gitleaks/gitleaks/releases/download/v$GITLEAKS_VERSION/gitleaks_${GITLEAKS_VERSION}_linux_$gl_arch.tar.gz"
    gl_tmp=$(mktemp -d)
    curl -fsSL -o "$gl_tmp/gitleaks.tar.gz" "$gl_url"
    gl_actual=$(sha256sum "$gl_tmp/gitleaks.tar.gz" | cut -d' ' -f1)
    if [ "$gl_actual" != "$gl_sha" ]; then
      rm -rf "$gl_tmp"
      printf 'ERROR: gitleaks checksum mismatch.\n' >&2
      printf '  expected %s\n' "$gl_sha" >&2
      printf '  actual   %s\n' "$gl_actual" >&2
      exit 1
    fi
    tar -xzf "$gl_tmp/gitleaks.tar.gz" -C "$gl_tmp" gitleaks
    as_root install -m 0755 "$gl_tmp/gitleaks" /usr/local/bin/gitleaks
    rm -rf "$gl_tmp"
    note 'Installed and checksum verified.'
  fi
fi

# --- markdownlint-cli2 ------------------------------------------------------

if want node; then
  step "markdownlint-cli2 v$MDLINT_VERSION"
  if have markdownlint-cli2 &&
    markdownlint-cli2 --version 2>/dev/null | grep -q "v$MDLINT_VERSION"; then
    note 'Already at the pinned version.'
  else
    # Only escalate when the global prefix is not already writable. sudo resets
    # PATH, so on a machine where a version manager put node somewhere of its
    # own -- a CI runner using actions/setup-node, for one -- "sudo npm" would
    # install into a different node than the one that is going to run it.
    npm_prefix=$(npm config get prefix 2>/dev/null || printf '')
    if [ -n "$npm_prefix" ] && [ -w "$npm_prefix/lib" ]; then
      npm install -g --silent "markdownlint-cli2@$MDLINT_VERSION"
    else
      as_root npm install -g --silent "markdownlint-cli2@$MDLINT_VERSION"
    fi
    note 'Installed.'
  fi
fi

# --- the LoRa bench ---------------------------------------------------------

if want lora; then
  step 'LoRa plane bench'
  if ! have docker; then
    note 'Installing docker.io for the two-node simulation.'
    as_root env DEBIAN_FRONTEND=noninteractive apt-get install -y -qq docker.io
  fi

  if [ ! -f "$LORA_LOCK" ]; then
    printf 'ERROR: %s is missing.\n' "$LORA_LOCK" >&2
    exit 1
  fi
  if [ ! -x "$LORA_VENV/bin/python" ]; then
    python3 -m venv "$LORA_VENV"
  fi
  "$LORA_VENV/bin/pip" install --quiet --upgrade pip
  "$LORA_VENV/bin/pip" install --quiet --requirement "$LORA_LOCK"
  note "Client installed from tools/requirements-lora.txt into .venv-lora."

  # Pull by digest now rather than on first use, so that a bench with no
  # network later still has the daemon, and so that a wrong digest fails here
  # instead of halfway through a probe.
  if have docker && docker info >/dev/null 2>&1; then
    docker pull --quiet "$MESHTASTICD_IMAGE" >/dev/null &&
      note 'meshtasticd image pulled by digest.'
  else
    note 'docker is installed but its daemon is not answering; image not'
    note 'pulled. Start it, then run this again with --only lora.'
  fi

  note ''
  note 'To talk to a physical device: .venv-lora/bin/meshtastic --port /dev/ttyACM0 --info'
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
