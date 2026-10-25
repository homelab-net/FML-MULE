#!/usr/bin/env python3
"""A synthetic TAK EUD for the TBR-HA-01 partition trial, on two planes.

  tak-partition-eud.py --role partitioned|control --host H [--port P] --cert C --key K
                       --ca CA --seconds N --log OUT.jsonl [--ctl DIR]

Two roles, run together with a real client (WinTAK) under test:

- ``partitioned`` sits on the client side of the cut, beside the real client.
  It keeps a mutual-TLS stream to the TAK server AND speaks peer-mode
  multicast (SA on 239.2.3.1:6969, GeoChat on 224.10.10.1:17012).
- ``control`` sits on the server side of the cut (on the server host, over
  loopback, which the cut leaves alone). It has no multicast: it stands for
  the rest of the network that still has the server.

Every chat it originates goes on exactly ONE path, alternating ``m``
(multicast) and ``s`` (server), with the path and a sequence number in the
text (``sim m 007``), so a receiver's log alone says which path delivered it.
Each send is logged with its messageId, so receipt is matched by id, not text.
It logs every chat and SA it hears, with the path it came on. A real client's
chat is logged by messageId and text whichever encoding it uses (TAK protocol
or XML). Logs carry uids, never positions; scrub uids before publishing.

The stream reconnects on failure and pings; it gives up on a silent stream
after ``--rx-timeout`` seconds, as a real client does, so the time it takes to
notice a partition is measured, not assumed. To send an extra chat by hand,
write its text to CTL/chat.req.

The identity and point are synthetic.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import select
import socket
import ssl
import struct
import threading
import time
import uuid
from datetime import UTC, datetime, timedelta
from xml.sax.saxutils import escape

LAT, LON = 38.8339, -104.8214  # the bench's synthetic point (tak-eud-ip.py)
SA_GROUP, CHAT_GROUP = ("239.2.3.1", 6969), ("224.10.10.1", 17012)
ROOM = "All Chat Rooms"
PING_EVERY = 15


def ts(off: float = 0.0) -> str:
    """Return a CoT timestamp, UTC with milliseconds."""
    t = datetime.now(UTC) + timedelta(seconds=off)
    return t.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"


class Eud:
    """One synthetic EUD: its identity, its log and its live stream."""

    def __init__(self, args: argparse.Namespace) -> None:
        """Open the log; nothing connects until run()."""
        self.a = args
        self.uid = args.uid
        self.callsign = args.callsign
        self.lock = threading.Lock()
        self.stream: ssl.SSLSocket | None = None
        self.log_f = open(args.log, "a")
        self.end = time.time() + args.seconds

    def log(self, path: str, event: str, **kw: object) -> None:
        """Append one timestamped JSON line."""
        with self.lock:
            line = {"t": ts(), "who": self.a.role, "path": path, "event": event, **kw}
            self.log_f.write(json.dumps(line) + "\n")
            self.log_f.flush()

    # --- CoT -------------------------------------------------------------

    def sa(self, n: int) -> bytes:
        """SA with takv and a contact endpoint, so a real client replies."""
        lat = LAT + 0.0001 * (n % 20)
        return (
            f'<event version="2.0" uid="{self.uid}" type="a-f-G-U-C" how="m-g" '
            f'time="{ts()}" start="{ts()}" stale="{ts(60)}">'
            f'<point lat="{lat:.7f}" lon="{LON:.7f}" hae="1800.0" ce="10" le="10"/>'
            f'<detail><contact callsign="{self.callsign}" endpoint="*:-1:stcp"/>'
            f'<takv device="FML bench" platform="{self.callsign}" os="linux" '
            'version="0"/>'
            '<__group name="Cyan" role="Team Member"/>'
            f'<uid Droid="{self.callsign}"/><remarks>sa {n}</remarks></detail></event>'
        ).encode()

    def ping(self) -> bytes:
        """Build a TAK ping, which keeps the server's view of the stream fresh."""
        return (
            f'<event version="2.0" uid="{self.uid}-ping" type="t-x-c-t" '
            'how="h-g-i-g-o" '
            f'time="{ts()}" start="{ts()}" stale="{ts(20)}">'
            '<point lat="0.0" lon="0.0" hae="0.0" ce="9999999" le="9999999"/>'
            "<detail/></event>"
        ).encode()

    def chat(self, text: str) -> tuple[bytes, str]:
        """Build an All Chat Rooms GeoChat, shaped like the bench gateway's."""
        mid = str(uuid.uuid4())
        uid, cs = self.uid, self.callsign
        return (
            f'<event version="2.0" uid="GeoChat.{uid}.{ROOM}.{mid}" type="b-t-f" '
            f'how="h-g-i-g-o" time="{ts()}" start="{ts()}" stale="{ts(86400)}">'
            '<point lat="0.0" lon="0.0" hae="9999999.0" ce="9999999" le="9999999"/>'
            f'<detail><__chat parent="RootContactGroup" groupOwner="false" '
            f'messageId="{mid}" chatroom="{ROOM}" id="{ROOM}" senderCallsign="{cs}">'
            f'<chatgrp uid0="{uid}" uid1="{ROOM}" id="{ROOM}"/></__chat>'
            f'<link uid="{uid}" type="a-f-G-U-C" relation="p-p"/>'
            f'<remarks source="BAO.F.ATAK.{uid}" to="{ROOM}" time="{ts()}">'
            f"{escape(text)}</remarks></detail></event>"
        ).encode(), mid

    # --- the server stream ------------------------------------------------

    def stream_loop(self) -> None:
        """Keep the server stream up for the whole run, logging every change."""
        a = self.a
        ctx = ssl.create_default_context(cafile=a.ca)
        ctx.check_hostname = False  # bench backends are CN=takserver[-b]
        ctx.load_cert_chain(a.cert, a.key)
        n = 0
        while time.time() < self.end:
            try:
                raw = socket.create_connection((a.host, a.port), timeout=5)
                s = ctx.wrap_socket(raw, server_hostname=a.host)
                s.settimeout(1.0)
            except Exception as e:  # every failure is logged, then retried
                self.log(
                    "server", "connect-failed", reason=f"{type(e).__name__}: {e}"[:100]
                )
                time.sleep(a.retry)
                continue
            self.log("server", "connected", local=s.getsockname()[1])
            self.stream = s
            try:
                n = self.session(s, n)
            except Exception as e:
                self.log(
                    "server", "disconnected", reason=f"{type(e).__name__}: {e}"[:100]
                )
            self.stream = None
            try:
                s.close()
            except OSError:
                pass
            time.sleep(a.retry)

    def session(self, s: ssl.SSLSocket, n: int) -> int:
        """Run one connected stream until it fails; return the SA counter."""
        buf, last_rx = b"", time.time()
        next_sa, next_ping = 0.0, time.time() + PING_EVERY
        while time.time() < self.end:
            now = time.time()
            if now >= next_sa:
                with self.lock:
                    s.sendall(self.sa(n))
                n, next_sa = n + 1, now + self.a.sa_every
            if now >= next_ping:
                with self.lock:
                    s.sendall(self.ping())
                next_ping = now + PING_EVERY
            if now - last_rx > self.a.rx_timeout:
                raise TimeoutError(f"nothing received for {self.a.rx_timeout} s")
            try:
                data = s.recv(65536)
            except TimeoutError:
                continue
            if not data:
                raise ConnectionError("closed by server")
            last_rx, buf = time.time(), buf + data
            while b"</event>" in buf:
                chunk, buf = buf.split(b"</event>", 1)
                i = chunk.find(b"<event")
                if i >= 0:
                    self.heard("server", chunk[i:] + b"</event>", None)
        return n

    # --- multicast ----------------------------------------------------------

    def mcast_loop(self, me: str) -> None:
        """Hear peer SA and chat on the multicast groups, on `me`'s interface."""
        socks = {}
        for (group, port), kind in ((SA_GROUP, "sa"), (CHAT_GROUP, "chat")):
            r = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
            r.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            r.bind(("", port))
            mreq = struct.pack("4s4s", socket.inet_aton(group), socket.inet_aton(me))
            r.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
            socks[r] = kind
        while time.time() < self.end:
            ready, _, _ = select.select(list(socks), [], [], 1)
            for r in ready:
                buf, (src, _) = r.recvfrom(65535)
                if src != me:
                    self.heard("mcast", buf, src)

    def heard(self, path: str, buf: bytes, src: str | None) -> None:
        """Log one received event: chats by id and text, SA by uid only."""
        text = buf.decode("utf-8", "replace")  # binary bytes become U+FFFD
        kind = "chat" if "b-t-f" in text[:400] else None
        if kind is None and re.search(r"a-f-G-U-C", text[:400]):
            kind = "sa"
        if kind is None:
            return
        uid = _field(r'uid="([^"]+)"', text)
        if kind == "sa":
            if uid and uid != self.uid and not uid.endswith("-ping"):
                self.log(path, "rx-sa", uid=uid, src=src)
            elif uid is None and buf[:1] == b"\xbf":
                self.log(path, "rx-sa", uid=_proto_uid(text), src=src)
            return
        mid = _field(r'messageId="([^"]+)"', text)
        sender = _field(r'senderCallsign="([^"]+)"', text)
        if sender == self.callsign:
            return
        body = _field(r"<remarks[^>]*>([^<]*)</remarks>", text)
        self.log(path, "rx-chat", messageId=mid, sender=sender, text=body, src=src)

    # --- sending chat -------------------------------------------------------

    def send_chat(self, tx: socket.socket, path: str, text: str) -> None:
        """Send one chat on one path and log it, or log why it was not sent."""
        body, mid = self.chat(text)
        if path == "m":
            tx.sendto(body, CHAT_GROUP)
            self.log("mcast", "tx-chat", messageId=mid, text=text)
            return
        s = self.stream
        if s is None:
            self.log(
                "server",
                "tx-chat-skipped",
                messageId=mid,
                text=text,
                reason="no stream",
            )
            return
        try:
            with self.lock:
                s.sendall(body)
            self.log("server", "tx-chat", messageId=mid, text=text)
        except OSError as e:
            self.log(
                "server", "tx-chat-failed", messageId=mid, text=text, reason=str(e)[:80]
            )

    def run(self) -> None:
        """Start the stream and multicast loops, then send chats on schedule."""
        a = self.a
        probe = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        probe.connect((a.host, 9))
        me = probe.getsockname()[0]  # the address facing the server
        probe.close()
        tx = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        tx.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 1)
        tx.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_LOOP, 0)
        mcast = a.role == "partitioned"
        if mcast:
            tx.setsockopt(
                socket.IPPROTO_IP, socket.IP_MULTICAST_IF, socket.inet_aton(me)
            )
            threading.Thread(target=self.mcast_loop, args=(me,), daemon=True).start()
        self.log(
            "local",
            "start",
            iface=me,
            callsign=self.callsign,
            uid=self.uid,
            mcast=mcast,
            chat_every=a.chat_every,
            sa_every=a.sa_every,
            rx_timeout=a.rx_timeout,
        )
        threading.Thread(target=self.stream_loop, daemon=True).start()
        paths = ["m", "s"] if mcast else ["s"]
        seq, n_sa = 0, 0
        next_sa, next_chat = 0.0, time.time() + a.chat_every
        req = os.path.join(a.ctl, "chat.req") if a.ctl else None
        while time.time() < self.end:
            now = time.time()
            if mcast and now >= next_sa:
                tx.sendto(self.sa(n_sa), SA_GROUP)
                self.log("mcast", "tx-sa", n=n_sa)
                n_sa, next_sa = n_sa + 1, now + a.sa_every
            if a.chat_every and now >= next_chat:
                path = paths[seq % len(paths)]
                self.send_chat(tx, path, f"{a.tag} {path} {seq:03d}")
                seq, next_chat = seq + 1, now + a.chat_every
            if req and os.path.exists(req):
                with open(req) as f:
                    text = f.read().strip()[:120]
                os.remove(req)
                self.send_chat(tx, "m" if mcast else "s", text)
            time.sleep(0.2)
        self.log("local", "done")


def _field(pat: str, text: str) -> str | None:
    m = re.search(pat, text)
    return m.group(1) if m else None


def _proto_uid(text: str) -> str | None:
    """Return a TAK-protocol SA's uid: its first long printable non-CoT-type run."""
    for m in re.finditer(r"[\w.:-]{12,}", text):
        if not m.group(0).startswith(("a-f-", "h-g-", "m-g")):
            return m.group(0).lstrip(".")  # a length byte can read as "."
    return None


def main() -> None:
    """Parse the arguments and run one EUD."""
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("--role", choices=["partitioned", "control"], required=True)
    p.add_argument("--host", required=True)
    p.add_argument("--port", type=int, default=8089)
    p.add_argument("--cert", required=True)
    p.add_argument("--key", required=True)
    p.add_argument("--ca", required=True)
    p.add_argument("--seconds", type=float, required=True)
    p.add_argument("--log", required=True)
    p.add_argument("--ctl", default=None)
    p.add_argument("--chat-every", type=float, default=20)
    p.add_argument("--sa-every", type=float, default=5)
    p.add_argument("--rx-timeout", type=float, default=25, help="WinTAK uses 25 s")
    p.add_argument("--retry", type=float, default=5)
    a = p.parse_args()
    defaults = {
        "partitioned": ("FML-EUD-SIM", "FML-EUD-SIM-UID", "sim"),
        "control": ("FML-CTL-SIM", "FML-CTL-SIM-UID", "ctl"),
    }
    a.callsign, a.uid, a.tag = defaults[a.role]
    Eud(a).run()


if __name__ == "__main__":
    main()
