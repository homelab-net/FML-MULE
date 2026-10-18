#!/bin/bash
# Failover and best-path selection between two batman-adv bearers, CONOPS 39.
#
#   sudo bearer-failover-real.sh up [restorer_secs]        add the second bearer
#   sudo bearer-failover-real.sh down                       remove it, clear faults
#   sudo bearer-failover-real.sh measure <label> <dev> <drop|loss30|admindown|none> \
#        <t_fault_s> <t_clear_s> <t_end_s> <peer_ip> <peer_orig>
#   sudo bearer-failover-real.sh monitor <label> <secs> <peer_orig>
#
# Two nodes have exactly one path between them, which is why the 2026-10-11
# real-radio artifact could not show failover or best-path selection. This
# gives the existing 802.11s bearer (wlan1, joined by 80211s-mesh-real.sh) a
# second hard interface in the same bat0: a VLAN subinterface of eth0. eth0
# itself is never reconfigured -- only the tagged child is created and removed
# -- so the management path cannot be disturbed, and a detached restorer
# removes the bearer if the session driving it is lost.
#
# The second bearer is WIRED. It stands in for a second radio so the routing
# behaviour can be observed; it says nothing about a second radio's physics.
# It also puts batman-adv frames, tagged, on whatever LAN eth0 is attached to,
# which is the operator's network to permit or refuse.
#
# A silent failure is emulated with tc: netem 100% loss on egress and a
# matchall drop on ingress, so the interface stays up and batman-adv has to
# notice the silence. admindown takes the interface down instead, which the
# local node sees at once and the far node sees only as silence.
#
# `measure` runs on the observing node: a 20 ms ping and a 100 ms poll of the
# outgoing interface batman-adv has selected toward the peer. `monitor` runs
# the same poll on the far node. Analysis happens off-node.
#
# INSTRUMENT DEFECT, recorded rather than hidden: on the throttled bench Pi
# (iputils 20240905), `ping -i 0.02` stops sending after a few seconds to a
# minute while the process stays alive, at no consistent point. Every outage
# reported from it must be cross-checked against the route poll, and windows
# after the ping stalled have no loss data. A sequence-numbered probe such as
# udpflow.py should replace it before the next run.
#
# CONOPS 39; FML-ADR-053 (BATMAN_IV); orig_interval is TBD in
# os/config/batman-adv.conf.template and TBR-RF-01 owns it.
set -u
export PATH=$PATH:/usr/sbin:/sbin
VID=3942
DEV=eth0.$VID
[ "$(id -u)" -eq 0 ] || {
  echo "FAIL: must run as root" >&2
  exit 1
}

down() {
  for d in "$DEV" wlan1; do
    tc qdisc del dev "$d" root 2>/dev/null
    tc qdisc del dev "$d" ingress 2>/dev/null
  done
  batctl meshif bat0 if del "$DEV" 2>/dev/null
  ip link del "$DEV" 2>/dev/null
  batctl meshif bat0 orig_interval 1000 >/dev/null 2>&1
  echo "second bearer down: $(batctl meshif bat0 if | tr '\n' ' ')"
}

up() {
  secs=${1:-3600}
  modprobe 8021q || {
    echo "FAIL: 8021q"
    exit 1
  }
  ip link show "$DEV" >/dev/null 2>&1 || ip link add link eth0 name "$DEV" type vlan id "$VID"
  ip link set "$DEV" up
  batctl meshif bat0 if add "$DEV" 2>&1
  setsid nohup bash -c "sleep $secs; '$0' down" >/tmp/bearer-failover-restorer.log 2>&1 &
  echo "restorer armed ${secs}s"
  ip -br link show "$DEV"
  batctl meshif bat0 if
}

route() { # selected outgoing interface and TQ toward originator $1
  batctl meshif bat0 o -H -n 2>/dev/null | tr -d '[]()' |
    awk -v m="$1" '$1=="*" && $2==m {print $NF, $4; f=1} END{if(!f) print "none -"}'
}

measure() {
  L=$1 D=$2 K=$3 TF=$4 TC=$5 TE=$6 PEER=$7 ORIG=$8
  case "$D" in "$DEV" | wlan1) ;; *)
    echo "FAIL: refusing dev $D" >&2
    exit 1
    ;;
  esac
  [ "$K" = admindown ] && [ "$D" != "$DEV" ] && {
    echo "FAIL: admindown only on $DEV" >&2
    exit 1
  }
  O=/tmp/m39-$L
  rm -rf "$O"
  mkdir -p "$O"
  now() { date +%s.%N; }
  cnt() { for d in wlan1 "$DEV"; do
    echo "$1 $d tx=$(cat /sys/class/net/$d/statistics/tx_packets) rx=$(cat /sys/class/net/$d/statistics/rx_packets)"
  done >>"$O/counters"; }
  {
    echo "label=$L dev=$D kind=$K t_fault=$TF t_clear=$TC t_end=$TE oi=$(batctl meshif bat0 orig_interval)"
    echo "kernel=$(uname -r) batadv=$(modinfo -F version batman_adv)"
    timedatectl timesync-status 2>&1 | grep -E 'Offset'
  } >"$O/meta"
  cnt start
  ping -D -i 0.02 -W 1 "$PEER" >"$O/ping" 2>&1 &
  PP=$!
  echo "t0 $(now)" >>"$O/events"
  end=$(($(date +%s) + TE))
  (while [ "$(date +%s)" -lt $end ]; do
    echo "$(now) $(route "$ORIG")"
    sleep 0.1
  done) >"$O/route" &
  RP=$!
  (while [ "$(date +%s)" -lt $end ]; do
    echo "$(now) $(vcgencmd get_throttled) $(vcgencmd measure_clock arm)"
    sleep 2
  done) >"$O/throttle" &
  sleep "$TF"
  if [ "$K" != none ]; then
    case "$K" in
      drop)
        tc qdisc replace dev "$D" root netem loss 100%
        tc qdisc replace dev "$D" ingress
        tc filter add dev "$D" parent ffff: matchall action drop
        ;;
      loss30) tc qdisc replace dev "$D" root netem loss 30% ;;
      admindown) ip link set "$D" down ;;
    esac
    echo "fault $(now)" >>"$O/events"
    cnt fault
  fi
  sleep $((TC - TF))
  if [ "$K" != none ]; then
    tc qdisc del dev "$D" root 2>/dev/null
    tc qdisc del dev "$D" ingress 2>/dev/null
    ip link set "$D" up
    echo "clear $(now)" >>"$O/events"
    cnt clear
  fi
  wait $RP
  kill $PP 2>/dev/null
  wait $PP 2>/dev/null
  cnt end
  echo "done $O"
}

monitor() {
  O=/tmp/m39-$1-far
  rm -rf "$O"
  mkdir -p "$O"
  end=$(($(date +%s) + $2))
  while [ "$(date +%s)" -lt $end ]; do
    echo "$(date +%s.%N) $(route "$3")"
    sleep 0.1
  done >"$O/route"
  timedatectl timesync-status 2>&1 | grep -E 'Offset' >"$O/meta"
  echo "done $O"
}

case "${1:-}" in
  up) up "${2:-3600}" ;;
  down) down ;;
  measure)
    shift
    [ $# -eq 8 ] || {
      echo "usage: measure <8 args>" >&2
      exit 64
    }
    measure "$@"
    ;;
  monitor)
    shift
    [ $# -eq 3 ] || {
      echo "usage: monitor <3 args>" >&2
      exit 64
    }
    monitor "$@"
    ;;
  *)
    echo "usage: bearer-failover-real.sh up [secs] | down | measure ... | monitor ..." >&2
    exit 64
    ;;
esac
