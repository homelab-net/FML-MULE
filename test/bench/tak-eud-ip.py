#!/usr/bin/env python3
"""Synthetic TAK EUDs on the IP plane, for running CoT across the real mesh.

Usage:
  tak-eud-ip.py listen [--port N] [--proto tcp|udp] [--seconds N] [--bind ADDR]
  tak-eud-ip.py send --url tcp://HOST:PORT --kind pli|geochat
                     [--from CALLSIGN] [--to CALLSIGN] [--message TEXT]
                     [--count N] [--interval S]

WHAT THIS IS FOR. `test/topology/cases/tak/send_cot.py` sends one synthetic PLI
to a CoT listener over a container network. This does two things that one does
not: it also speaks **GeoChat**, which is the chat half nothing here exercised
on the IP plane, and it carries a **receiving** end, so a message can be shown
to arrive rather than merely to have been sent. The transport is PyTAK, which
`FML-ADR-033` prefers for custom CoT clients.

The EUDs are synthetic -- they are this script. It exercises the CoT encoding
and the path, never a TAK application, never enrollment, and never certificates:
`listen` is a plain socket sink, not OpenTAKServer. A real ATAK client needs the
enrollment path, which is a separate question this does not touch.

WHY A SINK AND NOT A SERVER. Standing up OpenTAKServer is a container build with
its own failure modes, and it would confound two questions: whether CoT crosses
the bearer, and whether the server ingests it. This answers the first alone. The
sink prints the fields a GeoChat is judged by, so the comparison is byte-level.

ON THE MESH. Point --url at the far node's bat0 address and the CoT rides the
real 802.11s/batman-adv path. That link measured 0.172 ms voice jitter idle and
32.5 ms under a saturating bulk flow (docs/evidence/TBR-RF-01/), so the
interesting run is this traffic DURING that contention, not only on a quiet
mesh.
"""

from __future__ import annotations

import argparse
import asyncio
import socket
import sys
import time
import uuid
import xml.etree.ElementTree as ET

DEFAULT_PORT = 8088


def fail(msg: str) -> None:
    print("FAIL: " + msg, file=sys.stderr)
    raise SystemExit(1)


def cot_time(offset: int = 0) -> str:
    """A CoT timestamp, from the standard library only.

    This deliberately does NOT call pytak.cot_time(). An earlier version did,
    which quietly made `--transport raw` depend on PyTAK after all and defeated
    the reason that transport exists -- it failed on the one host chosen
    precisely because PyTAK is not installed there. The format is plain
    ISO 8601 with milliseconds and a Zulu suffix, which is what TAK expects.
    """
    from datetime import datetime, timedelta, timezone
    t = datetime.now(timezone.utc) + timedelta(seconds=offset)
    return t.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"


def build_pli(callsign: str, uid: str) -> bytes:
    """A position location information event: the 'I am here' of TAK."""
    ev = ET.Element("event", {
        "version": "2.0", "type": "a-f-G-U-C", "uid": uid,
        "how": "m-g", "time": cot_time(), "start": cot_time(),
        "stale": cot_time(120),
    })
    ET.SubElement(ev, "point", {
        "lat": "38.8339", "lon": "-104.8214", "hae": "1840", "ce": "10", "le": "10",
    })
    det = ET.SubElement(ev, "detail")
    ET.SubElement(det, "contact", {"callsign": callsign})
    ET.SubElement(det, "__group", {"name": "Cyan", "role": "Team Member"})
    return ET.tostring(ev)


def build_geochat(sender: str, sender_uid: str, to: str, to_uid: str, message: str) -> bytes:
    """A GeoChat event, in the shape ATAK actually puts on the wire.

    The two fields FML-ADR-070 rests on appear here as `contact/@callsign` for
    the sender and the chatroom/recipient for `GeoChat.to`, so an IP-plane
    message and a Meshtastic TAKPacket carry the same two identities.
    """
    msg_id = str(uuid.uuid4())
    ev = ET.Element("event", {
        "version": "2.0", "type": "b-t-f",
        "uid": "GeoChat.%s.%s.%s" % (sender_uid, to, msg_id),
        "how": "h-g-i-g-o", "time": cot_time(), "start": cot_time(),
        "stale": cot_time(86400),
    })
    ET.SubElement(ev, "point", {
        "lat": "38.8339", "lon": "-104.8214", "hae": "1840", "ce": "10", "le": "10",
    })
    det = ET.SubElement(ev, "detail")
    chat = ET.SubElement(det, "__chat", {
        "parent": "RootContactGroup", "groupOwner": "false",
        "messageId": msg_id, "chatroom": to, "id": to_uid,
        "senderCallsign": sender,
    })
    ET.SubElement(chat, "chatgrp", {"uid0": sender_uid, "uid1": to_uid, "id": to_uid})
    ET.SubElement(det, "link", {"uid": sender_uid, "type": "a-f-G-U-C", "relation": "p-p"})
    rem = ET.SubElement(det, "remarks", {
        "source": "BAO.F.ATAK.%s" % sender_uid, "to": to_uid, "time": cot_time(),
    })
    rem.text = message
    ET.SubElement(det, "contact", {"callsign": sender})
    return ET.tostring(ev)


def summarise(xml: bytes) -> str:
    """Pull out the fields a CoT event is judged by, for a byte-level compare."""
    try:
        ev = ET.fromstring(xml)
    except ET.ParseError as exc:
        return "unparseable (%s): %r" % (exc, xml[:80])
    typ = ev.get("type", "?")
    uid = ev.get("uid", "?")
    contact = ev.find("./detail/contact")
    callsign = contact.get("callsign") if contact is not None else None
    chat = ev.find("./detail/__chat")
    remarks = ev.find("./detail/remarks")
    if chat is not None:
        return ("GeoChat  sender=%r -> chatroom=%r  message=%r  uid=%s"
                % (chat.get("senderCallsign"), chat.get("chatroom"),
                   (remarks.text if remarks is not None else None), uid))
    # PyTAK emits its own keepalive (type t-x-d-d, uid takPing) on every
    # connection. It is neither a PLI nor a chat, and counting it as a PLI
    # inflates the figure an evidence file would quote -- an early run of this
    # script reported "3 PLI" for one PLI and two pings.
    if typ == "t-x-d-d" or uid == "takPing":
        return "PING     pytak keepalive  type=%s  uid=%s" % (typ, uid)
    if typ.startswith("a-"):
        return "PLI      callsign=%r  type=%s  uid=%s" % (callsign, typ, uid)
    return "OTHER    callsign=%r  type=%s  uid=%s" % (callsign, typ, uid)


def do_listen(args) -> int:
    """A plain CoT sink. No server, no certificates, no enrollment."""
    seen = {"events": 0, "chat": 0, "pli": 0, "ping": 0, "other": 0, "bad": 0}
    deadline = time.time() + args.seconds

    def handle(xml: bytes, peer: str) -> None:
        seen["events"] += 1
        line = summarise(xml)
        kind = line.split(None, 1)[0] if line else ""
        seen[{"GeoChat": "chat", "PLI": "pli", "PING": "ping",
              "OTHER": "other"}.get(kind, "bad")] += 1
        print("  [%s] %s" % (peer, line), flush=True)

    if args.proto == "udp":
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((args.bind, args.port))
        s.settimeout(1.0)
        print("CoT sink: udp://%s:%d for %ss" % (args.bind, args.port, args.seconds), flush=True)
        while time.time() < deadline:
            try:
                data, addr = s.recvfrom(65535)
            except socket.timeout:
                continue
            handle(data, addr[0])
        s.close()
    else:
        srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        srv.bind((args.bind, args.port))
        srv.listen(5)
        srv.settimeout(1.0)
        print("CoT sink: tcp://%s:%d for %ss" % (args.bind, args.port, args.seconds), flush=True)
        while time.time() < deadline:
            try:
                conn, addr = srv.accept()
            except socket.timeout:
                continue
            conn.settimeout(2.0)
            buf = b""
            # CoT over TCP is concatenated <event>..</event>, not framed.
            try:
                while True:
                    chunk = conn.recv(65535)
                    if not chunk:
                        break
                    buf += chunk
                    while b"</event>" in buf:
                        one, buf = buf.split(b"</event>", 1)
                        handle(one + b"</event>", addr[0])
            except socket.timeout:
                pass
            finally:
                conn.close()
        srv.close()

    print("received %d event(s): %d GeoChat, %d PLI, %d pytak keepalive, "
          "%d other, %d unparseable"
          % (seen["events"], seen["chat"], seen["pli"], seen["ping"],
             seen["other"], seen["bad"]))
    # An empty run is not a result: say so rather than let it read as a pass.
    if seen["events"] == 0:
        print("NOTE: nothing arrived. That is an orchestration or path failure to")
        print("re-run, not a measurement.")
    return 0


def send_raw(url: str, events: list[bytes], settle: float) -> int:
    """Send over a plain socket, no PyTAK.

    PyTAK is the preferred client (FML-ADR-033) and is what `--transport pytak`
    uses. This exists so an EUD can be simulated on a host where installing
    PyTAK is not wanted -- the bench mule carries the COCON stack, and a test
    EUD there should not require adding packages to it. CoT over TCP is just
    concatenated <event>..</event>, so a socket is a faithful transport; what is
    lost is PyTAK's connection management and its keepalive, not the encoding.
    """
    scheme, _, rest = url.partition("://")
    host, _, port_s = rest.partition(":")
    port = int(port_s or DEFAULT_PORT)
    if scheme not in ("tcp", "udp"):
        fail("--transport raw understands tcp:// and udp://, not %r" % scheme)
    if scheme == "udp":
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        for i, ev in enumerate(events):
            s.sendto(ev, (host, port))
            print("  sent %d/%d: %s" % (i + 1, len(events), summarise(ev)), flush=True)
        s.close()
    else:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(10.0)
        s.connect((host, port))
        for i, ev in enumerate(events):
            s.sendall(ev)
            print("  sent %d/%d: %s" % (i + 1, len(events), summarise(ev)), flush=True)
        time.sleep(settle)
        s.close()
    return 0


def do_send(args) -> int:
    from configparser import ConfigParser

    sender_uid = args.uid or ("FML-EUD-" + args.from_callsign)
    to_uid = "FML-EUD-" + args.to if args.to else "All Chat Rooms"

    events: list[bytes] = []
    for _ in range(args.count):
        if args.kind == "pli":
            events.append(build_pli(args.from_callsign, sender_uid))
        else:
            if not args.message:
                fail("--kind geochat needs --message")
            events.append(build_geochat(args.from_callsign, sender_uid,
                                        args.to or "All Chat Rooms", to_uid,
                                        args.message))

    print("sending %d %s event(s) to %s via %s"
          % (args.count, args.kind, args.url, args.transport))
    if args.transport == "raw":
        return send_raw(args.url, events, args.settle)

    import pytak

    class Emit(pytak.QueueWorker):  # type: ignore[misc]
        async def run(self) -> None:
            for i, ev in enumerate(events):
                await self.put_queue(ev)
                print("  queued %d/%d: %s" % (i + 1, len(events), summarise(ev)), flush=True)
                if args.interval and i + 1 < len(events):
                    await asyncio.sleep(args.interval)
            # The transmitter is a separate task; give it time to drain before
            # the process exits, or the last events never leave.
            await asyncio.sleep(args.settle)
            import os
            os._exit(0)

    async def main() -> None:
        parser = ConfigParser()
        parser["sender"] = {"COT_URL": args.url}
        config = parser["sender"]
        tool = pytak.CLITool(config)
        await tool.setup()
        tool.add_tasks({Emit(tool.tx_queue, config)})
        await tool.run()

    asyncio.run(main())
    return 0


def main(argv: list[str]) -> int:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="mode", required=True)

    pl = sub.add_parser("listen", help="CoT sink; receives and decodes")
    pl.add_argument("--port", type=int, default=DEFAULT_PORT)
    pl.add_argument("--bind", default="0.0.0.0")  # noqa: S104
    pl.add_argument("--proto", choices=["tcp", "udp"], default="tcp")
    pl.add_argument("--seconds", type=float, default=60.0)

    ps = sub.add_parser("send", help="send synthetic CoT as a fake EUD")
    ps.add_argument("--url", required=True, help="e.g. tcp://10.42.0.2:8088")
    ps.add_argument("--kind", choices=["pli", "geochat"], default="geochat")
    ps.add_argument("--from", dest="from_callsign", default="FMLEUD1")
    ps.add_argument("--to", default=None, help="recipient callsign / chatroom")
    ps.add_argument("--message", default=None)
    ps.add_argument("--uid", default=None)
    ps.add_argument("--count", type=int, default=1)
    ps.add_argument("--interval", type=float, default=0.0)
    ps.add_argument("--settle", type=float, default=4.0)
    ps.add_argument("--transport", choices=["pytak", "raw"], default="pytak",
                    help="pytak is preferred (FML-ADR-033); raw needs only the "
                         "standard library, for hosts where PyTAK is not wanted")

    args = p.parse_args(argv)
    return do_listen(args) if args.mode == "listen" else do_send(args)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
