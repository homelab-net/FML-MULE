#!/bin/sh
# WAN overlay boundary: does the firewall keep the overlay off the EUD/mesh planes?
#
# Usage: sudo test/bench/wan-overlay-posture.sh
#
# WHAT THIS IS FOR. FML-ADR-082 (with CCR-04) makes the MULE the boundary of the WAN
# overlay: a remote EUD admitted under ASSIGNED_MULE_ONLY reaches only the assigned
# MULE's approved remote-EUD ingress, is never placed on the RF mesh, and the overlay
# is not bridged to the EUD access point. os/config/nftables.conf.template carries that
# boundary. docs/evidence/stage-06-wan-overlay/ holds the pass conditions as not-run.
# This exercises the ones that are firewall/boundary logic and need no real tailnet.
#
# WHAT A PASS PROVES. That the nftables boundary drops the cross-plane paths and admits
# only the ingress port on the overlay interface. It is netns + nftables: SIMULATED,
# per docs/evidence/README.md. It says NOTHING about RF, about Tailscale itself, or
# about WHICH tailnet peer is the assigned MULE -- that identity half is the tailnet
# policy (os/config/tailscale-acl.hujson.template), exercised on a real tailnet, not
# here. It is not HARDWARE-VERIFIED.
#
# THE MODEL. One netns is the MULE with four logical interfaces named as the template
# names them by function: an EUD access point (ap0), the RF mesh (mesh0), the WAN uplink
# (wan0), and the overlay (ovl0, standing for tailscale0). The RF mesh is modeled as a
# plain veth, not batman-adv: the boundary under test is interface-based forwarding (the
# drop rule keys on the mesh interface name), so batman-adv routing and its convergence
# are irrelevant to what is asserted and only add time. The mesh interface is named
# mesh0 here (a real node's is bat0) so a netns veth cannot collide with a real bat0 on a
# development host. Interface names are TBR-LINUX-01.
# Around the MULE: a local EUD on the AP, a remote peer on the overlay (the admitted
# remote EUD), a mesh peer, and an "unrelated infrastructure" host behind the WAN.
#
# Refs: FML-ADR-082 | FML-ADR-068
set -eu

PASS=0
FAIL=0
fail_case() {
  printf '  %-46s FAIL\n' "$1"
  FAIL=$((FAIL + 1))
}
pass_case() {
  printf '  %-46s pass\n' "$1"
  PASS=$((PASS + 1))
}

cleanup() {
  for n in mule eud rem mesh home; do ip netns del "fmlov$n" 2>/dev/null || true; done
}
trap cleanup EXIT INT TERM

[ "$(id -u)" -eq 0 ] || {
  echo "FAIL: must run as root (creates namespaces)"
  exit 1
}
for t in ip nft python3; do command -v "$t" >/dev/null 2>&1 || {
  echo "FAIL: $t not installed"
  exit 1
}; done

ns() {
  n=$1
  shift
  ip netns exec "fmlov$n" "$@"
}

listen() { # <ns> <bind-addr> <port> -- background TCP accept loop
  ns "$1" python3 - "$2" "$3" >/dev/null 2>&1 <<'PY' &
import socket,sys
s=socket.socket(); s.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
s.bind((sys.argv[1],int(sys.argv[2]))); s.listen(16)
while True:
    try: c,_=s.accept(); c.close()
    except Exception: break
PY
}

tcp_ok() { # <ns> <addr> <port> -> 0 if connect succeeds within 1.5s
  ns "$1" python3 - "$2" "$3" <<'PY' >/dev/null 2>&1
import socket,sys
s=socket.socket(); s.settimeout(1.5)
try: s.connect((sys.argv[1],int(sys.argv[2]))); s.close(); sys.exit(0)
except Exception: sys.exit(1)
PY
}

build() {
  cleanup
  for n in mule eud rem mesh home; do
    ip netns add "fmlov$n"
    ns "$n" ip link set lo up
  done
  ns mule sysctl -qw net.ipv4.ip_forward=1

  # EUD access point: mule ap0 <-> eud
  ip link add ap0 netns fmlovmule type veth peer name apx netns fmloveud
  ns mule ip addr add 10.41.0.1/24 dev ap0
  ns mule ip link set ap0 up
  ns eud ip addr add 10.41.0.50/24 dev apx
  ns eud ip link set apx up
  ns eud ip route add default via 10.41.0.1

  # Overlay (tailscale0 stand-in): mule ovl0 <-> rem (the admitted remote EUD)
  ip link add ovl0 netns fmlovmule type veth peer name ovlx netns fmlovrem
  ns mule ip addr add 100.100.0.1/24 dev ovl0
  ns mule ip link set ovl0 up
  ns rem ip addr add 100.100.0.50/24 dev ovlx
  ns rem ip link set ovlx up
  ns rem ip route add default via 100.100.0.1

  # WAN uplink: mule wan0 <-> home (unrelated infrastructure)
  ip link add wan0 netns fmlovmule type veth peer name wanx netns fmlovhome
  ns mule ip addr add 192.0.2.1/24 dev wan0
  ns mule ip link set wan0 up
  ns home ip addr add 192.0.2.2/24 dev wanx
  ns home ip link set wanx up
  ns home ip route add default via 192.0.2.1

  # RF mesh (plain veth stand-in; see header): mule mesh0 <-> mesh peer
  ip link add mesh0 netns fmlovmule type veth peer name meshx netns fmlovmesh
  ns mule ip addr add 10.44.0.1/24 dev mesh0
  ns mule ip link set mesh0 up
  ns mesh ip addr add 10.44.0.2/24 dev meshx
  ns mesh ip link set meshx up
  ns mesh ip route add default via 10.44.0.1
  ns rem ip route add 10.44.0.0/24 via 100.100.0.1
  ns eud ip route add 10.44.0.0/24 via 10.41.0.1

  # services: MULE ingress (8089), a non-ingress service (9999), home/mgmt, mesh svc
  listen mule 0.0.0.0 8089
  listen mule 0.0.0.0 9999
  listen home 192.0.2.2 80
  listen mesh 10.44.0.2 80
  sleep 1
}

apply_boundary() {
  ns mule nft -f - <<'NFT'
table inet filter {
  chain input {
    type filter hook input priority 0; policy drop;
    iif "lo" accept
    ct state established,related accept
    iifname "ap0" accept
    iifname "mesh0" accept
    # overlay terminates on the MULE: only the approved remote-EUD ingress (8089)
    # and admin (22) are exposed on the overlay interface (FML-ADR-082).
    iifname "ovl0" tcp dport 8089 accept
    iifname "ovl0" tcp dport 22 accept
  }
  chain forward {
    type filter hook forward priority 0; policy drop;
    ct state established,related accept
    # FML-ADR-068: an AP EUD reaches the general WAN uplink.
    iifname "ap0" oifname "wan0" accept
    # FML-ADR-082/068 boundary: the overlay is not bridged to the AP or the RF mesh,
    # and the remote EUD gets no general egress. Policy is already drop; these explicit
    # drops make the boundary auditable and let this test show it firing.
    iifname "ap0"  oifname "ovl0" drop
    iifname "ovl0" oifname "ap0"  drop
    iifname "mesh0" oifname "ovl0" drop
    iifname "ovl0" oifname "mesh0" drop
    iifname "ovl0" oifname "wan0" drop
  }
}
table ip nat {
  chain postrouting {
    type nat hook postrouting priority 100; policy accept;
    ip saddr 10.41.0.0/24 oifname "wan0" masquerade
  }
}
NFT
}

echo "FML WAN overlay boundary flat-sat (SIMULATED: netns + nftables; not RF, not Tailscale)"
echo

# BASELINE: with forwarding on and NO boundary, the cross-plane paths are reachable.
# The exercise is meaningless if the boundary has nothing to block, so prove it first.
build
echo "BASELINE (no boundary rules): the paths the boundary must block are open"
if tcp_ok rem 10.44.0.2 80; then printf '  %-46s open\n' 'overlay peer -> RF mesh service'; else fail_case 'baseline overlay->mesh should be open'; fi
if tcp_ok rem 192.0.2.2 80; then printf '  %-46s open\n' 'overlay peer -> unrelated infra'; else fail_case 'baseline overlay->home should be open'; fi
echo

echo "WITH boundary rules applied (os/config/nftables.conf.template, concretised):"
apply_boundary

if tcp_ok eud 192.0.2.2 80 && ! tcp_ok eud 100.100.0.50 22; then
  pass_case 'access-point-passthrough-not-overlay'
else fail_case 'access-point-passthrough-not-overlay'; fi

if ! ns eud ip -o addr show 2>/dev/null | grep -q '100\.100\.0\.' && ! tcp_ok eud 100.100.0.50 22; then
  pass_case 'posture-disabled (EUD has no overlay membership)'
else fail_case 'posture-disabled'; fi

if tcp_ok rem 100.100.0.1 8089 && ! tcp_ok rem 100.100.0.1 9999; then
  pass_case 'assigned-ingress-only (ingress 8089 yes, other port no)'
else fail_case 'assigned-ingress-only'; fi

if ! tcp_ok rem 10.44.0.2 80 && ! ns rem ip link show mesh0 >/dev/null 2>&1; then
  pass_case 'eud-not-on-rf-mesh'
else fail_case 'eud-not-on-rf-mesh'; fi

if ! tcp_ok rem 192.0.2.2 80; then
  pass_case 'unrelated-infrastructure-inaccessible'
else fail_case 'unrelated-infrastructure-inaccessible'; fi

ns mule ip link set ovl0 down
if tcp_ok eud 10.41.0.1 8089 && tcp_ok mesh 10.44.0.1 8089; then
  pass_case 'wan-loss-local-continuity'
else fail_case 'wan-loss-local-continuity'; fi
ns mule ip link set ovl0 up

echo
echo "cases passed: $PASS  failed: $FAIL"
[ "$FAIL" -eq 0 ] || exit 1
