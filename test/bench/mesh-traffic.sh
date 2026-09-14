#!/bin/bash
# Measure transport behaviour of the batman-adv mesh over hwsim: multi-hop
# latency, and voice-vs-data contention on one bearer.
#
# Usage: sudo test/bench/mesh-traffic.sh {latency|contention}
#
#   latency      line topology (3 nodes); RTT at one and two hops.
#   contention   flat 2-node mesh; a voice-profile flow's jitter/loss idle,
#                under a bulk flow, and under a bulk flow with an illustrative
#                QoS qdisc. The qdisc is illustrative, NOT a decision: the QoS
#                mechanism is TBR-RF-01's to choose.
#
# WHY THIS EXISTS. docs/architecture/roip-voice-data-flow.md lists two open
# questions -- multi-hop mouth-to-ear latency, and voice/data QoS contention.
# This bench answers the transport half of both. The audio pipeline (DigiRig,
# radio, Opus) is unbuilt (TBR-VOICE-01), so this is transport latency, not
# mouth-to-ear. CONOPS section 40 (traffic preference) is the charter;
# FML-ADR-021's "routing starves first" is the failure mode instrumented here.
#
# WHY IT IS NOT IN CI, and WHAT A RESULT IS NOT. Same as the other benches
# here: mac80211_hwsim needs a wireless stack a hosted runner lacks, so this
# runs on a development machine. hwsim models the 802.11 MAC and NOTHING
# physical -- no propagation, path loss, interference or rate adaptation. Its
# wire is perfect, so a latency figure here is hop-count and stack cost, not RF,
# and a contention result shows scheduling behaviour, not spectrum. Tier is
# SIMULATED; it advances TBR-RF-01 (requires-hardware) and cannot close it.
# See docs/dev-machine.md and docs/evidence/TBR-RF-01/.
#
# A NUMBER YOU MUST NOT CHASE. If a first reply takes tens of seconds, that is
# bridge_loop_avoidance left enabled against FML-ADR-056, not a property of
# hwsim -- .github/workflows/mesh-probe.yml records 31.5s against 2.150s for
# exactly that, one variable. This script disables it; if you see it, the fix
# is a config bug, not a finding.

set -eu

MESH_ID=fml-bench-mesh
MTU=1560
#: 2412 is channel 1, 2437 is channel 6: non-overlapping, so a line topology's
#: two segments cannot hear each other.
FREQ_A=2412
FREQ_B=2437
VOICE_PORT=5001
BULK_PORT=5002
FLOW="$(cd "$(dirname "$0")" && pwd)/udpflow.py"

fail() {
  printf 'FAIL: %s\n' "$1" >&2
  exit 1
}

info() {
  printf '  %s\n' "$1"
}

RADIOS=2
cleanup() {
  i=1
  while [ "$i" -le "$RADIOS" ]; do
    ip netns del "fmlbench$i" 2>/dev/null || true
    i=$((i + 1))
  done
  rmmod mac80211_hwsim 2>/dev/null || true
  rm -f /tmp/fml-mesh-traffic.*.$$ 2>/dev/null || true
}
trap cleanup EXIT INT TERM

[ "$(id -u)" -eq 0 ] || fail 'must run as root: it loads a module and creates namespaces.'

MODE="${1:-}"
case "$MODE" in
  latency) RADIOS=4 ;;
  contention) RADIOS=2 ;;
  *) fail 'usage: mesh-traffic.sh {latency|contention}' ;;
esac

for tool in ip iw batctl python3; do
  command -v "$tool" >/dev/null 2>&1 ||
    fail "$tool is not installed. apt-get install iproute2 iw batctl python3"
done
[ "$MODE" != "contention" ] || command -v tc >/dev/null 2>&1 ||
  fail 'tc is not installed. apt-get install iproute2'
modinfo mac80211_hwsim >/dev/null 2>&1 ||
  fail 'mac80211_hwsim is not in this kernel; this needs a distribution kernel.'

# Only phys under the mac80211_hwsim device tree are eligible. This is the guard
# that a name match once defeated, moving a live radio into a namespace: pick by
# driver, never by a fuzzy name (see the bench README and the program's memory).
hwsim_phys() {
  for d in /sys/devices/virtual/mac80211_hwsim/*/ieee80211/phy*; do
    [ -e "$d" ] && basename "$d"
  done
}

phy_for() {
  iw dev "$1" info 2>/dev/null | awk '/wiphy/ {print "phy"$2}'
}

move_phy() {
  # $1 device (wlanN), $2 namespace. Refuses to move anything that is not hwsim.
  phy="$(phy_for "$1")"
  [ -n "$phy" ] || fail "could not find the phy behind $1"
  hwsim_phys | grep -qx "$phy" ||
    fail "$1 resolves to $phy, which is not a mac80211_hwsim radio; refusing to move a real radio."
  iw phy "$phy" set netns name "$2"
}

join_mesh() {
  # $1 namespace, $2 device, $3 mesh id, $4 frequency
  ip netns exec "$1" ip link set "$2" down
  ip netns exec "$1" iw dev "$2" set type mp
  ip netns exec "$1" ip link set "$2" mtu "$MTU" up
  ip netns exec "$1" iw dev "$2" mesh join "$3" freq "$4"
}

start_batman() {
  # $1 namespace, $2 host octet, rest: hard interfaces to join to bat0.
  ns=$1
  octet=$2
  shift 2
  # BATMAN_IV is fixed at creation, not at first add (FML-ADR-053).
  ip netns exec "$ns" batctl routing_algo BATMAN_IV >/dev/null 2>&1 || true
  ip netns exec "$ns" ip link add name bat0 type batadv
  # Bridge loop avoidance OFF, permanently (FML-ADR-056,
  # os/config/batman-adv.conf.template). Enabled by default; leaving it on
  # withholds client frames ~30s while every batctl table reads converged.
  ip netns exec "$ns" batctl meshif bat0 bridge_loop_avoidance 0 >/dev/null 2>&1 || true
  for hard in "$@"; do
    ip netns exec "$ns" ip link set "$hard" master bat0
  done
  ip netns exec "$ns" ip addr add "10.41.0.$octet/16" dev bat0
  ip netns exec "$ns" ip link set bat0 up
}

wait_cross() {
  # $1 source namespace, $2 destination address. Wait for the condition, never
  # sleep a fixed interval: batman-adv convergence is not a fixed time.
  deadline=$(($(date +%s) + 60))
  while [ "$(date +%s)" -lt "$deadline" ]; do
    if ip netns exec "$1" ping -c 2 -W 2 "$2" >/dev/null 2>&1; then
      return 0
    fi
    sleep 2
  done
  fail "traffic did not reach $2 from $1 within 60s."
}

printf 'Preparing %s virtual radios\n' "$RADIOS"
rmmod mac80211_hwsim 2>/dev/null || true
modprobe mac80211_hwsim "radios=$RADIOS"
sleep 2

run_latency() {
  printf 'Building a line: node 1 -- node 2 -- node 3 (node 1 cannot hear 3)\n'
  for n in 1 2 3; do ip netns add "fmlbench$n"; done
  move_phy wlan0 fmlbench1
  move_phy wlan1 fmlbench2
  move_phy wlan2 fmlbench2
  move_phy wlan3 fmlbench3
  join_mesh fmlbench1 wlan0 "$MESH_ID-a" "$FREQ_A"
  join_mesh fmlbench2 wlan1 "$MESH_ID-a" "$FREQ_A"
  join_mesh fmlbench2 wlan2 "$MESH_ID-b" "$FREQ_B"
  join_mesh fmlbench3 wlan3 "$MESH_ID-b" "$FREQ_B"
  start_batman fmlbench1 1 wlan0
  start_batman fmlbench2 2 wlan1 wlan2
  start_batman fmlbench3 3 wlan3

  # Wait for the condition, then confirm the line is real before trusting a
  # two-hop number. Peering and batman convergence are not fixed intervals.
  wait_cross fmlbench1 10.41.0.2
  wait_cross fmlbench1 10.41.0.3
  seen=$(ip netns exec fmlbench1 iw dev wlan0 station dump 2>/dev/null | grep -c '^Station' || true)
  [ "$seen" -eq 1 ] || fail "node 1 sees $seen peers, expected 1; the segments are not separated."
  info 'line converged, both hops reachable, and node 1 sees exactly one peer'

  printf '\nRTT, 50 samples at 200 ms (ping -D, wire timestamps)\n'
  for pair in "1 hop:10.41.0.2" "2 hop:10.41.0.3"; do
    label="${pair%%:*}"
    dst="${pair##*:}"
    line=$(ip netns exec fmlbench1 ping -c 50 -i 0.2 -D "$dst" 2>/dev/null |
      awk -F'= ' '/rtt/ {print $2"  (min/avg/max/mdev)"}')
    printf '  %-6s %s\n' "$label" "${line:-no rtt line (unreachable)}"
  done
}

voice_run() {
  # $1 label, extra args after are passed to the voice sender (e.g. --dscp).
  label=$1
  shift
  out="/tmp/fml-mesh-traffic.voice.$$"
  ip netns exec fmlbench2 python3 "$FLOW" recv --port "$VOICE_PORT" --timeout 3 >"$out" 2>/dev/null &
  recv_pid=$!
  sleep 0.5
  ip netns exec fmlbench1 python3 "$FLOW" send --profile voice \
    --host 10.41.0.2 --port "$VOICE_PORT" --duration 10 "$@" >/dev/null 2>&1
  wait "$recv_pid" 2>/dev/null || true
  summary=$(python3 -c 'import json,sys
d=json.load(open(sys.argv[1]))
print("loss",d.get("loss_pct"),"%  jitter",d.get("jitter_ms"),
      "ms  latency avg",d.get("latency_ms_avg"),
      "ms  (recv",str(d.get("received"))+"/"+str(d.get("expected"))+")")' "$out" 2>/dev/null ||
    echo "no voice samples received")
  printf '  %-28s %s\n' "$label" "$summary"
  rm -f "$out"
}

start_bulk() {
  ip netns exec fmlbench2 python3 "$FLOW" recv --port "$BULK_PORT" --timeout 3 >/dev/null 2>&1 &
  ip netns exec fmlbench1 python3 "$FLOW" send --profile bulk \
    --host 10.41.0.2 --port "$BULK_PORT" --duration 12 >/dev/null 2>&1 &
  BULK_PIDS="$!"
}

stop_bulk() {
  for p in $BULK_PIDS; do kill "$p" 2>/dev/null || true; done
  wait 2>/dev/null || true
}

#: An imposed bottleneck rate. hwsim's wire has NO capacity of its own, so
#: without this a bulk flow cannot contend for bandwidth and nothing degrades.
#: This models a constrained bearer so the SCHEDULING behaviour is visible; the
#: rate is illustrative and says nothing about real RF capacity (TBR-RF-01).
BOTTLENECK=5mbit

tc_fifo() { # a plain rate-limited FIFO: bulk and voice share one queue
  ip netns exec fmlbench1 tc qdisc add dev bat0 root handle 1: \
    tbf rate "$BOTTLENECK" burst 32kbit latency 400ms
}

tc_prioritized() { # same rate, but voice (DSCP EF) gets a protected class
  ip netns exec fmlbench1 tc qdisc add dev bat0 root handle 1: htb default 20
  ip netns exec fmlbench1 tc class add dev bat0 parent 1: classid 1:1 \
    htb rate "$BOTTLENECK" ceil "$BOTTLENECK"
  ip netns exec fmlbench1 tc class add dev bat0 parent 1:1 classid 1:10 \
    htb rate 4mbit ceil "$BOTTLENECK" prio 0
  ip netns exec fmlbench1 tc class add dev bat0 parent 1:1 classid 1:20 \
    htb rate 1mbit ceil "$BOTTLENECK" prio 1
  ip netns exec fmlbench1 tc filter add dev bat0 parent 1: protocol ip prio 1 \
    u32 match ip dsfield 0xb8 0xfc flowid 1:10
}

tc_clear() { ip netns exec fmlbench1 tc qdisc del dev bat0 root 2>/dev/null || true; }

run_contention() {
  printf 'Building a flat 2-node mesh (one shared bearer)\n'
  for n in 1 2; do ip netns add "fmlbench$n"; done
  move_phy wlan0 fmlbench1
  move_phy wlan1 fmlbench2
  join_mesh fmlbench1 wlan0 "$MESH_ID" "$FREQ_A"
  join_mesh fmlbench2 wlan1 "$MESH_ID" "$FREQ_A"
  start_batman fmlbench1 1 wlan0
  start_batman fmlbench2 2 wlan1
  wait_cross fmlbench1 10.41.0.2
  info 'mesh converged'

  printf '\nVoice-profile flow (~160 B/20 ms) over an imposed %s bottleneck\n' "$BOTTLENECK"
  # (a) voice alone through the constrained pipe: the baseline.
  tc_fifo
  voice_run 'a. voice alone'
  tc_clear

  # (b) bulk contends in one FIFO: this is FML-ADR-021's "starves first".
  tc_fifo
  start_bulk
  voice_run 'b. + bulk, one FIFO (no QoS)'
  stop_bulk
  tc_clear

  # (c) same load, voice (DSCP EF) in a protected class. Illustrative ONLY:
  # TBR-RF-01 owns the QoS mechanism; this shows the contention is addressable.
  tc_prioritized
  start_bulk
  voice_run 'c. + bulk, voice prioritized' --dscp 46
  stop_bulk
  tc_clear
}

case "$MODE" in
  latency) run_latency ;;
  contention) run_contention ;;
esac

printf '\n'
printf 'Tier: SIMULATED. hwsim models the 802.11 MAC and nothing physical.\n'
printf 'Transport only (no audio pipeline). Advances TBR-RF-01; cannot close it.\n'
