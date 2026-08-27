---
id: TBR-ID-01
title: Browser-service identity provider
status: OPEN
owner: TBD-SRR
area: ID
priority: 14
function-owner: Security/Identity
critical-path: false
depends-on: [TBR-TIME-01]
feeds: []
requires-hardware: no
evidence: docs/evidence/TBR-ID-01/
adr: [FML-ADR-037, FML-ADR-036]
target-date: TBD-SRR
---

# TBR-ID-01 Browser-service identity provider

**Source:** SAD v0.31 section 16.5, and the TBR register in SAD section
30.2 (priority 14 of 16).

**Function owner:** Security/Identity. **Named owner:** `TBD-SRR`.

SAD section 30.2 records an SRR exit action: the Program Owner assigns one named
individual and one calendar target date to every open TBR. `TBD-SRR` marks the
gap explicitly rather than hiding it behind a functional organization.

## Question

Is a common browser-service IdP required beyond native app RBAC?

## Why it matters

`FML-ADR-037` prefers application-native RBAC and permits Open Policy Agent only
where cross-application policy justifies it. That rule does not answer whether
the browser-based field services need a **common identity provider** so that an
operator authenticates once rather than per application.

CONOPS section 66 requires that normal users not be required to perform
technical steps to reach their services. A separate login per browser service is
a usability cost paid every time the node reboots, in gloves, in darkness.

Against that, an IdP is another service on a constrained node, another failure
mode in the authentication path, and another thing that must work offline.

## Options

Axes: whether a common IdP is introduced at all; if so whether it is an existing
open-source project or an application-native shared session; how it works with
no WAN and no reachback; how role and scope from signed mission policy reach it;
and how it behaves when a node is in `TIME_DEGRADED`.

Doing nothing is a real option. Per-application native RBAC with credentials
provisioned by the mission configuration package may be sufficient for the
service catalog the program actually fields.

## Closure evidence

SAD section 30.2: role and scope workflow; offline login; administrative burden.

Specifically: a walkthrough of an operator reaching every service in the catalog
with and without a common IdP, recording the number of authentication events;
demonstrated offline login with no WAN; the provisioning burden on the
Communications and Identity Management function per user per mission; and the
behaviour when time is not credible.

Evidence is committed under `docs/evidence/TBR-ID-01/`.

## Closure gate

A decision is recorded, with the role and scope workflow documented end to end
and offline login demonstrated for the selected approach.

If a common IdP is selected it becomes a catalog entry with a measured resource
envelope under `TBR-COMP-01`; if not, the per-application provisioning burden is
stated so the identity function knows what it is signing up for.

**Closure gate per SAD section 30.2:** Before Security Architecture lock / Stages 1, 9.

No TBR closes on document wording alone. It closes only when its listed evidence
exists, the named owner accepts the evidence, and the resulting architecture
decision is entered into the persistent ADR register.

## Dependencies

- **Depends on:** `TBR-TIME-01`
- **Feeds:** none
- **Related decisions:** `FML-ADR-037`, `FML-ADR-036`
- **Validating stage:** Stage 9 (CONOPS section 78)
- **Requires hardware:** **No.** Workflow analysis and offline login can be
  exercised against fakes on an
ordinary laptop. Another good candidate for a contributor without hardware.
