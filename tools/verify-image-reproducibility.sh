#!/bin/sh
# Execute the FML-ADR-081 three-build and QEMU acceptance sequence.
#
# Usage: tools/verify-image-reproducibility.sh

set -eu

[ $# -eq 0 ] || {
  printf 'Usage: %s\n' "$0" >&2
  exit 2
}

ROOT=$(cd "$(dirname "$0")/.." && pwd)
IMAGE_DIR="$ROOT/os/image"
INPUTS="$IMAGE_DIR/build-inputs.yml"
OUTPUT_NAME=mule-development.raw
mkdir -p "$ROOT/out"
EVIDENCE_DIR=$(mktemp -d "$ROOT/out/gap09c.XXXXXX")

[ "$(id -u)" -eq 0 ] || {
  printf '%s\n' 'Image reproducibility verification requires root.' >&2
  exit 1
}
command -v timeout >/dev/null 2>&1 || {
  printf '%s\n' 'timeout is required for the bounded QEMU boot.' >&2
  exit 1
}
mkosi_bin=$("$ROOT/tools/resolve-mkosi-builder.sh" "$INPUTS")

run_build() {
  label=$1
  mode=$2
  output_dir=$3
  package_cache=$4
  log="$EVIDENCE_DIR/$label.log"
  [ ! -e "$output_dir" ] || {
    printf 'Clean build output already exists: %s\n' "$output_dir" >&2
    exit 1
  }
  if [ "$mode" = --populate-cache ] && [ -e "$package_cache" ]; then
    printf 'Clean networked build cache already exists: %s\n' "$package_cache" >&2
    exit 1
  fi
  if FML_IMAGE_OUTPUT_DIR="$output_dir" \
    FML_IMAGE_PACKAGE_CACHE="$package_cache" \
    "$ROOT/tools/build-image.sh" "$mode" >"$log" 2>&1; then
    sed -n '1,160p' "$log"
  else
    status=$?
    sed -n '1,240p' "$log" >&2
    printf '%s build failed with status %s. Evidence: %s\n' \
      "$label" "$status" "$log" >&2
    exit "$status"
  fi
  for artifact in \
    "$OUTPUT_NAME" \
    "$OUTPUT_NAME.sha256" \
    "mule-development.sbom.cdx.json" \
    "mule-development.license-exceptions.json"; do
    [ -s "$output_dir/$artifact" ] || {
      printf 'Required %s output is absent after %s.\n' "$artifact" "$label" >&2
      exit 1
    }
    cp --reflink=auto --sparse=always \
      "$output_dir/$artifact" "$EVIDENCE_DIR/$label-$artifact"
  done
}

networked_1_output="$EVIDENCE_DIR/build-networked-1"
networked_1_cache="$EVIDENCE_DIR/cache-networked-1"
networked_2_output="$EVIDENCE_DIR/build-networked-2"
networked_2_cache="$EVIDENCE_DIR/cache-networked-2"
isolated_output="$EVIDENCE_DIR/build-isolated-cache"

run_build networked-1 --populate-cache "$networked_1_output" "$networked_1_cache"
run_build networked-2 --populate-cache "$networked_2_output" "$networked_2_cache"
run_build isolated-cache --offline "$isolated_output" "$networked_1_cache"

first=$(sha256sum "$EVIDENCE_DIR/networked-1-$OUTPUT_NAME" | awk '{print $1}')
second=$(sha256sum "$EVIDENCE_DIR/networked-2-$OUTPUT_NAME" | awk '{print $1}')
offline=$(sha256sum "$EVIDENCE_DIR/isolated-cache-$OUTPUT_NAME" | awk '{print $1}')
{
  printf 'networked-1 %s\n' "$first"
  printf 'networked-2 %s\n' "$second"
  printf 'isolated-cache %s\n' "$offline"
} >"$EVIDENCE_DIR/raw-image-sha256.txt"

if [ "$first" != "$second" ] || [ "$first" != "$offline" ]; then
  printf '%s\n' 'Raw image identities differ; retained artifacts require diagnosis.' >&2
  printf 'Evidence: %s\n' "$EVIDENCE_DIR" >&2
  exit 1
fi

boot_log="$EVIDENCE_DIR/qemu-no-network.log"
set +e
# mkosi v25.3 manual: native console mode connects the VM console directly to
# standard input/output. Debian 13 lacks the newer systemd-pty-forward helper
# needed by mkosi's read-only mode, so /dev/null enforces the same no-input
# acceptance boundary without adding an unavailable host binary.
timeout 180 "$mkosi_bin" \
  --directory "$IMAGE_DIR" \
  --output-directory "$isolated_output" \
  --output mule-development \
  --runtime-network=none \
  --console=native \
  vm </dev/null >"$boot_log" 2>&1
boot_status=$?
set -e
case "$boot_status" in
  0 | 124) ;;
  *)
    sed -n '1,240p' "$boot_log" >&2
    printf 'QEMU boot failed with status %s. Evidence: %s\n' \
      "$boot_status" "$boot_log" >&2
    exit "$boot_status"
    ;;
esac
grep -F 'Reached target multi-user.target' "$boot_log" >/dev/null || {
  sed -n '1,240p' "$boot_log" >&2
  printf '%s\n' 'QEMU did not report the selected systemd target.' >&2
  exit 1
}

printf 'Three identical raw images and offline QEMU boot: SIMULATED.\n'
printf 'Evidence: %s\n' "$EVIDENCE_DIR"
