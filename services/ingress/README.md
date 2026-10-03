# Ingress

Local DNS and reverse proxy configuration: how an operator's device reaches the
services on a node.

**Nothing is configured. Martin now exists, but there is no EUD-facing route.**
Its Quadlet publishes the backend only on `127.0.0.1:3000`, preserving the
requirement below that an application port is not directly reachable. GAP-09E
still owns the AP/ingress path, GAP-09H the operator procedure, and GAP-09I the
phone-over-AP acceptance.

**Forward-path template drafted (2026-09-27, `SIMULATED`).**
`os/config/haproxy.conf.template` is the `FML-ADR-031` HAProxy forward config: an
HTTP frontend on the EUD AP interface routing by host name to Martin's loopback
backend. The reproducible bench script `test/bench/ingress-name-routing.sh` (`SIMULATED`,
x86) runs HAProxy `lts` in front of the Martin container and asserts the routing:
a request with the matching `Host` reaches Martin (`/catalog` and a `z/x/y` tile,
HTTP 200), and a non-matching `Host` gets **503** (no default backend -- fail
closed). Still owed, and marked `TBD` in the template: the frontend bind address
and the DNS name resolve onto the **EUD AP subnet**, which is undecided and now
owned by **`TBR-NET-05`** (raised because `TBR-NET-01` closed only the mesh
prefix); **TLS**, which stays a **recommended v0.0.1 deferral pending the Owner's
recorded disposition** (GAP-09H G5b; `THREAT_MODEL.md` requires browser traffic
leaving a MULE to be encrypted, so plaintext ingress is not deployed until the
Owner accepts the deferral or TLS is built); and the reverse-proxy authentication
(`X-Ssl-Cert`, `TBR-ID-01`) below.

`FML-ADR-031` selects local DNS plus a lightweight TCP/HTTP proxy layer, with
**HAProxy** as the preferred initial proxy, and prefers **TCP passthrough** for
end-to-end protected protocols so the proxy is not a decryption point. Each
eligible backend may hold its own key and a certificate valid for the same
logical identity; **one service private key is not copied to every node**.

Backend selection is fed by the Service Authority Registry (`FML-ADR-049`): a
process that is alive but does not hold authoritative state is not an acceptable
backend for authoritative traffic.

## What ingress must provide

An operator associates a phone with the node's access point and needs to reach
browser-based field services **by name**, with no configuration, no internet,
and no central directory. Local-first is a requirement, not a preference; see
`docs/NON-GOALS.md`.

That means:

- **Local DNS**, authoritative for the deployment's local domain, forwarding
  nothing by default. Template in `os/config/dnsmasq.conf.template`.
- **A reverse proxy** in front of the services, so that they are reached by
  name and path rather than by port.
- **TLS**, which is the hard part. See below.

## Rootless containers and privileged ports

Services run rootless under Podman (`FML-ADR-029`), and a rootless container
cannot bind a privileged port without explicit handling. This is the main
reason ingress is a separate concern rather than a per-service setting: the
handling is decided once, here, rather than repeated and diverged across every
service.

The mechanism is `TBD`.

## The reverse proxy authenticates, and that is not written down anywhere else

**Added 2026-08-31**, from
`docs/evidence/TBR-TAK-01/2026-08-31-certificate-enrollment.md` and
`2026-08-31-mission-api-and-the-header-that-authenticates.md`.

OpenTAKServer's Marti API does not perform client-certificate authentication
itself. It reads a **header**, `X-Ssl-Cert` by default, containing a PEM
certificate, and verifies that the certificate chains to its own CA. Measured:
a certificate presented in that header, **with no private key and over plain
HTTP**, is accepted.

That makes the reverse proxy the authenticating component, and it puts three
requirements here rather than on the service:

- **The proxy shall SET the header, never forward one.** A proxy that passes
  through a client-supplied `X-Ssl-Cert` lets any client authenticate as the
  subject of any certificate it can obtain, and a certificate is public data.
- **The application port shall not be reachable except through the proxy.**
  Upstream mitigates by binding `127.0.0.1`; `FML-ADR-029` puts services in
  containers, where a published port or a shared network namespace removes that
  mitigation without anyone editing a security setting.
- **Revocation has to happen somewhere.** The service's verification path loads
  the CA and no CRL, so a revoked certificate verifies like any other. If
  revocation is to mean anything on this path, the proxy is where it can.

None of this is decided. It is recorded here because ingress is where it lands,
and because it was found in a state study rather than in a security review.

## TLS in a local-first system

A browser reaching a service over plain HTTP produces warnings, blocks features
that require a secure context, and teaches operators to click through security
warnings, which is a habit with consequences beyond this program.

Producing a certificate a browser accepts, on a node with no internet, no
public DNS, and no reachable certificate authority, is genuinely unsolved here.
The obvious approaches each have a real cost:

- **A program certificate authority**, with its root distributed to operator
  devices in advance. Works, and requires provisioning every device before a
  deployment, which is exactly the kind of preparation that does not happen.
- **A public certificate for a real domain**, with the private key on every
  node. A node is expected to be captured (`THREAT_MODEL.md`), so this
  distributes a publicly trusted key to devices designed to be lost.
- **Self-signed with an operator exception.** Trains the wrong habit.
- **Reusing a certificate authority the program already runs** — in particular
  the OpenTAKServer CA, whose bench leaf already carries the EUD access-point
  address in its SAN and whose root the enrolled EUDs already hold. This looks
  nearly free and **must not be done.** `THREAT_MODEL.md` records that the Marti
  API "reads a certificate from an `X-Ssl-Cert` header and checks that it chains
  to the server CA", that this "proves the certificate is valid and **not** that
  the sender holds the private key" because "a certificate is public", and that
  "**revocation is not consulted on that path**". A TLS server certificate is
  transmitted in clear in every handshake. Fronting a browser service with a
  leaf from that CA therefore hands a usable, unrevocable API authenticator to
  every device that completes a handshake, including one that has merely
  associated to the access point. Installing that root on an operator's personal
  device is worse: a certificate authority with no working revocation becomes a
  trust anchor for everything else that device does.

  The general rule the specific case produces: **the CA that signs the ingress
  certificate must not be a CA that authenticates anything.** A separate
  authority whose only purpose is server identity is sound; borrowing one that
  is already an authorisation root is not, however convenient its SAN happens to
  be.

This is not currently anyone's trade. It should be, and it is recorded here
rather than discovered later. It interacts with `services/identity/`,
`TBR-SEC-01`, and with `FML-ADR-042`, since certificate validation depends on
credible time.

## Naming and collisions

Two independently built deployments meeting at an incident must not collide. A
fixed local domain across every deployment makes that collision certain. The
domain comes from the mission configuration package.

**No trade currently owns it, and that is a gap rather than an oversight to
leave standing.** This line cited `TBR-NET-01` until 2026-10-02; that trade is
`CLOSED` and decided the per-deployment **mesh field prefix**, not the local
domain a browser resolves on the access-point subnet. `TBR-NET-05` owns the AP
subnet, DHCP range and lease. `TBR-NET-06` owns how a **remote** EUD resolves
one stable service name to its assigned MULE across the WAN overlay. Neither
decides the local domain itself, which the HAProxy `hdr(host)` ACL, the
`dnsmasq` configuration and any ingress certificate's SAN all need before a
phone can reach a service by name.

## What never appears here

No real domain, hostname, member identity, callsign, or deployment location, in
any form, including in comments and examples. A DNS or proxy configuration
discloses the structure of a deployment and the names of its participants. See
`SECURITY.md`.
