#!/bin/sh
# Ask the Podman Quadlet generator to accept the TAK units.
# Image=TBD is replaced only in this temporary copy. The committed units
# keep Image=TBD. This does not build or start a container.
#
# The generator does not echo the source name ots.network. A .network
# file becomes <name>-network.service, and the podman argument is the
# derived network name. Success is those generated names, plus --internal.
set -eu

root=$(CDPATH= cd -- "$(dirname "$0")/../.." && pwd)
work=$(mktemp -d)
dest="$work/units"

cleanup() {
  rm -rf "$work"
}
trap cleanup EXIT

mkdir -p "$dest"

base_image="docker.io/library/python@sha256:dbbe4ceb97851e2e5fa83798b239811f871cb743b259ba3563737349f6bcfaa0"
for src in "$root"/services/quadlets/*.container.disabled \
  "$root"/services/quadlets/*.network.disabled; do
  [ -f "$src" ] || continue
  base=$(basename "$src" .disabled)
  case "$base" in
    example.container) continue ;;
  esac
  sed "s|^Image=TBD$|Image=${base_image}|" "$src" >"$dest/$base"
done

quadlet=""
for candidate in \
  quadlet \
  /usr/local/libexec/podman/quadlet \
  /usr/libexec/podman/quadlet \
  /usr/lib/podman/quadlet \
  /usr/local/lib/systemd/system-generators/podman-system-generator \
  /usr/lib/systemd/system-generators/podman-system-generator; do
  if [ -x "$candidate" ] || command -v "$candidate" >/dev/null 2>&1; then
    quadlet=$candidate
    break
  fi
done
if [ -z "$quadlet" ]; then
  echo "podman quadlet generator not found" >&2
  exit 1
fi

# Absolute, and preferred over the user or system search path, so a
# runner HOME or XDG_CONFIG_HOME cannot hide this copy.
export QUADLET_UNIT_DIRS="$dest"
user_flag=""
if [ "$(id -u)" -ne 0 ]; then
  user_flag="-user"
fi

# shellcheck disable=SC2086
if ! output=$("$quadlet" $user_flag -dryrun 2>&1); then
  printf '%s\n' "$output" >&2
  exit 1
fi

missing=""
for needle in \
  ots-network.service \
  postgresql.service \
  rabbitmq.service \
  opentakserver.service \
  eud-handler.service \
  cot-parser.service \
  --internal \
  --sdnotify=healthy \
  --health-cmd \
  pg_isready; do
  if ! printf '%s\n' "$output" | grep -q -F -- "$needle"; then
    missing="$missing $needle"
  fi
done
if [ -n "$missing" ]; then
  printf '%s\n' "$output" >&2
  echo "quadlet dry-run output missing:$missing" >&2
  exit 1
fi
echo "quadlet dry-run accepted the TAK units"
