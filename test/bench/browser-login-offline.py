#!/usr/bin/env python3
"""Offline browser-service login against fakes, for TBR-ID-01.

``TBR-ID-01`` asks whether the browser services need a common identity
provider, and its closure evidence asks for offline login to be demonstrated
with no WAN. This exercises one candidate on an ordinary computer, with every
component a fake:

* an **ephemeral PKI** made with the ``openssl`` CLI in a temporary directory:
  a mission client-certificate authority standing in for the ``FML-ADR-036``
  mission/enrollment authority, a separate server-identity authority for the
  ingress certificate (``services/ingress/README.md``: the CA that signs the
  ingress certificate must not authenticate anything), and a second
  deployment's authority that must not be trusted;
* a **fake ingress** per node, standing in for ``FML-ADR-031`` HAProxy. It
  terminates TLS, requires a client certificate that chains to the mission
  authority, checks a revocation list, refuses everything while node time is
  not credible (``FML-ADR-042``), strips any client-supplied identity header
  and sets its own;
* a **fake application** doing application-native RBAC (``FML-ADR-037``) from
  role and scope data held apart from the certificate (SAD section 16.4),
  standing in for signed policy the ``FML-ADR-047`` Mission Trust Service
  would distribute. It is not signed here.

Nothing is installed and nothing persists: keys live in a temporary directory
removed on exit, and every identity is a placeholder. Run it inside a network
namespace that has only loopback, so "no WAN" is a precondition the script
checks rather than a claim::

    unshare -rn sh -c 'ip link set lo up && \
        python3 test/bench/browser-login-offline.py --require-offline'

It proves the mechanism composes with stock OpenSSL and stdlib TLS. It is not
HAProxy, not a browser and not an EUD: how a phone's browser presents a client
certificate, and how often it asks, is the measurement this cannot make.
``SIMULATED``. See ``docs/evidence/TBR-ID-01/``.
"""

from __future__ import annotations

import argparse
import errno
import http.client
import http.server
import json
import shutil
import socket
import ssl
import subprocess
import sys
import tempfile
import threading
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from pathlib import Path

HOST = "127.0.0.1"
SERVER_NAME = "portal.mule.test"
ID_HEADERS = frozenset({"x-fml-principal", "x-fml-serial"})
REFUSED = "refused-tls"
# The TLS alert a refusal carries, so a refusal for the wrong reason is a miss.
# With no client certificate the server closes as it sends its alert, and the
# client sees the alert, a reset or an EOF depending on which it reads first:
# all three were observed. Any refusal passes that case; the application-reached
# check in cases() is what establishes it was one.
NO_CERT_ANY = f"{REFUSED} (any reason)"
EXPIRED = f"{REFUSED} (SSLV3_ALERT_CERTIFICATE_EXPIRED)"
# OpenSSL maps a not-yet-valid peer to the generic bad_certificate alert.
NOT_YET = f"{REFUSED} (SSLV3_ALERT_BAD_CERTIFICATE)"
UNKNOWN_CA = f"{REFUSED} (TLSV1_ALERT_UNKNOWN_CA)"
REVOKED = f"{REFUSED} (SSLV3_ALERT_CERTIFICATE_REVOKED)"
HOUR = timedelta(hours=1)
DAY = timedelta(days=1)

CA_CONF = """[ca]
default_ca = d
[d]
dir = {d}
database = $dir/index.txt
new_certs_dir = $dir/issued
serial = $dir/serial
crlnumber = $dir/crlnumber
certificate = $dir/ca.crt
private_key = $dir/ca.key
default_md = sha256
default_crl_days = 1
policy = p
unique_subject = no
[p]
commonName = supplied
[client]
basicConstraints = critical, CA:FALSE
keyUsage = critical, digitalSignature
extendedKeyUsage = clientAuth
subjectKeyIdentifier = hash
authorityKeyIdentifier = keyid
[server]
basicConstraints = critical, CA:FALSE
keyUsage = critical, digitalSignature
extendedKeyUsage = serverAuth
subjectAltName = DNS:{server_name}
subjectKeyIdentifier = hash
authorityKeyIdentifier = keyid
"""


def _openssl(*argv: str) -> str:
    exe = shutil.which("openssl")
    if exe is None:
        raise SystemExit("openssl is not on PATH")
    # Fixed argv built by this script, no shell, a throwaway temporary PKI.
    done = subprocess.run(  # noqa: S603
        [exe, *argv], check=False, capture_output=True, text=True
    )
    if done.returncode != 0:
        raise SystemExit(f"openssl {argv[0]} failed: {done.stderr.strip()}")
    return done.stdout


def verify_at(ca: Path, leaf: Path, offset: timedelta) -> str:
    """Verify a leaf as a node whose clock is off by ``offset`` would."""
    exe = shutil.which("openssl")
    if exe is None:
        raise SystemExit("openssl is not on PATH")
    when = int((datetime.now(UTC) + offset).timestamp())
    done = subprocess.run(  # noqa: S603
        [exe, "verify", "-CAfile", str(ca), "-attime", str(when), f"{leaf}.crt"],
        check=False, capture_output=True, text=True,
    )  # fmt: skip
    if done.returncode == 0:
        return "verify OK"
    errors = [ln for ln in done.stderr.splitlines() if "error" in ln]
    return errors[0].split(": ", 1)[-1] if errors else "verify failed"


def _asn1(when: datetime) -> str:
    return when.strftime("%Y%m%d%H%M%SZ")


class Pki:
    """One throwaway certificate authority driven through ``openssl ca``."""

    def __init__(self, root: Path, name: str) -> None:
        """Create the authority's directory, database and self-signed root."""
        self.dir = root / name
        (self.dir / "issued").mkdir(parents=True)
        (self.dir / "index.txt").write_text("")
        (self.dir / "serial").write_text("1000\n")
        (self.dir / "crlnumber").write_text("1000\n")
        self.conf = self.dir / "ca.cnf"
        self.conf.write_text(CA_CONF.format(d=self.dir, server_name=SERVER_NAME))
        self.cert = self.dir / "ca.crt"
        _openssl(
            "req", "-x509", "-newkey", "ec", "-pkeyopt", "ec_paramgen_curve:P-256",
            "-nodes", "-days", "30", "-subj", f"/CN={name} (fake)",
            # Python 3.13 verifies with VERIFY_X509_STRICT by default, which
            # needs these explicit; a CA a modern client accepts carries them.
            "-addext", "basicConstraints=critical,CA:TRUE",
            "-addext", "keyUsage=critical,keyCertSign,cRLSign",
            "-keyout", str(self.dir / "ca.key"), "-out", str(self.cert),
        )  # fmt: skip

    def issue(self, cn: str, ext: str, start: timedelta, end: timedelta) -> Path:
        """Issue a leaf valid from ``now + start`` to ``now + end``."""
        base = self.dir / cn
        _openssl(
            "req", "-new", "-newkey", "ec", "-pkeyopt", "ec_paramgen_curve:P-256",
            "-nodes", "-subj", f"/CN={cn}",
            "-keyout", f"{base}.key", "-out", f"{base}.csr",
        )  # fmt: skip
        now = datetime.now(UTC)
        _openssl(
            "ca", "-batch", "-notext", "-config", str(self.conf), "-extensions", ext,
            "-startdate", _asn1(now + start), "-enddate", _asn1(now + end),
            "-in", f"{base}.csr", "-out", f"{base}.crt",
        )  # fmt: skip
        return base

    def revoke(self, leaf: Path) -> None:
        """Mark a leaf revoked in this authority's database."""
        _openssl("ca", "-config", str(self.conf), "-revoke", f"{leaf}.crt")

    def crl(self, name: str) -> Path:
        """Write the current revocation list, as the trust service would carry."""
        out = self.dir / f"{name}.crl.pem"
        _openssl("ca", "-config", str(self.conf), "-gencrl", "-out", str(out))
        return out


@dataclass
class Node:
    """A fake node: a TLS ingress in front of one loopback application."""

    name: str
    client_ca: Path
    crl: Path
    server_leaf: Path
    roles: Path
    time_credible: bool = True
    ingress_port: int = 0
    app_port: int = 0
    app_hits: int = 0
    servers: list[http.server.ThreadingHTTPServer] = field(default_factory=list)


def _reply(handler: http.server.BaseHTTPRequestHandler, code: int, data: bytes) -> None:
    handler.send_response(code)
    handler.send_header("Content-Length", str(len(data)))
    handler.end_headers()
    handler.wfile.write(data)


def _authorize(who: str, path: str, roles: Path) -> tuple[int, dict[str, str]]:
    """Application-native RBAC: role and scope come from data, not the cert."""
    # Re-read on every request, so a role or scope change takes effect without
    # reissuing the certificate (SAD section 16.4).
    users = json.loads(roles.read_text())["users"]
    if who not in users:
        return 403, {"error": "not in role data"}
    role, teams = users[who]["role"], users[who]["teams"]
    parts = path.strip("/").split("/")
    if parts == ["whoami"]:
        allowed = True
    elif parts == ["admin"]:
        # CONOPS 7.1: a Unit Member receives no infrastructure administration.
        allowed = role == "field-network-administrator"
    elif len(parts) == 3 and parts[0] == "team" and parts[2] == "status":
        # CONOPS 7.2: no automatic access to another team's scope.
        allowed = parts[1] in teams
    else:
        return 404, {"error": "no such path"}
    return (200 if allowed else 403), {"who": who, "role": role}


def _app_handler(node: Node) -> type[http.server.BaseHTTPRequestHandler]:
    class App(http.server.BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            node.app_hits += 1
            who = self.headers.get("X-Fml-Principal")
            if who is None:
                code, body = 401, {"error": "no principal"}
            else:
                code, body = _authorize(who, self.path, node.roles)
            _reply(self, code, json.dumps({**body, "node": node.name}).encode())

        def log_message(self, *_: object) -> None:
            pass

    return App


def _ingress_handler(node: Node) -> type[http.server.BaseHTTPRequestHandler]:
    class Ingress(http.server.BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            if not node.time_credible:
                # FML-ADR-042: certificate checks shall not fail open on invalid
                # time. TLS cannot know the clock is wrong, so the gate is here.
                _reply(self, 503, b'{"error": "node time not credible"}')
                return
            cert = self.connection.getpeercert()
            subject = dict(x[0] for x in cert["subject"])
            headers = {
                k: v for k, v in self.headers.items() if k.lower() not in ID_HEADERS
            }
            # SET, never forward: services/ingress/README.md.
            headers["X-Fml-Principal"] = subject["commonName"]
            headers["X-Fml-Serial"] = cert["serialNumber"]
            upstream = http.client.HTTPConnection(HOST, node.app_port, timeout=5)
            upstream.request("GET", self.path, headers=headers)
            resp = upstream.getresponse()
            _reply(self, resp.status, resp.read())

        def log_message(self, *_: object) -> None:
            pass

    return Ingress


def start(node: Node) -> None:
    """Bring up the node's application, then its TLS ingress, on loopback."""
    app = http.server.ThreadingHTTPServer((HOST, 0), _app_handler(node))
    node.app_port = app.server_address[1]
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    ctx.minimum_version = ssl.TLSVersion.TLSv1_3
    ctx.load_cert_chain(f"{node.server_leaf}.crt", f"{node.server_leaf}.key")
    ctx.verify_mode = ssl.CERT_REQUIRED
    ctx.load_verify_locations(cafile=str(node.client_ca))
    ctx.load_verify_locations(cafile=str(node.crl))
    ctx.verify_flags |= ssl.VERIFY_CRL_CHECK_LEAF
    ingress = http.server.ThreadingHTTPServer((HOST, 0), _ingress_handler(node))
    ingress.socket = ctx.wrap_socket(ingress.socket, server_side=True)
    node.ingress_port = ingress.server_address[1]
    node.servers = [app, ingress]
    for server in node.servers:
        threading.Thread(target=server.serve_forever, daemon=True).start()


def request(
    node: Node,
    path: str,
    leaf: Path | None,
    server_ca: Path,
    headers: dict[str, str] | None = None,
    direct: bool = False,
) -> str:
    """Make one request as a client would; return the outcome as text."""
    try:
        if direct:
            conn = http.client.HTTPConnection(HOST, node.app_port, timeout=5)
        else:
            ctx = ssl.create_default_context(cafile=str(server_ca))
            if leaf is not None:
                ctx.load_cert_chain(f"{leaf}.crt", f"{leaf}.key")
            raw = socket.create_connection((HOST, node.ingress_port), timeout=5)
            conn = http.client.HTTPSConnection(SERVER_NAME, timeout=5, context=ctx)
            conn.sock = ctx.wrap_socket(raw, server_hostname=SERVER_NAME)
        conn.request("GET", path, headers=headers or {})
        resp = conn.getresponse()
        body = json.loads(resp.read() or b"{}")
    except ssl.SSLCertVerificationError as exc:
        return f"{REFUSED} (client: {exc.verify_message})"
    except ssl.SSLError as exc:
        return f"{REFUSED} ({exc.reason or type(exc).__name__})"
    except (ConnectionResetError, BrokenPipeError) as exc:
        return f"{REFUSED} ({type(exc).__name__})"
    who = body.get("who")
    return f"{resp.status} as {who}" if who else str(resp.status)


def check_offline() -> str:
    """Refuse to run unless the only network is loopback; describe what was seen."""
    names = sorted(name for _, name in socket.if_nameindex())
    probe = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    probe.settimeout(2)
    try:
        # A public address. With no route this fails before anything is sent.
        probe.connect(("1.1.1.1", 443))
    except OSError as exc:
        if exc.errno != errno.ENETUNREACH:
            raise SystemExit(f"not offline: connect failed with {exc!r}") from exc
        outcome = "ENETUNREACH"
    else:
        raise SystemExit("not offline: a connection to 1.1.1.1:443 succeeded")
    finally:
        probe.close()
    up = [n for n in names if n != "lo" and _is_up(n)]
    if up:
        raise SystemExit(f"not offline: interfaces up besides lo: {up}")
    return f"interfaces={names} (only lo up); connect 1.1.1.1:443 -> {outcome}"


def _is_up(name: str) -> bool:
    flags = Path(f"/sys/class/net/{name}/flags")
    return flags.exists() and int(flags.read_text(), 16) & 0x1 == 1


@dataclass
class World:
    """Everything the cases need: two nodes of one deployment and the leaves."""

    a: Node
    b: Node
    server_ca: Path
    leaf: dict[str, Path]
    roles: Path
    mission_ca: Path


def build(tmp: Path) -> World:
    """Make the fake PKI, role data and two nodes sharing one mission authority."""
    mission = Pki(tmp, "mission-enrollment-authority")
    serverid = Pki(tmp, "ingress-server-identity")
    foreign = Pki(tmp, "other-deployment-authority")
    valid = (-HOUR, 2 * DAY)  # a short-lived mission credential (FML-ADR-036)
    leaf = {
        cn: mission.issue(cn, "client", *valid)
        for cn in ("member-a1", "lead-a", "admin-1", "member-revoked", "not-rostered")
    }
    leaf["expired"] = mission.issue("expired", "client", -10 * DAY, -DAY)
    leaf["not-yet-valid"] = mission.issue("not-yet-valid", "client", DAY, 10 * DAY)
    leaf["foreign"] = foreign.issue("member-a1", "client", *valid)
    crl_before = mission.crl("before-revocation")
    mission.revoke(leaf["member-revoked"])
    crl_after = mission.crl("after-revocation")
    roles = tmp / "roles.json"
    roles.write_text(json.dumps({"users": {
        "member-a1": {"role": "unit-member", "teams": ["a"]},
        "member-revoked": {"role": "unit-member", "teams": ["a"]},
        "lead-a": {"role": "team-lead", "teams": ["a"]},
        "admin-1": {"role": "field-network-administrator", "teams": []},
        "expired": {"role": "unit-member", "teams": ["a"]},
        "not-yet-valid": {"role": "unit-member", "teams": ["a"]},
    }}))  # fmt: skip
    # Node A has received the revocation; node B is a partition that has not.
    a = Node(
        "node-a",
        mission.cert,
        crl_after,
        serverid.issue(SERVER_NAME, "server", -HOUR, 2 * DAY),
        roles,
    )
    b = Node(
        "node-b",
        mission.cert,
        crl_before,
        serverid.issue(f"{SERVER_NAME}-b", "server", -HOUR, 2 * DAY),
        roles,
    )
    start(a)
    start(b)
    return World(a, b, serverid.cert, leaf, roles, mission.cert)


def _promote(roles: Path, who: str, team: str) -> None:
    data = json.loads(roles.read_text())
    data["users"][who]["teams"].append(team)
    roles.write_text(json.dumps(data))


def cases(w: World) -> list[tuple[str, str, str, bool]]:
    """Run every case in order; return (case, expected, observed, ok) rows."""
    rows: list[tuple[str, str, str, bool]] = []

    def case(
        label: str,
        expected: str,
        node: Node,
        path: str,
        leaf: str | None,
        **kw: object,
    ) -> None:
        hits = node.app_hits
        got = request(node, path, w.leaf[leaf] if leaf else None, w.server_ca, **kw)
        if got.startswith(REFUSED) and node.app_hits != hits:
            # A refusal is only a refusal if the application never saw it.
            got += " but the application was reached"
        if expected == NO_CERT_ANY:
            ok = got.startswith(REFUSED) and not got.endswith("reached")
        else:
            ok = got == expected
        rows.append((label, expected, got, ok))

    def offline_check(label: str, expected: str, got: str) -> None:
        rows.append((label, expected, got, got == expected))

    case("member, own identity", "200 as member-a1", w.a, "/whoami", "member-a1")
    case("member, own team", "200 as member-a1", w.a, "/team/a/status", "member-a1")
    case("member, admin function", "403 as member-a1", w.a, "/admin", "member-a1")
    case("team lead, other team", "403 as lead-a", w.a, "/team/b/status", "lead-a")
    case("administrator, admin function", "200 as admin-1", w.a, "/admin", "admin-1")
    case("no client certificate", NO_CERT_ANY, w.a, "/whoami", None)
    case("valid certificate, not in role data", "403", w.a, "/whoami", "not-rostered")
    case("expired certificate", EXPIRED, w.a, "/whoami", "expired")
    case("certificate not yet valid", NOT_YET, w.a, "/whoami", "not-yet-valid")
    case("another deployment's authority", UNKNOWN_CA, w.a, "/whoami", "foreign")
    case(
        "forged identity header via ingress",
        "403 as member-a1",
        w.a,
        "/admin",
        "member-a1",
        headers={"X-Fml-Principal": "admin-1"},
    )
    case(
        "CONTROL: forged header, ingress bypassed",
        "200 as admin-1",
        w.a,
        "/admin",
        None,
        headers={"X-Fml-Principal": "admin-1"},
        direct=True,
    )
    case(
        "revoked, node that has the revocation",
        REVOKED,
        w.a,
        "/whoami",
        "member-revoked",
    )
    case(
        "revoked, partition without it (CONOPS 15)",
        "200 as member-revoked",
        w.b,
        "/whoami",
        "member-revoked",
    )
    case(
        "same credential at a second node",
        "200 as member-a1",
        w.b,
        "/whoami",
        "member-a1",
    )
    _promote(w.roles, "lead-a", "b")
    case(
        "scope change, same certificate",
        "200 as lead-a",
        w.a,
        "/team/b/status",
        "lead-a",
    )
    w.a.time_credible = False
    case("node time not credible (FML-ADR-042)", "503", w.a, "/whoami", "member-a1")
    w.a.time_credible = True
    case("node time credible again", "200 as member-a1", w.a, "/whoami", "member-a1")
    # Why the gate cannot be left to TLS: certificate checks use the node clock.
    early = w.leaf["not-yet-valid"]
    offline_check(
        "not-yet-valid, true clock",
        "certificate is not yet valid",
        verify_at(w.mission_ca, early, 0 * DAY),
    )
    offline_check(
        "not-yet-valid, clock 2 days fast",
        "verify OK",
        verify_at(w.mission_ca, early, 2 * DAY),
    )
    return rows


def main() -> int:
    """Build the fakes, run the cases, print a table, exit non-zero on a miss."""
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument(
        "--require-offline",
        action="store_true",
        help="refuse to run unless only loopback is up",
    )
    args = ap.parse_args()
    print(f"openssl: {_openssl('version').strip()}; python ssl: {ssl.OPENSSL_VERSION}")
    if args.require_offline:
        print(f"offline precondition: {check_offline()}")
    with tempfile.TemporaryDirectory(prefix="id01-") as tmp:
        world = build(Path(tmp))
        rows = cases(world)
        for node in (world.a, world.b):
            for server in node.servers:
                server.shutdown()
    width = max(len(r[0]) for r in rows)
    misses = 0
    for label, expected, got, ok in rows:
        misses += not ok
        print(
            f"{'PASS' if ok else 'FAIL'}  {label:<{width}}  expected {expected:<50} "
            f"got {got}"
        )
    print(f"{len(rows) - misses}/{len(rows)} cases as expected")
    return 1 if misses else 0


if __name__ == "__main__":
    sys.exit(main())
