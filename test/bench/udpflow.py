#!/usr/bin/env python3
"""A tiny UDP flow generator and receiver for the mesh transport bench.

Used by ``test/bench/mesh-traffic.sh``. Stdlib only, so it needs nothing
installed on the bench beyond the interpreter already present.

Two profiles model the two traffic classes CONOPS section 40 distinguishes:

* ``voice`` -- a real-time flow: small packets at a fixed cadence (defaults
  ~160 bytes every 20 ms, an Opus-like profile). Its cost is jitter and loss,
  not throughput.
* ``bulk`` -- a saturating flow: large packets sent as fast as the socket
  accepts them, standing in for video or file synchronisation.

The receiver reports one-way latency, jitter and loss. One-way latency is
meaningful here **only because** the bench runs every node in a network
namespace on one host, so sender and receiver read the same system clock. On
two real nodes this number would be a clock-offset artefact; the bench is what
makes it valid, and the evidence artifact says so. See docs/dev-machine.md.

Not a decision about a wire format, a codec or a QoS mechanism: it is an
instrument for the bench, cited from docs/evidence/TBR-RF-01/. CONOPS section 40;
TBR-RF-01; FML-ADR-021 (one compute element, so routing and a bulk flow compete).
"""

from __future__ import annotations

import argparse
import json
import socket
import struct
import sys
import time

# seq (uint64) then send time (double seconds). Big-endian, fixed 16 bytes, so
# the receiver can find both in any payload at least this large.
HEADER = struct.Struct("!Qd")


def _send(args: argparse.Namespace) -> int:
    """Send a voice- or bulk-profile UDP flow for a fixed duration."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    if args.dscp is not None:
        # IP_TOS carries the DSCP in its high six bits, so the value shifts left
        # by two. EF (voice) is DSCP 46 -> TOS 0xB8. This is what a QoS filter
        # on the mesh egress would match; marking here lets the bench show a
        # mitigation without asserting one is the decision (TBR-RF-01 owns that).
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_TOS, args.dscp << 2)

    payload = bytearray(args.size)
    deadline = time.time() + args.duration
    seq = 0
    sent = 0
    while time.time() < deadline:
        HEADER.pack_into(payload, 0, seq, time.time())
        try:
            sock.sendto(payload, (args.host, args.port))
            sent += 1
        except OSError:
            # A saturating bulk flow can fill the socket buffer; that is the
            # contention the bench is creating, not an error to abort on.
            pass
        seq += 1
        if args.interval > 0:
            time.sleep(args.interval)
    sock.close()
    print(json.dumps({"role": "send", "profile": args.profile, "sent": sent}))
    return 0


def _recv(args: argparse.Namespace) -> int:
    """Receive a flow and report one-way latency, jitter and loss."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 4 << 20)
    # Binds all interfaces on purpose: this runs inside an isolated bench network
    # namespace with one address, not on a real node. noqa: S104 (bench only).
    sock.bind(("0.0.0.0", args.port))  # noqa: S104
    sock.settimeout(args.timeout)

    latencies_ms: list[float] = []
    seqs: list[int] = []
    while True:
        try:
            data, _ = sock.recvfrom(65535)
        except TimeoutError:
            break
        recv_time = time.time()
        if len(data) < HEADER.size:
            continue
        seq, send_time = HEADER.unpack_from(data, 0)
        seqs.append(seq)
        latencies_ms.append((recv_time - send_time) * 1000.0)
    sock.close()

    summary = _summarize(latencies_ms, seqs)
    summary["role"] = "recv"
    print(json.dumps(summary))
    return 0


def _summarize(latencies_ms: list[float], seqs: list[int]) -> dict[str, object]:
    """Reduce received samples to loss, latency and jitter figures.

    Loss is measured against the sender's sequence span (max seq seen minus min
    plus one), so a flow that never arrives at all reports as fully lost rather
    than as a clean run of zero packets. Jitter is the mean absolute difference
    of successive one-way delays -- the RFC 3550 sense, the quantity a jitter
    buffer sizes against.
    """
    received = len(latencies_ms)
    if received == 0:
        return {"received": 0, "expected": None, "loss_pct": None}

    expected = max(seqs) - min(seqs) + 1
    loss_pct = round(100.0 * (expected - received) / expected, 2) if expected else 0.0
    jitter = 0.0
    if received > 1:
        diffs = [abs(latencies_ms[i] - latencies_ms[i - 1]) for i in range(1, received)]
        jitter = sum(diffs) / len(diffs)
    return {
        "received": received,
        "expected": expected,
        "loss_pct": loss_pct,
        "latency_ms_min": round(min(latencies_ms), 3),
        "latency_ms_avg": round(sum(latencies_ms) / received, 3),
        "latency_ms_max": round(max(latencies_ms), 3),
        "jitter_ms": round(jitter, 3),
    }


def _parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="mode", required=True)

    send = sub.add_parser("send", help="send a flow")
    send.add_argument("--profile", choices=["voice", "bulk"], required=True)
    send.add_argument("--host", required=True)
    send.add_argument("--port", type=int, default=5001)
    send.add_argument("--duration", type=float, default=10.0)
    send.add_argument("--interval", type=float, help="seconds between packets")
    send.add_argument("--size", type=int, help="payload bytes")
    send.add_argument("--dscp", type=int, default=None, help="DSCP to mark, e.g. 46=EF")
    send.set_defaults(func=_send)

    recv = sub.add_parser("recv", help="receive a flow and report")
    recv.add_argument("--port", type=int, default=5001)
    recv.add_argument("--timeout", type=float, default=3.0, help="idle seconds to stop")
    recv.set_defaults(func=_recv)

    args = parser.parse_args(argv)
    if args.mode == "send":
        # Profile defaults, overridable for experiments.
        if args.interval is None:
            args.interval = 0.02 if args.profile == "voice" else 0.0
        if args.size is None:
            args.size = 160 if args.profile == "voice" else 1400
    return args


def main(argv: list[str]) -> int:
    args = _parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
