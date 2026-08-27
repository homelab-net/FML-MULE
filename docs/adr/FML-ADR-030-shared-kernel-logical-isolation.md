---
id: FML-ADR-030
title: Shared-kernel logical isolation using users/namespaces/cgroups/nftables
status: SELECTED
date: 2026-08-25
supersedes: none
superseded-by: none
trades: [TBR-COMP-01]
verification: Stage 1
---

# FML-ADR-030 Shared-kernel logical isolation using users/namespaces/cgroups/nftables

**Source of rationale:** SAD v0.31 section 10. See also sections 2.3, 26, 27 and
32.1.

Supersedes draft `AD-010`; see SAD section 0.8.

## Context

`FML-ADR-021` consolidates the planes onto one kernel. SAD section 10.1 states
plainly that this is a weaker boundary than two physically separate computers.

## Decision

Network, service, management and security functions **shall** be separated
logically on one Linux host using distinct Unix users and groups, rootless OCI
containers, Linux network namespaces where useful, veth/bridge boundaries,
nftables policy between the EUD, service, management, WAN and external-RF
domains, minimized per-process capabilities, cgroups and systemd resource
limits, read-only mounts where practical, and separate secrets and configuration
permissions.

SELinux or AppArmor **may** be added if the selected Debian baseline supports it
cleanly and the operational burden is acceptable.

The accepted v1 objective is to prevent routine application compromise, crash or
resource exhaustion from automatically granting the ability to reconfigure
radios, routing, firewall policy or privileged mission trust.

## Status

`SELECTED`.

**The isolation claim is explicitly one-directional.** SAD section 10.1:

> ordinary application/service contexts are constrained from changing Network/RF
> state; the privileged host Network/RF context is not itself contained by those
> application namespaces.

The shared host does not provide the bidirectional enforcement-domain separation
that two physical computers would. SAD sections 10.1 and 27 state that this
limitation is part of the security review and is not hidden by container
terminology.

## Consequences

- Critical network functions receive reserved CPU and memory priority sufficient
  to remain responsive during application load (SAD section 10.4). The
  reservation mechanism is `TBR-COMP-01`.
- S2 and S3 services are resource-limited and may be stopped under battery,
  thermal, memory, CPU or mission-profile constraint.
- The same logical interface model can be implemented on a second compute
  element without changing EUD-facing services or field procedures (SAD section
  10.5), which is what makes the `FML-ADR-021` fallback affordable.
- A security finding that this boundary is insufficient is one of the six
  fallback triggers in SAD section 2.3.

## Accepted cost

The program accepts a weaker isolation boundary than physical separation would
give, for an unclassified volunteer and training threat model, in exchange for
the power, mass, cost and sustainment benefits of one board.

It accepts that a kernel-level compromise reaches everything on the node.

## Fallback

Physical separation onto a second compute element (SAD sections 2.3 and 10.5).
This is an implementation fallback, not a separate operational architecture.

## Superseded by

None.

## Verification dependency

Stages 1 and 7 for resource behaviour. For the isolation boundary itself, SAD
section 32.1 item 3 names an **independent shared-kernel security reviewer** as
a required SRR/PDR action, and states that a negative finding is an explicit
trigger for the dual-compute fallback. That review has not been performed.
