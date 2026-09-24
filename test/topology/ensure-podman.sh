#!/bin/sh
# Install a distro Podman whose health checks can be scheduled by systemd.
#
# PR173 previously fell back to mgoltzsche/podman-static on Ubuntu 24.04.
# That bundle is built without systemd support. It accepted
# --sdnotify=healthy/HealthCmd but never scheduled the health checks, so
# containers remained "starting" until systemd timed out. The topology jobs
# therefore run on Ubuntu 26.04 and use Ubuntu's systemd-enabled Podman 5.
set -eu

if [ "$(id -u)" -ne 0 ]; then
  echo "ensure-podman.sh must run as root" >&2
  exit 1
fi

apt-get update -qq
apt-get install -y -qq podman uidmap slirp4netns dbus-user-session ca-certificates

major=$(podman version -f '{{.Client.Version}}' | cut -d. -f1)
if [ "${major:-0}" -lt 5 ]; then
  echo "Podman 5 or newer is required for Quadlet Notify=healthy" >&2
  podman version >&2 || true
  exit 1
fi

quadlet=""
for candidate in \
  /usr/libexec/podman/quadlet \
  /usr/lib/podman/quadlet \
  /usr/local/libexec/podman/quadlet; do
  if [ -x "$candidate" ]; then
    quadlet=$candidate
    break
  fi
done
if [ -z "$quadlet" ]; then
  echo "Podman Quadlet generator is not installed" >&2
  exit 1
fi
if [ ! -x /usr/lib/systemd/user-generators/podman-user-generator ]; then
  echo "systemd-enabled Podman user generator is not installed" >&2
  exit 1
fi

podman version
printf 'quadlet=%s\n' "$quadlet"
