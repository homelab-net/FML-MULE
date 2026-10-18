#!/usr/bin/env python3
"""Reconnecting TAK probe for the tak.field failover trials.

Usage::

    tak-probe.py send|recv HOST PORT CERT KEY CA SECONDS LOG [PEER_UID]

``send`` reports a position every second; ``recv`` logs every event whose uid
is ``PEER_UID`` (or every event, if none is given). Both connect over mutual
TLS, log every connect and disconnect with a UTC timestamp, and reconnect 0.5 s
after any failure. Recovery after a fault is measured as the first peer report
received after the fault, minus the fault time.

The position is a fixed placeholder, never a real location. Used by
``test/bench/tak-failover-campaign.sh``. CONOPS 25 and 27; FML-ADR-031 and
FML-ADR-049; TBR-HA-01. See ``docs/evidence/TBR-HA-01/``.
"""

from __future__ import annotations

import json
import socket
import ssl
import sys
import time
import xml.etree.ElementTree as ET
from datetime import UTC, datetime, timedelta
from typing import TextIO
from uuid import uuid4


def iso(d: datetime) -> str:
    """Render a UTC timestamp the way CoT does."""
    return d.strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def note(log: TextIO, role: str, **fields: object) -> None:
    """Append one timestamped event to the JSON-lines log."""
    log.write(json.dumps({"at": iso(datetime.now(UTC)), "role": role, **fields}) + "\n")
    log.flush()


def pli(uid: str) -> bytes:
    """One position report at the placeholder position."""
    t = datetime.now(UTC)
    stale = iso(t + timedelta(seconds=60))
    return (
        f'<event version="2.0" uid="{uid}" type="a-f-G-U-C" how="h-e" '
        f'time="{iso(t)}" start="{iso(t)}" stale="{stale}">'
        '<point lat="0.0" lon="0.0" hae="0" ce="10" le="10"/>'
        f'<detail><contact callsign="{uid[-16:]}"/>'
        '<__group name="Cyan" role="Team Member"/>'
        f"<remarks>seq {uuid4().hex[:8]}</remarks></detail></event>"
    ).encode()


def events(buf: bytes) -> tuple[list[ET.Element], bytes]:
    """Split complete CoT events off the front of a stream buffer."""
    out = []
    while b"</event>" in buf:
        chunk, buf = buf.split(b"</event>", 1)
        start = chunk.find(b"<event")
        if start < 0:
            continue
        try:
            # Parses this bench's own TAK Server stream, not untrusted input.
            out.append(ET.fromstring(chunk[start:] + b"</event>"))  # noqa: S314
        except ET.ParseError:
            continue
    return out, buf


def session(
    s: ssl.SSLSocket, role: str, uid: str, peer: str | None, end: float, log: TextIO
) -> None:
    """Run one connected session until it ends or fails."""
    buf, next_tx = b"", 0.0
    while time.time() < end:
        if role == "send" and time.time() >= next_tx:
            s.sendall(pli(uid))
            next_tx = time.time() + 1
        try:
            data = s.recv(65536)
        except TimeoutError:
            continue
        if not data:
            raise ConnectionError("closed by peer")
        received, buf = events(buf + data)
        for ev in received:
            if role == "recv" and (peer is None or ev.get("uid") == peer):
                note(log, role, event="rx", uid=ev.get("uid"), type=ev.get("type"))


def main() -> None:
    """Connect, run, and reconnect until the time is up."""
    role, host, port, cert, key, ca, secs, logf = sys.argv[1:9]
    peer = sys.argv[9] if len(sys.argv) > 9 else None
    uid = f"FML-PROBE-{role.upper()}-{socket.gethostname()}"
    ctx = ssl.create_default_context(cafile=ca)
    # Bench backends are CN=takserver and CN=takserver-b behind one name.
    ctx.check_hostname = False
    ctx.load_cert_chain(cert, key)
    end = time.time() + int(secs)
    with open(logf, "a") as log:
        while time.time() < end:
            try:
                raw = socket.create_connection((host, int(port)), timeout=3)
                s = ctx.wrap_socket(raw, server_hostname=host)
                s.settimeout(1.0)
                note(log, role, event="connected", tls=s.version())
                session(s, role, uid, peer, end, log)
                s.close()
            except Exception as e:  # every failure is logged, then retried
                reason = f"{type(e).__name__}: {e}"[:160]
                note(log, role, event="disconnected", reason=reason)
                time.sleep(0.5)
        note(log, role, event="done")


if __name__ == "__main__":
    main()
