# Service controller

**PLACEHOLDER. DO NOT IMPLEMENT.**

This directory contains this `README.md` and nothing else, by decision. See
`AGENTS.md`, constraint one, and `services/README.md`, the placeholder rule.

## What this component will do

Decide what runs on a node, when, and what happens when something fails.

Expected to cover:

- Starting and stopping services according to the mission profile, including
  EMCON, where a node must not emit.
- Ordering: services start after the network plane is up.
- Failure handling: whether a failed service is restarted, how often, and when
  the node stops trying.
- Reporting the result to the operator status surface, so that a service the
  node has given up on is visible rather than silently absent.

## Decision reference

`FML-ADR-029` selects rootless Podman with Quadlet units under systemd, which
means **systemd already provides supervision, ordering and restart
mechanics**. This component is not a second supervisor. It is the policy layer
that decides what systemd is told to do, and the honest possibility is that it
turns out to be a small amount of configuration rather than a service at all.

That is another reason not to build it yet: building it guarantees it becomes a
service.

## What must close before implementation starts

| Question | Trade |
| --- | --- |
| Under what conditions a service may be restarted automatically | `TBR-HA-01` |
| What state a restart must not lose | `TBR-TAK-01` |

## Why not build it anyway

The failure mode is specific, well documented, and severe.

A service fails because the node is out of memory. It restarts immediately. It
consumes the memory again. The restart loop competes with the routing daemon
for CPU. Mesh links flap. A single service fault becomes total node loss, in
the field, with nobody present.

`FML-ADR-021` put both planes on one compute element and explicitly accepted
that a fault in the mission-service plane can starve the network plane. This
component is where that accepted cost is either managed or realised.

The opposite failure matters too: a service that stays down after a transient
fault, during an incident, with nobody watching.

`TBR-HA-01` exists to determine which restart policy avoids both. Writing one
now means picking a systemd default and shipping it, which is precisely the
thing the trade was raised to prevent.

## What can be done now

- **Close `TBR-HA-01`.** Its fault injection work runs largely against fakes on
  an ordinary machine, per the hardware abstraction rule; only the network
  plane interaction needs radios.
- **Close `TBR-TAK-01`**, which requires no hardware.
- **Leave `Restart=` unset** in every Quadlet unit until then. See
  `services/quadlets/example.container.disabled`.
