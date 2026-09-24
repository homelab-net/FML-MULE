#!/bin/sh
# Install a Podman that understands Notify=healthy.
#
# Apt is preferred. Quadlet gained Notify=healthy in Podman 5. A pinned
# static build is the fallback so a generator from Podman 4 cannot ignore
# the readiness key. The checksums are the GitHub release asset digests
# for mgoltzsche/podman-static v5.8.7.
set -eu

version_ok() {
  command -v podman >/dev/null 2>&1 || return 1
  major=$(podman version -f '{{.Client.Version}}' | cut -d. -f1)
  [ "$major" -ge 5 ]
}

if [ "$(id -u)" -ne 0 ]; then
  echo "ensure-podman.sh must run as root" >&2
  exit 1
fi

apt-get update -qq
apt-get install -y -qq podman uidmap slirp4netns dbus-user-session curl ca-certificates
if version_ok; then
  podman version
  exit 0
fi

case $(uname -m) in
  x86_64)
    asset=podman-linux-amd64.tar.gz
    sum=1957a6ec8f4848b748bded0d9c778a9c1735b9b0055506a0521947e934b2997f
    ;;
  aarch64)
    asset=podman-linux-arm64.tar.gz
    sum=89bbe9278238f85077e65c57a9a0ba50ed2d3fcaa6da141cee514ef8bb8b6df6
    ;;
  *)
    echo "no pinned Podman 5 build for $(uname -m)" >&2
    exit 1
    ;;
esac

url="https://github.com/mgoltzsche/podman-static/releases/download/v5.8.7/${asset}"
archive=$(mktemp)
workdir=$(mktemp -d)
cleanup() {
  rm -rf "$archive" "$workdir"
}
trap cleanup EXIT

curl -fsSL -o "$archive" "$url"
echo "$sum  $archive" | sha256sum -c -
tar -xzf "$archive" -C "$workdir"
src=$(find "$workdir" -mindepth 1 -maxdepth 1 -type d | head -n 1)
cp -a "$src/usr/." /usr/
hash -r
# Apt's crun rejects the OCI spec this Podman writes ("unknown version
# specified"). The static build ships a crun that accepts it, and the
# engine calls /usr/bin/crun ahead of /usr/local/bin/crun.
ln -sfn /usr/local/bin/crun /usr/bin/crun
# Ubuntu 24.04 denies a user namespace to a binary with no AppArmor
# profile. The pinned static build has none. Apt's podman would have
# shipped a profile and would not reach this branch. This is the
# runner, not a field sysctl.
if [ -w /proc/sys/kernel/apparmor_restrict_unprivileged_userns ]; then
  printf '0\n' >/proc/sys/kernel/apparmor_restrict_unprivileged_userns
fi
podman version
version_ok
