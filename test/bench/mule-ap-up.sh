#!/bin/bash
# Field-faithful, device-agnostic EUD access-point bring-up for the lab bench.
#
#   mule-ap-up.sh [up|down] [node-id]      (default: up lab-bench)
#
# The code names ROLES, never devices. The role->device map lives in
# nodes/<node-id>/node.yml under `interfaces:` (FML-ADR-045). Moving to the field
# prototype is a descriptor swap, not an edit here; retasking a radio, or
# building a different device on this codebase, is likewise a map change only.
#
# It uses the field mechanisms -- hostapd for the AP, nftables for the uplink
# passthrough (FML-ADR-059's networkd link ownership is not yet mirrored on this
# NetworkManager box; see docs/dev-machine.md). RF/channel/SSID values here are
# bench placeholders; on the prototype they come from gen-config + the region
# profile, not from this script.
set -eu

MODE="${1:-up}"
NODE="${2:-lab-bench}"
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
NODE_YML="$ROOT/nodes/$NODE/node.yml"

SUBNET="10.41.0.0/24"
GW="10.41.0.1"
SSID="${MULE_AP_SSID:-feralmulenet}" # override via env; field SSID is mission data
CONF="/tmp/mule-hostapd.conf"
DPID="/tmp/mule-dnsmasq.pid"
PSK_FILE="/tmp/mule-psk" # runtime only, 0600; the passphrase never lives in git

say() { printf '  %s\n' "$1"; }

# Read one interface role's device from the node descriptor. No YAML library:
# the block is a flat `role: device` list, and comment lines never match a role.
role_device() {
  awk -v want="$1:" '
		/^interfaces:/ { inblock = 1; next }
		inblock && /^[^[:space:]]/ { inblock = 0 }
		inblock && $1 == want { print $2; exit }
	' "$NODE_YML"
}

# Read a top-level scalar (e.g. ap_channel) from the node descriptor.
node_scalar() {
  awk -v k="$1:" '$0 !~ /^[[:space:]#]/ && $1 == k { print $2; exit }' "$NODE_YML"
}

[ -f "$NODE_YML" ] || {
  echo "node descriptor not found: $NODE_YML"
  exit 1
}
AP="$(role_device eud_ap)"
WAN="$(role_device wan)"
if [ -z "$AP" ] || [ "$AP" = "none" ]; then
  echo "node $NODE has no eud_ap interface"
  exit 1
fi
if [ -z "$WAN" ] || [ "$WAN" = "none" ]; then
  echo "node $NODE has no wan interface"
  exit 1
fi
# AP channel from the descriptor (field: from gen-config + region profile). The
# band follows the channel: 5 GHz is >= 36, below that is 2.4 GHz.
AP_CHANNEL="$(node_scalar ap_channel)"
AP_CHANNEL="${AP_CHANNEL:-36}"
if [ "$AP_CHANNEL" -ge 36 ]; then HW_MODE=a; else HW_MODE=g; fi

down() {
  say "stopping dnsmasq/hostapd"
  if [ -f "$DPID" ]; then kill "$(cat "$DPID")" 2>/dev/null || true; fi
  pkill -x hostapd 2>/dev/null || true
  rm -f "$PSK_FILE" 2>/dev/null || true
  nft delete table ip mule 2>/dev/null || true
  ip addr flush dev "$AP" 2>/dev/null || true
  ip link set "$AP" down 2>/dev/null || true
  nmcli device set "$AP" managed yes 2>/dev/null || true
  say "AP down; $AP handed back to NetworkManager"
}

[ "$(id -u)" -eq 0 ] || {
  echo "run as root"
  exit 1
}
[ "$MODE" = "down" ] && {
  down
  exit 0
}

# Safety: the roles must be distinct devices, and the AP must not be the device
# currently carrying the uplink -- taking it would cut the box off. These are the
# lab drifts the role model exists to prevent.
[ "$AP" != "$WAN" ] || {
  echo "REFUSED: eud_ap and wan resolve to the same device ($AP)"
  exit 1
}
DEFAULT_DEV="$(ip route show default 2>/dev/null | awk '/default/ {print $5; exit}')"
[ "$AP" != "$DEFAULT_DEV" ] || {
  echo "REFUSED: eud_ap ($AP) is the current default-route device; bringing up"
  echo "         the AP on it would drop the box's uplink."
  exit 1
}
ip link show "$AP" >/dev/null 2>&1 || {
  echo "eud_ap device $AP not present"
  exit 1
}

say "eud_ap=$AP  wan=$WAN  (node $NODE)"
nmcli device set "$AP" managed no 2>/dev/null || true
rfkill unblock wifi 2>/dev/null || true
pkill -x hostapd 2>/dev/null || true
sleep 1
ip addr flush dev "$AP" 2>/dev/null || true
ip link set "$AP" down 2>/dev/null || true
iw reg set US 2>/dev/null || true

# The AP passphrase is a secret and is never committed. Supply it via the
# environment; hostapd reads it from a runtime 0600 PSK file (below), so neither
# the passphrase nor an inline passphrase directive lives in this file.
# SECURITY.md.
PSK="${MULE_AP_PSK:?set MULE_AP_PSK; the AP passphrase is never committed (SECURITY.md)}"
(
  umask 077
  printf '00:00:00:00:00:00 %s\n' "$PSK" >"$PSK_FILE"
)

cat >"$CONF" <<EOF
interface=$AP
driver=nl80211
ssid=$SSID
country_code=US
ieee80211d=1
hw_mode=$HW_MODE
channel=$AP_CHANNEL
ieee80211n=1
wmm_enabled=1
auth_algs=1
wpa=2
wpa_key_mgmt=WPA-PSK
rsn_pairwise=CCMP
wpa_psk_file=$PSK_FILE
disassoc_low_ack=0
ap_max_inactivity=3600
ap_isolate=0
max_num_sta=16
EOF

say "starting hostapd on $AP"
hostapd -B "$CONF" >/dev/null 2>&1
sleep 4
pgrep -x hostapd >/dev/null || {
  echo "FAIL: hostapd did not start"
  exit 1
}
iw dev "$AP" info 2>/dev/null | grep -q "type AP" || {
  echo "FAIL: $AP not in AP mode"
  exit 1
}

ip addr add "$GW/24" dev "$AP"
ip link set "$AP" up
iw dev "$AP" set power_save off 2>/dev/null || true

dnsmasq --interface="$AP" --bind-interfaces --except-interface=lo \
  --dhcp-range=10.41.0.50,10.41.0.150,255.255.255.0,12h \
  --dhcp-option=3,"$GW" --dhcp-option=6,"$GW" \
  --dhcp-authoritative --pid-file="$DPID" >/dev/null 2>&1
say "dnsmasq serving DHCP on $AP"

# Uplink passthrough via nftables (the field firewall mechanism), added in its
# own table so teardown is a single delete and nothing else is flushed.
sysctl -qw net.ipv4.ip_forward=1
nft add table ip mule
nft add chain ip mule postrouting "{ type nat hook postrouting priority 100 ; }"
nft add rule ip mule postrouting ip saddr "$SUBNET" oifname "$WAN" masquerade
nft add chain ip mule forward "{ type filter hook forward priority 0 ; }"
nft add rule ip mule forward iifname "$AP" oifname "$WAN" accept
nft add rule ip mule forward iifname "$WAN" oifname "$AP" ct state established,related accept
say "uplink passthrough: $SUBNET -> $WAN (nft table 'mule')"

echo
echo "AP UP.  role eud_ap=$AP  ssid=$SSID  gw=$GW  uplink=$WAN"
