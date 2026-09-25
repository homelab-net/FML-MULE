#!/bin/sh
# Require a distro Podman whose health checks can be scheduled by systemd.
#
# A prior CI fallback used mgoltzsche/podman-static. That bundle is built
# without systemd support: it accepted --sdnotify=healthy/HealthCmd but never
# scheduled the checks. Prefer the runner's distro Podman when it already
# satisfies the contract. Only install packages when that contract is missing.
set -eu

if [ "$(id -u)" -ne 0 ]; then
  echo "ensure-podman.sh must run as root" >&2
  exit 1
fi

quadlet_path() {
  for candidate in \
    /usr/libexec/podman/quadlet \
    /usr/lib/podman/quadlet \
    /usr/local/libexec/podman/quadlet; do
    if [ -x "$candidate" ]; then
      printf '%s\n' "$candidate"
      return 0
    fi
  done
  return 1
}

runtime_ok() {
  command -v podman >/dev/null 2>&1 || return 1
  major=$(podman version -f '{{.Client.Version}}' 2>/dev/null | cut -d. -f1)
  [ "${major:-0}" -ge 5 ] || return 1
  quadlet_path >/dev/null 2>&1 || return 1
  [ -x /usr/lib/systemd/user-generators/podman-user-generator ] || return 1
  [ -x /usr/lib/podman/netavark ] || return 1
  [ -x /usr/lib/podman/aardvark-dns ] || return 1
}

if ! runtime_ok; then
  # Hosted runners can carry vendor package sources unrelated to this test.
  # Restrict apt to Ubuntu's own deb822 source when available so a broken
  # third-party repository cannot make the topology proof fail before Podman.
  if [ -f /etc/apt/sources.list.d/ubuntu.sources ]; then
    apt_opts='-o Dir::Etc::sourcelist=/etc/apt/sources.list.d/ubuntu.sources -o Dir::Etc::sourceparts=-'
  else
    apt_opts=''
  fi
  # shellcheck disable=SC2086
  apt-get $apt_opts update -qq
  # shellcheck disable=SC2086
  apt-get $apt_opts install -y -qq podman uidmap slirp4netns dbus-user-session ca-certificates netavark aardvark-dns
fi

if ! runtime_ok; then
  echo "Podman 5 or newer is required with systemd health scheduling, Netavark/Aardvark DNS, and the user Quadlet generator" >&2
  podman version >&2 || true
  exit 1
fi

quadlet=$(quadlet_path)
podman version
printf 'quadlet=%s\n' "$quadlet"
