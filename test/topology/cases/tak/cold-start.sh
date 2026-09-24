#!/bin/sh
# Start the TAK capability from the Quadlet texts and persist one CoT.
#
# Podman is rootless, as the field pattern requires. The account is a
# throwaway on this runner. The catalog has not selected a field user.
# systemd starts opentakserver.target. The script does not launch the
# five containers itself.
#
# Members Requires= the mesh gate. The interface name is still TBD, so
# this runner installs a user unit of that same name and holds it until
# the dependency edge has been observed. That stub is not a mesh.
#
# A later stop and start of the target must leave the row in place.
# That is not Restart=, and it is not a different-node restore.
set -eu

here=$(CDPATH='' cd -- "$(dirname "$0")" && pwd)
if [ "$(id -u)" -ne 0 ]; then
  if ! command -v sudo >/dev/null 2>&1; then
    echo "cold-start provisions a rootless account and sudo is absent" >&2
    exit 1
  fi
  exec sudo sh "$here/$(basename "$0")"
fi

root=$(CDPATH='' cd -- "$here/../../../.." && pwd)
cd "$root"
sh "$root/test/topology/ensure-podman.sh"

account=fml
uid_name=fml-topology-pli
home=/home/$account
runtime=""

as_user() {
  # This runner's sudo keeps XDG_CONFIG_HOME on the invoking home, and
  # Podman refuses a cwd this account cannot enter. env -i and a home
  # the account owns are what make the commands its own.
  (
    cd "$home" || exit
    sudo -u "$account" env -i \
      PATH="/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin" \
      HOME="$home" \
      USER="$account" \
      LOGNAME="$account" \
      XDG_RUNTIME_DIR="$runtime" \
      DBUS_SESSION_BUS_ADDRESS="unix:path=${runtime}/bus" \
      XDG_CONFIG_HOME="$home/.config" \
      XDG_DATA_HOME="$home/.local/share" \
      "$@"
  )
}

dump() {
  as_user systemctl --user --no-pager --full status \
    opentakserver.target \
    postgresql.service \
    rabbitmq.service \
    opentakserver.service \
    eud-handler.service \
    cot-parser.service \
    "systemd-networkd-wait-online@TBD.service" || true
  as_user journalctl --user -n 160 --no-pager || true
  as_user podman ps -a || true
  for name in postgresql rabbitmq opentakserver eud-handler cot-parser; do
    as_user podman logs "$name" || true
  done
}

cleanup() {
  if id "$account" >/dev/null 2>&1 && [ -n "$runtime" ] && [ -S "$runtime/bus" ]; then
    as_user systemctl --user stop opentakserver.target >/dev/null 2>&1 || true
    as_user podman rm -f health-scheduler-probe postgresql rabbitmq opentakserver eud-handler cot-parser \
      >/dev/null 2>&1 || true
    as_user podman network prune -f >/dev/null 2>&1 || true
  fi
  rm -rf /var/lib/fml /run/fml
  rm -f "$home/mesh-gate-open"
}
trap cleanup EXIT

if ! id "$account" >/dev/null 2>&1; then
  useradd --create-home --user-group --shell /bin/bash "$account"
fi
grep -q "^${account}:" /etc/subuid || printf '%s:200000:65536\n' "$account" >>/etc/subuid
grep -q "^${account}:" /etc/subgid || printf '%s:200000:65536\n' "$account" >>/etc/subgid
if ! loginctl enable-linger "$account"; then
  mkdir -p /var/lib/systemd/linger
  touch "/var/lib/systemd/linger/$account"
fi
# This image pins XDG_* to the invoking account in /etc/environment.
# pam_env copies that into every user manager, and Quadlet follows it
# instead of this account's home. %h in a system unit is root's home,
# so a user@.service drop-in cannot name this account.
if [ -f /etc/environment ]; then
  grep -v -E '^(XDG_CONFIG_HOME|XDG_RUNTIME_DIR|XDG_DATA_HOME|XDG_CACHE_HOME)=' \
    /etc/environment >/etc/environment.fml || true
  mv /etc/environment.fml /etc/environment
fi
account_uid=$(id -u "$account")
systemctl start "user@${account_uid}.service"
runtime="/run/user/${account_uid}"
i=0
while [ ! -S "$runtime/bus" ]; do
  i=$((i + 1))
  if [ "$i" -gt 30 ]; then
    echo "user manager for ${account} did not open a bus" >&2
    exit 1
  fi
  sleep 1
done

rm -rf /var/lib/fml /run/fml "$home/mesh-gate-open"
mkdir -p /var/lib/fml/ots /var/lib/fml/postgresql /run/fml \
  "$home/.config/containers/systemd" \
  "$home/.config/systemd/user"
# The throwaway account has no delegated cgroup. cgroupfs keeps the
# rootless runtime from depending on a login session. This is not a
# field containers.conf.
cat >"$home/.config/containers/containers.conf" <<'EOF'
[engine]
cgroup_manager = "cgroupfs"
events_logger = "file"
EOF
chown -R "$account:$account" /var/lib/fml /run/fml "$home/.config"

db_pass=$(python3 -c 'import secrets; print(secrets.token_hex(16))')
umask 077
cat >/run/fml/postgresql.env <<EOF
POSTGRES_USER=fmlots
POSTGRES_PASSWORD=${db_pass}
POSTGRES_DB=ots
EOF
cat >/run/fml/rabbitmq.env <<EOF
RABBITMQ_DEFAULT_USER=fmlots
RABBITMQ_DEFAULT_PASS=${db_pass}
EOF
cat >/run/fml/ots.env <<EOF
SQLALCHEMY_DATABASE_URI=postgresql+psycopg://fmlots:${db_pass}@postgresql/ots
OTS_RABBITMQ_USERNAME=fmlots
OTS_RABBITMQ_PASSWORD=${db_pass}
EOF
chown -R "$account:$account" /run/fml
chmod 600 /run/fml/*.env

# The checkout is not traversable by this account. Build from a copy it owns.
src="$home/src"
rm -rf "$src"
mkdir -p "$src/tak" "$src/client"
cp "$root/services/tak/Containerfile" "$root/services/tak/listen_ready.py" \
  "$src/tak/"
cp "$root/test/topology/cases/tak/Clientfile" \
  "$root/test/topology/cases/tak/send_cot.py" "$src/client/"
chown -R "$account:$account" "$src"
as_user podman build -t fml-ots-topology:test -f "$src/tak/Containerfile" \
  "$src/tak"
as_user podman build -t fml-ots-client:test -f "$src/client/Clientfile" \
  "$src/client"
postgres_image=$(sed -n 's/^Image=//p' services/quadlets/postgresql.container.disabled)
rabbit_image=$(sed -n 's/^Image=//p' services/quadlets/rabbitmq.container.disabled)
as_user podman pull "$postgres_image"
as_user podman pull "$rabbit_image"

# A previous CI fallback used a Podman binary built without systemd support.
# It accepted health configuration but never scheduled the checks, leaving
# containers permanently in "starting". Prove the rootless health scheduler
# works before asking systemd to wait on Notify=healthy.
as_user podman rm -f health-scheduler-probe >/dev/null 2>&1 || true
as_user podman run -d --name health-scheduler-probe \
  --health-cmd=true \
  --health-interval=1s \
  --health-timeout=2s \
  --health-retries=5 \
  localhost/fml-ots-topology:test sleep 30 >/dev/null
health=""
i=0
while [ "$i" -lt 20 ]; do
  health=$(as_user podman inspect --format '{{.State.Health.Status}}' \
    health-scheduler-probe 2>/dev/null || true)
  if [ "$health" = "healthy" ]; then
    break
  fi
  i=$((i + 1))
  sleep 1
done
if [ "$health" != "healthy" ]; then
  echo "rootless Podman did not schedule health checks (state: ${health:-unknown})" >&2
  as_user podman inspect health-scheduler-probe >&2 || true
  exit 1
fi
as_user podman rm -f health-scheduler-probe >/dev/null

dest="$home/.config/containers/systemd"
for src in "$root"/services/quadlets/*.container.disabled \
  "$root"/services/quadlets/*.network.disabled; do
  [ -f "$src" ] || continue
  base=$(basename "$src" .disabled)
  case "$base" in
    example.container) continue ;;
  esac
  sed 's|^Image=TBD$|Image=localhost/fml-ots-topology:test|' "$src" >"$dest/$base"
done
cp "$root/services/quadlets/opentakserver.target.disabled" \
  "$home/.config/systemd/user/opentakserver.target"
cat >"$home/.config/systemd/user/systemd-networkd-wait-online@.service" <<'EOF'
[Unit]
Description=CI stand-in for the unresolved mesh interface gate
Documentation=file:///usr/share/doc/fml/tak

[Service]
Type=oneshot
RemainAfterExit=yes
TimeoutStartSec=240
ExecStart=/bin/sh -c 'i=0; while [ ! -f /home/fml/mesh-gate-open ]; do i=$((i+1)); if [ "$i" -gt 180 ]; then exit 1; fi; sleep 1; done'
EOF
chown -R "$account:$account" "$home/.config"
# This runner's home has a default ACL, so the copies are group
# writable. Quadlet ignores those files. Drop the group and other
# write bits or the generator installs nothing.
chmod -R go-w "$home/.config"

# User generators on this runner do not see this account's home, so
# they never read these files. Run the same generator with the
# account's environment and install what it writes. systemd starts
# those units. The script does not start the containers.
quadlet_out="$runtime/quadlet-out"
rm -rf "$quadlet_out"
mkdir -p "$quadlet_out"
chown "$account:$account" "$quadlet_out"
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
  echo "quadlet generator not found" >&2
  exit 1
fi
if ! as_user "$quadlet" -user "$quadlet_out"; then
  echo "quadlet did not accept the TAK units" >&2
  exit 1
fi
find "$quadlet_out" -type f -name '*.service' -exec cp {} "$home/.config/systemd/user/" \;
chown -R "$account:$account" "$home/.config/systemd/user"
chmod -R go-w "$home/.config/systemd/user"
as_user systemctl --user daemon-reload
for unit in ots-network.service postgresql.service rabbitmq.service \
  opentakserver.service eud-handler.service cot-parser.service \
  opentakserver.target systemd-networkd-wait-online@TBD.service; do
  if ! as_user systemctl --user cat "$unit" >/dev/null; then
    echo "generator did not install ${unit}" >&2
    ls -l /usr/lib/systemd/user-generators "$home/.config/containers/systemd" >&2 || true
    as_user journalctl --user -n 80 --no-pager >&2 || true
    as_user systemctl --user --no-pager --failed || true
    exit 1
  fi
done

set +e
as_user systemctl --user start opentakserver.target &
start_pid=$!
state=""
i=0
while [ "$i" -lt 40 ]; do
  state=$(as_user systemctl --user show -P ActiveState \
    systemd-networkd-wait-online@TBD.service || true)
  if [ "$state" = "activating" ]; then
    break
  fi
  i=$((i + 1))
  sleep 1
done
if [ "$state" != "activating" ]; then
  echo "mesh gate did not hold the start (state ${state})" >&2
  dump
  kill "$start_pid" >/dev/null 2>&1 || true
  wait "$start_pid" || true
  exit 1
fi
if as_user podman ps --format '{{.Names}}' | grep -q .; then
  echo "a container ran while the mesh gate was still activating" >&2
  dump
  kill "$start_pid" >/dev/null 2>&1 || true
  wait "$start_pid" || true
  exit 1
fi
touch "$home/mesh-gate-open"
chown "$account:$account" "$home/mesh-gate-open"
wait "$start_pid"
status=$?
set -e
if [ "$status" -ne 0 ]; then
  echo "opentakserver.target did not become active" >&2
  dump
  exit 1
fi

net=$(as_user podman inspect --format '{{range $name, $_ := .NetworkSettings.Networks}}{{$name}}{{end}}' eud-handler)
dns_enabled=$(as_user podman network inspect --format '{{.DNSEnabled}}' "$net")
if [ "$dns_enabled" != "true" ]; then
  echo "TAK internal network does not have container-name DNS enabled" >&2
  as_user podman network inspect "$net" >&2 || true
  dump
  exit 1
fi
if ! as_user podman run --rm --network "$net" \
  localhost/fml-ots-client:test \
  python -c 'import socket; print(socket.getaddrinfo("eud-handler", 8088))'; then
  echo "client on $net cannot resolve eud-handler" >&2
  as_user podman network inspect "$net" >&2 || true
  dump
  exit 1
fi
as_user podman run --rm --network "$net" --name cot-client \
  localhost/fml-ots-client:test python /send_cot.py

row_count() {
  as_user podman exec postgresql psql -U fmlots -d ots -tAc \
    "select count(*) from cot where uid = '${uid_name}'" 2>/dev/null || true
}

found=0
i=0
while [ "$i" -lt 45 ]; do
  count=$(row_count | tr -d '[:space:]')
  if [ "$count" = "1" ] || [ "${count:-0}" -gt 1 ]; then
    found=1
    break
  fi
  i=$((i + 1))
  sleep 2
done
if [ "$found" -ne 1 ]; then
  echo "cot row for ${uid_name} was not persisted" >&2
  dump
  exit 1
fi

as_user systemctl --user stop opentakserver.target
as_user systemctl --user start opentakserver.target
found=0
i=0
while [ "$i" -lt 45 ]; do
  count=$(row_count | tr -d '[:space:]')
  if [ "$count" = "1" ] || [ "${count:-0}" -gt 1 ]; then
    found=1
    break
  fi
  i=$((i + 1))
  sleep 2
done
if [ "$found" -ne 1 ]; then
  echo "cot row for ${uid_name} did not survive a target stop and start" >&2
  dump
  exit 1
fi
echo "tak cold-start persisted ${uid_name} and kept it across a stop"
