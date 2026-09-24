#!/bin/sh
# Ask the Podman Quadlet generator to accept the TAK units.
# Image=TBD is replaced only in this temporary copy. The committed units
# keep Image=TBD. This does not build or start a container.
set -eu

root=$(CDPATH= cd -- "$(dirname "$0")/../.." && pwd)
work=$(mktemp -d)
copied=""

cleanup() {
  # shellcheck disable=SC2086
  if [ -n "$copied" ]; then
    rm -f $copied
  fi
  rm -rf "$work"
}
trap cleanup EXIT

if [ "$(id -u)" -eq 0 ]; then
  dest=/usr/share/containers/systemd
  user_flag=""
else
  dest="$work/home/.config/containers/systemd"
  export HOME="$work/home"
  export XDG_RUNTIME_DIR="$work/run"
  mkdir -p "$XDG_RUNTIME_DIR"
  user_flag="--user"
fi
mkdir -p "$dest"

base_image="docker.io/library/python@sha256:dbbe4ceb97851e2e5fa83798b239811f871cb743b259ba3563737349f6bcfaa0"
for src in "$root"/services/quadlets/*.container.disabled "$root"/services/quadlets/*.network.disabled; do
  [ -f "$src" ] || continue
  base=$(basename "$src" .disabled)
  case "$base" in
    example.container) continue ;;
  esac
  sed "s|^Image=TBD$|Image=${base_image}|" "$src" >"$dest/$base"
  copied="$copied $dest/$base"
done

quadlet=""
for candidate in \
  quadlet \
  /usr/libexec/podman/quadlet \
  /usr/lib/podman/quadlet \
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

# shellcheck disable=SC2086
if ! output=$("$quadlet" $user_flag --dryrun 2>&1); then
  printf '%s\n' "$output" >&2
  exit 1
fi
printf '%s\n' "$output" | grep -q 'ots.network'
echo "quadlet dry-run accepted the TAK units"
