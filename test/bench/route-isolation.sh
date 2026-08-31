#!/bin/sh
# Can any routing mechanism protect the mesh from an overlapping uplink route?
#
# Usage: sudo test/bench/route-isolation.sh
#
# WHAT THIS IS FOR. docs/evidence/TBR-NET-01/2026-08-31-external-network-collision-analysis.md
# showed that an external network overlapping the field prefix silently takes
# part of the mesh away, and named four candidate mechanisms explicitly NOT
# measured. TBR-NET-01's decision needs them measured first: FML-ADR-060 was
# superseded one day after it was written for deciding something untested, and
# this exists so that does not happen twice.
#
# WHAT A PASS PROVES. Nothing about which mechanism to choose. It reproduces the
# failure, applies each candidate, and reports what each one costs. The useful
# output is the table, not the exit code.
#
# THE RESULT THIS WAS BUILT TO FIND. A destination like 10.41.5.7 is claimed by
# two networks at once. No routing mechanism can disambiguate a destination that
# is genuinely ambiguous; it can only choose which claimant to serve. So policy
# routing does not fix the failure, it MOVES it, and only a VRF separates the
# two -- at the cost of every mesh-using application having to bind into it.
#
# WHAT IT DOES NOT PROVE. veth, not radios, and one venue with one overlapping
# /24. It says nothing about a Tailscale subnet router, which is the other route
# source the analysis identified and which needs a tailnet to test.

set -eu

fail() {
  printf 'FAIL: %s\n' "$1" >&2
  exit 1
}

cleanup() {
  for n in mule peer venue; do ip netns del "fmlrt$n" 2>/dev/null || true; done
}
trap cleanup EXIT INT TERM

[ "$(id -u)" -eq 0 ] || fail 'must run as root: it creates namespaces.'
for tool in ip batctl; do
  command -v "$tool" >/dev/null 2>&1 ||
    fail "$tool is not installed. apt-get install iproute2 batctl"
done

ns() {
  n=$1
  shift
  ip netns exec "fmlrt$n" "$@"
}

build() {
  cleanup
  sleep 1
  for n in mule peer venue; do ip netns add "fmlrt$n"; done

  # The mesh: one peer holding an address INSIDE the venue's range and one
  # outside it, so the difference between "some of the mesh" and "all of it" is
  # visible rather than inferred.
  ip link add fmlm1 type veth peer name fmlm2
  ip link set fmlm1 netns fmlrtmule
  ip link set fmlm2 netns fmlrtpeer
  for p in mule peer; do
    ns "$p" ip link add name bat0 type batadv
    # FML-ADR-056. Without it the mesh carries nothing for ~30s and every
    # measurement below would be a timing artefact.
    ns "$p" batctl meshif bat0 bridge_loop_avoidance 0 >/dev/null 2>&1 || true
  done
  ns mule ip link set fmlm1 mtu 1560 up
  ns mule ip link set fmlm1 master bat0
  ns peer ip link set fmlm2 mtu 1560 up
  ns peer ip link set fmlm2 master bat0
  ns mule ip addr add 10.41.0.1/16 dev bat0
  ns peer ip addr add 10.41.5.7/16 dev bat0
  ns peer ip addr add 10.41.9.9/16 dev bat0
  for p in mule peer; do
    ns "$p" ip link set bat0 up
    ns "$p" ip link set lo up
  done

  ip link add fmlu1 type veth peer name fmlu2
  ip link set fmlu1 netns fmlrtmule
  ip link set fmlu2 netns fmlrtvenue
  ns mule ip link set fmlu1 up
  ns venue ip link set fmlu2 up
  ns venue ip link set lo up
  ns venue ip addr add 10.41.5.1/24 dev fmlu2
  sleep 4
}

# reach <label> <addr> [ping-args...] -> prints ok / LOST / unreachable
reach() {
  label=$1
  addr=$2
  shift 2
  out=$(ns mule ping "$@" -c 2 -W 2 "$addr" 2>&1) && verdict=ok || verdict=LOST
  case "$out" in *'Network is unreachable'*) verdict='unreachable' ;; esac
  printf '  %-40s %s\n' "$label" "$verdict"
}

row() {
  reach 'mesh node inside the venue range' 10.41.5.7 "$@"
  reach 'mesh node outside it' 10.41.9.9 "$@"
  reach 'the venue gateway' 10.41.5.1 "$@"
}

printf 'BASELINE, the failure reproduced\n'
build
ns mule ip addr add 10.41.5.20/24 dev fmlu1
sleep 2
row
# The whole exercise is meaningless if the failure does not reproduce.
ns mule ping -c 2 -W 2 10.41.5.7 >/dev/null 2>&1 &&
  fail 'the mesh node inside the venue range was reachable. The failure did not reproduce, so nothing below means anything.'

printf '\nCANDIDATE 1, policy routing: the mesh prefix in its own table\n'
ns mule ip route add 10.41.0.0/16 dev bat0 table 100
ns mule ip rule add to 10.41.0.0/16 lookup 100 priority 100
sleep 1
row
printf '  -> the mesh is whole and the venue gateway is gone. The loss moved.\n'

printf '\nCANDIDATE 4, no overlapping lease on the uplink\n'
build
ns mule ip addr add 192.0.2.20/24 dev fmlu1
ns venue ip addr add 192.0.2.1/24 dev fmlu2
sleep 2
row
reach 'the venue on its own range' 192.0.2.1
printf '  -> nothing overlaps so nothing is lost, but the venue chooses the\n'
printf '     range it hands you and this program does not control it.\n'

printf '\nCANDIDATE 2, a VRF holding the mesh interface\n'
build
ns mule ip addr add 10.41.5.20/24 dev fmlu1
modprobe vrf 2>/dev/null || true
if ns mule ip link add vrf-mesh type vrf table 100 2>/dev/null; then
  ns mule ip link set vrf-mesh up
  ns mule ip link set bat0 master vrf-mesh
  sleep 3
  printf ' from the default VRF, which is what an ordinary application uses:\n'
  row
  printf ' bound into the VRF, which needs a VRF-aware application:\n'
  row -I vrf-mesh
  printf '  -> the only candidate that separates them, and it requires every\n'
  printf '     mesh-using application to bind into the VRF.\n'
else
  printf '  VRF unavailable on this kernel; CONFIG_NET_VRF.\n'
fi

printf '\n'
printf 'No mechanism is selected here. 10.41.5.7 is claimed by two networks at\n'
printf 'once, and no routing rule can disambiguate an ambiguous destination. It\n'
printf 'can only choose which claimant to serve. TBR-NET-01.\n'
printf 'Tier: SIMULATED. veth, no radios, one venue, one overlapping /24.\n'
