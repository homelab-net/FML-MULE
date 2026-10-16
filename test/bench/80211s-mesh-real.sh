#!/bin/bash
# Bring up one real 802.11s mesh node and join it to batman-adv, then gate on a
# single packet. The real-radio counterpart to test/bench/80211s-mesh.sh.
#
# Usage: sudo test/bench/80211s-mesh-real.sh
#            {up <octet>|gate <peer-ip>|status|peers|line-assert <n>|hops <ip>|down}
#
#   up <octet>      configure THIS node; bat0 takes 10.42.0.<octet>/24.
#   gate <peer-ip>  the one-packet gate: peer established, batman sees the
#                   hard interface, and exactly one ICMP echo crosses.
#   status          current mesh and batman state, for evidence capture.
#   peers           established mesh peers with signal, for positioning nodes.
#   line-assert <n> fail unless this node sees exactly <n> established peers.
#   hops <ip>       assert a RELAYED route exists and measure RTT to <ip>.
#   down            full teardown; returns the radio to NetworkManager.
#
# STATUS OF THE LINE SUBCOMMANDS, precisely. `peers`, `line-assert` and `hops`
# exist for Step 2's multi-hop item, which needs three mesh nodes. At the time
# of writing this bench has exactly TWO mesh-capable radios (both MT7612U), and
# no third candidate exists: the bench mule's phy0 does not list `mesh point`
# under supported interface modes -- it appears only in that phy's frame-type
# tables, which is not a mode declaration -- and it is that host's sole uplink
# besides; its phy1 `rtl8812au` offers managed and AP only.
#
# What that let us exercise on a two-node mesh, and what it did not:
#
#   EXERCISED  `peers` against real radios; `line-assert 1` passing on an end
#              node; `line-assert 2` failing loudly; and `hops` correctly
#              REFUSING a flat mesh, which also confirms the originator-table
#              parsing against real `batctl 2025.4` output. Separately, the
#              hwsim refusal below was exercised for real: `mac80211_hwsim` was
#              loaded, `DRIVER=mac80211_hwsim` resolved phy2 and was refused,
#              the real radio kept working throughout, and the module was
#              unloaded again.
#   UNTESTED   the positive multi-hop path: `hops` reporting a relayed route
#              and a two-hop RTT. Nothing with two radios can reach it.
#
# So the failure paths are proven and the success path is not. Treat the first
# three-node run as debugging, not as measurement.
#
# WHY A LINE NEEDS ONLY THREE RADIOS HERE, NOT FOUR. `80211s-mesh.sh --line`
# uses four because every `mac80211_hwsim` radio hears every other, so the two
# segments must be separated by channel and the relay needs one radio per
# channel. Real radios have propagation: put the end nodes out of each other's
# range and one channel and one radio per node suffice. That is what
# `line-assert` is for -- at -13 dBm, which is what two of these adapters read
# on a bench, the end nodes hear each other perfectly well and the result is a
# flat three-node mesh that proves nothing about relaying.
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
#: Channel width for the mesh BSS, and the single most consequential value in
#: this file for throughput. `iw ... mesh join` takes
#: NOHT|HT20|HT40+|HT40-|80MHz and **defaults to NOHT when omitted**, which is
#: what the first runs of this script did, inheriting the omission from
#: 80211s-mesh.sh where it did not matter because hwsim has no PHY. NOHT caps
#: the link at the 802.11a legacy ceiling of 54 MBit/s on a part that advertises
#: HT20/HT40, MCS 0-15 and VHT80. Measured goodput at NOHT was 19.6 Mbps.
#:
#: Measured on this bench, 64 MiB over HTTP on bat0, one hop, md5 verified:
#:
#:   NOHT    54 MBit/s PHY, estimate  29.6 Mbps, goodput  19.6 Mbps   1.0x
#:   HT40+  270 MBit/s PHY, estimate 143.5 Mbps, goodput  89.5 Mbps   4.6x
#:   80MHz  780 MBit/s PHY, estimate 208.9 Mbps, goodput 114.7 Mbps   5.9x
#:
#: HT40+ is the default here because 80MHz buys 28% more goodput for twice the
#: channel occupancy, and on a field MANET spectrum reuse and interference
#: susceptibility are not free. That is a trade-off, and the trade-off is
#: TBR-RF-01's to settle, not this script's: treat HT40+ as a BENCH DEFAULT that
#: beats an accidental NOHT, not as a program decision. Override with WIDTH=.
#:
#: Both nodes must use the SAME width or they will not peer.
WIDTH=${WIDTH:-HT40+}
MESH_IF=bat0
#: NOT the hwsim bench's 10.41.0.0/16: 10.41.0.1/24 is already the bench mule's
#: EUD AP subnet, and reusing it makes this evidence ambiguous to read. The real
#: field prefix is TBR-NET-01's to decide; this is a bench address, not a choice.
PREFIX=10.42.0
#: Select the radio by DRIVER, never by name. docs/bench-hardware-bringup.md
#: makes this a rule for every step: a fuzzy name match once grabbed the real
#: WAN radio and broke it.
#:
#: Overridable for two reasons: another mesh-capable chipset can be driven
#: without editing this file, and setting it to `mac80211_hwsim` is how the
#: refusal guard below is exercised, which is otherwise unreachable on a bench
#: that has only real radios.
DRIVER=${DRIVER:-mt76x2u}
#: FML-ADR-053 selects BATMAN-IV over BATMAN-V, and the template requires it be
#: set BEFORE any interface joins the mesh.
ROUTING_ALGO=BATMAN_IV

fail() {
  printf 'FAIL: %s\n' "$*" >&2
  exit 1
}
note() { printf '  %-22s %s\n' "$1" "$2"; }

# Throttle state, as provenance. docs/bench-hardware-bringup.md requires the
# kernel, radio, driver and image with every result; this belongs in that list
# and was missing from it.
#
# WHY IT MATTERS MORE THAN IT LOOKS. Both bench nodes were found under-voltage
# and pinned at 600 MHz against a nominal 1.5 GHz, which moved mesh RTT from
# 0.9 ms to 61.8 ms on a link whose every radio indicator read healthy -- 400
# MBit/s, -13 dBm, powersave off. A throttled node UNDER-reports the bearer,
# which is the direction that gets believed, so a figure taken on one is worse
# than no figure. Bits 0 and 2 are the live ones; 16 and 18 only say it has
# happened before. See addendum 8 of the TBR-RF-01 artifact.
throttle_state() {
  command -v vcgencmd >/dev/null 2>&1 || {
    echo "unknown (no vcgencmd)"
    return
  }
  local t v out=""
  t=$(vcgencmd get_throttled 2>/dev/null | cut -d= -f2)
  v=$((t))
  [ $((v & 0x1)) -ne 0 ] && out="$out under-voltage-now"
  [ $((v & 0x4)) -ne 0 ] && out="$out THROTTLED-NOW"
  [ $((v & 0x10000)) -ne 0 ] && out="$out under-voltage-occurred"
  [ $((v & 0x40000)) -ne 0 ] && out="$out throttling-occurred"
  [ -z "$out" ] && out=" clean"
  printf '%s (%s MHz)%s' "$t" \
    "$(vcgencmd measure_clock arm 2>/dev/null | cut -d= -f2 | awk '{printf "%.0f", $1/1000000}')" \
    "$out"
}

# True when a live throttle bit is set, so a caller can refuse to measure.
throttled_now() {
  command -v vcgencmd >/dev/null 2>&1 || return 1
  local v
  v=$(($(vcgencmd get_throttled 2>/dev/null | cut -d= -f2)))
  [ $((v & 0x1)) -ne 0 ] || [ $((v & 0x4)) -ne 0 ]
}

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
    if [ "$d" = "$DRIVER" ]; then
      basename "$p"
      return 0
    fi
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
      basename "$n"
      return 0
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
  note 'phy' "$PHY"
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
  iw dev "$DEV" mesh join "$MESH_ID" freq "$FREQ" "$WIDTH"
  note 'mesh id' "$MESH_ID"
  note 'frequency' "${FREQ} MHz ${WIDTH}"
  note 'negotiated width' "$(iw dev "$DEV" info 2>/dev/null | awk '/channel/ {$1=""; print substr($0,2)}')"
  note 'regdomain' "$(iw reg get 2>/dev/null | awk '/^country/ {print $2; exit}')"

  printf '\nbatman-adv\n'
  ip link add name "$MESH_IF" type batadv 2>/dev/null || true

  # Give bat0 a STABLE address derived from this node's radio, instead of the
  # fresh random one the kernel assigns on every creation.
  #
  # WHY. A random MAC per creation means that every teardown and rejoin -- and
  # every reboot -- leaves peers holding a neighbour entry for an address that
  # no longer exists. Observed on this bench: the mesh came back healthy by
  # every mesh-layer measure (plink ESTAB, originator TQ 236, nexthop direct)
  # while IP over bat0 was 100% packet loss, because the peer's cache still
  # pointed at the previous bat0 MAC and was marked REACHABLE, so nothing
  # retried it. See addendum 6 of docs/evidence/TBR-RF-01/2026-10-11-*.
  #
  # The derivation sets the locally-administered bit on the radio's own address
  # and keeps the rest, so it is stable per node, unique between nodes, and
  # cannot collide with the radio's real address. It must happen while bat0 is
  # still down.
  #
  # NOT a program decision. The field addressing plan is TBR-NET-01's, and it
  # may well want an identity-derived address rather than one borrowed from a
  # radio that could be swapped. This is the bench fixing a bench defect.
  hw=$(cat "/sys/class/net/$DEV/address")
  stable_mac=$(printf '%02x:%s' "$((0x${hw%%:*} | 0x02))" "${hw#*:}")
  if ip link set "$MESH_IF" address "$stable_mac" 2>/dev/null; then
    note 'bat0 address' "$stable_mac (stable, derived from $DEV)"
  else
    note 'bat0 address' "$(cat "/sys/class/net/$MESH_IF/address") (RANDOM: could not set a stable one)"
  fi
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

  # Announce this address unsolicited, so peers and batman-adv's distributed ARP
  # table learn it now rather than when something eventually expires.
  #
  # WHY THIS IS NEEDED EVEN WITH A STABLE MAC. batman-adv's DAT answers ARP on
  # behalf of the mesh, and it was observed answering with a DEAD bat0 MAC for
  # over two minutes after a rejoin -- which re-confirmed the peer's neighbour
  # entry as REACHABLE and so stopped it ever retrying. The stable address above
  # removes the usual cause; this removes the mechanism's ability to serve a
  # wrong answer after any address change, including a radio swap or a first
  # join. Cheap, and it fails quietly if arping is absent.
  if command -v arping >/dev/null 2>&1; then
    arping -c 2 -U -I "$MESH_IF" "$PREFIX.$octet" >/dev/null 2>&1 || true
    note 'gratuitous ARP' "announced $PREFIX.$octet on $MESH_IF"
  fi
  note 'batctl' "$(batctl -v 2>/dev/null | head -1)"
  note 'throttle' "$(throttle_state)"
  if throttled_now; then
    printf '\n  WARNING: this node is throttled RIGHT NOW. Connectivity checks are\n'
    printf '  still meaningful; a PERFORMANCE figure taken here is not, and\n'
    printf '  mesh-traffic-real.sh will refuse to run. Fix the supply first.\n'
  fi
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
  printf '   throttle  %s\n' "$(throttle_state)"
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
  #
  # Capture, THEN test. An earlier version wrote
  #   if ping ... | sed 's/^/   /'; then
  # whose exit status is sed's, not ping's, so sed always succeeded and the gate
  # could never fail -- it printed GATE PASSED over "100% packet loss". The one
  # check the whole runbook step rests on must be the one that cannot lie.
  local out rc
  out=$(ping -c 1 -W 5 -I "$MESH_IF" "$peer" 2>&1)
  rc=$?
  printf '%s\n' "$out" | sed 's/^/   /'
  # Belt and braces: a zero exit AND a received packet. ping can exit 0 in
  # corners (a host-unreachable error reply still being "a reply"), so assert
  # the receive count too rather than trusting the status alone.
  if [ "$rc" -eq 0 ] && printf '%s' "$out" | grep -qE '1 (packets )?received'; then
    printf '\nGATE PASSED: one packet crossed a real 802.11s + batman-adv mesh.\n'
  else
    fail "one-packet gate FAILED to $peer (rc=$rc). The mesh may be up while nothing crosses: check PHY, association and config, never routing."
  fi
}

# --- line topology support (UNEXERCISED: see the header) --------------------

# Established peers only. A peer in OPN_SNT or similar is not carrying traffic,
# and counting it would make line-assert pass on a half-formed mesh.
peer_count_estab() {
  iw dev "$DEV" station dump 2>/dev/null |
    awk '/mesh plink:/ && /ESTAB/ {n++} END {print n+0}'
}

mesh_peers() {
  printf 'mesh peers seen by %s (%s)\n' "$(hostname)" "$(cat "/sys/class/net/$DEV/address")"
  iw dev "$DEV" station dump 2>/dev/null | awk '
    /^Station/      { mac = $2 }
    /signal:/       { sig = $2 }
    /mesh plink:/   { printf "   %s  signal %s dBm  plink %s\n", mac, sig, $3 }'
  printf '   established peers: %s\n' "$(peer_count_estab)"
  printf '\nFor a line, the end nodes must each see 1 and the relay 2. Signal is\n'
  printf 'the lever: move the end nodes apart until they stop seeing each other.\n'
}

# The topology assertion that must pass BEFORE any multi-hop number is taken.
# 80211s-mesh.sh asserts the same thing on hwsim by counting node 1's peers.
mesh_line_assert() {
  local want=${1:-} got
  [ -n "$want" ] || fail 'usage: line-assert <expected-established-peers>'
  got=$(peer_count_estab)
  printf '%s: expected %s established peer(s), found %s\n' "$(hostname)" "$want" "$got"
  if [ "$got" -ne "$want" ]; then
    mesh_peers
    fail "the line is not formed: this node sees $got established peers, not $want. If it sees too many, the end nodes are still in range of each other -- separate or attenuate them. Do NOT take a multi-hop reading until this passes."
  fi
  printf 'LINE ASSERTION PASSED.\n'
}

# Multi-hop is proved by the originator table, not by reachability: a route
# whose Nexthop is not the Originator itself is one batman-adv is relaying.
mesh_hops() {
  local far=${1:-} relayed
  [ -n "$far" ] || fail 'usage: hops <far-node-ip>'

  printf 'originator table on %s\n' "$(hostname)"
  batctl meshif "$MESH_IF" originators 2>&1 | sed 's/^/   /'

  relayed=$(batctl meshif "$MESH_IF" originators 2>/dev/null |
    awk '/^ *\*/ { if ($2 != "" && $5 != "" && $2 != $5) n++ } END {print n+0}')
  printf '\n   relayed routes (nexthop != originator): %s\n' "$relayed"
  [ "$relayed" -gt 0 ] ||
    fail 'no relayed route: every originator is its own nexthop, so this is a flat mesh and nothing is multi-hop. Re-check line-assert.'

  printf '\nRTT to %s over %s\n' "$far" "$MESH_IF"
  ping -c 20 -i 0.2 -W 5 -I "$MESH_IF" "$far" 2>&1 | tail -3 | sed 's/^/   /'
  printf '\nMULTI-HOP CONFIRMED: %s is reached through a relay.\n' "$far"
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
  up)
    shift
    mesh_up "${1:-}"
    ;;
  gate)
    shift
    mesh_gate "${1:-}"
    ;;
  status) mesh_status ;;
  peers) mesh_peers ;;
  line-assert)
    shift
    mesh_line_assert "${1:-}"
    ;;
  hops)
    shift
    mesh_hops "${1:-}"
    ;;
  down) mesh_down ;;
  *) fail 'usage: 80211s-mesh-real.sh {up <octet>|gate <peer-ip>|status|peers|line-assert <n>|hops <ip>|down}' ;;
esac
