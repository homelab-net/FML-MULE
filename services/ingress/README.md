# Ingress

Local DNS and reverse proxy configuration: how an operator's device reaches the
services on a node.

**Nothing is configured. No service exists to reach.**

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

This is not currently anyone's trade. It should be, and it is recorded here
rather than discovered later. It interacts with `services/identity/`,
`TBR-SEC-01`, and with `FML-ADR-042`, since certificate validation depends on
credible time.

## Naming and collisions

Two independently built deployments meeting at an incident must not collide. A
fixed local domain across every deployment makes that collision certain. The
domain comes from the mission configuration package; see `TBR-NET-01`.

## What never appears here

No real domain, hostname, member identity, callsign, or deployment location, in
any form, including in comments and examples. A DNS or proxy configuration
discloses the structure of a deployment and the names of its participants. See
`SECURITY.md`.
