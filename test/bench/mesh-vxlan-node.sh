#!/bin/bash
# Bench: put the bench mule (mule1) on the batman-adv mesh as a third node, over
# a unicast VXLAN tunnel across the home Wi-Fi to pi-mule-2. This is an
# EMULATED IP-tunnel bearer (mule1's radios cannot be 802.11s mesh points), not
# the selected mesh; label every result that way.
#
#   mesh-vxlan-node.sh mule1-up|mule1-down   (root on mule1)
#   mesh-vxlan-node.sh pi-up|pi-down         (root on pi-mule-2)
#
# Settings match the Pis' bat0: BATMAN_IV (kernel default), bridge_loop_avoidance
# off, multicast_mode off, fragmentation on. Addresses come from /etc/fml/mesh.env
# (MULE1_LAN, PI2_LAN, LAN_IF, AP_IF, BAT_ADDR, AP_NET, TAK_HOSTS).
#
# On mule1, which also hosts a live server, a guard in its own tables lets ONLY
# the bench AP's clients reach the bench TAK servers' 8089 across the mesh, and
# lets nothing from the mesh reach mule1's own services. COCON's TAK service and
# containers are not touched. Everything is removed by *-down.
set -euo pipefail
export PATH=/usr/sbin:/usr/bin:/sbin:/bin
# shellcheck source=/dev/null
. /etc/fml/mesh.env
VX=vxfml
VNI=4242

case "${1:-}" in
  mule1-up)
    modprobe batman-adv
    ip link show "$VX" >/dev/null 2>&1 ||
      ip link add "$VX" type vxlan id "$VNI" local "$MULE1_LAN" remote "$PI2_LAN" dstport 4789 dev "$LAN_IF"
    ip link set "$VX" up
    batctl if add "$VX" 2>/dev/null || true
    batctl bl 0 # bridge_loop_avoidance off, FML-ADR-056
    batctl mm 0
    batctl f 1
    ip link set bat0 up
    ip addr replace "$BAT_ADDR/24" dev bat0
    nft -f - <<EOF
table inet fml_mesh_guard {
  chain input {
    type filter hook input priority filter - 15; policy accept;
    iifname "bat0" ct state established,related accept
    iifname "bat0" icmp type echo-request accept
    iifname "bat0" drop
    iifname "$LAN_IF" udp dport 4789 ip saddr != $PI2_LAN drop
  }
  chain forward {
    type filter hook forward priority filter - 15; policy accept;
    iifname "$AP_IF" oifname "bat0" ip daddr { ${TAK_HOSTS// /, } } tcp dport 8089 accept
    iifname "bat0" oifname "$AP_IF" ct state established,related accept
    iifname "bat0" drop
    oifname "bat0" drop
  }
}
table ip fml_mesh_nat {
  chain postrouting {
    type nat hook postrouting priority srcnat; policy accept;
    oifname "bat0" ip saddr $AP_NET masquerade
  }
}
EOF
    # The host's iptables FORWARD policy is drop (docker); a drop in any base
    # chain wins, so the same narrow pair is also inserted there.
    for t in $TAK_HOSTS; do
      iptables -C FORWARD -i "$AP_IF" -o bat0 -d "$t" -p tcp --dport 8089 -j ACCEPT 2>/dev/null ||
        iptables -I FORWARD -i "$AP_IF" -o bat0 -d "$t" -p tcp --dport 8089 -j ACCEPT
    done
    iptables -C FORWARD -i bat0 -o "$AP_IF" -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT 2>/dev/null ||
      iptables -I FORWARD -i bat0 -o "$AP_IF" -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT
    echo "mule1 on bat0 $BAT_ADDR via $VX -> $PI2_LAN"
    ;;
  mule1-down)
    for t in $TAK_HOSTS; do
      while iptables -C FORWARD -i "$AP_IF" -o bat0 -d "$t" -p tcp --dport 8089 -j ACCEPT 2>/dev/null; do
        iptables -D FORWARD -i "$AP_IF" -o bat0 -d "$t" -p tcp --dport 8089 -j ACCEPT
      done
    done
    while iptables -C FORWARD -i bat0 -o "$AP_IF" -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT 2>/dev/null; do
      iptables -D FORWARD -i bat0 -o "$AP_IF" -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT
    done
    nft delete table inet fml_mesh_guard 2>/dev/null || true
    nft delete table ip fml_mesh_nat 2>/dev/null || true
    batctl if del "$VX" 2>/dev/null || true
    ip link del "$VX" 2>/dev/null || true
    ip link del bat0 2>/dev/null || true
    echo "mule1 removed from the mesh"
    ;;
  pi-up)
    ip link show "$VX" >/dev/null 2>&1 ||
      ip link add "$VX" type vxlan id "$VNI" local "$PI2_LAN" remote "$MULE1_LAN" dstport 4789 dev eth0
    ip link set "$VX" up
    batctl if add "$VX" 2>/dev/null || true
    echo "pi-mule-2 bat0 hard interfaces: $(batctl if | tr '\n' ' ')"
    ;;
  pi-down)
    batctl if del "$VX" 2>/dev/null || true
    ip link del "$VX" 2>/dev/null || true
    echo "pi-mule-2 tunnel removed"
    ;;
  *)
    echo "usage: mesh-vxlan-node.sh mule1-up|mule1-down|pi-up|pi-down" >&2
    exit 64
    ;;
esac
