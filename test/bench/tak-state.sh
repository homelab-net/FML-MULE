#!/bin/sh
# Reproduce the TBR-TAK-01 findings that a decision now rests on.
#
# Usage: sudo test/bench/tak-state.sh
#
# WHAT THIS IS FOR. docs/evidence/TBR-TAK-01/ holds five artifacts taken from a
# running OpenTAKServer, and until this script existed none of them could be
# reproduced by anyone else. FML-ADR-034 makes PostgreSQL conditional on this
# state study, and the different-node restore is the measurement that condition
# now rests on. A decision resting on an unreproducible measurement rests on
# somebody's word; FML-ADR-061 had that problem this morning and
# test/bench/keyed-mesh.sh fixed it.
#
# WHAT IT ASSERTS, and it is deliberately not everything the artifacts record:
#
#   1. OpenTAKServer is three processes. With only the `opentakserver` entry
#      point running, the CoT streaming port is absent. Starting `eud_handler`
#      brings it up. Upstream's Dockerfile runs the first only.
#   2. A different-node restore restores every row and authenticates nobody.
#      The origin's default administrator logs in; after a database-only
#      restore onto a host with an empty data folder, the same credential
#      fails, and the replacement reports healthy throughout.
#
# The second is the one FML-ADR-034 depends on.
#
# WHAT IT DOES NOT DO. It runs no client, so it does not reproduce the queue
# findings or the CoT path; those need PyTAK and are recorded in
# docs/evidence/TBR-TAK-01/ rather than scripted here. It builds no image from
# upstream's Dockerfile and makes no claim about one.
#
# WHY IT IS NOT IN CI. It needs a container runtime and pulls three images. A
# hosted runner has no Podman and this would be minutes of network per run. It
# runs on a development machine. See docs/dev-machine.md.
#
# NO CREDENTIAL IS COMMITTED. The database password is generated per run. The
# administrator credential it tests is upstream's own default, published in
# OpenTAKServer's source, and is the finding rather than a secret.

set -eu

PG_DIGEST="docker.io/library/postgres@sha256:485935f94cc7165afa896978809c37b592dc07f0a37d2c8f645f12412d0212c8"
MQ_DIGEST="docker.io/library/rabbitmq@sha256:9cfb7e92ae7d296aec4d1ae799e431209f7ed57d55f9c929d95667d0ccf1c920"
PY_DIGEST="docker.io/library/python@sha256:de8ba566572ebcb35cbd10e03f5f351cad00a0d0d50a11e084f1a0fd24a0c41a"
OTS_VERSION=1.7.13
IMAGE=localhost/fml-bench-tak:$OTS_VERSION

WORK=$(mktemp -d /tmp/fml-tak.XXXXXX)
PGPASS=$(head -c 12 /dev/urandom | od -An -tx1 | tr -d ' \n')

fail() {
  printf 'FAIL: %s\n' "$1" >&2
  exit 1
}
info() { printf '  %s\n' "$1"; }

cleanup() {
  for c in fmltak-ots fmltak-eud fmltak-pg fmltak-mq; do
    podman rm -f "$c" >/dev/null 2>&1 || true
  done
  rm -rf "$WORK"
}
trap cleanup EXIT INT TERM

[ "$(id -u)" -eq 0 ] || fail 'must run as root in this environment.'
command -v podman >/dev/null 2>&1 ||
  fail 'podman is not installed. FML-ADR-029 selects it. apt-get install podman'

# --- build, to this program's rules rather than upstream's --------------------
#
# Upstream's Dockerfile is unpinned at three layers: FROM python:3.13 by tag,
# an unpinned apt install, and `pip install git+https://...` from master with no
# ref. FML-ADR-029 requires images by immutable digest, so the base is pinned and
# the application comes from a pinned release.
printf 'Building the image\n'
cat >"$WORK/Containerfile" <<CONTAINERFILE
FROM $PY_DIGEST
RUN python -m venv /app/venv
ENV PATH="/app/venv/bin:\$PATH"
RUN pip install --no-cache-dir "opentakserver==$OTS_VERSION"
ENV OTS_DATA_FOLDER=/data
ENTRYPOINT ["opentakserver"]
CONTAINERFILE
podman build --network=host -t "$IMAGE" "$WORK" >/dev/null 2>&1 ||
  fail 'image build failed. Network is needed to reach PyPI.'
info "built $IMAGE"

start_backing() {
  podman run -d --network host --name fmltak-pg \
    -e POSTGRES_USER=ots -e "POSTGRES_PASSWORD=$PGPASS" -e POSTGRES_DB=ots \
    "$PG_DIGEST" >/dev/null
  podman run -d --network host --name fmltak-mq "$MQ_DIGEST" >/dev/null
  deadline=$(($(date +%s) + 120))
  while [ "$(date +%s)" -lt "$deadline" ]; do
    if podman exec fmltak-pg pg_isready -U ots >/dev/null 2>&1; then return 0; fi
    sleep 3
  done
  fail 'postgres did not become ready within 120s.'
}

start_ots() {
  # $1 data folder on the host
  podman run -d --network host --name fmltak-ots -v "$1":/data:Z \
    -e OTS_DATA_FOLDER=/data \
    -e "SQLALCHEMY_DATABASE_URI=postgresql+psycopg://ots:$PGPASS@127.0.0.1/ots" \
    -e OTS_RABBITMQ_USERNAME=guest -e OTS_RABBITMQ_PASSWORD=guest \
    "$IMAGE" >/dev/null
  # Waited for rather than slept through: first start runs the whole alembic
  # migration chain, which is not a fixed interval.
  deadline=$(($(date +%s) + 240))
  while [ "$(date +%s)" -lt "$deadline" ]; do
    if curl -fsS --max-time 5 http://127.0.0.1:8081/api/health >/dev/null 2>&1; then return 0; fi
    sleep 5
  done
  fail 'OpenTAKServer did not answer /api/health within 240s.'
}

login() {
  curl -sS --max-time 15 -X POST http://127.0.0.1:8081/api/login \
    -H 'Content-Type: application/json' \
    -d '{"username":"administrator","password":"password"}' 2>/dev/null
}

printf 'Starting the origin node\n'
mkdir -p "$WORK/origin"
start_backing
start_ots "$WORK/origin"
info 'origin is serving'

# --- assertion 1: three processes, one entry point ---------------------------

printf 'Assertion 1: the CoT listener is a separate process\n'
if ss -lnt 2>/dev/null | grep -q ':8088'; then
  fail 'port 8088 is listening with only the opentakserver entry point running. Upstream would then serve clients from one process and this finding is wrong.'
fi
info 'with only `opentakserver` running, 8088 is absent'

podman run -d --network host --name fmltak-eud -v "$WORK/origin":/data:Z \
  -e OTS_DATA_FOLDER=/data \
  -e "SQLALCHEMY_DATABASE_URI=postgresql+psycopg://ots:$PGPASS@127.0.0.1/ots" \
  -e OTS_RABBITMQ_USERNAME=guest -e OTS_RABBITMQ_PASSWORD=guest \
  --entrypoint eud_handler "$IMAGE" >/dev/null
deadline=$(($(date +%s) + 90))
up=0
while [ "$(date +%s)" -lt "$deadline" ]; do
  if ss -lnt 2>/dev/null | grep -q ':8088'; then
    up=1
    break
  fi
  sleep 3
done
[ "$up" -eq 1 ] || fail 'eud_handler did not bring up 8088 within 90s.'
info 'starting `eud_handler` brings up 8088'

# --- assertion 2: the different-node restore ---------------------------------

printf 'Assertion 2: a database-only restore authenticates nobody\n'
case "$(login)" in
  *'"code":200'*) info 'origin: the default administrator logs in' ;;
  *) fail 'the default administrator did not log in on the origin, so the restore comparison would be meaningless.' ;;
esac

podman exec fmltak-pg pg_dump -U ots -d ots >"$WORK/db.sql" 2>/dev/null
[ -s "$WORK/db.sql" ] || fail 'pg_dump produced nothing.'
info "database-only backup taken: $(wc -l <"$WORK/db.sql") lines"

podman rm -f fmltak-ots fmltak-eud >/dev/null 2>&1
podman exec fmltak-pg psql -U ots -d postgres -c 'drop database ots' >/dev/null 2>&1
podman exec fmltak-pg psql -U ots -d postgres -c 'create database ots' >/dev/null 2>&1
podman exec -i fmltak-pg psql -U ots -d ots <"$WORK/db.sql" >/dev/null 2>&1
users=$(podman exec fmltak-pg psql -U ots -d ots -tAc 'select count(*) from "user"' 2>/dev/null | tr -d ' ')
[ "$users" = "1" ] || fail "the restore did not bring back the user row; got '$users'. Nothing below would mean anything."
info 'restored onto a fresh database: the user row is back'

# The replacement gets an EMPTY data folder, which is what a host rebuilt from a
# database backup has.
mkdir -p "$WORK/replacement"
start_ots "$WORK/replacement"

case "$(login)" in
  *'"code":200'*)
    fail 'the restored credential worked. The salt would then be inside the database and FML-ADR-034 needs no filesystem-shaped mechanism, which contradicts the recorded finding.'
    ;;
esac
info 'replacement: the same credential is refused'

curl -fsS --max-time 10 http://127.0.0.1:8081/api/health >/dev/null 2>&1 ||
  fail 'the replacement stopped answering /api/health, which changes the finding: it would be visibly broken rather than silently so.'
info 'replacement: /api/health still answers 200 while authenticating nobody'

if [ -f "$WORK/origin/ca/ca.pem" ] && [ -f "$WORK/replacement/ca/ca.pem" ]; then
  a=$(openssl x509 -in "$WORK/origin/ca/ca.pem" -noout -fingerprint -sha256 2>/dev/null)
  b=$(openssl x509 -in "$WORK/replacement/ca/ca.pem" -noout -fingerprint -sha256 2>/dev/null)
  [ "$a" != "$b" ] ||
    fail 'the replacement inherited the origin certificate authority, which contradicts the recorded finding.'
  info 'replacement: a DIFFERENT certificate authority was silently generated'
fi

printf '\n'
printf 'PASS. Three processes, and a database-only restore that restores every\n'
printf 'row and authenticates nobody while reporting healthy. TBR-TAK-01,\n'
printf 'FML-ADR-034.\n'
printf 'Tier: SIMULATED. Containers on a development machine, no MULE hardware.\n'
