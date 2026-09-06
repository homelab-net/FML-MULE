#!/bin/sh
# Does FML-ADR-070's chosen LoRa encoding survive the Meshtastic bearer?
#
# Usage: sudo -n false; test/bench/geochat-survival.sh   (needs docker + the
#        meshtastic python client in .venv-lora)
#
# WHAT THIS IS FOR. FML-ADR-070 carries the sender in an ATAK Contact.callsign
# and the recipient in an ATAK GeoChat.to -- upstream's own TAK fields on the
# ATAK plugin port -- rather than a custom member index, because a custom tag on
# a private port is discarded by the FML-ADR-048 gateway
# (docs/evidence/TBR-NET-02/2026-08-30-opentakserver-meshtastic-path.md). The
# gateway evidence inspected the fields the gateway HANDLES; it did not carry a
# live GeoChat two nodes apart. This does: it sends a TAKPacket with those two
# fields between two meshtasticd nodes and asserts both arrive intact. It fits
# upstream's own encoding rather than inventing a channel beside it (AGENTS.md
# rule 6).
#
# WHY DOCKER, NOT PODMAN. meshtasticd nodes exchange over IP multicast
# 224.0.0.69. When docker is installed its FORWARD policy is drop, and
# br_netfilter pushes even same-bridge frames on a podman network through that
# chain, so podman-bridged nodes never hear each other; docker's own bridges
# carry it. Assessed 2026-09-06. This is the transport .github/workflows/
# lora-probe.yml uses in CI.
#
# WHAT A PASS RECORDS. A plain text message crosses (single-step, first), then a
# TAKPacket sent on the ATAK plugin port from node 1 is received on node 2 with
# Contact.callsign and GeoChat.to byte-identical to what was sent.
#
# WHAT IT DOES NOT PROVE. Tier SIMULATED. UDP on a docker bridge is a perfect
# wire: no LoRa RF, no modulation, no airtime, no range. It says the encoding is
# carriable on the bearer, nothing about sub-GHz behaviour (TBR-RF-02).
set -eu

ROOT=$(CDPATH='' cd -- "$(dirname -- "$0")/../.." && pwd)
MT="$ROOT/.venv-lora/bin/meshtastic"
PY="$ROOT/.venv-lora/bin/python"
NET=fml-geochat-seg
P1=14413
P2=14414
A_CALL="FMLPROBE-ALPHA"
B_CALL="FMLPROBE-BRAVO"
MSG="fml-geochat-probe-marker"

fail() {
  printf 'FAIL: %s\n' "$1" >&2
  exit 1
}

# One source of the daemon image, shared with lora-probe.yml.
# shellcheck source=/dev/null
. "$ROOT/tools/toolchain-versions.sh"
IMG="docker.io/$MESHTASTICD_IMAGE"
case "$MESHTASTICD_IMAGE" in docker.io/*) IMG="$MESHTASTICD_IMAGE" ;; esac

cleanup() {
  docker rm -f geo1 geo2 >/dev/null 2>&1 || true
  docker network rm "$NET" >/dev/null 2>&1 || true
  if [ -n "${TMP:-}" ]; then rm -rf "$TMP"; fi
}
trap cleanup EXIT INT TERM
cleanup
TMP=$(mktemp -d)

command -v docker >/dev/null 2>&1 || fail "docker not installed (see the header: podman does not carry the multicast here)"
[ -x "$MT" ] || fail "$MT missing; the meshtastic client lives in .venv-lora"

wait_api() { # $1 host:port  $2 timeout
  end=$(($(date +%s) + $2))
  while [ "$(date +%s)" -lt "$end" ]; do
    "$MT" --host "$1" --info >/dev/null 2>&1 && return 0
    sleep 3
  done
  return 1
}

docker network create "$NET" >/dev/null
for n in 1 2; do
  cat >"$TMP/cfg$n.yaml" <<CFG
Lora:
  Module: sim
General:
  MaxNodes: 200
  MACAddress: "AA:BB:CC:DD:EE:0$n"
  ConfigDirectory: /etc/meshtasticd/config.d/
  AvailableDirectory: /etc/meshtasticd/available.d/
Logging:
  LogLevel: info
CFG
done

docker run -d --name geo1 --network "$NET" --restart unless-stopped \
  -p "127.0.0.1:$P1:4403" -v "$TMP/cfg1.yaml:/etc/meshtasticd/config.yaml:ro" "$IMG" >/dev/null
docker run -d --name geo2 --network "$NET" --restart unless-stopped \
  -p "127.0.0.1:$P2:4403" -v "$TMP/cfg2.yaml:/etc/meshtasticd/config.yaml:ro" "$IMG" >/dev/null

echo "waiting for both node APIs..."
wait_api "127.0.0.1:$P1" 90 || fail "geo1 API did not come up"
wait_api "127.0.0.1:$P2" 90 || fail "geo2 API did not come up"

echo "enabling UDP_BROADCAST on both (this reboots each node)..."
"$MT" --host "127.0.0.1:$P1" --set network.enabled_protocols UDP_BROADCAST >/dev/null 2>&1 || true
"$MT" --host "127.0.0.1:$P2" --set network.enabled_protocols UDP_BROADCAST >/dev/null 2>&1 || true
sleep 12
wait_api "127.0.0.1:$P1" 90 || fail "geo1 API did not return from reboot"
wait_api "127.0.0.1:$P2" 90 || fail "geo2 API did not return from reboot"
sleep 8

# Single-step before multi-step (AGENTS.md): does the segment carry anything.
echo "=== single-step: a plain text message crosses ==="
"$PY" - "$MSG" "$P1" "$P2" <<'PYEOF' || fail "nodes do not exchange even plain text; the segment is not carrying traffic"
import sys, time
import meshtastic.tcp_interface as tcp
from pubsub import pub
MSG, P1, P2 = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
seen = []
def on_recv(packet=None, interface=None):
    d = (packet or {}).get("decoded") or {}
    if d.get("portnum") == "TEXT_MESSAGE_APP":
        seen.append(d.get("text", ""))
pub.subscribe(on_recv, "meshtastic.receive")
rx = tcp.TCPInterface("127.0.0.1", portNumber=P2)
tx = tcp.TCPInterface("127.0.0.1", portNumber=P1)
tx.sendText(MSG); time.sleep(2); tx.close()
end = time.time() + 30
while time.time() < end and not any(MSG in t for t in seen):
    time.sleep(0.5)
rx.close()
print("  text crossed:", any(MSG in t for t in seen), seen)
sys.exit(0 if any(MSG in t for t in seen) else 1)
PYEOF

echo "=== multi-step: FML-ADR-070's TAKPacket (Contact.callsign + GeoChat.to) survives ==="
"$PY" - "$A_CALL" "$B_CALL" "$MSG" "$P1" "$P2" <<'PYEOF' || fail "the TAKPacket did not survive with both fields intact"
import sys, time
import meshtastic.tcp_interface as tcp
from pubsub import pub
from meshtastic.protobuf import portnums_pb2, atak_pb2
A_CALL, B_CALL, MSG, P1, P2 = sys.argv[1], sys.argv[2], sys.argv[3], int(sys.argv[4]), int(sys.argv[5])
ATAK = portnums_pb2.PortNum.Value("ATAK_PLUGIN")
got = []
def on_recv(packet=None, interface=None):
    d = (packet or {}).get("decoded") or {}
    if d.get("portnum") not in ("ATAK_PLUGIN", ATAK):
        return
    raw = d.get("payload")
    if raw:
        try:
            got.append(atak_pb2.TAKPacket.FromString(raw))
        except Exception as e:
            got.append(("decode-error", str(e)))
pub.subscribe(on_recv, "meshtastic.receive")
rx = tcp.TCPInterface("127.0.0.1", portNumber=P2)
tx = tcp.TCPInterface("127.0.0.1", portNumber=P1)
tp = atak_pb2.TAKPacket()
tp.contact.callsign = A_CALL
tp.chat.to = B_CALL
tp.chat.message = MSG
tx.sendData(tp.SerializeToString(), portNum=ATAK, wantAck=False)
print(f"  sent      contact.callsign={A_CALL!r}  chat.to={B_CALL!r}")
time.sleep(2); tx.close()
end = time.time() + 30
while time.time() < end and not any(isinstance(x, atak_pb2.TAKPacket) for x in got):
    time.sleep(0.5)
rx.close()
tps = [x for x in got if isinstance(x, atak_pb2.TAKPacket)]
if not tps:
    print("  no TAKPacket received on the ATAK port; captures:", got)
    sys.exit(1)
r = tps[0]
print(f"  received  contact.callsign={r.contact.callsign!r}  chat.to={r.chat.to!r}  message={r.chat.message!r}")
ok = r.contact.callsign == A_CALL and r.chat.to == B_CALL and r.chat.message == MSG
print("  Contact.callsign survived:", r.contact.callsign == A_CALL)
print("  GeoChat.to survived:      ", r.chat.to == B_CALL)
sys.exit(0 if ok else 1)
PYEOF

printf '\nPASS. FML-ADR-070 encoding carried on the bearer: Contact.callsign and\n'
printf 'GeoChat.to survived a TAKPacket between two Meshtastic nodes on the ATAK\n'
printf 'plugin port. Tier: SIMULATED (UDP on a docker bridge; no LoRa RF).\n'
