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
TOOLS_PACKAGES="$IMAGE_DIR/manifest/tools-tree-packages.list"
TARGET_LOCK="$IMAGE_DIR/manifest/target-lock.json"
TOOLS_LOCK="$IMAGE_DIR/manifest/tools-tree-lock.json"
OUTPUT_DIR=${FML_IMAGE_OUTPUT_DIR:-"$ROOT/out/image"}
PACKAGE_CACHE=${FML_IMAGE_PACKAGE_CACHE:-"$IMAGE_DIR/mkosi.pkgcache"}
OUTPUT_BASENAME=$(sed -n 's/^  image_id: //p' "$INPUTS")
[ -n "$OUTPUT_BASENAME" ] || {
  printf '%s\n' 'Image output identity is missing from build-inputs.yml.' >&2
  exit 1
}
OUTPUT_NAME="$OUTPUT_BASENAME.raw"

python3 "$ROOT/tools/validate-image.py" "$ROOT"
[ "$mode" = --check ] && exit 0

if [ "$mode" = --offline ]; then
  python3 "$ROOT/tools/validate-package-cache.py" \
    "$PACKAGE_CACHE" "$TARGET_LOCK" "$TOOLS_LOCK"
fi

active_packages=$(sed 's/[[:space:]]*#.*$//' "$PACKAGES" | sed '/^[[:space:]]*$/d')
[ -n "$active_packages" ] || {
  printf '%s\n' 'The exact target package closure is empty.' >&2
  exit 1
}
active_tools_packages=$(
  sed 's/[[:space:]]*#.*$//' "$TOOLS_PACKAGES" | sed '/^[[:space:]]*$/d'
)
[ -n "$active_tools_packages" ] || {
  printf '%s\n' 'The exact tools-tree package closure is empty.' >&2
  exit 1
}

[ "$(id -u)" -eq 0 ] || {
  printf '%s\n' 'Image builds require root-capable Linux image facilities.' >&2
  exit 1
}
mkosi_bin=$("$ROOT/tools/resolve-mkosi-builder.sh" "$INPUTS")

mkdir -p "$OUTPUT_DIR" "$PACKAGE_CACHE"
set -- "$mkosi_bin" \
  --directory "$IMAGE_DIR" \
  --output-directory "$OUTPUT_DIR" \
  --output "$OUTPUT_BASENAME" \
  --package-cache-dir "$PACKAGE_CACHE" \
  --force

if [ "$mode" = --offline ]; then
  # mkosi v25.3 manual: CacheOnly=always instructs the package manager not to
  # contact the network. The default is auto and does not prove offline input.
  set -- "$@" --cache-only=always
  command -v unshare >/dev/null 2>&1 || {
    printf '%s\n' 'unshare is required to prove external-network isolation.' >&2
    exit 1
  }
else
  # The first controlled build is the only mode permitted to populate cache.
  set -- "$@" --cache-only=never
fi

printf '%s\n' "$active_packages" | while IFS= read -r package; do
  printf '%s\n' "$package"
done >"$OUTPUT_DIR/requested-packages.txt"
printf '%s\n' "$active_tools_packages" >"$OUTPUT_DIR/requested-tools-packages.txt"

while IFS= read -r package; do
  set -- "$@" --package "$package"
done <<EOF
$active_packages
EOF

while IFS= read -r package; do
  set -- "$@" --tools-tree-package "$package"
done <<EOF
$active_tools_packages
EOF

if [ "$mode" = --offline ]; then
  # FML-ADR-081 requires the cache-only build to have no external network
  # namespace, independently of the package-manager cache setting above.
  set -- unshare --net -- "$@"
fi

"$@" build

python3 "$ROOT/tools/validate-package-cache.py" \
  "$PACKAGE_CACHE" "$TARGET_LOCK" "$TOOLS_LOCK"

artifact="$OUTPUT_DIR/$OUTPUT_NAME"
[ -f "$artifact" ] || {
  printf 'mkosi did not produce the expected artifact: %s\n' "$artifact" >&2
  exit 1
}
(cd "$OUTPUT_DIR" && sha256sum "$OUTPUT_NAME" >"$OUTPUT_NAME.sha256")
for evidence in \
  "$OUTPUT_DIR/$OUTPUT_BASENAME.sbom.cdx.json" \
  "$OUTPUT_DIR/$OUTPUT_BASENAME.license-exceptions.json"; do
  [ -s "$evidence" ] || {
    printf 'mkosi did not produce required provenance: %s\n' "$evidence" >&2
    exit 1
  }
done
printf 'Built %s\n' "$artifact"
