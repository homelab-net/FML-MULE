#!/bin/sh
# Run the TAK software topology on an internal network and persist one CoT.
# This is not a mesh proof, a restart proof, or a different-node restore.
# The runner here is rootful. The unit files stay rootless in intent.
set -eu

root=$(CDPATH= cd -- "$(dirname "$0")/../../.." && pwd)
cd "$root"

if ! command -v podman >/dev/null 2>&1; then
  echo "podman is required" >&2
  exit 1
fi

net=fml-tak-topology
volume=fml-ots-data
db_user=fmlots
db_name=ots
uid=fml-topology-pli
db_pass=$(python3 -c 'import secrets; print(secrets.token_hex(16))')
postgres="docker.io/library/postgres@sha256:485935f94cc7165afa896978809c37b592dc07f0a37d2c8f645f12412d0212c8"
rabbit="docker.io/library/rabbitmq@sha256:9cfb7e92ae7d296aec4d1ae799e431209f7ed57d55f9c929d95667d0ccf1c920"

cleanup() {
  podman rm -f postgresql rabbitmq opentakserver eud-handler cot-parser cot-client \
    >/dev/null 2>&1 || true
  podman volume rm "$volume" >/dev/null 2>&1 || true
  podman network rm "$net" >/dev/null 2>&1 || true
}
trap cleanup EXIT
cleanup

podman network create --internal "$net" >/dev/null
podman volume create "$volume" >/dev/null
podman build -t fml-ots-topology -f services/tak/Containerfile services/tak
podman build -t fml-ots-client -f test/topology/cases/tak/Clientfile \
  test/topology/cases/tak

podman run -d --name postgresql --network "$net" \
  -e POSTGRES_USER="$db_user" \
  -e POSTGRES_PASSWORD="$db_pass" \
  -e POSTGRES_DB="$db_name" \
  "$postgres" >/dev/null
podman run -d --name rabbitmq --network "$net" \
  -e RABBITMQ_DEFAULT_USER="$db_user" \
  -e RABBITMQ_DEFAULT_PASS="$db_pass" \
  "$rabbit" >/dev/null

ready=0
i=0
while [ "$i" -lt 60 ]; do
  if podman exec postgresql pg_isready -U "$db_user" -d "$db_name" >/dev/null 2>&1 \
    && podman exec rabbitmq rabbitmq-diagnostics -q ping >/dev/null 2>&1; then
    ready=1
    break
  fi
  i=$((i + 1))
  sleep 2
done
if [ "$ready" -ne 1 ]; then
  echo "database or broker did not become ready" >&2
  podman logs postgresql >&2 || true
  podman logs rabbitmq >&2 || true
  exit 1
fi

uri="postgresql+psycopg://${db_user}:${db_pass}@postgresql/${db_name}"
run_ots() {
  name=$1
  cmd=$2
  podman run -d --name "$name" --network "$net" \
    -e OTS_DATA_FOLDER=/var/lib/opentakserver \
    -e OTS_LISTENER_ADDRESS=0.0.0.0 \
    -e OTS_STREAMING_INTERFACE=0.0.0.0 \
    -e OTS_RABBITMQ_SERVER_ADDRESS=rabbitmq \
    -e OTS_RABBITMQ_USERNAME="$db_user" \
    -e OTS_RABBITMQ_PASSWORD="$db_pass" \
    -e OTS_MEDIAMTX_ENABLE=false \
    -e SQLALCHEMY_DATABASE_URI="$uri" \
    -v "$volume":/var/lib/opentakserver \
    fml-ots-topology "$cmd" >/dev/null
}

run_ots opentakserver opentakserver

ready=0
i=0
while [ "$i" -lt 90 ]; do
  if podman exec opentakserver python -c \
    'import socket; socket.create_connection(("127.0.0.1", 8081), 2)' \
    >/dev/null 2>&1; then
    ready=1
    break
  fi
  i=$((i + 1))
  sleep 2
done
if [ "$ready" -ne 1 ]; then
  echo "API did not accept a connection inside its own netns" >&2
  podman logs opentakserver >&2 || true
  exit 1
fi

# Migrations run in the API process. That is startup order for this test,
# not a Requires= from the workers onto the API.
run_ots eud-handler eud_handler
run_ots cot-parser cot_parser

ready=0
i=0
while [ "$i" -lt 60 ]; do
  if podman exec eud-handler python -c \
    'import socket; socket.create_connection(("127.0.0.1", 8088), 2)' \
    >/dev/null 2>&1; then
    ready=1
    break
  fi
  i=$((i + 1))
  sleep 2
done
if [ "$ready" -ne 1 ]; then
  echo "listener did not bind inside its own netns" >&2
  podman logs eud-handler >&2 || true
  podman logs cot-parser >&2 || true
  exit 1
fi

podman run --rm --name cot-client --network "$net" \
  fml-ots-client python /send_cot.py

found=0
i=0
while [ "$i" -lt 45 ]; do
  count=$(podman exec postgresql psql -U "$db_user" -d "$db_name" -tAc \
    "select count(*) from cot where uid = '${uid}'" 2>/dev/null || true)
  count=$(printf '%s' "$count" | tr -d '[:space:]')
  if [ "$count" = "1" ] || [ "$count" -gt 1 ] 2>/dev/null; then
    found=1
    break
  fi
  i=$((i + 1))
  sleep 2
done
if [ "$found" -ne 1 ]; then
  echo "cot row for ${uid} was not persisted" >&2
  podman logs eud-handler >&2 || true
  podman logs cot-parser >&2 || true
  podman logs opentakserver >&2 || true
  exit 1
fi
echo "tak topology persisted ${uid}"
