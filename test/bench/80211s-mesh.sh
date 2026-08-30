#!/bin/sh
# Exercise 802.11s association and batman-adv over it, with no radio.
#
# Usage: sudo test/bench/80211s-mesh.sh [node-count]
#
#   node-count  virtual radios to create. Default 2. See the topology note.
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
# WHAT A PASS PROVES. That the kernel's 802.11s implementation forms a peer
# link, that a mesh point reports carrier only once joined, and that batman-adv
# accepts a wireless mesh interface as a hard interface and carries traffic
# over it.
#
# WHAT IT DOES NOT PROVE, and the gap is larger than the result. hwsim models
# the 802.11 MAC. There is no propagation, no path loss, no interference, no
# rate adaptation, no antenna and no regulatory domain in any physical sense.
# Every number TBR-RF-01, TBR-RF-02 and TBR-RF-03 exist to obtain is untouched
# by a green run here, and so is every question about a real vendor driver.
#
# TOPOLOGY, AND WHY THE NODE COUNT DOES NOT BUY MULTI-HOP. Every hwsim radio
# hears every other: with three radios each sees two peers, measured. There is
# no line and therefore no relay, so this cannot demonstrate multi-hop.
# Controlling which radio hears which needs wmediumd, which Debian does not
# package. The veth probe remains the only thing that proves multi-hop, and
# these two do not overlap.

set -eu

RADIOS=${1:-2}
MESH_ID=fml-bench-mesh
MTU=1560

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

printf 'Building the mesh\n'
i=1
while [ "$i" -le "$RADIOS" ]; do
  ns="fmlbench$i"
  dev="wlan$((i - 1))"
  phy=$(iw dev "$dev" info 2>/dev/null | awk '/wiphy/ {print "phy"$2}')
  [ -n "$phy" ] || fail "could not find the phy behind $dev"

  ip netns add "$ns"
  iw phy "$phy" set netns name "$ns"
  ip netns exec "$ns" ip link set "$dev" down
  ip netns exec "$ns" iw dev "$dev" set type mp
  ip netns exec "$ns" ip link set "$dev" mtu "$MTU" up
  ip netns exec "$ns" iw dev "$dev" mesh join "$MESH_ID"

  # Order matters and is mule/bringup.py's: the algorithm is fixed when the
  # interface is created, so it is set before bat0 exists, not after.
  ip netns exec "$ns" batctl routing_algo BATMAN_IV >/dev/null 2>&1 || true
  ip netns exec "$ns" ip link add name bat0 type batadv
  ip netns exec "$ns" ip link set "$dev" master bat0
  ip netns exec "$ns" ip addr add "10.41.0.$i/16" dev bat0
  ip netns exec "$ns" ip link set bat0 up
  i=$((i + 1))
done
sleep 8

# --- assertions -------------------------------------------------------------

printf 'Assertions\n'

peers=$(ip netns exec fmlbench1 iw dev wlan0 station dump 2>/dev/null | grep -c '^Station' || true)
[ "$peers" -ge 1 ] || fail 'no 802.11s peer link established.'
info "802.11s peer links seen by node 1: $peers"

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
  if ip netns exec fmlbench1 ping -c 2 -W 2 10.41.0.2 >/tmp/fml-bench-ping.$$ 2>&1; then
    crossed=1
    break
  fi
  sleep 3
done
[ "$crossed" -eq 1 ] ||
  fail "traffic did not cross within 60s. $(tail -2 /tmp/fml-bench-ping.$$)"
info "traffic crossed batman-adv over 802.11s: $(grep -o '[0-9]* received' /tmp/fml-bench-ping.$$ | head -1)"
rm -f /tmp/fml-bench-ping.$$

printf '\n'
printf 'PASS. 802.11s formed, batman-adv carried traffic over it, no radio.\n'
printf 'Tier: SIMULATED. hwsim models the 802.11 MAC and nothing physical.\n'
printf 'This says nothing about RF, and nothing about a real driver.\n'
