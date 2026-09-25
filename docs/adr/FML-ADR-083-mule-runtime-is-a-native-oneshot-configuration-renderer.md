---
id: FML-ADR-083
title: MULE runtime is a native oneshot configuration renderer
status: SELECTED
date: 2026-09-25
supersedes: none
superseded-by: none
trades: [TBR-HA-01, TBR-COMP-01, TBR-LINUX-01]
verification: Stage 1
---

# FML-ADR-083 MULE runtime is a native oneshot configuration renderer

## Context

`mule/` contains the decisions a node makes at run time, but no image installs
the package and no process entry point invokes it. GAP-09D therefore prevents
the v0.0.1 image from applying the decision logic already exercised by the
software digital twin.

The node runtime is not a mission service. `FML-ADR-029` puts mission services
in rootless Podman Quadlets, while link and host configuration remain native
host responsibilities. A long-running supervisor would also require a restart
and recovery policy that `TBR-HA-01` has not selected.

The Program Owner approved the bounded oneshot recommendation on 2026-09-25.

## Decision

The MULE runtime shall be installed into the image as a Python distribution and
invoked as `python -m mule` by a native systemd `Type=oneshot` unit.

The entry point shall validate its inputs, render the bounded node
configuration it owns, and exit. It shall not become a second service
controller or a long-running supervisor.

The image release manifest shall bind the installed MULE distribution version
to the kernel, radio driver, firmware and userspace compatibility set governed
by `FML-ADR-040`. The unit shall carry no `Restart=` or `OnFailure=` policy
until `TBR-HA-01` selects one. Interface-bound unit naming remains deferred to
`TBR-LINUX-01`.

## Status

`SELECTED`.

This decides the entry-point, installation and unit shape requested by
GAP-09D. It does not claim the package is already installed in an image or that
the oneshot has run under the target init system.

## Consequences

- Contributors can exercise the same importable decision package through the
  node's declared entry point without adding a daemon.
- The image gains Python and the pinned package closure required to install the
  distribution; `TBR-COMP-01` shall measure that footprint.
- Configuration failure is a failed oneshot, not an indefinitely retrying
  process. Recovery remains an operator or later policy action.
- Host configuration stays outside rootless service containers, preserving the
  authority split in `FML-ADR-028` and `FML-ADR-029`.

## Accepted cost

The image carries a Python runtime and package installation solely to execute a
bounded native control path. A compiled or shell-only implementation could be
smaller, but would duplicate the Python decisions already exercised end to end.

The oneshot also cannot react continuously to a changed condition by itself.
Time-bound transitions therefore require a timer or another explicit invocation
of the same bounded entry point; this ADR does not create a resident watcher.

## Fallback

If image footprint or measured start-up behaviour makes the Python distribution
unacceptable, replace it with a Debian package carrying the same module and
entry point. A long-running supervisor requires a new ADR after `TBR-HA-01`
selects its failure and recovery semantics.

## Superseded by

None.

## Verification dependency

Stage 1 shall install the distribution into the development image, start the
native oneshot under systemd, observe a successful exit after rendering, and
exercise a malformed-input refusal. The result is `SIMULATED` or lab evidence
until repeated on the selected hardware.
