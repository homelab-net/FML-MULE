#!/usr/bin/env python3
"""An application-level probe of a TAK server, for partition detection.

  tak-partition-probe.py --host H --cert C --key K --ca CA --seconds N
                         --log OUT.jsonl [--every 1] [--rx-timeout 5]

The TBR-HA-01 decision packet (option A, parameter 2) detects a partition with
"a TLS session plus an SA round trip", because a port check once passed 13 s
before the server relayed anything. This is that probe, as a bench instrument.

It holds two mutual-TLS sessions to the server, ``tx`` and ``rx``, each with
its own synthetic uid. Every ``--every`` seconds ``tx`` sends an SA whose
remarks carry a sequence number, and ``rx`` logs the moment the server relays
it. Each session also gives up on a silent stream after ``--rx-timeout``
seconds and reconnects, as a node's probe would. Both sessions send SA at the
same rate, so each always has traffic to hear while the server relays.

The probe decides nothing. It logs every send, every relay and every session
event as JSON lines, and the sweep analyzer replays that log against candidate
entry and exit thresholds, so one run scores many settings. The identities
and the point are synthetic.
"""

from __future__ import annotations

import argparse
import json
import re
import socket
import ssl
import threading
import time
from datetime import UTC, datetime, timedelta

LAT, LON = 38.8339, -104.8214  # the bench's synthetic point
UIDS = {"tx": "FML-PROBE-TX", "rx": "FML-PROBE-RX"}
PROBE = re.compile(rb'uid="FML-PROBE-TX".*?<remarks>probe (\d+)</remarks>', re.S)


def ts(off: float = 0.0) -> str:
    """Return a CoT timestamp, UTC with milliseconds."""
    t = datetime.now(UTC) + timedelta(seconds=off)
    return t.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"


def sa(uid: str, remarks: str) -> bytes:
    """Build a minimal SA, which the server relays to every other client."""
    return (
        f'<event version="2.0" uid="{uid}" type="a-f-G-U-C" how="m-g" '
        f'time="{ts()}" start="{ts()}" stale="{ts(30)}">'
        f'<point lat="{LAT:.7f}" lon="{LON:.7f}" hae="1800.0" ce="10" le="10"/>'
        f'<detail><contact callsign="{uid}"/><remarks>{remarks}</remarks></detail>'
        "</event>"
    ).encode()


class Probe:
    """Two sessions, one sequence counter, one log."""

    def __init__(self, a: argparse.Namespace) -> None:
        """Open the log and the TLS context; no connection yet."""
        self.a = a
        self.lock = threading.Lock()
        self.log_f = open(a.log, "a")
        self.end = time.time() + a.seconds
        self.ctx = ssl.create_default_context(cafile=a.ca)
        self.ctx.check_hostname = False  # bench servers are CN=takserver
        self.ctx.load_cert_chain(a.cert, a.key)
        self.live: dict[str, ssl.SSLSocket | None] = {"tx": None, "rx": None}
        self.seq = -1  # the current tick; each session sends once per tick

    def log(self, who: str, event: str, **kw: object) -> None:
        """Append one timestamped JSON line."""
        with self.lock:
            line = {"t": ts(), "who": f"probe-{who}", "event": event, **kw}
            self.log_f.write(json.dumps(line) + "\n")
            self.log_f.flush()

    def connect(self, who: str) -> ssl.SSLSocket | None:
        """One connection attempt, logged either way."""
        try:
            raw = socket.create_connection(
                (self.a.host, self.a.port), timeout=self.a.connect_timeout
            )
            s = self.ctx.wrap_socket(raw, server_hostname=self.a.host)
        except (OSError, ssl.SSLError) as e:
            self.log(who, "connect-failed", reason=f"{type(e).__name__}: {e}"[:100])
            return None
        s.settimeout(0.2)
        self.log(who, "connected", local=s.getsockname()[1])
        return s

    def session_loop(self, who: str) -> None:
        """Keep one session up for the whole run."""
        while time.time() < self.end:
            s = self.connect(who)
            if s is None:
                time.sleep(self.a.retry)
                continue
            self.live[who] = s
            try:
                self.serve(who, s)
            except (OSError, ssl.SSLError, TimeoutError, ConnectionError) as e:
                self.log(who, "disconnected", reason=f"{type(e).__name__}: {e}"[:100])
            self.live[who] = None
            try:
                s.close()
            except OSError:
                pass
            time.sleep(self.a.retry)

    def serve(self, who: str, s: ssl.SSLSocket) -> None:
        """Hear one session until it is silent for too long or fails."""
        buf, last_rx, sent = b"", time.time(), None
        while time.time() < self.end:
            seq = self.seq
            if (
                seq != sent and seq >= 0
            ):  # sends stay on this thread: an SSL socket is not thread-safe
                s.sendall(sa(UIDS[who], f"probe {seq}" if who == "tx" else "keepalive"))
                if who == "tx":
                    self.log(who, "probe-tx", seq=seq)
                sent = seq
            if time.time() - last_rx > self.a.rx_timeout:
                raise TimeoutError(f"nothing received for {self.a.rx_timeout} s")
            try:
                data = s.recv(65536)
            except TimeoutError:
                continue
            if not data:
                raise ConnectionError("closed by server")
            last_rx, buf = time.time(), buf + data
            while b"</event>" in buf:
                event, buf = buf.split(b"</event>", 1)
                m = PROBE.search(event)
                if who == "rx" and m:
                    self.log(who, "probe-rx", seq=int(m.group(1)))

    def tick_loop(self) -> None:
        """Advance the tick every interval; a tick with no tx session is a failure."""
        next_t = time.time()
        while time.time() < self.end:
            self.seq += 1
            if self.live["tx"] is None:
                self.log("tx", "probe-skipped", seq=self.seq, reason="no session")
            next_t += self.a.every
            time.sleep(max(0.0, next_t - time.time()))

    def run(self) -> None:
        """Run both sessions and the tick until the time is up."""
        self.log(
            "tx",
            "start",
            every=self.a.every,
            rx_timeout=self.a.rx_timeout,
            connect_timeout=self.a.connect_timeout,
            retry=self.a.retry,
        )
        threads = [
            threading.Thread(target=self.session_loop, args=(w,), daemon=True)
            for w in UIDS
        ]
        for t in threads:
            t.start()
        self.tick_loop()
        for t in threads:
            t.join(timeout=self.a.rx_timeout + 2)
        self.log("tx", "done")


def main() -> None:
    """Parse the arguments and run the probe."""
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--host", required=True)
    p.add_argument("--port", type=int, default=8089)
    p.add_argument("--cert", required=True)
    p.add_argument("--key", required=True)
    p.add_argument("--ca", required=True)
    p.add_argument("--seconds", type=float, required=True)
    p.add_argument("--log", required=True)
    p.add_argument("--every", type=float, default=1.0, help="probe interval, s")
    p.add_argument(
        "--rx-timeout", type=float, default=5.0, help="give up on a silent session, s"
    )
    p.add_argument("--connect-timeout", type=float, default=3.0)
    p.add_argument(
        "--retry", type=float, default=1.0, help="wait before reconnecting, s"
    )
    Probe(p.parse_args()).run()


if __name__ == "__main__":
    main()
