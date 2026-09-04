#!/usr/bin/env python3
"""Bench demonstration of the offline map tile interface (TBR-MAP-01).

Proves the interface ``services/map/README.md`` commits to: an ``MBTiles`` store
(SQLite, the leading candidate offline container) read by a server that exposes
a ``z/x/y`` tile endpoint an EUD or browser fetches from.

This is a ``SIMULATED`` demonstration on an x86_64 bench. It is NOT CM4 footprint
evidence and NOT an EUD render. It does not select the production single-binary
server; the stdlib server here is a stand-in that exercises the same ``z/x/y``
contract. Tiles are procedurally generated solid-colour placeholders, not map
imagery: nothing real, no location, no licensed data.

Run it with no arguments; it builds the store, serves it on loopback, checks a
handful of ``z/x/y`` fetches and one out-of-range miss, prints ``PASS`` or
``FAIL`` and exits non-zero on failure. The ``.mbtiles`` it writes is a build
product and is regenerated deterministically, so it is not committed.
"""

import http.server
import os
import socketserver
import sqlite3
import struct
import sys
import threading
import urllib.error
import urllib.request
import zlib

OUT = os.path.dirname(os.path.abspath(__file__))
MBTILES = os.path.join(OUT, "bench-placeholder.mbtiles")
PORT = 8811


def png_solid(r: int, g: int, b: int, size: int = 256) -> bytes:
    """Return a minimal valid solid-colour truecolour PNG, no dependencies."""

    def chunk(typ: bytes, data: bytes) -> bytes:
        body = typ + data
        crc = zlib.crc32(body) & 0xFFFFFFFF
        return struct.pack(">I", len(data)) + body + struct.pack(">I", crc)

    sig = b"\x89PNG\r\n\x1a\n"
    ihdr = struct.pack(">IIBBBBB", size, size, 8, 2, 0, 0, 0)
    row = b"\x00" + bytes([r, g, b]) * size
    idat = zlib.compress(row * size, 9)
    return sig + chunk(b"IHDR", ihdr) + chunk(b"IDAT", idat) + chunk(b"IEND", b"")


def build_mbtiles() -> int:
    """Build an MBTiles 1.3 store of placeholder tiles; return the tile count."""
    if os.path.exists(MBTILES):
        os.remove(MBTILES)
    con = sqlite3.connect(MBTILES)
    cur = con.cursor()
    cur.execute("CREATE TABLE metadata (name text, value text)")
    cur.execute(
        "CREATE TABLE tiles (zoom_level integer, tile_column integer, "
        "tile_row integer, tile_data blob)"
    )
    cur.execute(
        "CREATE UNIQUE INDEX tile_index ON tiles (zoom_level, tile_column, tile_row)"
    )
    metadata = [
        ("name", "FML-MULE bench placeholder"),
        ("format", "png"),
        ("type", "baselayer"),
        ("version", "1.0"),
        ("minzoom", "0"),
        ("maxzoom", "2"),
        ("description", "Procedurally generated placeholder tiles. Not map data."),
    ]
    cur.executemany("INSERT INTO metadata VALUES (?,?)", metadata)

    count = 0
    for z in range(3):  # zoom 0..2
        span = 2**z
        for x in range(span):
            for y in range(span):  # XYZ row
                r = (40 + z * 60) % 256
                g = (x * 90 + 40) % 256
                b = (y * 90 + 40) % 256
                tms_y = span - 1 - y  # XYZ -> TMS row
                cur.execute(
                    "INSERT INTO tiles VALUES (?,?,?,?)",
                    (z, x, tms_y, png_solid(r, g, b)),
                )
                count += 1
    con.commit()
    con.close()
    return count


class TileHandler(http.server.BaseHTTPRequestHandler):
    """Serve ``/tiles/{z}/{x}/{y}.png`` (XYZ) from the MBTiles store."""

    def log_message(self, *args: object) -> None:
        """Silence the default per-request logging."""

    def do_GET(self) -> None:
        """Answer an XYZ tile request, flipping the row to the store's TMS."""
        parts = self.path.strip("/").split("/")
        try:
            if len(parts) != 4 or parts[0] != "tiles":
                raise ValueError
            z = int(parts[1])
            x = int(parts[2])
            y = int(parts[3].split(".")[0])
        except ValueError:
            self.send_error(404)
            return
        span = 2**z
        tms_y = span - 1 - y
        con = sqlite3.connect(MBTILES)
        row = con.execute(
            "SELECT tile_data FROM tiles WHERE zoom_level=? AND "
            "tile_column=? AND tile_row=?",
            (z, x, tms_y),
        ).fetchone()
        con.close()
        if not row:
            self.send_error(404)
            return
        self.send_response(200)
        self.send_header("Content-Type", "image/png")
        self.send_header("Content-Length", str(len(row[0])))
        self.end_headers()
        self.wfile.write(row[0])


class ReusableServer(socketserver.TCPServer):
    """TCPServer that sets SO_REUSEADDR so a re-run does not hit TIME_WAIT."""

    allow_reuse_address = True


def _get(url: str) -> tuple[int, str, bytes]:
    """Fetch a fixed loopback http URL; return status, content-type and body."""
    # Hardcoded http://127.0.0.1 loopback URL, not user input; the bandit
    # audit for arbitrary schemes does not apply here.
    with urllib.request.urlopen(url, timeout=5) as resp:  # noqa: S310
        return resp.status, resp.headers.get("Content-Type", ""), resp.read()


def main() -> None:
    """Build the store, serve it, check z/x/y fetches, print PASS/FAIL."""
    ntiles = build_mbtiles()
    print(f"MBTILES built: {MBTILES}")
    print(f"  tiles: {ntiles}  zoom: 0-2  store bytes: {os.path.getsize(MBTILES)}")

    httpd = ReusableServer(("127.0.0.1", PORT), TileHandler)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    base = f"http://127.0.0.1:{PORT}/tiles"

    ok = True
    print(f"z/x/y fetches against {base}/{{z}}/{{x}}/{{y}}.png :")
    for z, x, y in [(0, 0, 0), (1, 0, 0), (1, 1, 1), (2, 3, 3)]:
        try:
            status, ctype, body = _get(f"{base}/{z}/{x}/{y}.png")
        except OSError as exc:
            print(f"  GET {z}/{x}/{y}.png -> ERROR {exc}")
            ok = False
            continue
        sig = body[:8] == b"\x89PNG\r\n\x1a\n"
        print(f"  GET {z}/{x}/{y}.png -> {status} {ctype} {len(body)}B pngsig={sig}")
        ok = ok and status == 200 and ctype == "image/png" and sig

    try:
        _get(f"{base}/9/9/9.png")
        print("  GET 9/9/9.png -> UNEXPECTED 200 (should 404)")
        ok = False
    except urllib.error.HTTPError as exc:
        print(f"  GET 9/9/9.png -> {exc.code} (out-of-range correctly refused)")
        ok = ok and exc.code == 404

    httpd.shutdown()
    print("RESULT:", "PASS" if ok else "FAIL")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
