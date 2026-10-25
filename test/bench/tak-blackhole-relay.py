#!/usr/bin/env python3
"""A TCP relay in front of a TAK server that goes silent on a schedule.

  tak-blackhole-relay.py --listen 18089 --to 127.0.0.1:8089 --log CUT.log
                         --sweep "5 10 15" --gap 75 [--baseline 60]

A no-root stand-in for tak-partition-cut.sh's nftables drop, for clients that
connect through it (the TLS passes through untouched). During a cut it stops
moving bytes in both directions and stops accepting, but closes nothing, so a
client sees a silent partition: its sends back up, nothing arrives, and a new
connection completes TCP in the kernel backlog but its TLS handshake hangs.
After the lift, traffic held in socket buffers flows again, as TCP
retransmission would deliver it after a real drop.

Differences from the nftables cut, stated so results are read correctly: only
clients that use this port are cut; connections queued during a cut are
accepted at the lift even if their client has given up. The cut log uses the
cut script's format, so the sweep analyzer reads either.
"""

from __future__ import annotations

import argparse
import selectors
import socket
import threading
import time
from datetime import UTC, datetime


class Relay:
    """Accept, pair each client with a server socket, and pump bytes unless cut."""

    def __init__(self, a: argparse.Namespace) -> None:
        """Open the listener; the sweep runs on its own thread."""
        self.a = a
        self.cut = threading.Event()
        self.sel = selectors.DefaultSelector()
        self.peer: dict[socket.socket, socket.socket] = {}
        host, port = a.to.rsplit(":", 1)
        self.target = (host, int(port))
        # Remote bench clients connect to it, so it listens on every interface.
        self.lsock = socket.create_server(("0.0.0.0", a.listen), backlog=64)  # noqa: S104
        self.lsock.setblocking(False)
        self.sel.register(self.lsock, selectors.EVENT_READ)

    def record(self, text: str) -> None:
        """Append one transition with a UTC millisecond timestamp."""
        stamp = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
        with open(self.a.log, "a") as f:
            f.write(f"{stamp} {text}\n")
        print(f"{stamp} {text}", flush=True)

    def sweep(self) -> None:
        """Baseline, then each cut and its gap; then stop."""
        lens = [int(s) for s in self.a.sweep.split()]
        self.record(
            f"sweep: {self.a.baseline} s baseline, cuts of {self.a.sweep} s, "
            f"{self.a.gap} s apart (relay)"
        )
        time.sleep(self.a.baseline)
        for s in lens:
            self.cut.set()
            self.record(f"cut on (sweep {s} s)")
            time.sleep(s)
            self.cut.clear()
            self.record("cut off (sweep)")
            time.sleep(self.a.gap)
        self.record("sweep done")

    def accept(self) -> None:
        """Pair one new client with a fresh server connection."""
        c, _ = self.lsock.accept()
        try:
            s = socket.create_connection(self.target, timeout=5)
        except OSError:
            c.close()
            return
        for x in (c, s):
            x.setblocking(False)
            self.sel.register(x, selectors.EVENT_READ)
        self.peer[c], self.peer[s] = s, c

    def close(self, x: socket.socket) -> None:
        """Close one pair."""
        y = self.peer.pop(x, None)
        for z in (x, y):
            if z is not None:
                self.peer.pop(z, None)
                try:
                    self.sel.unregister(z)
                except (KeyError, ValueError):
                    pass
                z.close()

    def pump(self, x: socket.socket) -> None:
        """Move what one side has to the other, blocking briefly if needed."""
        try:
            data = x.recv(65536)
        except (BlockingIOError, InterruptedError):
            return
        except OSError:
            self.close(x)
            return
        if not data:
            self.close(x)
            return
        y = self.peer.get(x)
        if y is None:
            return
        try:
            y.setblocking(True)
            y.settimeout(2)
            y.sendall(data)
            y.setblocking(False)
        except OSError:
            self.close(x)

    def run(self) -> None:
        """Serve until the sweep ends, plus a minute for clients to settle."""
        t = threading.Thread(target=self.sweep, daemon=True)
        t.start()
        while t.is_alive():
            if self.cut.is_set():
                time.sleep(0.05)  # silent: read nothing, accept nothing, close nothing
                continue
            for key, _ in self.sel.select(timeout=0.05):
                if key.fileobj is self.lsock:
                    self.accept()
                else:
                    self.pump(key.fileobj)


def main() -> None:
    """Parse the arguments and run the relay."""
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--listen", type=int, default=18089)
    p.add_argument("--to", default="127.0.0.1:8089")
    p.add_argument("--log", required=True)
    p.add_argument(
        "--sweep", required=True, help='cut lengths, seconds, e.g. "5 10 15"'
    )
    p.add_argument("--gap", type=int, default=75)
    p.add_argument("--baseline", type=int, default=60)
    Relay(p.parse_args()).run()


if __name__ == "__main__":
    main()
