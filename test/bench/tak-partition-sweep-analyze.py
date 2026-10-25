#!/usr/bin/env python3
"""Replay a partition sweep against candidate detection thresholds.

  tak-partition-sweep-analyze.py --cut CUT.log --probe PROBE.jsonl
      [--clients LOG.jsonl ...] [--sessions S.jsonl --watch NAME=IP ...]

The TBR-HA-01 decision packet leaves a node's partition entry threshold, exit
threshold and hold time "TBD, set by measurement". This reads one sweep (the
cut script's log of cuts from seconds to minutes) and one probe log, and
reports, for each candidate setting:

- entry E: the node declares a partition when no probe has been relayed for
  E seconds;
- exit K: it declares the partition over at the K-th consecutive relayed
  probe;

which cuts it enters on, how long after each cut began, how long after each
lift it exits, and how often it enters with no cut at all (a false partition).
Beside that it reports what the clients did in each cut, because a partition
the clients never notice is one the node need not declare. It prints Markdown.
"""

from __future__ import annotations

import argparse
import json
import re
import statistics
from collections import defaultdict
from datetime import UTC, datetime

ENTRY = (2, 3, 5, 8, 10, 15, 20, 30)
EXIT = (1, 3)
CLIENT_DOWN = {"disconnected", "connect-attempt", "stream-silent"}
CLIENT_UP = {"connected", "stream-up"}
Cuts = list[tuple[float, float, int]]  # (on, off, planned seconds)


def t_of(s: str) -> float:
    """Parse an ISO-8601 UTC timestamp to epoch seconds."""
    return datetime.fromisoformat(s.replace("Z", "+00:00")).timestamp()


def hms(t: float) -> str:
    """Format epoch seconds as UTC HH:MM:SS."""
    return datetime.fromtimestamp(t, UTC).strftime("%H:%M:%S")


def read_cuts(path: str) -> Cuts:
    """Return (on, off, planned seconds) for each sweep cut in the log."""
    cuts, on, planned = [], None, 0
    for line in open(path):
        stamp, _, rest = line.strip().partition(" ")
        m = re.match(r"cut on \(sweep (\d+) s\)", rest)
        if m:
            on, planned = t_of(stamp), int(m.group(1))
        elif rest.startswith("cut off") and on is not None:
            cuts.append((on, t_of(stamp), planned))
            on = None
    return cuts


def sweep_end(path: str) -> float | None:
    """Return when the sweep finished, if the log says; a relay stops there."""
    for line in open(path):
        stamp, _, rest = line.strip().partition(" ")
        if rest == "sweep done":
            return t_of(stamp)
    return None


def read_jsonl(path: str) -> list[dict]:
    """Read JSON lines, adding epoch seconds as 'ts'."""
    out = []
    for line in open(path):
        if line.strip():
            e = json.loads(line)
            e["ts"] = t_of(e["t"])
            out.append(e)
    return out


def replay(
    rx: list[tuple[float, int]], end: float, entry: float, k: int
) -> list[tuple[float, float | None]]:
    """Run one setting over the relayed probes; return (entered, exited) spans."""
    spans, entered, last, run, prev_seq = [], None, rx[0][0], 0, None
    for t, seq in rx:
        if entered is None and t - last >= entry:
            entered, run = last + entry, 0
        if entered is not None:
            run = run + 1 if prev_seq is not None and seq == prev_seq + 1 else 1
            if run >= k:
                spans.append((entered, t))
                entered = None
        last, prev_seq = t, seq
    if entered is None and end - last >= entry:
        entered = last + entry
    if entered is not None:
        spans.append((entered, None))
    return spans


def which_cut(t: float, cuts: Cuts, slack: float) -> int | None:
    """Index of the cut whose span (plus slack after the lift) holds t."""
    for i, (on, off, _) in enumerate(cuts):
        if on <= t <= off + slack:
            return i
    return None


def baseline(probe: list[dict], cuts: Cuts) -> list[str]:
    """Round-trip times and losses with no cut in force."""
    tx = {e["seq"]: e["ts"] for e in probe if e["event"] == "probe-tx"}
    rx = {e["seq"]: e["ts"] for e in probe if e["event"] == "probe-rx"}

    def clear(t: float) -> bool:
        return all(not (on - 1 <= t <= off + 60) for on, off, _ in cuts)

    sent = [s for s, t in tx.items() if clear(t)]
    rtt = sorted(1000 * (rx[s] - tx[s]) for s in sent if s in rx)
    lost = len(sent) - len(rtt)
    if not rtt:
        return ["No probe was relayed outside the cuts."]
    p99 = rtt[min(len(rtt) - 1, int(0.99 * len(rtt)))]
    return [
        "## Probe with no cut in force",
        "",
        f"{len(sent)} probes, {lost} not relayed. Round trip: median "
        f"{statistics.median(rtt):.0f} ms, 99th percentile {p99:.0f} ms, "
        f"max {rtt[-1]:.0f} ms.",
    ]


def settings(probe: list[dict], cuts: Cuts) -> list[str]:
    """Build the candidate-setting table."""
    rx = sorted((e["ts"], e["seq"]) for e in probe if e["event"] == "probe-rx")
    end = max(e["ts"] for e in probe)
    lens = " | ".join(f"{p} s" for _, _, p in cuts)
    out = [
        "## Candidate settings",
        "",
        "Each cell: seconds from cut start to entry / seconds from lift to exit; "
        "`-` means no entry. False: entries with no cut.",
        "",
        f"| entry E | exit K | {lens} | false |",
        "| ---: | ---: | " + " | ".join("---" for _ in cuts) + " | ---: |",
    ]
    for entry in ENTRY:
        for k in EXIT:
            cells, false = ["-"] * len(cuts), 0
            for entered, exited in replay(rx, end, entry, k):
                i = which_cut(entered, cuts, slack=5)
                if i is None:
                    false += 1
                    continue
                on, off, _ = cuts[i]
                ex = "never" if exited is None else f"{exited - off:.1f}"
                cells[i] = f"{entered - on:.1f} / {ex}"
            out.append(f"| {entry} | {k} | " + " | ".join(cells) + f" | {false} |")
    return out


def clients(logs: list[list[dict]], cuts: Cuts) -> list[str]:
    """Report what each client did in each cut: dropped or not, and when back."""
    rows = defaultdict(dict)
    for events in logs:
        for e in events:
            who = e.get("who", "?")
            if who.startswith("probe"):
                continue
            i = which_cut(e["ts"], cuts, slack=90)
            if i is None:
                continue
            on, off, _ = cuts[i]
            cell = rows[who].setdefault(i, {"down": None, "up": None})
            if (
                e["event"] in CLIENT_DOWN
                and cell["down"] is None
                and e["ts"] <= off + 1
            ):
                cell["down"] = e["ts"] - on
            if (
                e["event"] in CLIENT_UP
                and e["ts"] >= off
                and cell["down"] is not None
                and cell["up"] is None
            ):
                cell["up"] = e["ts"] - off
    lens = " | ".join(f"{p} s" for _, _, p in cuts)
    out = [
        "## What the clients did",
        "",
        "Each cell: seconds from cut start to the client noticing / seconds "
        "from lift to its stream back; `kept` means it never noticed.",
        "",
        f"| client | {lens} |",
        "| --- | " + " | ".join("---" for _ in cuts) + " |",
    ]
    for who in sorted(rows):
        cells = []
        for i in range(len(cuts)):
            c = rows[who].get(i)
            if not c or c["down"] is None:
                cells.append("kept")
            else:
                up = "-" if c["up"] is None else f"{c['up']:.1f}"
                cells.append(f"{c['down']:.1f} / {up}")
        out.append(f"| {who} | " + " | ".join(cells) + " |")
    return out


def sessions(path: str, watch: dict[str, str], cuts: Cuts) -> list[dict]:
    """Turn sampled server sessions into client events: a new port is a reconnect."""
    events, seen = [], {}
    for line in open(path):
        s = json.loads(line)
        ts = t_of(s["t"])
        for name, ip in watch.items():
            ports = {p["peer"] for p in s["peers"] if p["peer"].startswith(ip + ":")}
            new = ports - seen.get(name, ports)
            if new and name in seen:
                events.append({"who": name, "event": "connected", "ts": ts})
                i = which_cut(ts, cuts, slack=90)
                if i is not None:
                    events.append(
                        {"who": name, "event": "disconnected", "ts": cuts[i][0]}
                    )
            seen[name] = ports
    return events


def main() -> None:
    """Parse the arguments and print the report."""
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--cut", required=True)
    p.add_argument("--probe", required=True)
    p.add_argument("--clients", nargs="*", default=[])
    p.add_argument("--sessions")
    p.add_argument(
        "--watch", nargs="*", default=[], help="NAME=IP clients seen only by the server"
    )
    a = p.parse_args()
    cuts = read_cuts(a.cut)
    end = sweep_end(a.cut)
    probe = [e for e in read_jsonl(a.probe) if end is None or e["ts"] <= end]
    logs = [read_jsonl(f) for f in a.clients]
    if a.sessions and a.watch:
        logs.append(sessions(a.sessions, dict(w.split("=", 1) for w in a.watch), cuts))
    out = [
        "# Partition detection sweep",
        "",
        "| cut | planned | on | actual |",
        "| ---: | ---: | --- | ---: |",
    ]
    out += [
        f"| {i + 1} | {pl} s | {hms(on)} | {off - on:.1f} s |"
        for i, (on, off, pl) in enumerate(cuts)
    ]
    out += ["", *baseline(probe, cuts), "", *settings(probe, cuts), ""]
    out += clients(logs, cuts)
    print("\n".join(out))


if __name__ == "__main__":
    main()
