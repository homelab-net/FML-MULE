#!/bin/bash
# tak.field failover trials across two bench nodes, run from an operator machine.
#
#   tak-failover-campaign.sh phase1 USER@NODE_A USER@NODE_B
#   tak-failover-campaign.sh phase2 USER@NODE_A USER@NODE_B
#
# phase1: tak.field resolution and ingress state, shared trust (a client
#         certificate from the shared CA, and a foreign-CA control, against each
#         backend over the mesh), and alive-is-not-authoritative routing.
# phase2: administrative promotion trials (CONOPS 30): six partitions of the
#         authoritative backend from the mesh, alternating direction; one planned
#         switchover; one process death. Recovery is read from tak-probe.py logs.
#
# Prerequisites on each node: tak-server-bench-install.sh, tak-field-ingress.sh
# up, and ~/campaign/ holding tak-probe.py and certs/{itak-bench,wintak-bench,
# foreign}/{c,k,ca}.pem. Key-based ssh and sudo on both nodes; no credential is
# held here. Node A must be the backend on 10.42.0.1 and node B on 10.42.0.2.
#
# Faults reject TCP 8089 only from mesh sources (10.42.0.0/24), so clients that
# reach a server from elsewhere are untouched; each fault is cleared by the step
# that set it, and a detached guard clears it after fifteen minutes regardless.
# Executed 2026-10-17 through an equivalent password-ssh wrapper; see
# docs/evidence/TBR-HA-01/2026-10-17-tak-field-ingress-and-administrative-promotion.md.
#
# Commands are single-quoted on purpose: they are expanded on the node, not here.
# shellcheck disable=SC2016
set -u
PHASE=${1:?phase1|phase2}
A=${2:?USER@NODE_A}
B=${3:?USER@NODE_B}
OUT=campaign-out
mkdir -p "$OUT"
run() { ssh -o BatchMode=yes "$1" "$2"; }
sud() { ssh -o BatchMode=yes "$1" "sudo bash -c '$2'"; }
log() { echo "[$(date +%H:%M:%S)] $*" | tee -a "$OUT/driver.log"; }
probe() { # host role target port certdir secs logname [peer]
  run "$1" "cd ~/campaign; setsid nohup python3 tak-probe.py $2 $3 $4 certs/$5/c.pem certs/$5/k.pem certs/$5/ca.pem $6 ~/campaign/$7 ${8:-} >/dev/null 2>&1 < /dev/null & echo started $2 on \$(hostname)"
}
ip_of() { if [ "$1" = a ]; then echo "$A"; else echo "$B"; fi; }

phase1() {
  log "== phase1"
  for h in "$A" "$B"; do run "$h" 'echo "$(hostname): $(getent hosts tak.field)"; timedatectl timesync-status 2>/dev/null | grep -E "Offset"' | tee -a "$OUT/driver.log"; done
  for h in "$A" "$B"; do sud "$h" 'echo "show servers state tak" | socat stdio /run/haproxy/admin.sock | awk "NR>2 && \$4!=\"\" {print \"  \" \$4, \"admin=\" \$7, \"op=\" \$6}"; cat /etc/fml/tak-authority' | tee -a "$OUT/driver.log"; done

  log "T2 trust: shared-CA client cert direct to each backend over the mesh; foreign-CA control"
  for tgt in 10.42.0.1 10.42.0.2; do
    for c in itak-bench foreign; do
      run "$A" "cd ~/campaign && rm -f t2.jsonl && timeout 15 python3 tak-probe.py recv $tgt 8089 certs/$c/c.pem certs/$c/k.pem certs/$c/ca.pem 8 t2.jsonl none >/dev/null 2>&1; python3 -c \"import json;l=[json.loads(x) for x in open('t2.jsonl')];c=sum(e['event']=='connected' for e in l);d=[e['reason'] for e in l if e['event']=='disconnected'];print('T2 $tgt $c connected=',c,'disconnects=',len(d),(d[0][:90] if d else ''))\"" | tee -a "$OUT/driver.log"
    done
    run "$A" "echo | timeout 10 openssl s_client -connect $tgt:8089 -cert ~/campaign/certs/itak-bench/c.pem -key ~/campaign/certs/itak-bench/k.pem -CAfile ~/campaign/certs/itak-bench/ca.pem 2>/dev/null | grep -E '^subject=|^issuer=|Verify return code' | sed 's/^/  T2 $tgt server /'" | tee -a "$OUT/driver.log"
  done

  log "T3 alive-is-not-authoritative: both backends up, authority=a, probes via tak.field for 90 s"
  run "$A" 'rm -f ~/campaign/t3-*.jsonl'
  run "$B" 'rm -f ~/campaign/t3-*.jsonl'
  probe "$A" recv tak.field 18089 wintak-bench 90 t3-recv.jsonl FML-PROBE-SEND-pi-mule-2
  probe "$B" send tak.field 18089 itak-bench 90 t3-send.jsonl
  sleep 45
  sud "$A" 'echo "A 8089 sessions from:"; ss -tnH state established "( sport = :8089 )" | awk "{print \$4}" | sed -E "s/:[0-9]+$//" | sort | uniq -c' | tee -a "$OUT/driver.log"
  sud "$B" 'echo "B 8089 sessions from:"; ss -tnH state established "( sport = :8089 )" | awk "{print \$4}" | sed -E "s/:[0-9]+$//" | sort | uniq -c' | tee -a "$OUT/driver.log"
  sleep 55
  run "$A" 'python3 -c "import json;l=[json.loads(x) for x in open(\"/home/mule_admin/campaign/t3-recv.jsonl\")];print(\"T3 recv events:\",{k:sum(e[\"event\"]==k for e in l) for k in (\"connected\",\"rx\",\"disconnected\")})"' | tee -a "$OUT/driver.log"
}

trial() { # n from to fault(reject|stop)
  local n=$1 from=$2 to=$3 kind=$4 h
  h=$(ip_of "$from")
  log "trial $n: fault $kind on $from, promote $to"
  if [ "$kind" = none ]; then
    echo "fault_at none $(date -u +%s.%N)" | tee -a "$OUT/events-$n.log"
  elif [ "$kind" = reject ]; then
    sud "$h" 'setsid nohup sh -c "sleep 900; iptables -D INPUT -s 10.42.0.0/24 -p tcp --dport 8089 -j REJECT --reject-with tcp-reset" >/dev/null 2>&1 < /dev/null & echo "fault_at $(date -u +%s.%N)"; iptables -I INPUT -s 10.42.0.0/24 -p tcp --dport 8089 -j REJECT --reject-with tcp-reset' | tee -a "$OUT/events-$n.log"
  else
    sud "$h" 'echo "fault_at $(date -u +%s.%N)"; systemctl stop takserver' | tee -a "$OUT/events-$n.log"
  fi
  sud "$A" "fml-tak-promote $to" >"$OUT/promote-$n-a.log" 2>&1 &
  sud "$B" "fml-tak-promote $to" >"$OUT/promote-$n-b.log" 2>&1 &
  wait
  cat "$OUT/promote-$n-a.log" "$OUT/promote-$n-b.log" | grep promoted | sed 's/^/  /' | tee -a "$OUT/events-$n.log"
  sleep 40
  if [ "$kind" = reject ]; then
    sud "$h" 'iptables -D INPUT -s 10.42.0.0/24 -p tcp --dport 8089 -j REJECT --reject-with tcp-reset; echo "clear_at $(date -u +%s.%N)"' | tee -a "$OUT/events-$n.log"
  fi
  sleep 20
}

phase2() {
  log "== phase2: probes for the whole phase, then trials"
  run "$A" 'rm -f ~/campaign/p2-*.jsonl'
  run "$B" 'rm -f ~/campaign/p2-*.jsonl'
  probe "$A" recv tak.field 18089 wintak-bench 1500 p2-recv.jsonl FML-PROBE-SEND-pi-mule-2
  probe "$B" send tak.field 18089 itak-bench 1500 p2-send.jsonl
  sleep 30
  trial 1 a b reject
  trial 2 b a reject
  trial 3 a b reject
  trial 4 b a reject
  trial 5 a b reject
  trial 6 b a reject
  trial 7 a b none
  trial 8 b a stop
  log "trial 8 left pi-mule-2 TAK Server stopped; authority is a. Restarting b."
  sud "$B" 'systemctl start takserver; echo restart_issued $(date -u +%s.%N)' | tee -a "$OUT/driver.log"
  for h in "$A" "$B"; do run "$h" 'timedatectl timesync-status 2>/dev/null | grep -E Offset | sed "s/^/$(hostname) /"'; done | tee -a "$OUT/driver.log"
  log "== phase2 done"
}

"$PHASE"
