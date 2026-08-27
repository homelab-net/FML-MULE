---
id: FML-ADR-029
title: Rootless Podman + Quadlet is default OCI execution model
status: SELECTED
date: 2026-08-25
supersedes: none
superseded-by: none
trades: [TBR-HA-01, TBR-COMP-01]
verification: Stage 1
---

# FML-ADR-029 Rootless Podman + Quadlet is default OCI execution model

**Source of rationale:** SAD v0.31 section 9.2. See also sections 9.3, 9.4,
10.2, 19.3 and 29.

Carries forward draft `AD-009`; see SAD section 0.8.

## Context

The Mission Service Plane hosts several independent services with different
upstreams, update cadences and dependency sets. Installing them into the host
userland couples them to each other and to the image. CONOPS section 81 excludes
Kubernetes-scale orchestration.

## Decision

The default application deployment pattern **shall** be Debian, systemd, Podman,
and rootless Quadlet-managed OCI containers.

Rootless containers **shall** be the default for ordinary browser applications,
file services, status services and other workloads that do not require
privileged hardware or host networking access.

Container images **shall** be referenced by immutable digest for field releases
(SAD section 19.3), never by tag.

## Status

`SELECTED`.

Two explicit exceptions exist:

- **Privileged service rule** (SAD section 9.3). Hardware-touching or
  host-networking functions run as narrowly scoped native systemd services or
  purpose-built privileged helpers, not as a general population of rootful
  containers. Mixed rootless and arbitrary rootful operation is not the normal
  deployment model.
- **Native service exception** (SAD section 9.4). A mission application may run
  natively under a dedicated Unix identity and systemd where that is the
  upstream-supported installation method, where no mature maintained image
  exists, where hardware access makes containerization harmful, or where it
  materially complicates recovery. **OpenTAKServer is currently a valid
  candidate.**

Restart and recovery policy is **not** decided here. `TBR-HA-01` is open, and a
naive restart policy on a constrained node turns one failed service into a dead
node.

## Consequences

- The service plane is part of the image build and the promotion gate rather
  than configured by hand on a device.
- systemd provides supervision, ordering and journal integration without a
  second supervisor.
- Rootless containers constrain what a compromised service reaches. That claim
  is **UNVERIFIED**.
- Rootless networking and privileged port binding need explicit handling, which
  is why ingress is a separate concern (`FML-ADR-031`, `services/ingress/`).
- Digest pinning makes an image update a reviewable change to a file rather than
  a silent pull, and means updates do not happen by themselves. That is the
  intent; see `FML-ADR-040`.
- If OpenTAKServer is deployed natively, SAD section 9.4 requires a
  version-controlled Ansible role, pinned versions, configuration templates,
  backup and restore procedures, an automated health check and a Stage 5
  recovery test. **The restore must be demonstrated onto a different eligible
  node**, so hostname, certificate, data-path and service-identity assumptions
  are exercised.

## Accepted cost

The program accepts container runtime overhead in memory and storage on a node
whose budget is unknown (`TBR-COMP-01`), and the operational awkwardness of
rootless networking. It accepts that every image update is manual work, which is
the price of the compatibility-set rule.

It accepts, in the native-service case, that the most important shared service
may be the least containerized one, and imposes the reproducibility requirements
above precisely because SAD section 9.4 warns it must not also become the least
reproducible.

## Fallback

Running the same services as host packages or rootful containers is possible, at
the cost of the isolation claim and the clean separation between image and
services. Would require a superseding ADR.

## Superseded by

None.

## Verification dependency

Stage 1, with Stage 5 for the native-service restore-to-different-node test. The
promotion gate in `os/release/README.md` requires a candidate to serve its
services and pass a traffic smoke test.
