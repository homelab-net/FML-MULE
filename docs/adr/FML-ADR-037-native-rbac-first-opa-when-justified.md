---
id: FML-ADR-037
title: Application-native RBAC first; OPA only when cross-application policy justifies it
status: SELECTED
date: 2026-08-25
supersedes: none
superseded-by: none
trades: [TBR-ID-01]
verification: Stage 9
---

# FML-ADR-037 Application-native RBAC first; OPA only when cross-application policy justifies it

**Source of rationale:** SAD v0.31 section 16.5. See also sections 16.4 and
CONOPS section 13.

Supersedes draft `AD-018`; see SAD section 0.8.

## Context

CONOPS section 13 requires separating network admission, user identity, role and
scope, application authorization, TAK authorization and infrastructure
administration. A policy engine is one way to enforce role and scope
consistently; it is also a way to insert a dependency into every request path
for architectural tidiness rather than need.

## Decision

Application-native RBAC **shall** be preferred when it correctly enforces MULE
role plus scope and can be provisioned and reviewed reproducibly.

Open Policy Agent **may** be used when multiple applications require the same
cross-application policy decision, when application-native RBAC cannot express
the required role and scope semantics consistently, or when policy-as-code
materially reduces drift.

OPA **shall not** be inserted into every request path merely for architectural
uniformity.

## Status

`SELECTED` as a rule. This is a selection rule, not a component selection.

Identity and authorization remain separate: a credential proves principal or
device identity, and role and organizational scope are carried in signed mission
policy data or equivalent controlled claims (SAD section 16.4).

The architecture **should** avoid embedding mutable organizational policy
permanently into long-lived device certificates.

## Consequences

- Fewer moving parts on a constrained node by default.
- Role and scope definitions live in the mission configuration package (CONOPS
  section 19), so they are provisioned rather than configured per application.
- Where several browser services need the same decision, the rule permits OPA
  rather than duplicating policy. Whether a common identity provider is needed
  at all is `TBR-ID-01`.
- Reviewability is a stated criterion: native RBAC qualifies only if it can be
  provisioned and reviewed reproducibly, which excludes per-application GUI
  state (governing principle 12).

## Accepted cost

The program accepts potential inconsistency between applications' native RBAC
models, and the review burden of checking each one, in exchange for not making
every request depend on a policy service on a power-constrained node.

## Fallback

Adopt OPA broadly if the inconsistency proves unmanageable. The rule already
permits this on stated grounds, so exercising it is not a supersession.

## Superseded by

None.

## Verification dependency

Stage 9, with Stage 1 for the role and scope workflow. `TBR-ID-01` closure
evidence covers the role and scope workflow, offline login and administrative
burden.
