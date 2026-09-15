#!/bin/bash
# Induce a batman-adv bridging loop and detect it live with mule.loops.
#
# Usage: sudo test/bench/loop-detect.sh
#
# WHAT THIS IS FOR. FML-ADR-056 disables batman-adv's bridge loop avoidance and,
# in exchange, asks for a detector -- and says the stronger half of verifying it
# is "a loop that is deliberately created and then detected". mule.loops is that
# detector's decision; mule.mesh is its reader. This builds the loop that
# docs/evidence/TBR-NET-01/2026-08-30-loop-detected-on-the-bench.md reproduced,
# then runs loop_signatures LIVE over the reader and asserts a signature fires.
#
# THE VIOLATION, ON PURPOSE. On both nodes bat0 and a shared veth segment sit in
# one bridge, with bridge_loop_avoidance OFF -- exactly what FML-ADR-056 forbids,
# and its being off is what lets the loop appear (a node that leaves the setting
# at its enabled default gets protection the architecture says it does not have).
#
# WHY IT IS NOT IN CI / WHAT IT IS NOT. Like the other benches here, hwsim needs
# a wireless stack a hosted runner lacks; it models the 802.11 MAC and nothing
# physical. Tier SIMULATED. A signature is a "look", not a proven loop (mule.loops
# says so); here we know a loop exists because we built one.

set -eu

MESH_ID=fml-loop-lab
MTU=1560
FREQ=2412
RADIOS=2
REPO="$(cd "$(dirname "$0")/../.." && pwd)"

fail() {
  printf 'FAIL: %s\n' "$1" >&2
  exit 1
}
info() { printf '  %s\n' "$1"; }
step() { printf '\n== %s ==\n' "$1"; }

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

setup_node() {
  # $1 ns, $2 mesh device, $3 host octet, $4 local veth name
  ns=$1
  dev=$2
  octet=$3
  veth=$4
  ip netns exec "$ns" ip link set "$dev" down
  ip netns exec "$ns" iw dev "$dev" set type mp
  ip netns exec "$ns" ip link set "$dev" mtu "$MTU" up
  ip netns exec "$ns" iw dev "$dev" mesh join "$MESH_ID" freq "$FREQ"
  ip netns exec "$ns" batctl routing_algo BATMAN_IV >/dev/null 2>&1 || true
  ip netns exec "$ns" ip link add name bat0 type batadv
  # Bridge loop avoidance OFF (FML-ADR-056). Its being off is the point of this
  # bench: it is what lets the induced loop appear.
  ip netns exec "$ns" batctl meshif bat0 bridge_loop_avoidance 0 >/dev/null 2>&1 || true
  ip netns exec "$ns" ip link set "$dev" master bat0
  ip netns exec "$ns" ip link set bat0 up
  # The violation: bat0 and the shared veth segment in one bridge.
  ip netns exec "$ns" ip link add name br-field type bridge
  ip netns exec "$ns" ip link set bat0 master br-field
  ip netns exec "$ns" ip link set "$veth" master br-field
  ip netns exec "$ns" ip link set "$veth" up
  ip netns exec "$ns" ip addr add "10.41.0.$octet/16" dev br-field
  ip netns exec "$ns" ip link set br-field up
}

step "Preparing two virtual radios"
rmmod mac80211_hwsim 2>/dev/null || true
modprobe mac80211_hwsim "radios=$RADIOS"
sleep 2

for n in 1 2; do ip netns add "fmlbench$n"; done
move_phy wlan0 fmlbench1
move_phy wlan1 fmlbench2
# The shared segment: a veth pair joining the two namespaces directly, a second
# path besides the 802.11s mesh -- the loop.
ip link add fldveth1 netns fmlbench1 type veth peer name fldveth2 netns fmlbench2

step "Building the loop (bat0 + a shared veth in one bridge, on both nodes)"
setup_node fmlbench1 wlan0 1 fldveth1
setup_node fmlbench2 wlan1 2 fldveth2

step "Traffic, so the translation table populates on both paths"
deadline=$(($(date +%s) + 60))
crossed=0
while [ "$(date +%s)" -lt "$deadline" ]; do
  if ip netns exec fmlbench1 ping -c 2 -W 2 10.41.0.2 >/dev/null 2>&1; then
    crossed=1
    break
  fi
  sleep 3
done
[ "$crossed" -eq 1 ] || fail "the two nodes could not exchange traffic within 60s."
info "traffic crossed; giving batman-adv a moment to announce translations"
ip netns exec fmlbench1 ping -c 20 -i 0.2 10.41.0.2 >/dev/null 2>&1 || true

step "Detecting the loop live with mule.loops over mule.mesh"
ip netns exec fmlbench1 env PYTHONPATH="$REPO" python3 - <<'PY'
import subprocess
import sys

from mule.loops import loop_signatures
from mule.mesh import MeshTranslationReadings


def batctl():
    result = subprocess.run(
        ["batctl", "meshif", "bat0", "transglobal"],
        capture_output=True,
        text=True,
        check=False,
    )
    return result.stdout if result.returncode == 0 else None


signatures = loop_signatures(MeshTranslationReadings(batctl_transglobal=batctl))
for signature in signatures:
    print(f"  signature: {signature}")
if not signatures:
    print("  no signature fired -- the loop was not detected", file=sys.stderr)
    sys.exit(1)
PY
detected=$?
[ "$detected" -eq 0 ] || fail "mule.loops fired no signature on an induced loop."
info "mule.loops detected the induced loop from live batctl/sysfs readings"

printf '\n'
printf 'PASS. A deliberate batman-adv loop was induced and detected live by\n'
printf 'mule.loops over mule.mesh -- the stronger half of FML-ADR-056 verification.\n'
printf 'Tier: SIMULATED. hwsim models the 802.11 MAC and nothing physical.\n'
