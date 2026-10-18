#!/bin/bash
# Bench stand-in for SAD 11.2 / FML-ADR-031 local ingress and the FML-ADR-049
# authority registry, on one Pi. Run as root:  ingress-setup.sh up|down
#
#   EUD -> tak.field (hosts entry -> local ingress) -> HAProxy TCP passthrough
#       -> the ONE authoritative TAK backend, reached over the 802.11s mesh
#
# Authority is a one-line registry file, /etc/fml/tak-authority ("a" or "b").
# HAProxy health checks are reported but never move traffic: CONOPS 29 forbids
# uncontrolled competing authority, and TBR-HA-01 has selected no automatic
# mechanism, so promotion is administrative (CONOPS 30) via fml-tak-promote.
# Bench deviations, stated: a hosts entry stands in for dnsmasq; the ingress
# listens on 18089 because the co-located TAK Server owns 8089.
set -euo pipefail
export DEBIAN_FRONTEND=noninteractive
CFG=/etc/haproxy/haproxy.cfg
REG=/etc/fml/tak-authority

render() { # $1 = authoritative backend
  local a_state=disabled b_state=disabled
  [ "$1" = a ] && a_state=enabled
  [ "$1" = b ] && b_state=enabled
  cat >"$CFG" <<EOF
# Rendered by fml ingress-setup.sh from $REG; do not hand-edit.
global
    log /dev/log local0
    stats socket /run/haproxy/admin.sock mode 660 level admin
    maxconn 512
defaults
    mode tcp
    log global
    option tcplog
    timeout connect 3s
    timeout client 1h
    timeout server 1h
frontend tak_field
    bind 0.0.0.0:18089
    default_backend tak
backend tak
    # authoritative: $1
    server a 10.42.0.1:8089 check inter 2s $([ "$a_state" = disabled ] && echo disabled)
    server b 10.42.0.2:8089 check inter 2s $([ "$b_state" = disabled ] && echo disabled)
EOF
  haproxy -c -q -f "$CFG"
}

case "${1:-}" in
  up)
    command -v haproxy >/dev/null || apt-get install -y -q haproxy socat
    command -v socat >/dev/null || apt-get install -y -q socat
    install -d -m 755 /etc/fml
    [ -s "$REG" ] || echo a >"$REG"
    grep -q ' tak\.field$' /etc/hosts || echo '127.0.0.1 tak.field' >>/etc/hosts
    render "$(cat "$REG")"
    systemctl enable -q haproxy
    systemctl restart haproxy
    cat >/usr/local/sbin/fml-tak-promote <<'EOP'
#!/bin/bash
# Administrative promotion (CONOPS 30): fml-tak-promote a|b
set -euo pipefail
new=$1; [ "$new" = a ] || [ "$new" = b ] || { echo "usage: fml-tak-promote a|b"; exit 64; }
old=$([ "$new" = a ] && echo b || echo a)
echo "$new" >/etc/fml/tak-authority
S=/run/haproxy/admin.sock
# Demote and cut the old authority BEFORE enabling the new, so two backends
# are never enabled at once (CONOPS 29). Enabling first was tried and made no
# measurable difference: slow recoveries come from clients retrying into the
# faulted backend before promotion lands, then waiting out their own timeout.
echo "set server tak/$old state maint" | socat stdio "$S" >/dev/null
echo "shutdown sessions server tak/$old" | socat stdio "$S" >/dev/null
echo "set server tak/$new state ready" | socat stdio "$S" >/dev/null
echo "$(date -u +%H:%M:%S.%N) promoted $new (demoted $old)"
EOP
    chmod 755 /usr/local/sbin/fml-tak-promote
    echo "ingress up: authority=$(cat "$REG"); $(getent hosts tak.field)"
    echo "show servers state tak" | socat stdio /run/haproxy/admin.sock | awk 'NR>2 {print "  server", $4, "admin_state", $7, "op_state", $6}'
    ;;
  down)
    systemctl stop haproxy 2>/dev/null || true
    systemctl disable -q haproxy 2>/dev/null || true
    sed -i '/ tak\.field$/d' /etc/hosts
    rm -f /usr/local/sbin/fml-tak-promote
    echo "ingress down (haproxy package left installed, stopped and disabled)"
    ;;
  *)
    echo "usage: ingress-setup.sh up|down" >&2
    exit 64
    ;;
esac
