#!/bin/bash
# Demonstrate the operator status view over a live batman-adv/hwsim mesh.
#
# Usage: sudo test/bench/operator-view.sh
#
# Brings up a two-node 802.11s + batman-adv mesh on mac80211_hwsim, then runs
# test/bench/operator-view.py inside one node's namespace so it reads that node's
# real radios (iw/batctl) and composes the operator view from them. The mesh peer
# shows as a live link. The node is mesh-only, so the view correctly reports FAULT
# for the missing required wifi_ap (REQUIRED_BEARERS) -- the point is that the view
# tells the truth from real readings, not that this minimal node is GREEN.
#
# WHY IT IS NOT IN CI / WHAT IT IS NOT. Same as the other benches here: hwsim
# needs a wireless stack a hosted runner lacks; it models the 802.11 MAC and
# nothing physical. Tier SIMULATED. This is the buildable Phase-1 slice of the
# Status Aggregator (FML-ADR-046), unblocked by TBR-TAK-01's closure (FML-ADR-071);
# the Service Authority Registry (TBR-HA-01), a fielded daemon (TBR-COMP-01) and a
# production mesh-links reader (parked on TBR-RF-01/RF-03/LINUX-01) stay out.

set -eu

MESH_ID=fml-bench-mesh
MTU=1560
FREQ=2412
RADIOS=2
REPO="$(cd "$(dirname "$0")/../.." && pwd)"

fail() {
  printf 'FAIL: %s\n' "$1" >&2
  exit 1
}

cleanup() {
  for n in 1 2; do ip netns del "fmlbench$n" 2>/dev/null || true; done
  rmmod mac80211_hwsim 2>/dev/null || true
}
trap cleanup EXIT INT TERM

[ "$(id -u)" -eq 0 ] || fail 'must run as root: it loads a module and creates namespaces.'
for tool in ip iw batctl python3; do
  command -v "$tool" >/dev/null 2>&1 || fail "$tool is not installed."
done
modinfo mac80211_hwsim >/dev/null 2>&1 || fail 'mac80211_hwsim is not in this kernel.'

hwsim_phys() {
  for d in /sys/devices/virtual/mac80211_hwsim/*/ieee80211/phy*; do
    [ -e "$d" ] && basename "$d"
  done
}
phy_for() { iw dev "$1" info 2>/dev/null | awk '/wiphy/ {print "phy"$2}'; }
move_phy() {
  phy="$(phy_for "$1")"
  [ -n "$phy" ] || fail "no phy behind $1"
  hwsim_phys | grep -qx "$phy" || fail "$1 ($phy) is not a hwsim radio; refusing to move it."
  iw phy "$phy" set netns name "$2"
}

printf 'Preparing %s virtual radios\n' "$RADIOS"
rmmod mac80211_hwsim 2>/dev/null || true
modprobe mac80211_hwsim "radios=$RADIOS"
sleep 2

for n in 1 2; do ip netns add "fmlbench$n"; done
move_phy wlan0 fmlbench1
move_phy wlan1 fmlbench2
octet=1
for n in 1 2; do
  ns="fmlbench$n"
  dev="wlan$((n - 1))"
  ip netns exec "$ns" ip link set "$dev" down
  ip netns exec "$ns" iw dev "$dev" set type mp
  ip netns exec "$ns" ip link set "$dev" mtu "$MTU" up
  ip netns exec "$ns" iw dev "$dev" mesh join "$MESH_ID" freq "$FREQ"
  ip netns exec "$ns" batctl routing_algo BATMAN_IV >/dev/null 2>&1 || true
  ip netns exec "$ns" ip link add name bat0 type batadv
  # Bridge loop avoidance OFF, permanently (FML-ADR-056).
  ip netns exec "$ns" batctl meshif bat0 bridge_loop_avoidance 0 >/dev/null 2>&1 || true
  ip netns exec "$ns" ip link set "$dev" master bat0
  ip netns exec "$ns" ip addr add "10.41.0.$octet/16" dev bat0
  ip netns exec "$ns" ip link set bat0 up
  octet=$((octet + 1))
done

# Wait for the condition, never sleep a fixed interval.
deadline=$(($(date +%s) + 60))
while [ "$(date +%s)" -lt "$deadline" ]; do
  ip netns exec fmlbench1 ping -c 2 -W 2 10.41.0.2 >/dev/null 2>&1 && break
  sleep 2
done
ip netns exec fmlbench1 ping -c 1 -W 2 10.41.0.2 >/dev/null 2>&1 ||
  fail 'mesh did not converge within 60s.'
printf 'Mesh converged; node 1 has a live peer.\n\n'

printf '=== operator view (text) ===\n'
ip netns exec fmlbench1 env PYTHONPATH="$REPO" python3 "$REPO/test/bench/operator-view.py" --once
printf '\n=== operator view (JSON, the served schema) ===\n'
ip netns exec fmlbench1 env PYTHONPATH="$REPO" python3 "$REPO/test/bench/operator-view.py" --once --json

printf '\nTier: SIMULATED. hwsim models the 802.11 MAC and nothing physical.\n'
