#!/bin/sh
# Exercise batman-adv gateway mode: sharing a WAN uplink across the mesh.
#
# Usage: sudo test/bench/wan-gateway-sharing.sh
#
# WHAT THIS IS FOR. TBR-NET-04 asks how a mesh with several WAN uplinks decides
# which node's uplink carries a WAN-less node's traffic, and whether uplinks are
# pooled or held as failover. FML-ADR-069 decides WAN is a mesh-wide capability
# and names no mechanism; FML-ADR-068 is the node-local first step. This bench
# exercises the routing-logic half of TBR-NET-04's closure evidence on
# mac80211_hwsim: two gateway-holding nodes, one WAN-less node, and it records
# which gateway the client selects, that the WAN-less node reaches a peer's
# uplink, failover when the serving gateway leaves, and the default-route state
# on both sides of an induced partition.
#
# WHY IT IS NOT IN CI. Like test/bench/80211s-mesh.sh, mac80211_hwsim needs a
# wireless stack a hosted runner does not have. This runs on a development
# machine with an ordinary distribution kernel. See docs/dev-machine.md.
#
# THE MECHANISM, AND IT IS batman-adv's OWN. A gateway node runs
# `gw_mode server` with a bandwidth class; the WAN-less node runs `gw_mode
# client` and batman-adv steers its DHCP to the SELECTED gateway. So the lease
# the client obtains, and the default route it installs, reveal batman's own
# selection -- this is not a route set by hand. The client then reaches the
# internet through that gateway's uplink by source NAT on the gateway, which is
# the FML-ADR-068 rule generalised one hop across the mesh.
#
# WHAT A PASS RECORDS (the TBR-NET-04 closure-evidence bullets):
#   1. which gateway the client selects, read from the DHCP lease and route;
#   2. that a WAN-less node reaches a peer's uplink (a server that exists ONLY
#      behind that uplink, so reaching it cannot be the mesh);
#   3. failover: when the serving gateway leaves, the client re-selects the
#      surviving gateway and reaches ITS uplink instead;
#   4. default-route state on both sides of an induced partition, and recovery
#      when the client rejoins.
#
# WHAT IT DOES NOT PROVE. hwsim models the 802.11 MAC and nothing physical: no
# propagation, no path loss, no rate adaptation. So no THROUGHPUT number here is
# a WAN throughput -- the closure evidence's throughput bullet is a hardware
# item (TBR-NET-04 is requires-hardware: partly), and this records reachability
# and latency only. Which gateway hwsim's equal-TQ tie-break selects is not a
# statement about which a real mesh would; the bench records the selection, it
# does not assert a particular winner. And the CONOPS section 43 overlay
# boundary is enforced by the firewall (nftables, EUD-prefix match), not by
# routing: this bench asserts only that no secure-overlay interface exists in
# the shared path, i.e. the uplink shared is the GENERAL uplink.
#
# Refs: TBR-NET-04 | FML-ADR-069 | FML-ADR-068

set -eu

MESH_ID=fml-gw-bench
MTU=1560
FREQ=2412
# Distinct per-uplink server addresses. Reaching 10.201.0.254 can only be node
# 2's uplink and 10.202.0.254 only node 3's, because each lives in a namespace
# reachable through one gateway's NAT and nowhere else.
WAN_A=10.201.0.254
WAN_B=10.202.0.254
UDHCPC_SCRIPT=/tmp/fml-gw-udhcpc.$$

fail() {
  printf 'FAIL: %s\n' "$1" >&2
  exit 1
}

info() {
  printf '  %s\n' "$1"
}

step() {
  printf '\n== %s ==\n' "$1"
}

cleanup() {
  # dnsmasq daemonises and, if left running, holds an inherited pipe fd open,
  # so kill it by its pid file before anything else. Its command line names no
  # namespace, so a pattern match would miss it.
  for pf in /tmp/fml-gw-dns2.pid /tmp/fml-gw-dns3.pid; do
    if [ -f "$pf" ]; then
      kill "$(cat "$pf")" 2>/dev/null || true
    fi
  done
  for n in 1 2 3; do
    ip netns del "fmlgw$n" 2>/dev/null || true
  done
  ip netns del fmlwanA 2>/dev/null || true
  ip netns del fmlwanB 2>/dev/null || true
  rm -f "$UDHCPC_SCRIPT" /tmp/fml-gw-dns2.pid /tmp/fml-gw-dns3.pid
  rmmod mac80211_hwsim 2>/dev/null || true
}
trap cleanup EXIT INT TERM

[ "$(id -u)" -eq 0 ] || fail 'must run as root: it loads a module and creates namespaces.'

for tool in ip iw batctl dnsmasq iptables busybox; do
  command -v "$tool" >/dev/null 2>&1 ||
    fail "$tool is not installed. apt-get install iproute2 iw batctl dnsmasq iptables busybox"
done

if ! modinfo mac80211_hwsim >/dev/null 2>&1; then
  fail 'mac80211_hwsim is not in this kernel. A hosted runner has no wireless
stack at all; this needs an ordinary distribution kernel.'
fi

# A lease-applying script for busybox udhcpc: it has no default one in a bare
# namespace. It applies the address and default route, and prints the lease so
# the run records which gateway answered.
cat >"$UDHCPC_SCRIPT" <<'EOS'
#!/bin/sh
case "$1" in
  bound | renew)
    ip addr flush dev "$interface"
    ip addr add "$ip/16" dev "$interface"
    [ -n "${router:-}" ] && ip route replace default via "$router" dev "$interface"
    echo "LEASE ip=$ip router=$router"
    ;;
esac
EOS
chmod +x "$UDHCPC_SCRIPT"

phy_for() {
  iw dev "$1" info 2>/dev/null | awk '/wiphy/ {print "phy"$2}'
}

join_mesh() {
  # $1 namespace, $2 device
  ip netns exec "$1" ip link set "$2" down
  ip netns exec "$1" iw dev "$2" set type mp
  ip netns exec "$1" ip link set "$2" mtu "$MTU" up
  ip netns exec "$1" iw dev "$2" mesh join "$MESH_ID" freq "$FREQ"
}

start_batman() {
  # $1 namespace, $2 device
  ns=$1
  dev=$2
  # BATMAN_IV before the interface exists: the algorithm is fixed at creation.
  # FML-ADR-053.
  ip netns exec "$ns" batctl routing_algo BATMAN_IV >/dev/null 2>&1 || true
  ip netns exec "$ns" ip link add name bat0 type batadv
  # Bridge loop avoidance OFF, which FML-ADR-056 decides and
  # os/config/batman-adv.conf.template configures. It is ENABLED BY DEFAULT, so
  # a bench that does not say this is testing a configuration the program has
  # decided against, and it withholds client frames for ~30s while every table
  # already reads converged. See test/bench/80211s-mesh.sh for the measurement.
  ip netns exec "$ns" batctl meshif bat0 bridge_loop_avoidance 0 >/dev/null 2>&1 || true
  ip netns exec "$ns" ip link set "$dev" master bat0
  ip netns exec "$ns" ip link set bat0 up
}

# Count the gateways the client currently sees. gateways_json has one object
# per gateway and nothing else, so counting orig_address is exact -- the plain
# `gateways` table repeats the node's own MAC in its header line, which a MAC
# grep would miscount.
count_gw() {
  ip netns exec fmlgw1 batctl meshif bat0 gateways_json 2>/dev/null |
    grep -o 'orig_address' | grep -c . || true
}

# A gateway node: a static mesh address, gateway mode with a bandwidth class, an
# uplink veth into a WAN namespace, NAT for the mesh prefix out that uplink, and
# a DHCP server whose lease range names the node so the client's lease says
# which gateway it reached.
make_gateway() {
  # $1 ns, $2 mesh octet, $3 wan-ns, $4 uplink cidr base (e.g. 10.201.0),
  # $5 dhcp range third octet, $6 gateway bandwidth class (down/up)
  ns=$1
  octet=$2
  wanns=$3
  ulbase=$4
  drange=$5
  bw=$6
  ip netns exec "$ns" ip addr add "10.41.0.$octet/16" dev bat0
  # Announce as a gateway. FML-ADR-069 / TBR-NET-04: this is the batman-native
  # mechanism the trade weighs against policy routing.
  ip netns exec "$ns" batctl meshif bat0 gw_mode server "$bw"

  ip netns add "$wanns"
  ip link add "up$octet" netns "$ns" type veth peer name "wan$octet" netns "$wanns"
  ip netns exec "$ns" ip addr add "$ulbase.1/24" dev "up$octet"
  ip netns exec "$ns" ip link set "up$octet" up
  ip netns exec "$wanns" ip addr add "$ulbase.254/24" dev "wan$octet"
  ip netns exec "$wanns" ip link set "wan$octet" up
  ip netns exec "$wanns" ip link set lo up

  ip netns exec "$ns" sysctl -qw net.ipv4.ip_forward=1
  # Source NAT the mesh prefix out the uplink -- the FML-ADR-068 rule, one hop
  # across the mesh. Scoped to the mesh prefix on purpose (FML-ADR-068 note):
  # nothing else is masqueraded.
  ip netns exec "$ns" iptables -t nat -A POSTROUTING -s 10.41.0.0/16 -o "up$octet" -j MASQUERADE
  ip netns exec "$ns" iptables -A FORWARD -i bat0 -o "up$octet" -j ACCEPT
  ip netns exec "$ns" iptables -A FORWARD -i "up$octet" -o bat0 -m state --state ESTABLISHED,RELATED -j ACCEPT

  # DHCP for the mesh: the range's third octet names the gateway, so a client
  # lease of 10.41.$drange.x means batman selected THIS gateway.
  # Redirected off this script's stdout: dnsmasq daemonises and would otherwise
  # hold the inherited pipe open, so a wrapping `| grep` never sees EOF.
  ip netns exec "$ns" dnsmasq --interface=bat0 --bind-interfaces --except-interface=lo \
    --dhcp-range="10.41.$drange.10,10.41.$drange.100,255.255.0.0" \
    --dhcp-option=3,"10.41.0.$octet" --dhcp-authoritative --leasefile-ro \
    --pid-file="/tmp/fml-gw-dns$octet.pid" >/dev/null 2>&1
}

client_dhcp() {
  # Runs udhcpc on the client and returns the leased router (selected gateway)
  # via the LEASE line. Empty if no gateway answered.
  ip netns exec fmlgw1 ip addr flush dev bat0
  ip netns exec fmlgw1 ip route del default 2>/dev/null || true
  ip netns exec fmlgw1 busybox udhcpc -i bat0 -n -q -t 10 -T 3 -s "$UDHCPC_SCRIPT" 2>&1 |
    sed -n 's/^LEASE //p'
}

selected_gateway() {
  ip netns exec fmlgw1 ip route show default 2>/dev/null | awk '{print $3; exit}'
}

wan_behind() {
  # map a selected gateway mesh IP to the server that lives ONLY behind it
  case "$1" in
    10.41.0.2) echo "$WAN_A" ;;
    10.41.0.3) echo "$WAN_B" ;;
    *) echo "" ;;
  esac
}

# --- build ------------------------------------------------------------------

step "Preparing three virtual radios"
rmmod mac80211_hwsim 2>/dev/null || true
modprobe mac80211_hwsim radios=3
sleep 2

i=1
for dev in wlan0 wlan1 wlan2; do
  ns="fmlgw$i"
  phy=$(phy_for "$dev")
  [ -n "$phy" ] || fail "could not find the phy behind $dev"
  ip netns add "$ns"
  # A fresh namespace has lo DOWN; bring it up so a local-stack check later
  # tests partition behaviour and not a loopback nobody enabled.
  ip netns exec "$ns" ip link set lo up
  iw phy "$phy" set netns name "$ns"
  join_mesh "$ns" "$dev"
  start_batman "$ns" "$dev"
  i=$((i + 1))
done
info "node 1 = WAN-less client, node 2 = gateway A, node 3 = gateway B"

# The client keeps a static address only long enough to prove the mesh carries
# traffic; it is flushed before DHCP so the lease is the only source of its
# address. Gateways get their addresses inside make_gateway.
ip netns exec fmlgw1 ip addr add 10.41.0.1/16 dev bat0

step "Mesh forms and carries traffic (single-step before anything clever)"
ip netns exec fmlgw2 ip addr add 10.41.0.2/16 dev bat0
ip netns exec fmlgw3 ip addr add 10.41.0.3/16 dev bat0
deadline=$(($(date +%s) + 60))
reached2=0
reached3=0
while [ "$(date +%s)" -lt "$deadline" ]; do
  [ "$reached2" -eq 0 ] && ip netns exec fmlgw1 ping -c1 -W2 10.41.0.2 >/dev/null 2>&1 && reached2=1
  [ "$reached3" -eq 0 ] && ip netns exec fmlgw1 ping -c1 -W2 10.41.0.3 >/dev/null 2>&1 && reached3=1
  [ "$reached2" -eq 1 ] && [ "$reached3" -eq 1 ] && break
  sleep 3
done
if [ "$reached2" -ne 1 ] || [ "$reached3" -ne 1 ]; then
  fail "client could not reach both gateway nodes over the mesh (n2=$reached2 n3=$reached3)."
fi
info "client reaches both gateway nodes over the mesh"
# node 2 and node 3 keep their static mesh addresses; the client's is removed so
# only DHCP gives it one.
ip netns exec fmlgw2 ip addr del 10.41.0.2/16 dev bat0 2>/dev/null || true
ip netns exec fmlgw3 ip addr del 10.41.0.3/16 dev bat0 2>/dev/null || true

step "Gateways come up with uplinks (node 2 -> WAN A, node 3 -> WAN B)"
# Distinct bandwidth classes so the two gateways are individually identifiable
# in the client's gateway list; which one hwsim's equal-TQ tie-break selects is
# recorded, not asserted.
make_gateway fmlgw2 2 fmlwanA 10.201.0 2 100000/20000
make_gateway fmlgw3 3 fmlwanB 10.202.0 3 2000/500
# The WAN-less node enters gateway client mode: batman-adv now steers its DHCP
# to whichever gateway it selects.
ip netns exec fmlgw1 batctl meshif bat0 gw_mode client
# The client holds NO uplink of its own: assert it, so "reaches WAN" cannot be
# the client's own link.
extra=$(ip netns exec fmlgw1 ip -o link show 2>/dev/null |
  awk -F': ' '{print $2}' | grep -vE '^(lo|bat0|wlan0)$' || true)
if [ -n "$extra" ]; then
  fail "the client has interface(s) beyond lo/bat0/wlan0 ($extra); it is not WAN-less."
fi
info "client is WAN-less: only lo, wlan0 and bat0 exist in its namespace"
# And no secure-overlay interface exists anywhere in the shared path (CONOPS 43:
# the uplink shared is the GENERAL uplink, never the overlay).
for n in 1 2 3; do
  if ip netns exec "fmlgw$n" ip -o link show 2>/dev/null | grep -qiE 'wg|tailscale|tun| overlay'; then
    fail "an overlay-like interface exists in fmlgw$n; the shared path must be the general uplink."
  fi
done
info "no wireguard/tailscale/tun interface in any node: the shared uplink is the general one"

step "1. Gateway announcement and election"
gwdeadline=$(($(date +%s) + 90))
seen=0
while [ "$(date +%s)" -lt "$gwdeadline" ]; do
  ip netns exec fmlgw1 ping -c1 -W1 10.41.0.2 >/dev/null 2>&1 || true
  ip netns exec fmlgw1 ping -c1 -W1 10.41.0.3 >/dev/null 2>&1 || true
  seen=$(count_gw)
  [ "$seen" -ge 2 ] && break
  sleep 5
done
[ "$seen" -ge 2 ] || fail "client saw $seen gateways within 90s, expected 2."
info "client sees both gateways:"
ip netns exec fmlgw1 batctl meshif bat0 gateways 2>&1 | sed 's/^/    /'
lease=$(client_dhcp)
[ -n "$lease" ] || fail "client obtained no DHCP lease; no gateway was selected."
sel=$(selected_gateway)
[ -n "$sel" ] || fail "client has no default route after DHCP."
info "batman selected gateway $sel; client lease: $lease"

step "2. A WAN-less node reaches the selected peer's uplink"
wan=$(wan_behind "$sel")
[ -n "$wan" ] || fail "selected gateway $sel maps to no known uplink."
ip netns exec fmlgw1 ping -c3 -W3 "$wan" >/tmp/fml-gw-wan.$$ 2>&1 ||
  fail "client could not reach $wan through gateway $sel. $(tail -2 /tmp/fml-gw-wan.$$)"
info "client reached $wan (only behind gateway $sel's uplink): $(grep -o '[0-9]* received' /tmp/fml-gw-wan.$$ | head -1)"
# Cross-check: the client must NOT reach the OTHER uplink's server, because its
# default route is the selected gateway and the other server lives only behind
# the other uplink. If it could, the result above would not prove the path.
other_wan="$WAN_A"
[ "$wan" = "$WAN_A" ] && other_wan="$WAN_B"
if ip netns exec fmlgw1 ping -c1 -W2 "$other_wan" >/dev/null 2>&1; then
  fail "client also reached $other_wan; the uplinks are not isolated and the reach proves nothing."
fi
info "client cannot reach $other_wan: the reach above is genuinely through $sel's uplink"
rm -f /tmp/fml-gw-wan.$$

step "3. Failover: the serving gateway leaves"
losing_ns=fmlgw2
[ "$sel" = "10.41.0.3" ] && losing_ns=fmlgw3
info "taking gateway $sel ($losing_ns) out of service"
ip netns exec "$losing_ns" batctl meshif bat0 gw_mode off
# and drop its uplink, so if any stale route lingered it could not carry traffic
ul=up2
[ "$losing_ns" = "fmlgw3" ] && ul=up3
ip netns exec "$losing_ns" ip link set "$ul" down
# wait for the client to stop seeing the departed gateway
fdeadline=$(($(date +%s) + 90))
while [ "$(date +%s)" -lt "$fdeadline" ]; do
  now=$(count_gw)
  [ "$now" -le 1 ] && break
  sleep 5
done
lease2=$(client_dhcp)
[ -n "$lease2" ] || fail "after the gateway left, the client got no lease; it did not fail over."
sel2=$(selected_gateway)
[ "$sel2" = "$sel" ] && fail "client still points at the departed gateway $sel; no failover."
info "client re-selected surviving gateway $sel2; lease: $lease2"
wan2=$(wan_behind "$sel2")
ip netns exec fmlgw1 ping -c3 -W3 "$wan2" >/tmp/fml-gw-wan2.$$ 2>&1 ||
  fail "after failover the client could not reach $wan2 through $sel2. $(tail -2 /tmp/fml-gw-wan2.$$)"
info "client now reaches $wan2 through the surviving uplink $sel2: $(grep -o '[0-9]* received' /tmp/fml-gw-wan2.$$ | head -1)"
rm -f /tmp/fml-gw-wan2.$$

step "4. Induced partition, and the default-route state on both sides"
info "isolating the client from the mesh (it leaves the 802.11s mesh)"
ip netns exec fmlgw1 iw dev wlan0 mesh leave 2>/dev/null || true
pdeadline=$(($(date +%s) + 60))
while [ "$(date +%s)" -lt "$pdeadline" ]; do
  gw=$(count_gw)
  [ "$gw" -eq 0 ] && break
  sleep 3
done
info "client side of the partition:"
info "  gateways seen: $(count_gw)"
info "  default route: $(ip netns exec fmlgw1 ip route show default 2>/dev/null || echo none)"
if ip netns exec fmlgw1 ping -c1 -W2 "$wan2" >/dev/null 2>&1; then
  fail "the isolated client still reached the WAN; the partition is not real."
fi
info "  WAN unreachable from the isolated client, as it must be"
info "  (the default route can linger stale until batman ages the gateway out;"
info "   what matters is that it carries nothing, shown above)"
# Local services on the client survive the loss of WAN: its own stack is up.
ip netns exec fmlgw1 ping -c1 -W2 127.0.0.1 >/dev/null 2>&1 ||
  fail "the client lost its own local stack on partition; it should only lose WAN."
info "  client keeps its own local stack (CONOPS 41: lose WAN, not local services)"
info "gateway side of the partition ($sel2 keeps its uplink):"
gwns=fmlgw2
[ "$sel2" = "10.41.0.3" ] && gwns=fmlgw3
ip netns exec "$gwns" ping -c1 -W2 "$wan2" >/dev/null 2>&1 ||
  fail "the surviving gateway lost its own uplink during the partition."
info "  gateway $sel2 still reaches its uplink server $wan2"

step "Recovery: the client rejoins"
ip netns exec fmlgw1 iw dev wlan0 mesh join "$MESH_ID" freq "$FREQ"
rdeadline=$(($(date +%s) + 90))
recovered=0
while [ "$(date +%s)" -lt "$rdeadline" ]; do
  ip netns exec fmlgw1 ping -c1 -W1 "${sel2}" >/dev/null 2>&1 || true
  if [ -n "$(client_dhcp)" ] && ip netns exec fmlgw1 ping -c2 -W3 "$wan2" >/dev/null 2>&1; then
    recovered=1
    break
  fi
  sleep 5
done
[ "$recovered" -eq 1 ] ||
  fail "client did not recover WAN through $sel2 within 90s of rejoining."
info "client rejoined, re-selected a gateway and reached the WAN again"

printf '\n'
printf 'PASS. batman-adv gateway mode shared a WAN uplink across the mesh:\n'
printf '  a WAN-less node selected a gateway, reached its uplink, failed over\n'
printf '  to the surviving uplink, lost only WAN on partition, and recovered.\n'
printf 'Tier: SIMULATED. hwsim models the 802.11 MAC and nothing physical; no\n'
printf 'number here is a WAN throughput. TBR-NET-04 pooling-vs-failover and the\n'
printf 'RF and real-uplink behaviour are hardware items.\n'
