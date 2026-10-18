#!/usr/bin/env python3
"""Synthetic TAK client: position reports and one GeoChat out, every event in.

Usage::

    tak-sim.py HOST PORT CERT KEY CA SECONDS LOG

Connects once over mutual TLS with a provisioned client certificate, reports a
position every five seconds, sends one GeoChat to All Chat Rooms ten seconds
in, and logs every CoT event the server relays (uid, type, callsign, chat
text). It does not reconnect: a single unbroken session is the point of a soak.
Its counterpart for failover trials is ``tak-probe.py``.

The position is a fixed placeholder, never a real location. CONOPS 21 and 24;
TBR-COMP-01. See ``docs/evidence/TBR-COMP-01/``.
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

UID = "FML-BENCH-SIM-" + uuid4().hex[:8]
CALLSIGN = "BENCH-SIM"
POINT = '<point lat="0.0" lon="0.0" hae="0" ce="10" le="10"/>'


def ts(offset: float = 0) -> str:
    """UTC time, offset by seconds, in CoT form."""
    t = datetime.now(UTC) + timedelta(seconds=offset)
    return t.strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def note(log: TextIO, **fields: object) -> None:
    """Append one timestamped event to the JSON-lines log."""
    log.write(json.dumps({"at": ts(), **fields}) + "\n")
    log.flush()


def pli() -> bytes:
    """One position report at the placeholder position."""
    return (
        f'<event version="2.0" uid="{UID}" type="a-f-G-U-C" how="h-e" '
        f'time="{ts()}" start="{ts()}" stale="{ts(120)}">{POINT}'
        f'<detail><contact callsign="{CALLSIGN}"/>'
        '<__group name="Cyan" role="Team Member"/>'
        '<takv platform="FML bench synthetic" version="1"/></detail></event>'
    ).encode()


def geochat(text: str) -> bytes:
    """One GeoChat message to All Chat Rooms."""
    mid = uuid4().hex
    room = "All Chat Rooms"
    return (
        f'<event version="2.0" uid="GeoChat.{UID}.{room}.{mid}" type="b-t-f" '
        f'how="h-g-i-g-o" time="{ts()}" start="{ts()}" stale="{ts(86400)}">'
        f'{POINT}<detail><__chat parent="RootContactGroup" groupOwner="false" '
        f'messageId="{mid}" chatroom="{room}" id="{room}" '
        f'senderCallsign="{CALLSIGN}"><chatgrp uid0="{UID}" uid1="{room}" '
        f'id="{room}"/></__chat><link uid="{UID}" type="a-f-G-U-C" '
        f'relation="p-p"/><remarks source="BAO.F.ATAK.{UID}" to="{room}" '
        f'time="{ts()}">{text}</remarks></detail></event>'
    ).encode()


def describe(chunk: bytes) -> dict[str, object] | None:
    """Summarise one relayed CoT event, or None if it does not parse."""
    try:
        # Parses this bench's own TAK Server stream, not untrusted input.
        ev = ET.fromstring(chunk)  # noqa: S314
    except ET.ParseError:
        return None
    contact, chat = ev.find("detail/contact"), ev.find("detail/__chat")
    remarks = ev.find("detail/remarks")
    if contact is not None:
        callsign = contact.get("callsign")
    else:
        callsign = chat.get("senderCallsign") if chat is not None else None
    text = remarks.text if remarks is not None and ev.get("type") == "b-t-f" else None
    return {
        "uid": ev.get("uid"),
        "type": ev.get("type"),
        "callsign": callsign,
        "chat": text,
    }


def main() -> None:
    """Hold one session for the requested time and log both directions."""
    host, port, cert, key, ca, secs, logf = sys.argv[1:8]
    ctx = ssl.create_default_context(cafile=ca)
    ctx.check_hostname = False  # the bench server certificate is CN=takserver
    ctx.load_cert_chain(cert, key)
    s = ctx.wrap_socket(
        socket.create_connection((host, int(port)), timeout=10), server_hostname=host
    )
    s.settimeout(1.0)
    start = time.time()
    end, next_pli, chat_sent, buf = start + int(secs), 0.0, False, b""
    with open(logf, "a") as log:
        note(log, event="connected", uid=UID, tls=s.version(), cipher=s.cipher()[0])
        while time.time() < end:
            if time.time() >= next_pli:
                s.sendall(pli())
                note(log, event="sent", kind="pli")
                next_pli = time.time() + 5
            if not chat_sent and time.time() > start + 10:
                text = f"FML bench GeoChat test {uuid4().hex[:6]}"
                s.sendall(geochat(text))
                note(log, event="sent", kind="geochat", text=text)
                chat_sent = True
            try:
                data = s.recv(65536)
            except TimeoutError:
                continue
            except ssl.SSLError as e:
                note(log, event="ssl-error", detail=str(e))
                break
            if not data:
                note(log, event="closed-by-server")
                break
            buf += data
            while b"</event>" in buf:
                chunk, buf = buf.split(b"</event>", 1)
                i = chunk.find(b"<event")
                if i >= 0 and (d := describe(chunk[i:] + b"</event>")) is not None:
                    note(log, event="received", **d)
        note(log, event="done")
    s.close()


if __name__ == "__main__":
    main()
