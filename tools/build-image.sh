#!/bin/sh
# Validate or build the FML-ADR-079 Debian development image.
#
# Usage: tools/build-image.sh --check | --populate-cache | --offline
#                             [--profile pi4b-arm64]
#
# Without --profile this builds the x86-64 image. --profile pi4b-arm64 builds
# the FML-ADR-088 Raspberry Pi 4B profile on an x86-64 host, which needs the
# qemu-user aarch64 binfmt handler registered (Debian qemu-user-binfmt).

set -eu

usage() {
  printf 'Usage: %s --check | --populate-cache | --offline [--profile NAME]\n' \
    "$0" >&2
  exit 2
}

[ $# -eq 1 ] || [ $# -eq 3 ] || usage
mode=$1
case "$mode" in
  --check | --populate-cache | --offline) ;;
  *) usage ;;
esac
profile=
if [ $# -eq 3 ]; then
  [ "$2" = --profile ] || usage
  profile=$3
  case "$profile" in
    pi4b-arm64) ;;
    *)
      printf 'Unknown image profile: %s\n' "$profile" >&2
      exit 2
      ;;
  esac
fi

ROOT=$(cd "$(dirname "$0")/.." && pwd)
IMAGE_DIR="$ROOT/os/image"
INPUTS="$IMAGE_DIR/build-inputs.yml"
PACKAGES="$IMAGE_DIR/manifest/packages.list"
TOOLS_PACKAGES="$IMAGE_DIR/manifest/tools-tree-packages.list"
TARGET_LOCK="$IMAGE_DIR/manifest/target-lock.json"
TOOLS_LOCK="$IMAGE_DIR/manifest/tools-tree-lock.json"
OUTPUT_DIR=${FML_IMAGE_OUTPUT_DIR:-"$ROOT/out/image"}
PACKAGE_CACHE=${FML_IMAGE_PACKAGE_CACHE:-"$IMAGE_DIR/mkosi.pkgcache"}
IDENTITY_INPUTS=$INPUTS
if [ -n "$profile" ]; then
  # The profile keeps the base builder, snapshot and tools tree; its target
  # closure, cache, output and identity are its own, so the x86-64 cache
  # validator never sees arm64 packages and the two images never collide.
  PACKAGES="$IMAGE_DIR/manifest/$profile/packages.list"
  TARGET_LOCK="$IMAGE_DIR/manifest/$profile/target-lock.json"
  OUTPUT_DIR=${FML_IMAGE_OUTPUT_DIR:-"$ROOT/out/image-$profile"}
  PACKAGE_CACHE=${FML_IMAGE_PACKAGE_CACHE:-"$IMAGE_DIR/mkosi.pkgcache.$profile"}
  IDENTITY_INPUTS="$IMAGE_DIR/mkosi.profiles/$profile/build-inputs.yml"
fi
DEBSBOM_VERSION=$(sed -n 's/^  sbom_package_version: //p' "$INPUTS")
[ -n "$DEBSBOM_VERSION" ] || {
  printf '%s\n' 'The selected debsbom version is missing from build-inputs.yml.' >&2
  exit 1
}
OUTPUT_BASENAME=$(sed -n 's/^  image_id: //p' "$IDENTITY_INPUTS")
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
if [ -n "$profile" ]; then
  # Linux binfmt-misc: a registered handler appears as an entry under the
  # binfmt_misc mount. Without it the image's arm64 maintainer scripts cannot
  # run on this host and the build fails part-way.
  binfmt=${FML_BINFMT_MISC:-/proc/sys/fs/binfmt_misc}
  [ -e "$binfmt/qemu-aarch64" ] || {
    printf '%s\n' "No qemu-aarch64 binfmt handler under $binfmt." \
      'Install Debian qemu-user-binfmt (it registers via systemd-binfmt).' >&2
    exit 1
  }
  # FML-ADR-088: "The host's qemu-user version shall be recorded with each
  # build's provenance, since it is outside the tools-tree lock."
  dpkg-query -W -f '${Package} ${Version}\n' qemu-user qemu-user-binfmt \
    >"$OUTPUT_DIR/host-emulator.txt" || {
    printf '%s\n' 'Cannot record the host qemu-user version.' >&2
    exit 1
  }
fi
# mkosi v25.3 manual: "If not configured explicitly, the current working
# directory is mounted to /work/src." Mount the repository so finalize can
# run the governed built-root validator through SRCDIR.
set -- "$mkosi_bin" \
  --directory "$IMAGE_DIR" \
  --build-sources "$ROOT" \
  --output-directory "$OUTPUT_DIR" \
  --output "$OUTPUT_BASENAME" \
  --package-cache-dir "$PACKAGE_CACHE" \
  --force
if [ -n "$profile" ]; then
  # mkosi v25.3 manual: "Select the given profiles. A profile is a
  # configuration file or directory in the mkosi.profiles/ directory."
  set -- "$@" --profile "$profile"
fi

if [ "$mode" = --offline ]; then
  # mkosi v25.3 manual: CacheOnly=always instructs the package manager not to
  # contact the network. The default is auto and does not prove offline input.
  set -- "$@" --cache-only=always
  # mkosi v25.3 manual: package specifications "may include ... file paths".
  # Reset the configured debsbom name so the loop below can select its already
  # authenticated cached .deb without backports repository metadata.
  set -- "$@" --tools-tree-package=
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
  if [ "$mode" = --offline ] && [ "$package" = "debsbom=$DEBSBOM_VERSION" ]; then
    package="/var/cache/apt/archives/debsbom_${DEBSBOM_VERSION}_all.deb"
  fi
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
