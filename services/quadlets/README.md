# Quadlets

Podman Quadlet and systemd unit definitions for the mission-service plane.

**Empty of service definitions.** No service has been selected or approved; see
`services/catalog/`. `example.container.disabled` is a commented reference
showing the conventions, and is deliberately not a loadable unit.

## What a Quadlet is

A declarative file describing a container that systemd turns into a service
unit at boot. It gives supervision, dependency ordering and journal integration
without a second supervisor, and it puts the service plane in this repository
rather than in a device's local state. See `FML-ADR-029`.

## Conventions

- **One file per service**, named for its catalog entry:
  `<service-name>.container`.
- **Rootless by default.** A service that genuinely cannot run rootless may run
  rootful, with the reason recorded in its catalog entry, not here.
- **Images referenced by immutable digest, never by tag.** This is checked; see
  `tools/validate-docs.sh`.
- **Every unit has a catalog entry.** A unit with no entry is a defect.
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

Services start after the network plane is up. The bring-up sequence is in
`os/config/interfaces.conf.template`, and the unit-level expression of it is
`TBD` pending `TBR-LINUX-01`.

A service that starts before its interface exists fails in a way that looks
like a service fault, and is not.

## Ingress

Services are reached through the local DNS and proxy arrangement in
`services/ingress/`. Rootless containers cannot bind privileged ports without
explicit handling, which is part of why ingress is a separate concern rather
than a per-service setting.
