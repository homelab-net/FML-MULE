---
id: FML-ADR-028
title: Mission services share the Debian host but cannot directly own network/RF configuration
status: SELECTED
date: 2026-08-25
supersedes: none
superseded-by: none
trades: [TBR-COMP-01]
verification: Stage 1
---

# FML-ADR-028 Mission services share the Debian host but cannot directly own network/RF configuration

**Source of rationale:** SAD v0.31 section 9.1. See also sections 9.3, 10.3 and
27.

Supersedes draft `AD-008`; see SAD section 0.8.

## Context

`FML-ADR-021` puts the Network Plane and the Mission Service Plane on one host.
Without an explicit rule, an application that needs a network change would
acquire the privilege to make one, and the isolation the single-host
architecture depends on would erode a convenience at a time.

## Decision

The Mission Service Plane **shall** run on the same Debian host as the Network
Plane but **shall** be logically constrained from modifying network or RF state
except through explicit privileged interfaces.

Ordinary application services **shall** run with least privilege.

A rootless application **shall not** be granted `CAP_NET_ADMIN` merely for
convenience (SAD section 10.3).

## Status

`SELECTED`.

The host root and network control context owns physical Ethernet, the HaLow
interface, high-rate Wi-Fi interfaces, the EUD AP interface, 802.11s,
batman-adv, routing, nftables, DHCP/DNS and the WAN overlay interface.
Mission-service containers receive only the network access necessary to provide
their service.

## Consequences

- Any service that genuinely needs to touch hardware or host networking becomes
  a narrowly scoped native systemd service or a purpose-built privileged helper
  (`FML-ADR-029`, SAD section 9.3), not a rootful container.
- The rule is enforceable and reviewable: the question "does this service hold
  `CAP_NET_ADMIN`" has a definite answer.
- Coexistence controls, DHCP/DNS, nftables and hardware monitoring sit on the
  privileged side of the line.
- The isolation remains **one-directional**. This decision constrains
  applications from reaching network state; it does not contain the privileged
  network context. See `FML-ADR-030` and SAD sections 10.1 and 27.

## Accepted cost

The program accepts additional friction whenever a mission service legitimately
needs network information: it must be exposed deliberately through a privileged
helper or a read-only interface rather than taken directly. The Status
Aggregator (`FML-ADR-046`) exists partly to satisfy that need without granting
configuration authority.

## Fallback

None. Relaxing this rule removes the only structural constraint that separates
the planes on a shared kernel, and would make `FML-ADR-021`'s accepted cost
unbounded.

## Verification dependency

Stage 1, with Stage 7 for load. SAD section 10.4 requires demonstrating that
representative service load does not destabilize the Network Plane.

## Superseded by

None.
