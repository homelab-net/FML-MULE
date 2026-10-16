#!/bin/bash
# Voice-vs-data contention on a REAL two-node batman-adv mesh. The real-radio
# counterpart to the `contention` half of test/bench/mesh-traffic.sh.
#
# Usage, one phase at a time, receiver started first:
#
#   on the receiving node:  sudo test/bench/mesh-traffic-real.sh recv <a|b|c>
#   on the sending node:    sudo test/bench/mesh-traffic-real.sh send <peer-ip> <a|b|c>
#
#   a   voice alone through the bottleneck -- the baseline.
#   b   voice + bulk in one FIFO -- FML-ADR-021's "routing starves first".
#   c   voice (DSCP EF) in a protected class under the same load.
#
# Run the pair three times, a then b then c. FLOW= overrides the path to
# udpflow.py when this script is not run from beside it.
#
# WHY THIS EXISTS, AND WHY IT IS NOT mesh-traffic.sh. That script cannot be
# pointed at hardware: it guards itself with "refusing to move a real radio",
# and it builds both endpoints as network namespaces on ONE host. Its
# `latency` mode is additionally a three-node line topology, which two nodes
# cannot form. So only the `contention` half is portable, and it is ported
# here value for value -- BOTTLENECK, the tbf and htb qdiscs, the DSCP EF
# filter, the ~160 B/20 ms voice profile and the 10 s duration are unchanged.
#
# THE ONE METRIC THAT CHANGED, AND WHY. udpflow.py says it itself: one-way
# latency "is meaningful here only because the bench runs every node in a
# network namespace on one host, so sender and receiver read the same system
# clock. On two real nodes this number would be a clock-offset artefact."
# These are two real nodes with two clocks, so:
#
#   * loss and jitter are REPORTED -- a count and a differential, both valid
#     across hosts.
#   * one-way latency is NOT reported. It is replaced by round-trip time from
#     `ping -D` over bat0, measured concurrently with the flow, which is valid
#     across hosts because one clock times both directions.
#
# Reading the suppressed figure off udpflow.py's JSON anyway would produce a
# number that looks like mouth-to-ear latency and is actually clock skew.
#
# WHAT A RESULT HERE IS NOT. The qdisc is ILLUSTRATIVE, not a decision:
# TBR-RF-01 owns the QoS mechanism, and this only shows the contention is
# addressable. BOTTLENECK is an imposed 5 Mbit limit, not a measurement of
# this radio's capacity. Two nodes means one hop, so nothing here speaks to
# multi-hop behaviour.

set -eu

VOICE_PORT=5001
BULK_PORT=5002
#: Unchanged from mesh-traffic.sh: without an imposed bottleneck a bulk flow
#: cannot contend and nothing degrades. The rate models a constrained bearer so
#: SCHEDULING is visible; it says nothing about real RF capacity (TBR-RF-01).
BOTTLENECK=5mbit
MESH_IF=bat0
#: udpflow.py's --timeout is an IDLE timeout: the receiver exits after this many
#: seconds with no data, including before the first packet ever arrives. The
#: single-host bench can use 3 because it starts the sender 0.5 s later in the
#: same script. Two hosts are started by two separate operators (or two SSH
#: sessions), so the skew is seconds, and 3 makes the receiver quit before the
#: flow begins and report a loss figure of 100% that is pure orchestration.
#: Raised for the cross-host case; it still exits this long after the flow ends.
#:
#: This value is a trade, and BOTH ends of it were hit on the bench. Too short
#: (3, the single-host default) and the receiver gives up before the sender has
#: finished SSH, sudo and six tc commands, reporting zero packets on a path that
#: is provably fine. Too long (20) and the receiver is still alive when the NEXT
#: phase starts, which breaks two ways at once: udpflow.py does not set
#: SO_REUSEADDR, so the second bind dies with EADDRINUSE and reports nothing;
#: and if it does survive, one receiver absorbs several phases and reports
#: nonsense -- 1475 packets received against 492 expected, a loss of -199.8%.
#:
#: So the phases must not overlap, and the guards below refuse to report rather
#: than let either failure be read as a measurement.
RECV_TIMEOUT=${RECV_TIMEOUT:-10}
FLOW=${FLOW:-$(cd "$(dirname "$0")" && pwd)/udpflow.py}

fail() {
  printf 'FAIL: %s\n' "$*" >&2
  exit 1
}

[ "$(id -u)" -eq 0 ] || fail 'must run as root'
[ -f "$FLOW" ] || fail "udpflow.py not found at $FLOW (set FLOW=/path/to/udpflow.py)"
ip link show "$MESH_IF" >/dev/null 2>&1 ||
  fail "$MESH_IF does not exist; bring the mesh up first (80211s-mesh-real.sh up <octet>)"

# Refuse to produce a number on a throttled node.
#
# This is a refusal rather than a warning on purpose. Both bench nodes were
# found under-voltage and pinned at 600 MHz against a nominal 1.5 GHz, and that
# alone moved mesh RTT from 0.9 ms to 61.8 ms while every radio indicator read
# healthy. A throttled node UNDER-reports the bearer, so the figure is not
# merely noisy, it is wrong in the believable direction: it makes the radio look
# worse than it is and nobody questions a disappointing result. A footnote on
# such a run gets dropped the first time someone quotes the number.
#
# ALLOW_THROTTLED=1 exists for deliberately characterising the degraded case,
# which is a different experiment and should say so in its own evidence.
if command -v vcgencmd >/dev/null 2>&1 && [ "${ALLOW_THROTTLED:-0}" != "1" ]; then
  t=$(vcgencmd get_throttled 2>/dev/null | cut -d= -f2)
  v=$((t))
  if [ $((v & 0x1)) -ne 0 ] || [ $((v & 0x4)) -ne 0 ]; then
    fail "node is under-voltage or throttled now ($t, $(vcgencmd measure_clock arm 2>/dev/null | cut -d= -f2 | awk '{printf "%.0f", $1/1000000}') MHz). A performance figure taken here understates the bearer. Fix the supply, or set ALLOW_THROTTLED=1 if characterising the degraded case deliberately."
  fi
fi

# --- qdiscs: ported from mesh-traffic.sh, minus the netns indirection --------

tc_clear() { tc qdisc del dev "$MESH_IF" root >/dev/null 2>&1 || true; }

tc_fifo() { # a plain rate-limited FIFO: bulk and voice share one queue
  tc_clear
  tc qdisc add dev "$MESH_IF" root handle 1: \
    tbf rate "$BOTTLENECK" burst 32kbit latency 400ms
}

tc_prioritized() { # same rate, but voice (DSCP EF) gets a protected class
  tc_clear
  tc qdisc add dev "$MESH_IF" root handle 1: htb default 20
  tc class add dev "$MESH_IF" parent 1: classid 1:1 \
    htb rate "$BOTTLENECK" ceil "$BOTTLENECK"
  tc class add dev "$MESH_IF" parent 1:1 classid 1:10 \
    htb rate 4mbit ceil "$BOTTLENECK" prio 0
  tc class add dev "$MESH_IF" parent 1:1 classid 1:20 \
    htb rate 1mbit ceil "$BOTTLENECK" prio 1
  tc filter add dev "$MESH_IF" parent 1: protocol ip prio 1 \
    u32 match ip dsfield 0xb8 0xfc flowid 1:10
}

# --- receiver ----------------------------------------------------------------

do_recv() {
  local label=${1:-run} vout vpid bpid port
  vout="/tmp/fml-mesh-real.voice.$label.json"
  rm -f "$vout"

  # Pre-flight: a receiver from the previous phase still holding the port would
  # otherwise fail this one with a silent EADDRINUSE and look like total loss.
  for port in "$VOICE_PORT" "$BULK_PORT"; do
    if ss -uln 2>/dev/null | grep -qE "[:.]$port\b"; then
      fail "UDP port $port is already bound -- a receiver from a previous phase is still alive. Wait for it to exit, then re-run this phase."
    fi
  done
  pgrep -f 'udpflow.py recv' >/dev/null 2>&1 &&
    fail 'another udpflow.py receiver is running; wait for it to exit before starting this phase'

  python3 "$FLOW" recv --port "$VOICE_PORT" --timeout "$RECV_TIMEOUT" >"$vout" 2>/dev/null &
  vpid=$!
  python3 "$FLOW" recv --port "$BULK_PORT" --timeout "$RECV_TIMEOUT" >/dev/null 2>&1 &
  bpid=$!

  printf 'listening for phase %s (voice :%s, bulk :%s)\n' "$label" "$VOICE_PORT" "$BULK_PORT"
  wait "$vpid" 2>/dev/null || true
  kill "$bpid" 2>/dev/null || true
  wait "$bpid" 2>/dev/null || true

  # latency_ms_avg is deliberately NOT printed: see the header.
  python3 - "$vout" "$label" <<'PY' || printf '  %-4s no voice samples received\n' "${1:-?}"
import json, sys
try:
    d = json.load(open(sys.argv[1]))
except Exception:
    d = None
if not d or not d.get("received"):
    # Not a loss figure. The receiver's idle timeout beat the sender's start-up,
    # so nothing was ever measured. Re-run the phase; do not record this.
    print("  phase %s  NO PACKETS ARRIVED -- orchestration failure, not a result." % sys.argv[2])
    print("  Re-run this phase (raise RECV_TIMEOUT if it repeats).")
    sys.exit(0)
recv, exp = d.get("received") or 0, d.get("expected") or 0
if exp and recv > exp:
    # More arrived than this phase sent: a receiver that outlived its phase and
    # collected the next one too. The loss figure goes negative and is garbage.
    print("  phase %s  CONTAMINATED -- received %s against %s expected, so this"
          % (sys.argv[2], recv, exp))
    print("  receiver outlived its phase and absorbed another. Not a result; re-run.")
    sys.exit(0)
print("  phase %s  loss %s %%   jitter %s ms   received %s/%s" % (
    sys.argv[2], d.get("loss_pct"), d.get("jitter_ms"),
    d.get("received"), d.get("expected")))
print("  (one-way latency withheld: two clocks, see header)")
PY
  printf '  raw: %s\n' "$vout"
}

# --- sender ------------------------------------------------------------------

start_bulk() {
  python3 "$FLOW" send --profile bulk \
    --host "$1" --port "$BULK_PORT" --duration 12 >/dev/null 2>&1 &
  BULK_PID=$!
}

stop_bulk() {
  [ -n "${BULK_PID:-}" ] || return 0
  kill "$BULK_PID" 2>/dev/null || true
  wait "$BULK_PID" 2>/dev/null || true
  BULK_PID=
}

# RTT concurrent with the voice flow. This is the honest substitute for the
# one-way latency the single-host bench could report and two nodes cannot.
voice_and_rtt() {
  local peer=$1
  shift
  local pf="/tmp/fml-mesh-real.ping.$$" ppid rtt iloss
  ping -D -i 0.2 -c 45 -I "$MESH_IF" "$peer" >"$pf" 2>&1 &
  ppid=$!
  python3 "$FLOW" send --profile voice \
    --host "$peer" --port "$VOICE_PORT" --duration 10 "$@" >/dev/null 2>&1
  wait "$ppid" 2>/dev/null || true
  rtt=$(awk -F'= ' '/rtt min/ {print $2}' "$pf" 2>/dev/null || true)
  iloss=$(grep -oE '[0-9.]+% packet loss' "$pf" 2>/dev/null | grep -oE '^[0-9.]+%' | head -1)
  printf '  RTT over %s (min/avg/max/mdev): %s\n' "$MESH_IF" "${rtt:-n/a}"
  printf '  ICMP loss during flow:          %s\n' "${iloss:-n/a}"
  rm -f "$pf"
}

do_send() {
  local peer=${1:-} phase=${2:-}
  if [ -z "$peer" ] || [ -z "$phase" ]; then
    fail 'usage: send <peer-ip> <a|b|c>'
  fi

  case "$phase" in
    a)
      printf 'phase a  voice alone through a %s bottleneck\n' "$BOTTLENECK"
      tc_fifo
      voice_and_rtt "$peer"
      ;;
    b)
      printf 'phase b  voice + bulk, one FIFO, no QoS (%s)\n' "$BOTTLENECK"
      tc_fifo
      start_bulk "$peer"
      voice_and_rtt "$peer"
      stop_bulk
      ;;
    c)
      printf 'phase c  voice (DSCP EF) prioritised under the same bulk load\n'
      tc_prioritized
      start_bulk "$peer"
      voice_and_rtt "$peer" --dscp 46
      stop_bulk
      ;;
    *) fail "unknown phase '$phase' (expected a, b or c)" ;;
  esac
  tc_clear
  printf '  qdisc cleared\n'
}

case "${1:-}" in
  recv)
    shift
    do_recv "${1:-}"
    ;;
  send)
    shift
    do_send "${1:-}" "${2:-}"
    ;;
  clear)
    tc_clear
    printf 'qdisc cleared on %s\n' "$MESH_IF"
    ;;
  *) fail 'usage: mesh-traffic-real.sh {recv <a|b|c>|send <peer-ip> <a|b|c>|clear}' ;;
esac
