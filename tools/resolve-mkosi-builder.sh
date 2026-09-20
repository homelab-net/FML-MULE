#!/bin/sh
# Resolve and authenticate the package-owned FML-ADR-079 mkosi executable.
#
# Usage: tools/resolve-mkosi-builder.sh BUILD_INPUTS_YML

set -eu

[ $# -eq 1 ] || {
  printf 'Usage: %s BUILD_INPUTS_YML\n' "$0" >&2
  exit 2
}

INPUTS=$1
[ -f "$INPUTS" ] || {
  printf 'Image build inputs do not exist: %s\n' "$INPUTS" >&2
  exit 1
}
command -v dpkg-query >/dev/null 2>&1 || {
  printf '%s\n' 'dpkg-query is required to authenticate the Debian builder package.' >&2
  exit 1
}
command -v dpkg-deb >/dev/null 2>&1 || {
  printf '%s\n' 'dpkg-deb is required to authenticate the installed builder payload.' >&2
  exit 1
}

expected_version=$(sed -n 's/^  version: //p' "$INPUTS")
actual_version=$(dpkg-query -W -f='${Version}' mkosi 2>/dev/null || true)
[ "$actual_version" = "$expected_version" ] || {
  printf 'mkosi package version mismatch: expected %s, got %s\n' \
    "$expected_version" "${actual_version:-not-installed}" >&2
  exit 1
}

# Looking up mkosi on PATH independently would allow another installation to
# shadow the exact package whose version was checked. FML-ADR-079, GAP-09C.
mkosi_bin=$(dpkg-query -L mkosi 2>/dev/null | awk '/\/bin\/mkosi$/ { print }')
[ "$(printf '%s\n' "$mkosi_bin" | sed '/^$/d' | wc -l)" -eq 1 ] || {
  printf '%s\n' 'The mkosi package shall own exactly one bin/mkosi executable.' >&2
  exit 1
}
[ -x "$mkosi_bin" ] || {
  printf 'The package-owned mkosi executable is absent or not executable: %s\n' \
    "$mkosi_bin" >&2
  exit 1
}
case $(dpkg-query -S "$mkosi_bin" 2>/dev/null || true) in
  mkosi:*) ;;
  *)
    printf 'The selected executable is not owned by the mkosi package: %s\n' \
      "$mkosi_bin" >&2
    exit 1
    ;;
esac

expected_package_sha=$(sed -n 's/^  package_sha256: //p' "$INPUTS")
builder_deb=${FML_MKOSI_PACKAGE_DEB:-/var/cache/apt/archives/mkosi_${expected_version}_all.deb}
[ -f "$builder_deb" ] || {
  printf 'The authenticated mkosi package archive is required: %s\n' \
    "$builder_deb" >&2
  exit 1
}
actual_package_sha=$(sha256sum "$builder_deb" | awk '{ print $1 }')
[ "$actual_package_sha" = "$expected_package_sha" ] || {
  printf 'mkosi package SHA-256 mismatch: expected %s, got %s\n' \
    "$expected_package_sha" "$actual_package_sha" >&2
  exit 1
}

# Package ownership and version identify the dpkg record, but do not prove that
# its installed Python modules and resources still contain the bytes from the
# authenticated archive. Extract the verified archive and bind every packaged
# non-directory payload entry to the installed tree.
# FML-ADR-079, GAP-09C.
payload_dir=$(mktemp -d)
trap 'rm -rf "$payload_dir"' 0 HUP INT TERM
dpkg-deb -x "$builder_deb" "$payload_dir"
find "$payload_dir" ! -type d -print | while IFS= read -r packaged_path; do
  installed_path=/${packaged_path#"$payload_dir"/}
  if [ -L "$packaged_path" ]; then
    if [ ! -L "$installed_path" ] ||
      [ "$(readlink "$installed_path")" != "$(readlink "$packaged_path")" ]; then
      printf 'Installed mkosi symlink differs from the authenticated package: %s\n' \
        "$installed_path" >&2
      exit 1
    fi
  elif [ -f "$packaged_path" ]; then
    if [ ! -f "$installed_path" ] || [ -L "$installed_path" ]; then
      printf 'Installed mkosi payload is absent or has the wrong type: %s\n' \
        "$installed_path" >&2
      exit 1
    fi
    installed_sha=$(sha256sum "$installed_path" | awk '{ print $1 }')
    packaged_sha=$(sha256sum "$packaged_path" | awk '{ print $1 }')
    [ "$installed_sha" = "$packaged_sha" ] || {
      printf 'Installed mkosi payload differs from the authenticated package: %s\n' \
        "$installed_path" >&2
      exit 1
    }
  else
    printf 'Authenticated mkosi package contains an unsupported payload type: %s\n' \
      "$packaged_path" >&2
    exit 1
  fi
done

printf '%s\n' "$mkosi_bin"
