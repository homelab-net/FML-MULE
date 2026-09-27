#!/bin/bash
# SIMULATED bench: the FML-ADR-031 ingress reverse proxy reaches a browser
# service by name, and refuses a name it does not front.
#
#   ingress-name-routing.sh
#
# It runs the v0.0.1 map service (Martin, the digest pinned in
# services/catalog/catalog.yml) bound to loopback, puts HAProxy in front of it
# with the routing from os/config/haproxy.conf.template concretised, and asserts:
#   - a request whose Host matches the fronted name reaches Martin (HTTP 200);
#   - a request with any other Host gets 503 (no default backend -- fail closed).
#
# The 503 case is the regression guard: if the host ACL is dropped or made a
# catch-all, the wrong-Host request reaches Martin and this test fails. This is a
# software-bench exercise on x86; it says nothing about the EUD AP subnet
# (TBR-NET-05), TLS (deferred, GAP-09H), or target hardware. Run on a dev machine
# with podman; not in CI (a hosted runner has no such stack; docs/dev-machine.md).
set -eu

ROOT=$(cd "$(dirname "$0")/../.." && pwd)
WORK=$(mktemp -d)
MARTIN=fml-bench-ingress-martin
HAPROXY=fml-bench-ingress-haproxy
NAME=map.example.invalid
# HAProxy is not (yet) a catalog service, so its image is pinned here by digest
# rather than read from services/catalog/ -- immutable digests, never tags
# (CLAUDE.md conventions). haproxy:lts as resolved 2026-09-27.
HAPROXY_DIGEST="docker.io/library/haproxy@sha256:07bc3cbc8fb7276e991124c24277a7c5de59a1bf4626ae2f3a30f73d6712114f"

# shellcheck disable=SC2317  # invoked via the EXIT trap, not inline.
cleanup() {
  podman rm -f "$MARTIN" "$HAPROXY" >/dev/null 2>&1 || true
  rm -rf "$WORK"
}
trap cleanup EXIT

command -v podman >/dev/null 2>&1 || {
  printf 'SKIP: podman is not installed.\n' >&2
  exit 0
}

# The Martin image identity is the digest in the service catalog, not a literal
# here, so the bench and the deployment cannot drift apart.
martin_image=$(grep -oE 'ghcr.io/maplibre/martin@sha256:[0-9a-f]+' \
  "$ROOT/services/catalog/catalog.yml" | head -1)
[ -n "$martin_image" ] || {
  printf 'FAIL: could not read the Martin image digest from the catalog.\n' >&2
  exit 1
}

# A pair of free loopback ports (avoid whatever else the bench is running).
free_port() {
  python3 - <<'PY'
import socket
s = socket.socket()
s.bind(("127.0.0.1", 0))
print(s.getsockname()[1])
s.close()
PY
}
mport=$(free_port)
hport=$(free_port)

# A one-tile synthetic MBTiles. No real map data.
python3 - "$WORK/mission.mbtiles" <<'PY'
import base64
import sqlite3
import sys

png = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk"
    "+M8AAAMBAQDJ/pLvAAAAAElFTkSuQmCC"
)
con = sqlite3.connect(sys.argv[1])
cur = con.cursor()
cur.execute("CREATE TABLE metadata (name text, value text)")
cur.execute(
    "CREATE TABLE tiles "
    "(zoom_level integer, tile_column integer, tile_row integer, tile_data blob)"
)
for k, v in [
    ("name", "fml-synthetic"),
    ("format", "png"),
    ("minzoom", "0"),
    ("maxzoom", "0"),
    ("bounds", "-180,-85,180,85"),
]:
    cur.execute("INSERT INTO metadata VALUES (?, ?)", (k, v))
cur.execute("INSERT INTO tiles VALUES (0, 0, 0, ?)", (png,))
con.commit()
con.close()
PY

# HAProxy config: the template's routing, concretised to the bench ports.
cat >"$WORK/haproxy.cfg" <<EOF
global
    log stdout format raw local0
defaults
    mode http
    timeout connect 5s
    timeout client 30s
    timeout server 30s
frontend eud_ingress
    bind 127.0.0.1:$hport
    use_backend martin_backend if { hdr(host) -i $NAME }
backend martin_backend
    server martin 127.0.0.1:$mport
EOF

# Martin listens on 3000 inside the container; publish it onto a free loopback
# port (do NOT use --network host, which would ignore $mport and bind 3000).
podman run -d --name "$MARTIN" -p "127.0.0.1:$mport:3000" \
  -v "$WORK/mission.mbtiles":/data/mission.mbtiles:ro --read-only \
  "$martin_image" /data/mission.mbtiles >/dev/null

podman run -d --name "$HAPROXY" --network host \
  -v "$WORK/haproxy.cfg":/usr/local/etc/haproxy/haproxy.cfg:ro \
  "$HAPROXY_DIGEST" >/dev/null

# Wait for BOTH listeners: Martin's catalog, and HAProxy actually bound (any
# HTTP status, even 503, proves the frontend is up -- polling only Martin races
# ahead of HAProxy and the first assertion hits a closed port).
martin_up=0
haproxy_up=0
for _ in $(seq 1 30); do
  if [ "$martin_up" = 0 ] &&
    curl -fsS --max-time 2 "http://127.0.0.1:$mport/catalog" >/dev/null 2>&1; then
    martin_up=1
  fi
  if [ "$haproxy_up" = 0 ] &&
    curl -s --max-time 2 -o /dev/null "http://127.0.0.1:$hport/" >/dev/null 2>&1; then
    haproxy_up=1
  fi
  if [ "$martin_up" = 1 ] && [ "$haproxy_up" = 1 ]; then
    break
  fi
  sleep 1
done

# The assertion curls tolerate their own connection failure (|| true) so a dead
# listener surfaces as http_code 000 with a clear FAIL, not a bare set -e exit.
fail=0
match=$(curl -s --max-time 5 -o /dev/null -w '%{http_code}' \
  -H "Host: $NAME" "http://127.0.0.1:$hport/mission/0/0/0" || true)
if [ "$match" = "200" ]; then
  printf 'PASS: matching Host reaches Martin (%s)\n' "$match"
else
  printf 'FAIL: matching Host expected 200, got %s\n' "$match" >&2
  fail=1
fi

wrong=$(curl -s --max-time 5 -o /dev/null -w '%{http_code}' \
  -H "Host: not-fronted.invalid" "http://127.0.0.1:$hport/mission/0/0/0" || true)
if [ "$wrong" = "503" ]; then
  printf 'PASS: non-fronted Host is refused (%s)\n' "$wrong"
else
  printf 'FAIL: non-fronted Host expected 503, got %s\n' "$wrong" >&2
  fail=1
fi

exit "$fail"
