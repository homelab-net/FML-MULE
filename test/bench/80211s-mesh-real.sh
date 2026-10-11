#!/bin/bash
# Bring up one real 802.11s mesh node and join it to batman-adv, then gate on a
# single packet. The real-radio counterpart to test/bench/80211s-mesh.sh.
#
# Usage: sudo test/bench/80211s-mesh-real.sh {up <octet>|gate <peer-ip>|status|down}
#
#   up <octet>      configure THIS node; bat0 takes 10.42.0.<octet>/24.
#   gate <peer-ip>  the one-packet gate: peer established, batman sees the
#                   hard interface, and exactly one ICMP echo crosses.
#   status          current mesh and batman state, for evidence capture.
#   down            full teardown; returns the radio to NetworkManager.
#
# WHY THIS EXISTS, AND WHY IT IS NOT 80211s-mesh.sh. That script proves the
# stack on mac80211_hwsim: it runs every node as a network namespace on ONE
# host, and `mesh-traffic.sh` beside it refuses outright to move a real radio.
# Neither can be pointed at hardware. This script is the same configuration
# sequence -- ported from 80211s-mesh.sh's join_mesh/join_batman, value for
# value -- applied to one real radio on one real host, run once per node.
#
# WHAT A RESULT HERE IS. The first real-RF mesh datapoint in this repository:
# every artifact under docs/evidence/TBR-RF-01/ before this one is SIMULATED,
# and os/config/batman-adv.conf.template says plainly that "veth is a perfect
# wire and nothing here has met a radio." This is a radio.
#
# WHAT IT IS NOT. It is not an independent RF witness. The bench mule cannot
# observe this mesh: its Alfa is an AWUS036ACH whose rtl8812au driver offers no
# monitor mode, and the RTL2838 SDR stops near 1.77 GHz with ~2.4 MHz of
# bandwidth against a 5 GHz 20 MHz channel. Every reading below is node-local,
# which is weaker evidence than a capture, and the evidence file says so.
# It is also two nodes, so it proves ONE hop and says nothing about multi-hop.
#
# A NUMBER YOU MUST NOT CHASE. If the first reply takes tens of seconds, that
# is bridge_loop_avoidance left enabled against FML-ADR-056, not a property of
# the radio -- .github/workflows/mesh-probe.yml records 31.5s against 2.150s on
# exactly that one variable. This script disables it; if you see it, the fix is
# a config bug, not a finding.

set -eu

#: Same mesh id and MTU as the hwsim bench, so the two are comparable.
MESH_ID=fml-bench-mesh
#: batman-adv prepends its own header; 1500 on the hard interface fragments at
#: layer 2 and the module says so on every add. os/config/batman-adv.conf.template
#: records 1560 as the figure that solves it.
MTU=1560
#: 5745 is channel 149: UNII-3, and NON-DFS under the `country US: DFS-FCC`
#: regdomain these nodes report. Deliberately NOT the hwsim bench's 2412/2437 --
#: 2.4 GHz here already carries Zobrist-2.4, the bench mule's feralmulenet EUD
#: AP on channel 11, and this node's own wlan0 client, so a 2.4 GHz run would
#: measure that interference and would put the live EUD AP at risk.
FREQ=5745
MESH_IF=bat0
#: NOT the hwsim bench's 10.41.0.0/16: 10.41.0.1/24 is already the bench mule's
#: EUD AP subnet, and reusing it makes this evidence ambiguous to read. The real
#: field prefix is TBR-NET-01's to decide; this is a bench address, not a choice.
PREFIX=10.42.0
#: Select the radio by DRIVER, never by name. docs/bench-hardware-bringup.md
#: makes this a rule for every step: a fuzzy name match once grabbed the real
#: WAN radio and broke it.
DRIVER=mt76x2u
#: FML-ADR-053 selects BATMAN-IV over BATMAN-V, and the template requires it be
#: set BEFORE any interface joins the mesh.
ROUTING_ALGO=BATMAN_IV

fail() { printf 'FAIL: %s\n' "$*" >&2; exit 1; }
note() { printf '  %-22s %s\n' "$1" "$2"; }

[ "$(id -u)" -eq 0 ] || fail 'must run as root'

for tool in ip iw batctl; do
  command -v "$tool" >/dev/null 2>&1 ||
    fail "$tool is not installed. apt-get install iproute2 iw batctl"
done

# The phy whose driver matches, not whose name looks right.
resolve_phy() {
  local p d
  for p in /sys/class/ieee80211/*; do
    [ -e "$p" ] || continue
    d=$(basename "$(readlink -f "$p/device/driver" 2>/dev/null)" 2>/dev/null) || continue
    if [ "$d" = "$DRIVER" ]; then basename "$p"; return 0; fi
  done
  return 1
}

# The inverse of mesh-traffic.sh's guard. That script refuses to move a real
# radio; this one refuses to accept a simulated one, because a SIMULATED result
# recorded as real-RF evidence is the one failure mode that would matter.
refuse_hwsim() {
  local d
  for d in /sys/devices/virtual/mac80211_hwsim/*/ieee80211/phy*; do
    [ -e "$d" ] || continue
    [ "$(basename "$d")" = "$1" ] &&
      fail "$1 is a mac80211_hwsim radio. This script records real-RF evidence; use 80211s-mesh.sh for hwsim."
  done
  return 0
}

netdev_for_phy() {
  local n
  for n in /sys/class/net/*; do
    [ -e "$n/phy80211" ] || continue
    if [ "$(basename "$(readlink -f "$n/phy80211")")" = "$1" ]; then
      basename "$n"; return 0
    fi
  done
  return 1
}

# Resolve once, up front, so every subcommand reports the same radio.
PHY=$(resolve_phy) || fail "no wireless phy with driver $DRIVER on this host"
refuse_hwsim "$PHY"
DEV=$(netdev_for_phy "$PHY") || fail "no net device for $PHY"

mesh_up() {
  local octet=${1:-}
  [ -n "$octet" ] || fail 'usage: up <octet>'

  printf 'Radio\n'
  note 'phy'    "$PHY"
  note 'device' "$DEV"
  note 'driver' "$DRIVER"
  note 'address' "$(cat "/sys/class/net/$DEV/address")"

  # NetworkManager and wpa_supplicant are both active on these nodes and will
  # reclaim the interface mid-test if it is left managed.
  if command -v nmcli >/dev/null 2>&1; then
    nmcli device set "$DEV" managed no >/dev/null 2>&1 || true
    note 'NetworkManager' "$DEV unmanaged"
  fi

  modprobe batman-adv
  # Module-wide and order-sensitive: this must precede the mesh interface.
  batctl routing_algo "$ROUTING_ALGO" >/dev/null 2>&1 ||
    fail "could not set routing_algo to $ROUTING_ALGO (is $MESH_IF already up? run: down)"
  note 'routing_algo' "$(cat /sys/module/batman_adv/parameters/routing_algo 2>/dev/null || echo unknown)"

  printf '\n802.11s\n'
  ip link set "$DEV" down
  iw dev "$DEV" set type mp
  ip link set "$DEV" mtu "$MTU" up
  note 'mtu' "$(cat "/sys/class/net/$DEV/mtu") (intended $MTU)"
  iw dev "$DEV" mesh join "$MESH_ID" freq "$FREQ"
  note 'mesh id' "$MESH_ID"
  note 'frequency' "${FREQ} MHz"
  note 'regdomain' "$(iw reg get 2>/dev/null | awk '/^country/ {print $2; exit}')"

  printf '\nbatman-adv\n'
  ip link add name "$MESH_IF" type batadv 2>/dev/null || true
  # FML-ADR-056 disabled bridge loop avoidance and named a detector in exchange
  # (mule.loops, reading mule.mesh). Leaving it on is the config bug above.
  batctl meshif "$MESH_IF" bridge_loop_avoidance 0
  note 'bridge_loop_avoid' "$(batctl meshif "$MESH_IF" bridge_loop_avoidance 2>/dev/null)"
  batctl meshif "$MESH_IF" multicast_mode 0
  note 'multicast_mode' "$(batctl meshif "$MESH_IF" multicast_mode 2>/dev/null)"
  # Never a bridge holding the mesh interface and an uplink together: FML-ADR-056.
  ip link set "$DEV" master "$MESH_IF"
  ip addr flush dev "$MESH_IF" >/dev/null 2>&1 || true
  ip addr add "$PREFIX.$octet/24" dev "$MESH_IF"
  ip link set "$MESH_IF" up
  note 'hard interface' "$DEV"
  note "$MESH_IF" "$PREFIX.$octet/24"
  note 'batctl' "$(batctl -v 2>/dev/null | head -1)"
}

mesh_status() {
  printf 'Radio: %s (%s, driver %s)\n' "$DEV" "$PHY" "$DRIVER"
  printf '\n-- iw dev %s info\n' "$DEV"
  iw dev "$DEV" info 2>&1 | sed 's/^/   /'
  printf '\n-- mesh peers (iw dev %s station dump)\n' "$DEV"
  iw dev "$DEV" station dump 2>&1 | grep -E 'Station|signal:|mesh plink|expected throughput' | sed 's/^/   /' || true
  printf '\n-- batctl meshif %s neighbors\n' "$MESH_IF"
  batctl meshif "$MESH_IF" neighbors 2>&1 | sed 's/^/   /' || true
  printf '\n-- batctl meshif %s originators\n' "$MESH_IF"
  batctl meshif "$MESH_IF" originators 2>&1 | sed 's/^/   /' || true
  printf '\n-- addresses\n'
  ip -br addr show "$MESH_IF" 2>&1 | sed 's/^/   /' || true
  printf '\n-- provenance\n'
  printf '   kernel    %s\n' "$(uname -r)"
  printf '   batctl    %s\n' "$(batctl -v 2>/dev/null | head -1)"
  printf '   host      %s\n' "$(hostname)"
}

# The gate docs/bench-hardware-bringup.md requires before anything multi-node:
# a failure here is PHY, association or config -- never routing.
mesh_gate() {
  local peer=${1:-} plink origin
  [ -n "$peer" ] || fail 'usage: gate <peer-ip>'

  printf 'Gate 1/3  mesh peer established\n'
  plink=$(iw dev "$DEV" station dump 2>/dev/null | awk '/mesh plink:/ {print $3; exit}')
  [ -n "$plink" ] || fail "no mesh peer on $DEV at all (PHY or association, not routing)"
  [ "$plink" = "ESTAB" ] || fail "mesh peer present but plink is $plink, not ESTAB"
  note 'mesh plink' "$plink"

  printf '\nGate 2/3  batman-adv sees the hard interface\n'
  batctl meshif "$MESH_IF" interface 2>/dev/null | grep -q "$DEV" ||
    fail "$DEV is not a batman-adv hard interface on $MESH_IF"
  note 'hard interface' "$DEV"
  origin=$(batctl meshif "$MESH_IF" originators 2>/dev/null | grep -c '^ \{0,3\}\*' || true)
  note 'originators' "$origin"

  printf '\nGate 3/3  one ICMP echo crosses %s\n' "$MESH_IF"
  # Exactly one packet. The point is that a packet crosses, not how fast.
  if ping -c 1 -W 5 -I "$MESH_IF" "$peer" 2>&1 | sed 's/^/   /'; then
    printf '\nGATE PASSED: one packet crossed a real 802.11s + batman-adv mesh.\n'
  else
    fail "one-packet gate failed to $peer (mesh is up but nothing crossed)"
  fi
}

mesh_down() {
  tc qdisc del dev "$MESH_IF" root >/dev/null 2>&1 || true
  ip link set "$MESH_IF" down >/dev/null 2>&1 || true
  ip link del "$MESH_IF" >/dev/null 2>&1 || true
  iw dev "$DEV" mesh leave >/dev/null 2>&1 || true
  ip link set "$DEV" down >/dev/null 2>&1 || true
  iw dev "$DEV" set type managed >/dev/null 2>&1 || true
  ip link set "$DEV" mtu 1500 >/dev/null 2>&1 || true
  if command -v nmcli >/dev/null 2>&1; then
    nmcli device set "$DEV" managed yes >/dev/null 2>&1 || true
  fi
  printf 'torn down: %s returned to managed/down, %s removed, radio back under NetworkManager\n' "$DEV" "$MESH_IF"
}

case "${1:-}" in
  up)     shift; mesh_up "${1:-}" ;;
  gate)   shift; mesh_gate "${1:-}" ;;
  status) mesh_status ;;
  down)   mesh_down ;;
  *) fail 'usage: 80211s-mesh-real.sh {up <octet>|gate <peer-ip>|status|down}' ;;
esac
