#!/bin/sh
# Exercise 802.11s association and batman-adv over it, with no radio.
#
# Usage: sudo test/bench/80211s-mesh.sh [--line] [node-count]
#
#   --line      three nodes in a line, proving multi-hop. Uses four radios.
#   node-count  virtual radios for a flat run. Default 2.
#
# WHAT THIS IS FOR. `.github/workflows/mesh-probe.yml` forms its mesh over
# `veth` and says so: a perfect wire, and not wireless at all. It proves
# batman-adv routes and exercises no 802.11s, so the association layer
# FML-ADR-053 selects has no coverage from it. This covers that layer.
#
# WHY IT IS NOT IN CI. mac80211_hwsim needs a wireless stack in the kernel's
# module tree, and a hosted runner has none: linux-modules-extra supplies
# batman-adv and no wireless driver. The mesh probe records that state on every
# run so the day it changes somebody finds out. Until then this runs on a
# development machine with an ordinary distribution kernel. See
# docs/dev-machine.md.
#
# A DIFFERENCE YOU WILL SEE AND SHOULD NOT CHASE. In the line topology the two
# end nodes report different `batctl originators` counts, and neither is wrong.
# batman-adv makes the FIRST hard interface added to bat0 the MainIF; its MAC is
# the node's originator address and is announced everywhere, while a secondary
# radio appears as an originator only to neighbours on its own segment. So the
# node on the MainIF's side sees one entry for a multi-radio node and the node
# on the far side sees two. Reversing the add order reverses which is which,
# measured. See docs/evidence/TBR-LINUX-01/2026-08-31-originator-count-differs-by-interface-order.md
#
# WHAT A PASS PROVES. That the kernel's 802.11s implementation forms a peer
# link, that a mesh point reports carrier only once joined, that batman-adv
# accepts a wireless mesh interface as a hard interface and carries traffic
# over it, and that BOTH ENDS CAN ORIGINATE. The far node sending on its own
# account is a separate assertion from the near node's ping returning, because
# a node can have a populated neighbour table, send happily, and lose
# everything: docs/evidence/TBR-NET-01/2026-08-30-collision-exercise.md has
# one. Until 2026-08-30 every assertion here was taken at node 1.
#
# WHAT IT DOES NOT PROVE, and the gap is larger than the result. hwsim models
# the 802.11 MAC. There is no propagation, no path loss, no interference, no
# rate adaptation, no antenna and no regulatory domain in any physical sense.
# Every number TBR-RF-01, TBR-RF-02 and TBR-RF-03 exist to obtain is untouched
# by a green run here, and so is every question about a real vendor driver.
#
# TWO TOPOLOGIES, AND THE SECOND IS THE INTERESTING ONE.
#
#   flat  (default)  every radio on one channel and one mesh id.
#   line  (--line)   three nodes, and node 1 cannot hear node 3.
#
# Every hwsim radio hears every other on a shared channel: with three radios
# each sees two peers, measured. So a flat run cannot demonstrate multi-hop.
#
# The line does, WITHOUT wmediumd, which Debian does not package. Channel
# separation makes the topology instead: node 1 and node 2 share mesh-a on one
# channel, node 2 and node 3 share mesh-b on another, and node 2 carries a
# radio on each with both in one batman-adv interface. Node 1 reaches node 3
# only by node 2 relaying, and node 1 sees exactly one peer, measured.
#
# That is not a trick to get a test to pass. It is the MULE architecture: a
# node with several bearers, joining them into one mesh, is what
# FML-ADR-045 describes and what os/config/networkd.conf.template configures.

set -eu

TOPOLOGY=flat
if [ "${1:-}" = "--line" ]; then
  TOPOLOGY=line
  shift
fi
RADIOS=${1:-2}
[ "$TOPOLOGY" = "line" ] && RADIOS=4
MESH_ID=fml-bench-mesh
MTU=1560
#: Two channels, so that a line topology has two segments that cannot hear
#: each other. 2412 is channel 1 and 2437 is channel 6, non-overlapping.
FREQ_A=2412
FREQ_B=2437

fail() {
  printf 'FAIL: %s\n' "$1" >&2
  exit 1
}

info() {
  printf '  %s\n' "$1"
}

cleanup() {
  i=1
  while [ "$i" -le "$RADIOS" ]; do
    ip netns del "fmlbench$i" 2>/dev/null || true
    i=$((i + 1))
  done
  rmmod mac80211_hwsim 2>/dev/null || true
}

# Registered before anything is created, so an early failure still tidies up.
# A bench that leaves namespaces and a module behind makes the next run lie.
trap cleanup EXIT INT TERM

[ "$(id -u)" -eq 0 ] || fail 'must run as root: it loads a module and creates namespaces.'

for tool in ip iw batctl; do
  command -v "$tool" >/dev/null 2>&1 ||
    fail "$tool is not installed. apt-get install iproute2 iw batctl"
done

if ! modinfo mac80211_hwsim >/dev/null 2>&1; then
  fail 'mac80211_hwsim is not in this kernel. A hosted runner has no wireless
stack at all; this needs an ordinary distribution kernel.'
fi

printf 'Preparing %s virtual radios\n' "$RADIOS"
rmmod mac80211_hwsim 2>/dev/null || true
modprobe mac80211_hwsim "radios=$RADIOS"
sleep 2

# --- the carrier assertion --------------------------------------------------
#
# FML-ADR-059 relies on systemd-networkd refusing to configure a link with no
# carrier, ConfigureWithoutCarrier= defaulting to false, so that
# BatmanAdvanced= cannot apply before wpa_supplicant has associated. That only
# holds if a mesh point has no carrier until it joins. This is where that is
# checked, and it is the assertion most worth keeping.

printf 'Carrier gating, which FML-ADR-059 depends on\n'
ip link set wlan0 down
iw dev wlan0 set type mp
ip link set wlan0 up
sleep 2
before=$(cat /sys/class/net/wlan0/carrier 2>/dev/null || echo unreadable)
[ "$before" = "0" ] ||
  fail "a mesh point reported carrier '$before' before joining, expected 0. FML-ADR-059's gating does not hold on this kernel."
info 'up but not joined: carrier 0'

iw dev wlan0 mesh join "$MESH_ID"
sleep 3
after=$(cat /sys/class/net/wlan0/carrier 2>/dev/null || echo unreadable)
[ "$after" = "1" ] || fail "a joined mesh point reported carrier '$after', expected 1."
info 'joined: carrier 1'
iw dev wlan0 mesh leave 2>/dev/null || true

# --- build the mesh ---------------------------------------------------------

join_mesh() {
  # $1 namespace, $2 device, $3 mesh id, $4 frequency
  ip netns exec "$1" ip link set "$2" down
  ip netns exec "$1" iw dev "$2" set type mp
  ip netns exec "$1" ip link set "$2" mtu "$MTU" up
  ip netns exec "$1" iw dev "$2" mesh join "$3" freq "$4"
}

start_batman() {
  # $1 namespace, $2 host octet, rest: hard interfaces to join to bat0
  ns=$1
  octet=$2
  shift 2
  # BATMAN_IV before the interface exists: the algorithm is fixed at creation,
  # not at the first add. See mule/bringup.py and systemd.netdev(5).
  ip netns exec "$ns" batctl routing_algo BATMAN_IV >/dev/null 2>&1 || true
  ip netns exec "$ns" ip link add name bat0 type batadv

  # Bridge loop avoidance OFF, which FML-ADR-056 decides and
  # os/config/batman-adv.conf.template configures. It is ENABLED BY DEFAULT, so
  # a bench that does not say this is testing a configuration the program has
  # decided against.
  #
  # It is not a detail. Until its claim mechanism settles, batman-adv withholds
  # client frames while every batctl table already reads correct, so the mesh
  # looks converged and carries nothing. Measured here, one variable, a fresh
  # mesh per value: 30972 ms to first reply with it enabled against 2056 ms
  # with it off. .github/workflows/mesh-probe.yml measured the same thing on
  # veth and recorded 31.5s against 2.150s.
  #
  # This line was missing until 2026-08-30. Its absence cost 30s on every run
  # of this bench and was misread, in a draft evidence artifact, as an
  # unexplained property of hwsim.
  ip netns exec "$ns" batctl meshif bat0 bridge_loop_avoidance 0 >/dev/null 2>&1 || true

  for hard in "$@"; do
    ip netns exec "$ns" ip link set "$hard" master bat0
  done
  ip netns exec "$ns" ip addr add "10.41.0.$octet/16" dev bat0
  ip netns exec "$ns" ip link set bat0 up
}

phy_for() {
  iw dev "$1" info 2>/dev/null | awk '/wiphy/ {print "phy"$2}'
}

if [ "$TOPOLOGY" = "line" ]; then
  printf 'Building a line: node 1 and node 3 cannot hear each other\n'
  for n in 1 2 3; do ip netns add "fmlbench$n"; done

  # node 2 takes two radios, one per segment. That is the whole mechanism.
  iw phy "$(phy_for wlan0)" set netns name fmlbench1
  iw phy "$(phy_for wlan1)" set netns name fmlbench2
  iw phy "$(phy_for wlan2)" set netns name fmlbench2
  iw phy "$(phy_for wlan3)" set netns name fmlbench3

  join_mesh fmlbench1 wlan0 "$MESH_ID-a" "$FREQ_A"
  join_mesh fmlbench2 wlan1 "$MESH_ID-a" "$FREQ_A"
  join_mesh fmlbench2 wlan2 "$MESH_ID-b" "$FREQ_B"
  join_mesh fmlbench3 wlan3 "$MESH_ID-b" "$FREQ_B"

  start_batman fmlbench1 1 wlan0
  start_batman fmlbench2 2 wlan1 wlan2
  start_batman fmlbench3 3 wlan3
  sleep 8

  printf 'Assertions\n'
  seen=$(ip netns exec fmlbench1 iw dev wlan0 station dump 2>/dev/null | grep -c '^Station' || true)
  [ "$seen" -eq 1 ] ||
    fail "node 1 sees $seen peers, expected exactly 1. The segments are not separated, so a reachable node 3 would prove nothing."
  info 'node 1 sees exactly one peer: the line is real'

  ip netns exec fmlbench2 batctl meshif bat0 interface 2>/dev/null | grep -q wlan2 ||
    fail 'node 2 is not carrying its second bearer into the mesh.'
  info 'node 2 carries both bearers in one batman-adv interface'

  # The far end of the line has to be separated too. Asserting it only at node 1
  # leaves the case where node 3 can hear both segments, which would make a
  # successful multi-hop result meaningless in the direction that matters.
  seen3=$(ip netns exec fmlbench3 iw dev wlan3 station dump 2>/dev/null | grep -c '^Station' || true)
  [ "$seen3" -eq 1 ] ||
    fail "node 3 sees $seen3 peers, expected exactly 1. The line is only separated at one end."
  info 'node 3 sees exactly one peer: the line is separated at both ends'

  far=10.41.0.3
  FAR_NS=fmlbench3
else
  printf 'Building a flat mesh\n'
  i=1
  while [ "$i" -le "$RADIOS" ]; do
    ns="fmlbench$i"
    dev="wlan$((i - 1))"
    phy=$(phy_for "$dev")
    [ -n "$phy" ] || fail "could not find the phy behind $dev"

    ip netns add "$ns"
    iw phy "$phy" set netns name "$ns"
    join_mesh "$ns" "$dev" "$MESH_ID" "$FREQ_A"
    start_batman "$ns" "$i" "$dev"
    i=$((i + 1))
  done
  sleep 8

  printf 'Assertions\n'
  peers=$(ip netns exec fmlbench1 iw dev wlan0 station dump 2>/dev/null | grep -c '^Station' || true)
  [ "$peers" -ge 1 ] || fail 'no 802.11s peer link established.'
  info "802.11s peer links seen by node 1: $peers"
  far=10.41.0.2
  FAR_NS=fmlbench2
fi

ip netns exec fmlbench1 iw dev wlan0 station dump 2>/dev/null | grep -q 'ESTAB' ||
  fail 'a peer link exists but is not ESTAB.'
info 'peer link state: ESTAB'

ip netns exec fmlbench1 batctl meshif bat0 neighbors 2>/dev/null | grep -q wlan0 ||
  fail 'batman-adv sees no neighbour over the wireless interface.'
info 'batman-adv sees a neighbour over 802.11s'

# A ping is the point: the layers above only matter if traffic crosses.
#
# Waited for rather than slept through. batman-adv convergence is not a fixed
# interval, and the first version of this script slept eight seconds and failed
# on a mesh that came up fine two seconds later. mesh-probe.yml learned the
# same thing the same way and its comments say so: wait for the condition.
deadline=$(($(date +%s) + 60))
crossed=0
while [ "$(date +%s)" -lt "$deadline" ]; do
  if ip netns exec fmlbench1 ping -c 2 -W 2 "$far" >/tmp/fml-bench-ping.$$ 2>&1; then
    crossed=1
    break
  fi
  sleep 3
done
[ "$crossed" -eq 1 ] ||
  fail "traffic did not reach $far within 60s. $(tail -2 /tmp/fml-bench-ping.$$)"
if [ "$TOPOLOGY" = "line" ]; then
  info "node 1 reached node 3 THROUGH node 2: $(grep -o '[0-9]* received' /tmp/fml-bench-ping.$$ | head -1)"
else
  info "traffic crossed batman-adv over 802.11s: $(grep -o '[0-9]* received' /tmp/fml-bench-ping.$$ | head -1)"
fi
rm -f /tmp/fml-bench-ping.$$

# --- and now the other way -------------------------------------------------
#
# WHY A SECOND DIRECTION IS NOT REDUNDANT. A successful ping proves a round
# trip for the pair that sent it, so the test above does show frames returning.
# What it does not show is any other node ORIGINATING traffic: its own ARP, its
# own translation-table lookup, its own next-hop choice. Every assertion above
# this line is taken at node 1, and a bench that only ever asks one node cannot
# see a node that is fine in one direction and dead in the other.
#
# That is not a hypothetical failure. docs/evidence/TBR-NET-01/2026-08-30-collision-exercise.md
# has one: a node whose neighbour table reads REACHABLE, which sends happily,
# and which loses 100% of ten packets over nine seconds because the replies go
# somewhere else. Interrogated from its own console it looks healthy. Node 1
# passing tells you nothing about node 3.
#
# Measured when this was added, on the line topology: all six directed pairs at
# 0% loss, with node 1 and node 3 each reaching the other through node 2.
reverse_deadline=$(($(date +%s) + 60))
returned=0
while [ "$(date +%s)" -lt "$reverse_deadline" ]; do
  if ip netns exec "$FAR_NS" ping -c 2 -W 2 10.41.0.1 >/tmp/fml-bench-rping.$$ 2>&1; then
    returned=1
    break
  fi
  sleep 3
done
[ "$returned" -eq 1 ] ||
  fail "$FAR_NS could not originate traffic to node 1 within 60s, though node 1 reached it. The mesh carries in one direction only. $(tail -2 /tmp/fml-bench-rping.$$)"
info "$FAR_NS originated traffic back to node 1: $(grep -o '[0-9]* received' /tmp/fml-bench-rping.$$ | head -1)"
rm -f /tmp/fml-bench-rping.$$

printf '\n'
printf 'PASS. 802.11s formed, batman-adv carried traffic over it, no radio.\n'
printf 'Tier: SIMULATED. hwsim models the 802.11 MAC and nothing physical.\n'
printf 'This says nothing about RF, and nothing about a real driver.\n'
