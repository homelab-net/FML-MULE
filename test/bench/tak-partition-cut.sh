#!/bin/bash
# Make this node's TAK server unreachable to its clients, and restore it.
#
#   tak-partition-cut.sh on [minutes]               cut now; lift after minutes (10)
#   tak-partition-cut.sh cycles N minutes gap       N cuts of minutes, gap apart
#   tak-partition-cut.sh sweep "S1 S2 ..." gap      after a 60 s baseline, cuts of
#                                                   S1, S2 ... seconds, gap s apart
#   tak-partition-cut.sh off                        lift now; cancel what is pending
#   tak-partition-cut.sh status
#
# The TBR-HA-01 option A prototype: with the server cut, do clients carry on
# peer-to-peer (multicast SA and GeoChat), and does each resume its server
# stream when the cut is lifted? The cut DROPS, rather than rejects, every TCP
# segment to or from the TAK ports on any interface but loopback, so a client
# sees a silent partition, not a refused connection. Loopback is spared, so a
# control client on this host stays on the server side of the cut. The server
# keeps running, and multicast is untouched.
#
# The sweep measures partition detection: cuts from seconds to minutes, timed
# to the second, so a probe's log can be replayed against candidate entry and
# exit thresholds. It runs as one transient service.
#
# Every cut lifts itself through a transient systemd timer or service, so a lost
# session cannot leave the node cut; a sweep also gets a backstop timer. Each
# transition is appended, with a UTC millisecond timestamp, to a world-readable
# log, so the trial's analysis reads the real times instead of an operator's
# notes. Runs as root.
set -eu

MODE="${1:-status}"
TABLE="fml_partition_cut"
PORTS="8089, 8443, 8446"
UNIT="fml-partition-cut"
LOG="/run/fml-partition-cut.log"
BASELINE=60

whole() {
  case "$1" in
    '' | *[!0-9]*)
      echo "$2 must be a whole number" >&2
      exit 64
      ;;
  esac
}

stamp() { date -u +%Y-%m-%dT%H:%M:%S.%3NZ; }

record() {
  echo "$(stamp) $*" | tee -a "$LOG"
  chmod 644 "$LOG"
}

is_cut() { nft list table inet "$TABLE" >/dev/null 2>&1; }

nft_on() {
  nft -f - <<NFT
table inet $TABLE {
  chain input {
    type filter hook input priority -10; policy accept;
    iifname != "lo" tcp dport { $PORTS } counter drop
  }
  chain output {
    type filter hook output priority -10; policy accept;
    oifname != "lo" tcp sport { $PORTS } counter drop
  }
}
NFT
}

nft_off() { nft delete table inet "$TABLE" 2>/dev/null || true; }

cut_off() {
  systemctl stop "$UNIT-*.timer" "$UNIT-sweep-*.service" 2>/dev/null || true
  nft_off
  record "cut off"
}

lift_one() {
  nft_off
  record "cut off (expired)"
}

cut_on() {
  whole "$1" minutes
  if is_cut; then
    echo "already cut; run off first" >&2
    exit 1
  fi
  nft_on
  systemd-run --quiet --unit "$UNIT-lift-$(date +%s%N)" \
    --on-active="${1}min" "$(readlink -f "$0")" lift
  record "cut on, lifts in ${1} min"
}

cut_cycles() {
  whole "$1" count
  whole "$2" minutes
  whole "$3" gap
  local i=0 self
  self="$(readlink -f "$0")"
  while [ "$i" -lt "$1" ]; do
    if [ "$i" -eq 0 ]; then
      cut_on "$2"
    else
      systemd-run --quiet --unit "$UNIT-on-$i-$(date +%s%N)" \
        --on-active="$((i * ($2 + $3)))min" "$self" on "$2"
    fi
    i=$((i + 1))
  done
  record "cycles: $1 cuts of $2 min, $3 min apart"
}

# Start a sweep as a transient service, with a backstop lift after its end.
cut_sweep() {
  local total=$BASELINE s
  whole "$2" gap
  [ -n "$1" ] || {
    echo "sweep needs at least one cut length" >&2
    exit 64
  }
  for s in $1; do
    whole "$s" seconds
    total=$((total + s + $2))
  done
  if is_cut; then
    echo "already cut; run off first" >&2
    exit 1
  fi
  systemd-run --quiet --unit "$UNIT-sweep-$(date +%s%N)" \
    "$(readlink -f "$0")" sweep-run "$1" "$2"
  systemd-run --quiet --unit "$UNIT-lift-$(date +%s%N)" \
    --timer-property=AccuracySec=1s --on-active="$((total + 30))s" \
    "$(readlink -f "$0")" lift
  record "sweep: ${BASELINE} s baseline, cuts of $1 s, $2 s apart, ends in about ${total} s"
}

# The sweep itself, inside its service. Stopping the service lifts the cut.
sweep_run() {
  trap 'nft_off' EXIT
  trap 'exit 143' TERM INT
  sleep "$BASELINE"
  for s in $1; do
    nft_on
    record "cut on (sweep ${s} s)"
    sleep "$s"
    nft_off
    record "cut off (sweep)"
    sleep "$2"
  done
  record "sweep done"
}

case "$MODE" in
  on) cut_on "${2:-10}" ;;
  cycles) cut_cycles "${2:-}" "${3:-}" "${4:-}" ;;
  sweep) cut_sweep "${2:-}" "${3:-}" ;;
  sweep-run) sweep_run "$2" "$3" ;;
  off) cut_off ;;
  lift) lift_one ;;
  status)
    if is_cut; then nft list table inet "$TABLE"; else echo "not cut"; fi
    systemctl list-timers "$UNIT-*" --no-pager 2>/dev/null || true
    systemctl list-units "$UNIT-sweep-*" --no-pager 2>/dev/null || true
    ;;
  *)
    echo "usage: $0 on [minutes] | cycles N minutes gap | sweep \"S1 S2 ...\" gap | off | status" >&2
    exit 64
    ;;
esac
