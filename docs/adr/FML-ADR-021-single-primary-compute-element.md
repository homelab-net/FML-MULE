---
id: FML-ADR-021
title: Single primary compute element, single Debian-family host
status: SELECTED
date: TBD
supersedes: none
superseded-by: none
trades: [TBR-COMP-01, TBR-HW-01, TBR-CARRIER-01, TBR-PWR-01]
verification: TBD
---

# FML-ADR-021 Single primary compute element, single Debian-family host

This is a stub. The **system architecture description is the source of
rationale**; it is not yet transcribed into this repository. See
`docs/architecture/README.md`. The decision, status and consequences below are
recorded accurately; the reasoning is summarised, not reproduced.

## Context

A multi-bearer appliance can be built as several small compute elements, one
per function, or as a single general-purpose host running everything. The
alternative considered was a distributed arrangement with a dedicated
controller per radio subsystem.

Constraints acting on the choice: the device is assembled and repaired by
volunteers, spares are scarce, power is a fixed budget, and the mission-service
plane needs enough memory and storage that a microcontroller-class element
cannot host it.

## Decision

The MULE **shall** host both the network plane and the mission-service plane on
a single primary compute element running a single Debian-family operating
system instance.

Auxiliary microcontrollers dedicated to a specific radio or sensor function are
permitted where a module requires one, and are not primary compute elements
under this decision.

## Status

`SELECTED`.

The compute element itself is **not selected**. Module class, memory, and
storage are `TBD` pending `TBR-COMP-01`, and the hardware block that carries it
is `TBD` pending `TBR-HW-01`. This ADR decides the topology, not the part.

## Consequences

- One operating system to build, patch, promote and roll back, rather than
  several. The promotion gate in `os/release/` applies to one artifact.
- One failure domain. Loss of the compute element is loss of every plane at
  once, including the degraded-communications plane's host-side handling.
- Resource contention between the network plane and the mission-service plane
  becomes a real design problem rather than being separated by hardware. This
  feeds `TBR-COMP-01`.
- A single thermal and power load, concentrated. Feeds `TBR-THERM-01` and
  `TBR-PWR-01`.
- Contributors can work against an ordinary Debian-family machine, which is
  what makes the hardware-abstraction rule in `AGENTS.md` workable.

## Accepted cost

The program accepts a single point of failure in the compute element, and
accepts that a fault in the mission-service plane can starve the network plane
of resources on the same host. Isolation between the planes is a software
problem from this point on, addressed partly by `FML-ADR-029`, and it is a
weaker guarantee than physical separation would have given.

## Fallback

None that is cheap. Moving to a distributed arrangement after the enclosure,
power distribution and thermal design are settled is effectively a new hardware
block and a new qualification cycle. This decision is close to structural.

## Superseded by

None.

## Verification dependency

`TBD`. Requires a selected compute element (`TBR-COMP-01`, `TBR-HW-01`) before
a stage can be defined. Expected to be validated by a loaded-node stage under
`test/stages/`, exercising both planes concurrently.
