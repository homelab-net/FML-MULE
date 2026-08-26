---
id: FML-ADR-023
title: Consume the upstream MANET reference project as configuration knowledge, not as mandatory production firmware
status: SELECTED
date: TBD
supersedes: none
superseded-by: none
trades: [TBR-LINUX-01, TBR-RF-01]
verification: TBD
---

# FML-ADR-023 Consume the upstream MANET reference project as configuration knowledge, not as mandatory production firmware

This is a stub. The **system architecture description is the source of
rationale**; see `docs/architecture/README.md`.

## Context

There is prior art in the form of an upstream open reference project covering
sub-GHz mesh networking on Linux. It encodes real, hard-won configuration
knowledge: driver invocation, mesh parameters, interface bring-up ordering, and
known-bad combinations.

The choice was whether to adopt that project's firmware images as the
production baseline, or to treat it as a source of knowledge to be
reimplemented inside this program's own build and promotion pipeline.

## Decision

The program **shall** consume the upstream MANET reference project as
configuration knowledge and as a source of validated parameters. Its images
**shall not** be a mandatory production artifact for MULE.

Where its configuration is adopted, the source **shall** be cited in the
adopting file so a reader can trace a parameter back to where it was
demonstrated.

## Status

`SELECTED`.

## Consequences

- The program keeps control of its own promotion gate, signing, and A/B update
  scheme, which an externally produced image would not have satisfied. See
  `FML-ADR-040` and `FML-ADR-041`.
- The program must reproduce configuration work that already exists elsewhere,
  and must keep watching upstream for changes it should absorb.
- Divergence from upstream is expected and is not, by itself, a defect. Where
  the program carries an actual patch against upstream code rather than
  re-expressing configuration, that is a fork and is registered under
  `docs/forks/` with a named owner.
- Upstream-first still applies: a fix that belongs upstream is offered upstream
  before it is carried here.

## Accepted cost

The program accepts duplicated effort and the risk of drifting away from a
reference that is being actively maintained by people with more sub-GHz mesh
experience than this program has. It also accepts that when something does not
work, the program cannot ask upstream about an image it does not run.

## Fallback

Adopting upstream images as the production baseline remains possible, at the
cost of the promotion and rollback properties this program has decided it
needs. That would supersede this ADR.

## Superseded by

None.

## Verification dependency

`TBD`. Comparative bring-up against the upstream reference configuration is the
natural evidence, and belongs to the mesh-formation stage under `test/stages/`.
