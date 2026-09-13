# GAP-09A execution card

## Finding and authority

- **Finding:** GAP-09A, development compute article (P1).
- **Governing records:** `ROADMAP.md`, the GAP-09 section of
  `REMEDIATION-AND-CLOSURE-PLAN-2026-09-08.md`, `FML-ADR-021`,
  `FML-ADR-022`, `FML-ADR-040`, `TBR-HW-01`, and `TBR-LINUX-01`.
- **Owner approval:** the Program Owner approved the existing Intel N150 lab
  device as the development article in the Codex thread on 2026-09-12.
- **Boundary:** the approval is not a production compute selection, hardware
  qualification, compatibility-set promotion, or permission to close a
  hardware trade.

## Exact scope

Record one existing x86-64 Intel N150 system running Debian 13.6 as the
development article for the `v0.0.1` one-node, one-service milestone. Preserve
the distinction between using available hardware and qualifying a production
block. Compare the article with the current CM4 planning direction and the
supported targets retained from OpenMANET prior art without adopting either.

No device configuration, package installation, image write, service restart,
or network change is in this child task.

## Versioned verification contract

GAP-09A is complete when all of the following hold:

1. The retained record states the selected article's architecture, processor,
   installed Debian release, memory, and storage from read-only operating-system
   inventory.
2. The record identifies the commands used, while retaining no credential,
   network identifier, serial number, deployment location, or captured traffic.
3. The comparison covers the existing article, the CM4 planning direction, and
   the OpenMANET-supported-target reference.
4. Every statement distinguishes development use from production selection and
   qualification.
5. An independent reviewer reproduces the repository checks and confirms the
   selection matches the Program Owner's approval.

This evidence-only change adds no behavior. A failing-first behavior test is not
applicable; the findings validator shall reject closure without a valid closure
packet and independent reviewer attribution.

## Red-team plan

- Search the evidence for claims that the article is a target, production
  baseline, qualified block, or compatibility-set promotion.
- Search for hostnames, addresses, interface identifiers, serial numbers, or
  credentials copied from the lab inventory.
- Compare the selected article and approval scope with the GAP-09A user gate.
- Run the complete repository gate and inspect its exit code.

## Rollback and completion

Revert the documentation commit to remove the designation. The article itself
is unchanged. Closure requires the independent review and a valid closure
packet; it does not authorize later GAP-09 child decisions.
