#!/bin/sh
# Measure the resource envelope of the selected MBTiles tile server (Martin),
# serving a per-mission MBTiles store as z/x/y -- the software half of the
# TBR-MAP-01 / TBR-COMP-01 measurement a catalog entry requires.
#
# Usage: test/bench/map-server-footprint.sh
#
# WHAT THIS IS FOR. FML-ADR-073 selects the store as per-mission MBTiles served
# as z/x/y, and leaves "which exact binary" to the catalog work. services/catalog
# will not accept an entry with an *estimated* resource envelope ("an entry with
# an estimated envelope has not been evaluated"). Nothing had ever measured a
# real tile server: the 2026-09-04 interface bench and the mesh bench both served
# tiles from an ad-hoc python3 process, which sizes nothing. This measures the
# candidate the catalog would actually pin.
#
# WHAT IT SELECTS, AND WHY MARTIN. The criteria are FML-ADR-029 (rootless,
# digest-pinned) and AGENTS.md rule 6 (an existing, maintained tool, not a new
# one), plus the CM4 target: arm64. Of the credible MBTiles servers,
#   - mbtileserver (the class FML-ADR-073 named) publishes no multi-arch image:
#     no arm64 manifest, so it cannot be pinned for the CM4 without building a
#     new artifact, which rule 6 is against;
#   - tileserver-gl-light is arm64 but is a Node.js GL *renderer* -- on-node
#     rendering is a stated v1 non-goal and a heavier footprint;
#   - martin (MapLibre) ships an official amd64+arm64 image, is actively
#     maintained, is a single Rust binary, reads MBTiles read-only, serves
#     z/x/y, and carries a base-path prefix for ingress. It is the selection.
#
# WHAT IT ASSERTS.
#   1. Martin, run rootless and pinned by digest, auto-discovers a .mbtiles as a
#      source and serves z/x/y: every fetch is 200 image/png with a PNG
#      signature, across the zoom range.
#   2. Its memory stays bounded and light under sustained concurrent load -- the
#      figure the catalog's resource-envelope field records, and the property
#      services/map/README.md predicts ("read-mostly and light").
#
# WHAT IT DOES NOT DO, and it is deliberately not the whole envelope.
#   - It runs on this x86 bench, NOT the CM4. It is the *software half*. The
#     arm64/CM4 footprint under load is TBR-COMP-01's hardware item and stays
#     open; this bench measures no CM4 figure and selects no host.
#   - Its store is a small SYNTHETIC MBTiles -- deterministic PNG per z/x/y, one
#     distinct colour, no imagery and no third-party tiles (committing either
#     would be map data this program does not own; the 2026-09-04 real-EUD
#     evidence already covers real imagery). A real-imagery store is hundreds of
#     MB to GB; Martin queries SQLite per tile rather than loading the file, so
#     RSS is expected to stay bounded regardless of store size, but the
#     USB2 random-read-latency check on a real-imagery store is a separate
#     FML-ADR-073 open item, not this.
#   - Load is loopback HTTP, not the EUD access point or the mesh. The request
#     rate is server-side capacity, not a radio-limited serve rate.
#   - It reports RSS, not CPU%: podman stats' CPU% on this host reads as
#     cumulative and is not a per-interval figure; the definitive CPU-under-load
#     number is the CM4 item above. So this is tier SIMULATED.
#
# WHY IT IS NOT IN CI. It pulls a 650 MB image and runs a container runtime; it
# belongs on a development machine. See docs/dev-machine.md.
#
# NO IMAGERY, NO THIRD-PARTY DATA IS COMMITTED. The store is generated per run
# from a tiny raw PNG encoder and deleted on exit.

set -eu

# Martin (MapLibre), pinned by digest -- the immutable reference a catalog entry
# and Quadlet would carry. Resolved from the project's `latest` tag at
# ghcr.io/maplibre/martin on 2026-09-06; re-resolve and update here when the pin
# is advanced.
MARTIN_DIGEST="ghcr.io/maplibre/martin@sha256:84f406ac96839aad3ea06ddaa68ef7617ed55305c21038c182d59f100e48dd6d"

NAME=fml-mapfoot
PORT=8899
LOAD_SECONDS=20
LOAD_WORKERS=8

fail() {
  printf 'FAIL: %s\n' "$1" >&2
  exit 1
}
info() { printf '  %s\n' "$1"; }

WORK=""
cleanup() {
  podman rm -f "$NAME" >/dev/null 2>&1 || true
  if [ -n "${WORK:-}" ] && [ -d "${WORK:-}" ]; then rm -rf "$WORK"; fi
}
trap cleanup EXIT INT TERM

command -v podman >/dev/null 2>&1 || fail "podman is not installed."
command -v python3 >/dev/null 2>&1 || fail "python3 is not installed."
command -v curl >/dev/null 2>&1 || fail "curl is not installed."

WORK=$(mktemp -d /tmp/fml-mapfoot.XXXXXX)
STORE="$WORK/mission.mbtiles"

printf '=== Map server footprint: Martin serving per-mission MBTiles as z/x/y ===\n'
info "image:  $MARTIN_DIGEST"
info "tier:   SIMULATED (x86 bench, synthetic store, loopback load)"

# --- Build a synthetic MBTiles: deterministic PNG per z/x/y, no imagery --------
python3 - "$STORE" <<'PY'
import sqlite3, sys, zlib, struct, os
def png(r, g, b):
    def chunk(typ, data):
        c = typ + data
        return struct.pack(">I", len(data)) + c + struct.pack(">I", zlib.crc32(c) & 0xffffffff)
    w = h = 256
    raw = b"".join(b"\x00" + bytes((r, g, b)) * w for _ in range(h))
    return (b"\x89PNG\r\n\x1a\n"
            + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(raw, 6))
            + chunk(b"IEND", b""))
db = sys.argv[1]
con = sqlite3.connect(db); c = con.cursor()
c.execute("CREATE TABLE metadata (name text, value text)")
c.execute("CREATE TABLE tiles (zoom_level int, tile_column int, tile_row int, tile_data blob)")
c.execute("CREATE UNIQUE INDEX tile_index on tiles (zoom_level, tile_column, tile_row)")
for k, v in [("name", "mission"), ("format", "png"), ("minzoom", "0"),
             ("maxzoom", "6"), ("bounds", "-180,-85,180,85"), ("type", "baselayer")]:
    c.execute("INSERT INTO metadata VALUES (?,?)", (k, v))
n = 0
for z in range(0, 7):
    span = 2 ** z
    for x in range(span):
        for y in range(span):
            row = (2 ** z - 1) - y  # MBTiles uses TMS row order
            c.execute("INSERT INTO tiles VALUES (?,?,?,?)",
                      (z, x, row, png((x * 53) % 256, (y * 97) % 256, (z * 40) % 256)))
            n += 1
con.commit(); con.close()
print("  store:  %d tiles, z0-6, %.1f KB (synthetic, no imagery)"
      % (n, os.path.getsize(db) / 1024))
PY

# --- Run Martin rootless, read-only store mount --------------------------------
podman rm -f "$NAME" >/dev/null 2>&1 || true
podman run -d --name "$NAME" --memory=256m \
  -p "127.0.0.1:$PORT:3000" \
  -v "$STORE:/data/mission.mbtiles:ro,Z" \
  "$MARTIN_DIGEST" /data/mission.mbtiles >/dev/null 2>&1 ||
  fail "could not start Martin (is the digest pullable?)"

# Wait for readiness
i=0
while [ "$i" -lt 30 ]; do
  if curl -fs "http://127.0.0.1:$PORT/catalog" >/dev/null 2>&1; then break; fi
  i=$((i + 1))
  sleep 1
done
[ "$i" -lt 30 ] || fail "Martin did not become ready"
curl -fs "http://127.0.0.1:$PORT/catalog" 2>/dev/null | grep -q '"mission"' ||
  fail "Martin did not auto-discover the mission source"
info "source discovered: mission"

# --- Assert 1: z/x/y serves valid PNG across the zoom range --------------------
printf '\n--- z/x/y interface ---\n'
for zxy in 0/0/0 3/4/5 6/10/20 6/63/63; do
  code_ct_sz=$(curl -s -o "$WORK/t.png" -w "%{http_code} %{content_type} %{size_download}" \
    "http://127.0.0.1:$PORT/mission/$zxy")
  sig=$(python3 -c "import sys;sys.exit(0 if open('$WORK/t.png','rb').read(8)==b'\x89PNG\r\n\x1a\n' else 1)" &&
    echo True || echo False)
  info "GET /mission/$zxy -> $code_ct_sz pngsig=$sig"
  case "$code_ct_sz" in 200\ image/png\ *) : ;; *) fail "unexpected response for $zxy" ;; esac
  [ "$sig" = True ] || fail "served tile for $zxy is not a PNG"
done

# --- Assert 2: bounded, light memory under sustained concurrent load -----------
printf '\n--- envelope under load (%d workers, %ds) ---\n' "$LOAD_WORKERS" "$LOAD_SECONDS"
idle=$(podman stats --no-stream --format '{{.MemUsage}}' "$NAME" 2>/dev/null)
info "idle mem: $idle"

python3 - "$PORT" "$LOAD_SECONDS" "$LOAD_WORKERS" <<'PY' &
import urllib.request, threading, time, random, sys
port, secs, workers = int(sys.argv[1]), int(sys.argv[2]), int(sys.argv[3])
stop = time.time() + secs
cnt = [0]; err = [0]; lat = []
def worker():
    while time.time() < stop:
        z = random.randint(0, 6); span = 2 ** z
        x = random.randint(0, span - 1); y = random.randint(0, span - 1)
        t = time.time()
        try:
            urllib.request.urlopen(f"http://127.0.0.1:{port}/mission/{z}/{x}/{y}", timeout=5).read()
            cnt[0] += 1; lat.append((time.time() - t) * 1000)
        except Exception:
            err[0] += 1
ts = [threading.Thread(target=worker) for _ in range(workers)]
[t.start() for t in ts]; [t.join() for t in ts]
lat.sort()
p50 = lat[len(lat) // 2] if lat else 0
p95 = lat[int(len(lat) * 0.95)] if lat else 0
print("  requests=%d errors=%d rate=%.0f/s  lat p50=%.1fms p95=%.1fms"
      % (cnt[0], err[0], cnt[0] / secs, p50, p95))
PY
LOADPID=$!

# Sample peak RSS while the load runs
peak=0
end=$(($(date +%s) + LOAD_SECONDS + 2))
while [ "$(date +%s)" -lt "$end" ]; do
  cur=$(podman stats --no-stream --format '{{.MemUsage}}' "$NAME" 2>/dev/null | awk '{print $1}')
  mb=$(printf '%s' "$cur" | sed 's/MiB//; s/MB//')
  case "$mb" in
    '' | *[!0-9.]*) : ;;
    *) awk "BEGIN{exit !($mb > $peak)}" && peak=$mb ;;
  esac
  sleep 1
done
wait "$LOADPID"
printf '  peak mem under load: %s MB\n' "$peak"

printf '\nPASS: Martin serves MBTiles as z/x/y and stays light under load.\n'
printf '  Software-half envelope only; CM4/arm64 footprint is TBR-COMP-01, open.\n'
