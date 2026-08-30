# Service controller

**APPROVED, NOT YET IMPLEMENTABLE. This directory contains this `README.md` and
nothing else.**

`FML-ADR-035` approves the MULE service controller as a **fixed-policy lifecycle
layer, not a cluster scheduler**.

Approval is not permission to start. The restart and recovery policy is
undecided, and that is the half most likely to cause harm.

## What it does

**Source:** SAD v0.31 section 15.

Translates mission profile, authenticated user demand, role and scope, battery,
thermal state, network state and shared-host availability into **systemd service
targets**.

It starts and stops a fixed approved service catalog, applies grace timers,
applies minimum-residency timers, prevents oscillation, and reports current
service state.

**It never replaces systemd or Podman health management.** Because it commands
systemd rather than supervising processes itself, its own failure does not take
services down with it.

## Scope limit

From SAD section 29.5:

> Starts/stops approved systemd targets only; not a cluster scheduler.

**Owner:** Platform / Systems.

Custom code is accepted here because this is MULE-specific policy glue, which is
governing principle 10 in SAD section 0.3, not a replacement for a mature
orchestration platform. CONOPS section 81 excludes Kubernetes-scale
orchestration.

## What must close before implementation starts

| Question | Trade | Priority |
| --- | --- | ---: |
| Under what conditions a service may be restarted automatically | `TBR-HA-01` | 12 |
| What state a restart must not lose | `TBR-TAK-01` | 9, `CRITICAL` |
| The reservation mechanism protecting the Network Plane | `TBR-COMP-01` | 2, `CRITICAL` |

## Why not build it anyway

The failure mode is specific, well documented and severe.

A service fails because the node is out of memory. It restarts immediately. It
consumes the memory again. The restart loop competes with the routing daemon for
CPU. Mesh links flap. **A single service fault becomes total node loss**, in the
field, with nobody present.

`FML-ADR-021` put both planes on one compute element and explicitly accepted
that a mission-service fault can starve the network plane. This component is
where that accepted cost is either managed or realised.

The opposite failure matters too: a service that stays down after a transient
fault, during an incident, with nobody watching.

`TBR-HA-01` exists to determine which policy avoids both. Writing one now means
picking a systemd default and shipping it, which is precisely what the trade was
raised to prevent.

**Leave `Restart=` unset in every Quadlet unit until it closes.** See
`services/quadlets/example.container.disabled`.

## What CONOPS behaviour it owns

- **Section 5.8:** damping, persistence, minimum-residency or threshold logic
  sufficient to prevent oscillation. Services do not move merely because another
  host looks marginally better.
- **Section 10:** service activation does not tie team capability to a single
  EUD remaining connected; grace periods absorb roaming and sleep states.
- **Section 11:** activation does not create externally observable behaviour
  revealing privileged-user login or leadership presence. Stable hosting
  behaviour is preferred for privileged services.
- **Section 9.4:** S3 services are the first class stopped under constrained
  battery, thermal, bandwidth or compute conditions.

## Assessed against `FML-ADR-052`, and deliberately not started

A pure function in `mule/` answering "which service classes are permitted right
now" was assessed against the four `FML-ADR-052` conditions on 2026-08-28 and
**declined by the Program Owner**. It is not written, and it should not be
written until `TBR-HA-01` closes.

The assessment is recorded because the conditions arguably permitted it, and an
argument that was made once will be made again. It ran: the hazard this README
names is a restart loop, a classifier commands nothing and cannot cause one, and
section 5.8's damping clause governs *moving* a service, which is an actuator's
act rather than a classifier's.

The decision went the other way, and the reasoning is worth keeping. Service
lifecycle is one subject, not two. Splitting the judgement from the actuation
would put the two halves under different trades and different reviewers, and
`TBR-HA-01` exists precisely because getting the relationship between them wrong
turns a single service fault into total node loss. A classifier nothing consumes
is also a classifier nothing validates.

What this leaves undone is real and is named rather than hidden: the section 9.4
`[SHALL]` making S3 the first class stopped has no implementation, and will not
have one until this component exists.

`CCR-02` records the shedding order below S3, which section 9 never stated, so
that the order is settled before anyone implements it rather than during.

## What already exists in `mule/`

`mule/bringup.py` cites `FML-ADR-035`, and is named here so that a reader
arriving at a blocked directory can see exactly how far it goes.

It holds the order the network plane is brought up in, and answers one
question: which ordering rules a sequence broke. `services_started` is one step
in that order, and the only thing the module says about it is that it comes
after the mesh interface is up.

It decides **nothing this component owns**. Not which services run, not their
classes, not the order among themselves, not what is shed first under
`CCR-02`'s order, and not whether a service should be restarted or moved. It
commands nothing at all: it is handed a sequence that already happened and
reports what was wrong with it, which is the opposite end of the problem from
an actuator.

The distinction is the same one the assessment above turns on. A restart loop
is the hazard this README names; a function that reads a completed sequence
cannot cause one.

## What can be done now

- **Close `TBR-HA-01`.** Its fault injection runs largely against fakes on an
  ordinary machine; only the network plane interaction needs radios.
- **Close `TBR-TAK-01`**, which needs no hardware.
