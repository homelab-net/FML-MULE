# Status aggregator

**PLACEHOLDER. DO NOT IMPLEMENT.**

This directory contains this `README.md` and nothing else, by decision. See
`AGENTS.md`, constraint one, and `services/README.md`, the placeholder rule.

## What this component will do

Collect health and state from every part of a node and present it as the
operator status surface: what a person looks at to answer "is this thing
working, and if not, which part".

Expected to cover:

- **Radio state** per bearer: enumerated, associated, link quality, peers.
- **Mesh state**: neighbours, originators, path selection.
- **Power state**: pack voltage, current draw, estimated endurance.
- **Thermal state**: component temperatures, whether anything is throttling.
- **Time state**: whether the clock is credible, and if not, why. Required by
  `FML-ADR-042`, which obliges a node to report that its time is not credible
  so that a refusal to validate is diagnosable rather than mysterious.
- **Service state**: what is running, what has failed, and what the node has
  given up trying to restart (`TBR-HA-01`).
- **Compatibility set version** the node is running, which is what makes a
  field fault report actionable (`FML-ADR-040`).

## Decision reference

No ADR selects this component's design. Its execution model follows
`FML-ADR-029` (rootless Podman, Quadlet) and it consumes the time-credibility
reporting obligation from `FML-ADR-042`.

## What must close before implementation starts

| Question | Trade |
| --- | --- |
| What mission state exists, and which of it is durable | `TBR-TAK-01` |
| What "failed" and "given up" mean for a service | `TBR-HA-01` |

`TBR-TAK-01` is the harder dependency. The status surface reports on mission
state, and until the state inventory exists and is classified, the data model
this component would aggregate is not defined. Building it now means defining
that model implicitly, in code, without the analysis, and then defending it.

## Why not build it anyway

It is tempting: a status page seems shallow, useful immediately, and unlikely
to constrain anything.

It is not shallow. It is the component that **defines the node's observable
data model**, and every other part of the system ends up conforming to whatever
it decided. An aggregator written before `TBR-TAK-01` closes will have invented
a state taxonomy, and that taxonomy will be the one the program uses, because
it works and rewriting it is expensive.

## What can be done now

Work that helps and does not prejudge the interface:

- **Close `TBR-TAK-01`.** It requires no hardware. It is the single most useful
  thing anyone can do for this component and for the program.
- **Capture fixtures.** Recorded output from real radio, power, thermal and
  time state, stored in `test/fixtures/` with the node, date and image build.
  Whoever eventually builds this needs them, and only someone with hardware can
  produce them.
- **Write the fakes**, once the interfaces are defined, per the hardware
  abstraction rule in `services/README.md`.
