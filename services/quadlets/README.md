# Quadlets

Podman Quadlet and systemd unit definitions for the mission-service plane.

**One loadable unit.** `martin.container` is the enabled v0.0.1 service. It runs
rootless, pins Martin 1.16.1 by immutable digest, reads one mission MBTiles file
at `/var/lib/fml/maps/mission.mbtiles`, and publishes only to host loopback for
the future ingress layer. It deliberately sets neither restart policy nor a
target-hardware resource limit while `TBR-HA-01` and `TBR-COMP-01` are open.

`example.container.disabled` shows the general conventions. The TAK capability
is `opentakserver`; its internal units and network remain disabled texts named
in that entry's bundle. The `.disabled` suffix is what keeps systemd from
starting them. PostgreSQL, RabbitMQ, the CoT listener, and the parser are not
catalog services.

## What a Quadlet is

A declarative file describing a container that systemd turns into a service
unit at boot. It gives supervision, dependency ordering and journal integration
without a second supervisor, and it puts the service plane in this repository
rather than in a device's local state. See `FML-ADR-029`.

## Conventions

- **One file per catalog service**, named `<service-name>.container`, or an
  internal unit named in that service's bundle. An internal unit is not
  itself a catalog entry.
- **Rootless by default.** A service that genuinely cannot run rootless may run
  rootful, with the reason recorded in its catalog entry, not here.
- **Images referenced by immutable digest, never by tag.** This is checked; see
  `tools/validate-docs.sh`.
- **Every loadable container is claimed by one enabled capability.** A
  single-unit service claims its `.container`. A bundle claims its member
  containers; those members are not catalog entries. A loadable file with no
  enabled owner is a defect. A disabled internal unit is a defect unless
  exactly one capability lists it in `bundle`.
- **Resource limits are set**, once `TBR-COMP-01` establishes the budget. An
  unbounded service on a shared compute element can starve the network plane
  and flap the mesh.
- **No restart policy is set yet.** `TBR-HA-01` is open. A naive restart policy
  on a constrained node turns one failed service into a dead node: the service
  fails on memory exhaustion, restarts, exhausts memory again, and the restart
  loop competes with routing. Leave restart handling to be decided rather than
  copying a default.
- **No secrets in a unit file.** No credential, key, passphrase, or token, in
  any form, including a comment or an example. See `SECURITY.md`.
- **No region-specific values.** Those come from a region profile; see
  `os/config/README.md`.

## Ordering

Network-facing services start after the network plane is up. The bring-up
sequence is in `os/config/interfaces.conf.template`, and the unit-level
expression for interface-bound services is `TBD` pending `TBR-LINUX-01`.
Martin binds only to loopback in this increment, so it does not invent that
open interface dependency.

A service that starts before its interface exists fails in a way that looks
like a service fault, and is not.

## Ingress

Services are reached through the local DNS and proxy arrangement in
`services/ingress/`. Rootless containers cannot bind privileged ports without
explicit handling, which is part of why ingress is a separate concern rather
than a per-service setting.
