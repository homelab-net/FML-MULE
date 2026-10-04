#!/usr/bin/env python3
"""Capture what a live ATAK/iTAK client puts in `<__chat id>` on a direct message.

WHY THIS EXISTS

`FML-ADR-070` carries the recipient in upstream's own `GeoChat.to`. What rides
there was grounded on 2026-09-28
(`docs/evidence/TBR-NET-02/2026-09-28-real-geochat-encoding-through-ots.md`):
OpenTAKServer's encoder copies the client-supplied `<__chat id>` **verbatim**,
substituting no callsign of its own. With a recipient whose id
(`UID-CHARLIE-9999`) differed from its callsign (`CHARLIE-CS`), the wire carried
the **UID**, and the recipient's callsign appeared nowhere in the packet.

That left one half owed, and `CCR-06` still lists it as owed: **what a live
client actually places in `<__chat id>`** -- a UID by ATAK convention, but a
callsign is not ruled out. `mule/recipients.py` keys its roster on that value
and says so, so the roster's `callsign -> key` binding rests on an assumption
nobody has confirmed against a real client.

This resolves it. It registers an **obviously fake** EUD against the bench CoT
port so a real client can address it, then prints the `<__chat id>` of any
GeoChat that arrives. The fake identity's **UID differs from its callsign on
purpose**: that is the whole discriminator. The 2026-09-28 first run could not
answer the question because it used `id == callsign`, which produces the same
string either way.

WHAT IT DOES NOT DO

It sends no LoRa traffic and decides nothing. It is a listener with a
registration, so that a human with a phone can produce one fact. It does not
scrub what it prints -- a live client's identity is the Owner's and
`AGENTS.md` forbids committing a callsign, so the operator scrubs before
filing. Run it, read it, do not redirect it into `docs/evidence/`.

Usage: test/bench/eud-chat-id-capture.py [--host H] [--port P] [--seconds N]
"""

from __future__ import annotations

import argparse
import re
import socket
import sys
import time
from datetime import UTC, datetime, timedelta

#: Obviously fake, per `AGENTS.md`: "mission/examples/ carries obviously fake
#: identities only". The UID and the callsign differ deliberately -- if a client
#: sends to the UID we see the UID, if it sends to the callsign we see the
#: callsign, and either way the answer is unambiguous. Naming follows the
#: `FMLPROBE-ALPHA` / `CHARLIE-CS` convention the 2026-09-28 record established.
PROBE_UID = "UID-FMLPROBE-DELTA-0001"
PROBE_CALLSIGN = "FMLPROBE-DELTA-CS"

#: Null Island. A real position would be a deployment location, which
#: `AGENTS.md` forbids committing, and this probe has no business asserting one.
PROBE_LAT = "0.0"
PROBE_LON = "0.0"


def _stamp(offset_seconds: int = 0) -> str:
    """Return a CoT timestamp, optionally offset into the future."""
    moment = datetime.now(UTC) + timedelta(seconds=offset_seconds)
    return moment.strftime("%Y-%m-%dT%H:%M:%S.000Z")


def presence_cot() -> bytes:
    """Build the fake EUD's own position report, so a client can address it.

    A TAK server streams nothing to a client that has not announced itself --
    verified on this bench, where a bare TCP connect to the CoT port returned
    zero bytes for ten seconds. This is the announcement.
    """
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        f'<event version="2.0" uid="{PROBE_UID}" type="a-f-G-U-C" how="m-g"'
        f' time="{_stamp()}" start="{_stamp()}" stale="{_stamp(300)}">'
        f'<point lat="{PROBE_LAT}" lon="{PROBE_LON}" hae="0.0"'
        ' ce="9999999.0" le="9999999.0"/>'
        "<detail>"
        f'<contact callsign="{PROBE_CALLSIGN}" endpoint="*:-1:stcp"/>'
        '<__group name="Cyan" role="Team Member"/>'
        '<takv device="FMLPROBE" platform="FML-MULE bench probe"'
        ' os="linux" version="0.0.1"/>'
        '<status battery="100"/>'
        f'<uid Droid="{PROBE_CALLSIGN}"/>'
        "</detail></event>"
    ).encode()


#: Extracted with regular expressions rather than an XML parser, deliberately.
#: This stream is relayed client data and so is untrusted input; feeding it to
#: `xml.etree` is the `S314` finding ("vulnerable to XML attacks"). The three
#: values wanted are single attributes, so dropping the parser removes the whole
#: vulnerability class instead of suppressing the warning, and `AGENTS.md`
#: forbids disabling a linter to make something pass.
_EVENT_RE = re.compile(r"<event\b.*?</event>", re.S)
_CHAT_RE = re.compile(r"<__chat\b([^>]*)>")
_CONTACT_RE = re.compile(r"<contact\b([^>]*)>")


def _attr(attrs: str, name: str) -> str:
    """Pull one attribute value out of a raw tag's attribute text."""
    found = re.search(rf'{name}="([^"]*)"', attrs)
    return found.group(1) if found else ""


def chat_ids(xml: str) -> list[tuple[str, str, str]]:
    """Return (chat_id, chat_parent, sender_callsign) for each GeoChat found.

    `<__chat id="...">` is the field the whole exercise is about. Scanning is
    tolerant because a stream carries concatenated documents and partial tails.
    """
    out: list[tuple[str, str, str]] = []
    for blob in _EVENT_RE.findall(xml):
        chat = _CHAT_RE.search(blob)
        if chat is None:
            continue
        contact = _CONTACT_RE.search(blob)
        out.append(
            (
                _attr(chat.group(1), "id"),
                _attr(chat.group(1), "parent"),
                _attr(contact.group(1), "callsign") if contact else "",
            )
        )
    return out


def run(host: str, port: int, seconds: int) -> int:
    """Register the probe, then report every GeoChat until the time runs out."""
    print(f"  probe uid      : {PROBE_UID}")
    print(f"  probe callsign : {PROBE_CALLSIGN}")
    print("  (uid and callsign differ on purpose -- that is the discriminator)")
    print(f"  connecting to {host}:{port} ...")
    try:
        stream = socket.create_connection((host, port), timeout=10)
    except OSError as exc:
        print(f"FAIL: cannot reach {host}:{port}: {exc}", file=sys.stderr)
        return 1
    stream.settimeout(5)
    stream.sendall(presence_cot())
    print("  registered; now addressable from a client's contact list")
    print(f"  listening {seconds}s -- send a direct message to {PROBE_CALLSIGN}\n")

    deadline = time.monotonic() + seconds
    pending = ""
    seen = 0
    last_announce = time.monotonic()
    while time.monotonic() < deadline:
        if time.monotonic() - last_announce > 60:
            stream.sendall(presence_cot())
            last_announce = time.monotonic()
        try:
            chunk = stream.recv(65535)
        except TimeoutError:
            continue
        except OSError as exc:
            print(f"  stream ended: {exc}", file=sys.stderr)
            break
        if not chunk:
            print("  stream closed by server", file=sys.stderr)
            break
        pending += chunk.decode("utf-8", "replace")
        for chat_id, parent, sender in chat_ids(pending):
            seen += 1
            print("  GeoChat received:")
            print(f"    <__chat id>     = {chat_id!r}")
            print(f"    <__chat parent> = {parent!r}")
            print(f"    sender callsign = {sender!r}")
            if chat_id == PROBE_UID:
                print("    => the client addressed the probe by its UID")
            elif chat_id == PROBE_CALLSIGN:
                print("    => the client addressed the probe by its CALLSIGN")
            else:
                print("    => neither the probe UID nor its callsign; read it above")
        if chat_ids(pending):
            pending = ""
        if len(pending) > 1_000_000:
            pending = pending[-100_000:]

    stream.close()
    if seen == 0:
        print("\n  no GeoChat arrived. The question is unanswered, not answered.")
        return 1
    print(f"\n  {seen} GeoChat(s) captured.")
    return 0


def main(argv: list[str]) -> int:
    """Parse arguments and run the capture."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default="10.41.0.1")
    parser.add_argument("--port", type=int, default=8088)
    parser.add_argument("--seconds", type=int, default=180)
    args = parser.parse_args(argv)
    return run(args.host, args.port, args.seconds)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
