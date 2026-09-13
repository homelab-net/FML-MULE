#!/bin/sh
# Validate or build the FML-ADR-079 Debian development image.
#
# Usage: tools/build-image.sh --check | --populate-cache | --offline

set -eu

usage() {
  printf 'Usage: %s --check | --populate-cache | --offline\n' "$0" >&2
  exit 2
}

[ $# -eq 1 ] || usage
mode=$1
case "$mode" in
  --check | --populate-cache | --offline) ;;
  *) usage ;;
esac

ROOT=$(cd "$(dirname "$0")/.." && pwd)
IMAGE_DIR="$ROOT/os/image"
INPUTS="$IMAGE_DIR/build-inputs.yml"
PACKAGES="$IMAGE_DIR/manifest/packages.list"
OUTPUT_DIR="$ROOT/out/image"
PACKAGE_CACHE="$IMAGE_DIR/mkosi.pkgcache"
OUTPUT_BASENAME=$(sed -n 's/^  image_id: //p' "$INPUTS")
[ -n "$OUTPUT_BASENAME" ] || {
  printf '%s\n' 'Image output identity is missing from build-inputs.yml.' >&2
  exit 1
}
OUTPUT_NAME="$OUTPUT_BASENAME.raw"

python3 "$ROOT/tools/validate-image.py" "$ROOT"
[ "$mode" = --check ] && exit 0

active_packages=$(sed 's/[[:space:]]*#.*$//' "$PACKAGES" | sed '/^[[:space:]]*$/d')
[ -n "$active_packages" ] || {
  printf '%s\n' 'GAP-09C package manifest is empty; no image can be built.' >&2
  exit 1
}

[ "$(id -u)" -eq 0 ] || {
  printf '%s\n' 'Image builds require root-capable Linux image facilities.' >&2
  exit 1
}
command -v mkosi >/dev/null 2>&1 || {
  printf '%s\n' 'mkosi is not installed.' >&2
  exit 1
}
command -v dpkg-query >/dev/null 2>&1 || {
  printf '%s\n' 'dpkg-query is required to authenticate the Debian builder package.' >&2
  exit 1
}

expected_version=$(sed -n 's/^  version: //p' "$INPUTS")
actual_version=$(dpkg-query -W -f='${Version}' mkosi 2>/dev/null || true)
[ "$actual_version" = "$expected_version" ] || {
  printf 'mkosi package version mismatch: expected %s, got %s\n' \
    "$expected_version" "${actual_version:-not-installed}" >&2
  exit 1
}

mkdir -p "$OUTPUT_DIR" "$PACKAGE_CACHE"
set -- mkosi \
  --directory "$IMAGE_DIR" \
  --output-directory "$OUTPUT_DIR" \
  --output "$OUTPUT_BASENAME" \
  --package-cache-dir "$PACKAGE_CACHE" \
  --force

if [ "$mode" = --offline ]; then
  # mkosi v25.3 manual: CacheOnly=always instructs the package manager not to
  # contact the network. The default is auto and does not prove offline input.
  set -- "$@" --cache-only=always
else
  # The first controlled build is the only mode permitted to populate cache.
  set -- "$@" --cache-only=never
fi

printf '%s\n' "$active_packages" | while IFS= read -r package; do
  printf '%s\n' "$package"
done >"$OUTPUT_DIR/requested-packages.txt"

while IFS= read -r package; do
  set -- "$@" --package "$package"
done <<EOF
$active_packages
EOF

"$@" build

artifact="$OUTPUT_DIR/$OUTPUT_NAME"
[ -f "$artifact" ] || {
  printf 'mkosi did not produce the expected artifact: %s\n' "$artifact" >&2
  exit 1
}
sha256sum "$artifact" >"$artifact.sha256"
printf 'Built %s\n' "$artifact"
