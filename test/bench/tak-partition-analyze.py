#!/usr/bin/env python3
"""Score a TBR-HA-01 partition trial from its logs.

  tak-partition-analyze.py --cut CUT.log --sessions S.jsonl --wintak-ip IP
                           --eud-ip IP LOG.jsonl [LOG.jsonl ...]

Inputs:
- ``--cut``: the cut script's transition log (``/run/fml-partition-cut.log``);
- ``--sessions``: ``tak-session-sample.sh`` output from the server host;
- the JSON-lines logs of ``tak-partition-eud.py`` (partitioned and control)
  and of ``wintak-export.js``.

It splits the run into phases (``pre``, ``cut1``, ``heal1``, ``cut2``, ...)
and reports, per chat flow and phase, how many were sent and delivered and
how fast; SA gaps; how long each client took to notice the cut and to resume
its server stream after it; and how long the server held a cut client's old
session. Then it scores the four gate checks below. A check with nothing to
score is reported ``NOT EXERCISED``, never passed.

Hosts' clocks are NTP-disciplined but not compared here; latencies across
hosts carry that error (sub-second on this bench).
"""

from __future__ import annotations

import argparse
import itertools
import json
import statistics
from collections import defaultdict
from datetime import datetime

RESUME_LIMIT_S = 60  # A4: stream and first server message back within this
SA_SLACK_S = 5  # A2: allowed SA gap = 2 x baseline interval + this
WINTAK_UID = "S-1-5-"  # WinTAK's uid is its Windows account SID; this is the SID prefix
Cuts = list[tuple[float, float | None]]  # (on, off); off is None if never lifted
Flows = dict[tuple[str, str, str], list[tuple]]


def t_of(s: str) -> float:
    """Parse an ISO-8601 UTC timestamp to epoch seconds."""
    return datetime.fromisoformat(s.replace("Z", "+00:00")).timestamp()


def iso(t: float) -> str:
    """Format epoch seconds in this host's zone, to the second."""
    return datetime.fromtimestamp(t).astimezone().isoformat(timespec="seconds")


def load_cuts(path: str) -> Cuts:
    """Return (on, off) pairs from the cut log; off is None if never lifted."""
    cuts: Cuts = []
    for line in open(path):
        stamp, _, what = line.strip().partition(" ")
        if what.startswith("cut on"):
            cuts.append((t_of(stamp), None))
        elif what.startswith("cut off") and cuts and cuts[-1][1] is None:
            cuts[-1] = (cuts[-1][0], t_of(stamp))
    return cuts


def phase_of(t: float, cuts: Cuts) -> str:
    """Name the phase t falls in: pre, cutN or healN."""
    name = "pre"
    for i, (on, off) in enumerate(cuts, 1):
        if t >= on:
            name = f"cut{i}"
        if off is not None and t >= off:
            name = f"heal{i}"
    return name


def load_events(paths: list[str]) -> list[dict]:
    """Read every JSON-lines log, adding epoch seconds as 'ts', in time order."""
    out = []
    for p in paths:
        for line in open(p):
            line = line.strip()
            if line:
                ev = json.loads(line)
                ev["ts"] = t_of(ev["t"])
                out.append(ev)
    return sorted(out, key=lambda e: e["ts"])


def text_key(text: str | None) -> str | None:
    """Return a chat text as a match key: misread UTF-8 repaired, ends trimmed."""
    if not text:
        return None
    try:
        text = text.encode("latin-1").decode("utf-8")
    except (UnicodeEncodeError, UnicodeDecodeError):
        pass
    return text.strip() or None


def chat_flows(events: list[dict], cuts: Cuts) -> Flows:
    """Match every chat sent to each receiver that could hear it.

    Returns {(sender, path, receiver): [(phase, sent_ts, rx_ts | None,
    rx_phase, rx_path)]}.
    """
    receivers = {e["who"] for e in events}
    rx = defaultdict(list)  # (receiver, key) -> [(ts, path)]
    for e in events:
        if e["event"] == "rx-chat":
            for key in (e.get("messageId"), text_key(e.get("text"))):
                if key:
                    rx[(e["who"], key)].append((e["ts"], e.get("path")))
    flows = defaultdict(list)
    for e in events:
        if e["event"] not in ("tx-chat", "tx-chat-skipped", "tx-chat-failed"):
            continue
        sender = e["who"]
        path = {"mcast": "m", "server": "s"}.get(e.get("path"), "both")
        key = e.get("messageId") or text_key(e.get("text"))
        for r in receivers - {sender}:
            if path == "m" and r == "control":
                continue  # control has no multicast by design
            got = sorted(
                rx.get((r, key), []) + rx.get((r, text_key(e.get("text"))), [])
            )
            first = got[0] if got else None
            flows[(sender, path, r)].append(
                (
                    phase_of(e["ts"], cuts),
                    e["ts"],
                    first[0] if first else None,
                    phase_of(first[0], cuts) if first else None,
                    sorted({p for _, p in got if p}) or ([first[1]] if first else []),
                    e["event"],
                )
            )
    return flows


def summarize_flows(flows: Flows) -> list[str]:
    """Tabulate delivery per flow and phase."""
    out = [
        "## Chat delivery, by flow and phase",
        "",
        "| sender | path | receiver | phase | sent | delivered in phase | later "
        "| never | median s | max s |",
        "| --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for (snd, path, rcv), rows in sorted(flows.items()):
        by_phase = defaultdict(list)
        for row in rows:
            by_phase[row[0]].append(row)
        for ph, rs in by_phase.items():
            same = [r for r in rs if r[2] is not None and r[3] == ph]
            later = [r for r in rs if r[2] is not None and r[3] != ph]
            never = [r for r in rs if r[2] is None]
            lat = [r[2] - r[1] for r in same]
            med = f"{statistics.median(lat):.1f}" if lat else "-"
            mx = f"{max(lat):.1f}" if lat else "-"
            out.append(
                f"| {snd} | {path} | {rcv} | {ph} | {len(rs)} | {len(same)} | "
                f"{len(later)} | {len(never)} | {med} | {mx} |"
            )
    return out


def sa_gaps(events: list[dict], cuts: Cuts) -> tuple[list[str], dict]:
    """Largest gap between SA receptions, per (receiver, path, source) and phase."""
    seen = defaultdict(list)
    for e in events:
        if e["event"] == "rx-sa":
            src = "wintak" if WINTAK_UID in (e.get("uid") or "") else e.get("uid")
            seen[(e["who"], e["path"], src)].append(e["ts"])
    out = [
        "## SA reception, largest gap per phase (s)",
        "",
        "| receiver | path | from | phase | received | median interval | largest gap |",
        "| --- | --- | --- | --- | ---: | ---: | ---: |",
    ]
    result = {}
    for k, ts in sorted(seen.items(), key=lambda kv: str(kv[0])):
        ts = sorted(
            set(round(t, 1) for t in ts)
        )  # one per send: WinTAK sends on two NICs
        by_phase = defaultdict(list)
        for t in ts:
            by_phase[phase_of(t, cuts)].append(t)
        for ph, pts in by_phase.items():
            gaps = [b - a for a, b in itertools.pairwise(pts)]
            med = statistics.median(gaps) if gaps else None
            mx = max(gaps) if gaps else None
            result[(k, ph)] = (len(pts), med, mx)
            out.append(
                f"| {k[0]} | {k[1]} | {k[2]} | {ph} | {len(pts)} | "
                f"{med if med is None else round(med, 1)} | "
                f"{mx if mx is None else round(mx, 1)} |"
            )
    return out, result


def stream_timing(events: list[dict], cuts: Cuts) -> tuple[list[str], dict]:
    """Per cut: when each client noticed, and when its stream came back."""
    # WinTAK logs either a silence timeout or, if the socket errors first, a reconnect
    lost = {
        "wintak": ("stream-silent", "connect-attempt"),
        "partitioned": ("disconnected",),
        "control": ("disconnected",),
    }
    up = {"wintak": "stream-up", "partitioned": "connected", "control": "connected"}
    out = [
        "## Server stream: noticing the cut and resuming",
        "",
        "| cut | client | noticed after (s) | resumed after lift (s) |",
        "| --- | --- | ---: | ---: |",
    ]
    res = {}
    for i, (on, off) in enumerate(cuts, 1):
        for who in lost:
            n = next(
                (
                    e["ts"] - on
                    for e in events
                    if e["who"] == who
                    and e["event"] in lost[who]
                    and on <= e["ts"]
                    and (off is None or e["ts"] <= off)
                ),
                None,
            )
            r = None
            if off is not None:
                r = next(
                    (
                        e["ts"] - off
                        for e in events
                        if e["who"] == who and e["event"] == up[who] and e["ts"] >= off
                    ),
                    None,
                )
            res[(i, who)] = (n, r)
            fmt = lambda v: "-" if v is None else f"{v:.1f}"  # noqa: E731
            out.append(f"| {i} | {who} | {fmt(n)} | {fmt(r)} |")
    return out, res


def stale_sessions(path: str, cuts: Cuts, ips: dict[str, str]) -> list[str]:
    """Report how long the server kept each cut client's pre-cut session open."""
    samples = [
        (t_of(j["t"]), [p["peer"] for p in j["peers"]])
        for j in map(json.loads, open(path))
    ]
    out = [
        "## Server-side sessions of cut clients",
        "",
        "| cut | client | pre-cut session held after cut (s) "
        "| new session after lift (s) |",
        "| --- | --- | ---: | ---: |",
    ]
    for i, (on, off) in enumerate(cuts, 1):
        for name, ip in ips.items():
            before = [
                s
                for t, peers in samples
                if t < on
                for s in peers
                if s.startswith(ip + ":")
            ]
            old = before[-1] if before else None
            held = None
            if old:
                gone = next(
                    (t for t, peers in samples if t >= on and old not in peers), None
                )
                held = (gone - on) if gone else None
            new = None
            if off is not None:
                new_t = next(
                    (
                        t
                        for t, peers in samples
                        if t >= off
                        and any(p.startswith(ip + ":") and p != old for p in peers)
                    ),
                    None,
                )
                new = (new_t - off) if new_t else None
            fmt = lambda v: "-" if v is None else f"{v:.0f}"  # noqa: E731
            held_s = fmt(held) if old else "no session"
            if old and held is None:
                held_s = "still open at end"
            out.append(f"| {i} | {name} | {held_s} | {fmt(new)} |")
    return out


def verdicts(flows: Flows, sa: dict, timing: dict, cuts: Cuts) -> list[str]:
    """Score gate checks A1 to A4, and report what the far side said in a cut."""

    def rows(snd: str, path: str, rcv: str) -> list[tuple]:
        return flows.get((snd, path, rcv), [])

    def in_cut(r: tuple) -> bool:
        return r[0].startswith("cut")

    out = ["## Gate checks", ""]
    # A1: peer chat during the cut, both directions between the cut clients.
    a = [r for r in rows("partitioned", "m", "wintak") if in_cut(r)]
    b = [r for r in rows("wintak", "both", "partitioned") if in_cut(r)]
    b_mcast = [r for r in b if r[2] is not None and "mcast" in r[4]]
    if not a or not b:
        a1 = "NOT EXERCISED" + ("" if b else " (no WinTAK chat sent during a cut)")
    else:
        ok = all(r[2] is not None for r in a) and len(b_mcast) == len(b)
        a1 = "PASS" if ok else "FAIL"
    out.append(
        f"- **A1 peer chat during the cut, both ways:** {a1}. "
        f"Simulated EUD to WinTAK {sum(r[2] is not None for r in a)}/{len(a)}; "
        f"WinTAK to simulated EUD on multicast {len(b_mcast)}/{len(b)}."
    )
    # A2: WinTAK's multicast SA keeps arriving at the partitioned EUD.
    key = ("partitioned", "mcast", "wintak")
    base = sa.get((key, "pre"))
    worst = [
        sa[(key, f"cut{i}")] for i in range(1, len(cuts) + 1) if (key, f"cut{i}") in sa
    ]
    if not base or not worst or base[1] is None:
        a2 = "NOT EXERCISED"
    else:
        limit = 2 * base[1] + SA_SLACK_S
        a2 = (
            "PASS" if all(w[2] is not None and w[2] <= limit for w in worst) else "FAIL"
        )
        a2 += (
            f" (largest gap {max(w[2] or 0 for w in worst):.0f} s, limit {limit:.0f} s)"
        )
    out.append(f"- **A2 peer SA during the cut (WinTAK to simulated EUD):** {a2}.")
    # A3: the cut is real: nothing crosses between cut clients and control by server.
    crossing = [
        r
        for k in (
            ("partitioned", "s", "control"),
            ("control", "s", "partitioned"),
            ("control", "s", "wintak"),
            ("wintak", "both", "control"),
        )
        for r in rows(*k)
        if in_cut(r) and r[2] is not None and r[3] == r[0]
    ]
    sent = [
        r
        for k in (
            ("partitioned", "s", "control"),
            ("control", "s", "partitioned"),
            ("control", "s", "wintak"),
        )
        for r in rows(*k)
        if in_cut(r)
    ]
    a3 = "NOT EXERCISED" if not sent else ("PASS" if not crossing else "FAIL")
    out.append(
        f"- **A3 the partition is real (no server-path delivery during a cut):** {a3}. "
        f"{len(crossing)} crossed of {len(sent)} sent."
    )
    # A4: both cut clients resume the stream, and server messages flow again.
    a4_bits, a4_ok, a4_any = [], True, False
    for i, (_, off) in enumerate(cuts, 1):
        if off is None:
            continue
        for who in ("wintak", "partitioned"):
            r = timing.get((i, who), (None, None))[1]
            a4_any = True
            a4_ok &= r is not None and r <= RESUME_LIMIT_S
            a4_bits.append(f"{who} cut{i} {'-' if r is None else f'{r:.0f} s'}")
        for k in (
            ("control", "s", "wintak"),
            ("control", "s", "partitioned"),
            ("partitioned", "s", "control"),
        ):
            first = next((r for r in rows(*k) if r[1] >= off), None)
            if first is None:
                continue
            d = None if first[2] is None else first[2] - off
            a4_ok &= d is not None and d <= RESUME_LIMIT_S + 20
            a4_bits.append(
                f"{k[0]}->{k[2]} first msg {'lost' if d is None else f'{d:.0f} s'}"
            )
    a4 = "NOT EXERCISED" if not a4_any else ("PASS" if a4_ok else "FAIL")
    out.append(
        f"- **A4 the server stream resumes on heal:** {a4}. " + "; ".join(a4_bits) + "."
    )
    # Reported, not scored: what the far side said during the cut.
    lost = [
        r
        for k in (("control", "s", "wintak"), ("control", "s", "partitioned"))
        for r in rows(*k)
        if in_cut(r)
    ]
    late = [r for r in lost if r[2] is not None]
    out.append(
        f"- **Reported: server-side chat sent during a cut:** {len(lost)} sent "
        f"to the cut clients, {len(late)} delivered after the heal, "
        f"{len(lost) - len(late)} never."
    )
    return out


def main() -> None:
    """Parse the arguments and print the report."""
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("--cut", required=True)
    p.add_argument("--sessions", required=True)
    p.add_argument("--wintak-ip", required=True)
    p.add_argument("--eud-ip", required=True)
    p.add_argument("logs", nargs="+")
    a = p.parse_args()
    cuts = load_cuts(a.cut)
    events = load_events(a.logs)
    lines = ["# Partition trial", ""]
    for i, (on, off) in enumerate(cuts, 1):
        span = f"{(off - on):.0f} s" if off else "not lifted"
        lines.append(f"- cut{i}: {iso(on)} to {iso(off) if off else '-'} ({span})")
    lines.append("")
    flows = chat_flows(events, cuts)
    sa_lines, sa = sa_gaps(events, cuts)
    t_lines, timing = stream_timing(events, cuts)
    ips = {"wintak": a.wintak_ip, "partitioned": a.eud_ip}
    lines += [*verdicts(flows, sa, timing, cuts), "", *t_lines, ""]
    lines += [*stale_sessions(a.sessions, cuts, ips), ""]
    lines += [*summarize_flows(flows), "", *sa_lines]
    print("\n".join(lines))


if __name__ == "__main__":
    main()
