---
id: FML-ADR-029
title: Rootless Podman and Quadlet as the default application execution model
status: SELECTED
date: TBD
supersedes: none
superseded-by: none
trades: [TBR-HA-01, TBR-COMP-01]
verification: TBD
---

# FML-ADR-029 Rootless Podman and Quadlet as the default application execution model

This is a stub. The **system architecture description is the source of
rationale**; see `docs/architecture/README.md`.

## Context

The mission-service plane hosts several independent services with different
upstreams, different update cadences, and different dependency sets. Installing
them directly into the host userland couples them to each other and to the
image. Alternatives considered were host packages, a cluster orchestrator
(rejected in `docs/NON-GOALS.md`), and a rootful container runtime.

## Decision

Application services **shall** run as OCI containers under rootless Podman,
declared as Podman Quadlet units and supervised by systemd.

Container images **shall** be referenced by immutable digest, never by tag.

A service that genuinely cannot run rootless **may** run rootful, with the
reason recorded in its catalog entry under `services/catalog/`.

## Status

`SELECTED`.

Restart, recovery and dependency-ordering policy is **not** decided here. Safe
automatic service recovery is `TBR-HA-01`; a naive restart policy on a
resource-constrained node is a way to turn one failed service into a dead node.

## Consequences

- Services are declared as files in `services/quadlets/`, so the service plane
  is part of the image build and the promotion gate rather than being
  configured by hand on a device.
- systemd provides supervision, ordering and journal integration without a
  second supervisor.
- Rootless containers constrain what a compromised service reaches, which is
  the lateral-movement mitigation claimed in `THREAT_MODEL.md`. That claim is
  `UNVERIFIED`.
- Rootless networking and privileged port binding need explicit handling, and
  interact with the ingress arrangement in `services/ingress/`.
- Digest pinning means an image update is a reviewable change to a file, not a
  silent pull. It also means updates do not happen by themselves, which is the
  intent; see `FML-ADR-040`.
- Container storage and memory overhead land on a compute budget that is not
  yet set: `TBR-COMP-01`.

## Accepted cost

The program accepts container runtime overhead in memory and storage on a node
whose budget is unknown, and accepts the operational awkwardness of rootless
networking. It accepts that every image update is manual work, which is the
price of the compatibility-set rule.

## Fallback

Running the same services as host packages or as rootful containers is
possible, at the cost of the isolation claim and of the clean separation
between image and services. Would require a superseding ADR.

## Superseded by

None.

## Verification dependency

`TBD`. The promotion gate in `os/release/README.md` requires a candidate to
serve its services and pass a traffic smoke test. Isolation properties need a
stage that does not yet exist.
