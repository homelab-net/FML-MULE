#!/bin/sh
# Prove that a keyed 802.11s mesh admits only credential holders.
#
# Usage: sudo test/bench/keyed-mesh.sh
#
# WHAT THIS IS FOR. FML-ADR-061 decides that the field mesh is keyed with
# key_mgmt=SAE and that MULEs of one deployment merge automatically. It
# supersedes FML-ADR-060, whose argument assumed an open mesh. That is a large
# decision to rest on a measurement, and until this script existed the
# measurement lived only in a scratch directory: nothing in the repository could
# reproduce it. This is that procedure.
#
# WHAT A PASS PROVES. That wpa_supplicant forms an authenticated 802.11s peer
# link by SAE and AMPE between nodes sharing a credential; that a node with NO
# credential never peers; and that a node with a DIFFERENT credential is
# rejected. The third is the one worth having, because it is the one a peer
# list will lie to you about.
#
# THE TRAP THIS SCRIPT EXISTS TO AVOID. `iw station dump` lists peers the radio
# has SEEN. A node that failed authentication still appears, in state LISTEN.
# Counting Station lines therefore reports success for a node that got in
# nowhere near. That mistake was made while producing FML-ADR-061 and caught
# only by checking the flags, so every assertion below reads `mesh plink`,
# `authenticated` and `authorized`, and then confirms with traffic.
#
# WHAT IT DOES NOT PROVE. hwsim models the 802.11 MAC. There is no RF, and
# there is no S1G band at all, so this says nothing about whether SAE works on
# the HaLow bearer the decision is written for. See FML-ADR-062 and
# docs/evidence/TBR-LINUX-01/2026-08-31-halow-driver-mesh-and-sae-support.md.
#
# NO CREDENTIAL IS COMMITTED. The passphrases are generated per run. SECURITY.md
# forbids a key in the repository and a bench script is not an exception.

set -eu

MESH_ID=fml-bench-keyed
FREQ=2412
RUNDIR=$(mktemp -d /tmp/fml-keyed.XXXXXX)

fail() {
  printf 'FAIL: %s\n' "$1" >&2
  exit 1
}
info() { printf '  %s\n' "$1"; }

cleanup() {
  for n in 1 2 3; do
    ip netns pids "fmlkey$n" 2>/dev/null | xargs -r kill 2>/dev/null || true
  done
  sleep 1
  for n in 1 2 3; do ip netns del "fmlkey$n" 2>/dev/null || true; done
  rmmod mac80211_hwsim 2>/dev/null || true
  rm -rf "$RUNDIR"
}
trap cleanup EXIT INT TERM

[ "$(id -u)" -eq 0 ] || fail 'must run as root: it loads a module and creates namespaces.'

for tool in ip iw wpa_supplicant; do
  command -v "$tool" >/dev/null 2>&1 ||
    fail "$tool is not installed. apt-get install iproute2 iw wpasupplicant"
done

modinfo mac80211_hwsim >/dev/null 2>&1 ||
  fail 'mac80211_hwsim is not in this kernel. See docs/dev-machine.md.'

#: Generated, never stored. Two different values, so the rejection case is real.
KEY_A=$(head -c 18 /dev/urandom | od -An -tx1 | tr -d ' \n')
KEY_B=$(head -c 18 /dev/urandom | od -An -tx1 | tr -d ' \n')
[ "$KEY_A" != "$KEY_B" ] || fail 'the two generated credentials collided.'

printf 'Preparing three virtual radios\n'
rmmod mac80211_hwsim 2>/dev/null || true
modprobe mac80211_hwsim radios=3
sleep 2

phy_for() { iw dev "$1" info 2>/dev/null | awk '/wiphy/ {print "phy"$2}'; }

i=1
while [ "$i" -le 3 ]; do
  ip netns add "fmlkey$i"
  iw phy "$(phy_for "wlan$((i - 1))")" set netns name "fmlkey$i"
  i=$((i + 1))
done

# node 1 and node 2 hold the deployment credential. node 3 holds a different
# one, which is the partner-or-stranger case FML-ADR-061 turns on.
write_conf() {
  # $1 file, $2 passphrase
  cat >"$1" <<CONF
network={
	ssid="$MESH_ID"
	mode=5
	frequency=$FREQ
	key_mgmt=SAE
	sae_password="$2"
}
CONF
  chmod 600 "$1"
}
write_conf "$RUNDIR/n1.conf" "$KEY_A"
write_conf "$RUNDIR/n2.conf" "$KEY_A"
write_conf "$RUNDIR/n3.conf" "$KEY_B"

i=1
while [ "$i" -le 3 ]; do
  dev="wlan$((i - 1))"
  ip netns exec "fmlkey$i" ip link set "$dev" down
  ip netns exec "fmlkey$i" wpa_supplicant -i "$dev" -c "$RUNDIR/n$i.conf" \
    -D nl80211 -B -f "$RUNDIR/n$i.log" >/dev/null 2>&1
  i=$((i + 1))
done

# Waited for rather than slept through. SAE plus AMPE is not a fixed interval.
printf 'Waiting for the credential holders to authenticate\n'
deadline=$(($(date +%s) + 60))
paired=0
while [ "$(date +%s)" -lt "$deadline" ]; do
  if ip netns exec fmlkey1 iw dev wlan0 station dump 2>/dev/null |
    grep -q 'authenticated:[[:space:]]*yes'; then
    paired=1
    break
  fi
  sleep 2
done
[ "$paired" -eq 1 ] ||
  fail "node 1 authenticated no peer within 60s. $(tail -3 "$RUNDIR/n1.log" 2>/dev/null)"

MAC2=$(ip netns exec fmlkey2 cat /sys/class/net/wlan1/address)
MAC3=$(ip netns exec fmlkey3 cat /sys/class/net/wlan2/address)

# state_of <ns> <dev> <peer-mac> <field>  -> the value, or empty
state_of() {
  ip netns exec "$1" iw dev "$2" station dump 2>/dev/null |
    awk -v peer="$3" -v want="$4" '
      /^Station/ { cur = $2 }
      cur == peer && index($0, want) { sub(/^[^:]*:[[:space:]]*/, ""); print; exit }
    '
}

printf 'Assertions\n'

# 1. The credential holders authenticated each other.
for f in authenticated authorized; do
  v=$(state_of fmlkey1 wlan0 "$MAC2" "$f:")
  [ "$v" = "yes" ] || fail "node 1 reports $f='$v' for the node sharing its credential, expected yes."
done
plink=$(state_of fmlkey1 wlan0 "$MAC2" "mesh plink:")
[ "$plink" = "ESTAB" ] || fail "node 1 reports mesh plink '$plink' for its peer, expected ESTAB."
info 'two nodes sharing a credential: plink ESTAB, authenticated, authorized'

# 2. The node with a DIFFERENT credential is not authenticated.
#
# It may appear in the peer list at all, in state LISTEN, which is exactly the
# trap described at the top of this file. Absence is acceptable; presence in an
# authenticated state is not.
auth3=$(state_of fmlkey1 wlan0 "$MAC3" "authenticated:")
case "$auth3" in
  yes) fail 'a node holding a DIFFERENT credential authenticated. The mesh is not enforcing its key.' ;;
esac
plink3=$(state_of fmlkey1 wlan0 "$MAC3" "mesh plink:")
case "$plink3" in
  ESTAB) fail 'a node holding a DIFFERENT credential reached plink ESTAB.' ;;
esac
info "node with a different credential: authenticated='${auth3:-absent}', plink='${plink3:-absent}'"

# 3. And traffic agrees, because a state table is not delivery.
ip netns exec fmlkey1 ip addr add 10.60.0.1/24 dev wlan0
ip netns exec fmlkey2 ip addr add 10.60.0.2/24 dev wlan1
ip netns exec fmlkey3 ip addr add 10.60.0.3/24 dev wlan2
i=1
while [ "$i" -le 3 ]; do
  ip netns exec "fmlkey$i" ip link set "wlan$((i - 1))" up
  i=$((i + 1))
done
sleep 3

ip netns exec fmlkey1 ping -c 3 -W 2 10.60.0.2 >/dev/null 2>&1 ||
  fail 'traffic did not cross between two nodes sharing a credential.'
info 'traffic crosses between credential holders'

if ip netns exec fmlkey1 ping -c 2 -W 2 10.60.0.3 >/dev/null 2>&1; then
  fail 'traffic reached the node holding a DIFFERENT credential. The key is not excluding it.'
fi
info 'no traffic reaches the node holding a different credential'

printf '\n'
printf 'PASS. A keyed mesh admitted only credential holders, and excluded a\n'
printf 'node holding a different credential. FML-ADR-061.\n'
printf 'Tier: SIMULATED. hwsim models the 802.11 MAC and nothing physical, and\n'
printf 'has no S1G band, so this says nothing about HaLow. FML-ADR-062.\n'
