---
id: FML-ADR-046
title: MULE Status Aggregator is approved thin original software
status: SELECTED
date: 2026-08-25
supersedes: none
superseded-by: none
trades: [TBR-TAK-01, TBR-HA-01, TBR-TIME-01, TBR-COMP-01]
verification: Stage 1
---

# FML-ADR-046 MULE Status Aggregator is approved thin original software

**Source of rationale:** SAD v0.31 section 22. See also sections 12, 21.2, 29.5
and CONOPS sections 31, 52 and 67.

New in SAD v0.3.

## Context

CONOPS section 67 lists thirteen questions the simplified status view must
answer, from "is the node operational" through "is shared data authoritative" to
"is EMCON active". No upstream project provides that state model across RF, TAK
authority, trust, power, time, storage and peer health.

## Decision

A local **MULE Status Aggregator** is approved original software. It **shall**
combine host, RF, network, mission-service, trust, time, storage and power state
into the simplified operator view the CONOPS requires.

It **shall not** require users to interpret BATMAN tables, Linux namespaces or
container status.

It **shall** distinguish `GREEN`, `DEGRADED`, `LOW-BANDWIDTH`,
`NON-AUTHORITATIVE`, `EMCON` and `FAULT`, and where shared data is not
authoritative **shall** provide a reason code from `PARTITION`, `STATE_LAG`,
`HOST_RECOVERY`, `NO_SAFE_AUTHORITY`, `UNSYNCHRONIZED` or `UNKNOWN`.

Where available it **shall** also report time since last authoritative
synchronization, the current shared-service host, and whether this node is
carrying elevated service-host power burden.

## Status

`SELECTED`, with owner Platform / Field UX / SRE in the MULE-original software
inventory (SAD section 29.5).

**Scope limit, from that inventory:** read-mostly normalization and a local
service-host registry. It **does not elect TAK authority** and **does not provide
broad configuration authority**.

`FML-ADR-049` folds the Service Authority Registry into this component rather
than creating a sixth standalone daemon.

## Consequences

- CONOPS section 31 requires the interface to indicate elevated service-host
  responsibility and reduced projected runtime. That is a stated obligation on
  this component.
- `FML-ADR-042` requires a node to report that its time is not credible, so that
  a refusal to validate is diagnosable rather than mysterious. This is where
  that surfaces.
- The **diagnostic tier** exposes deeper engineering data without granting
  configuration privilege (CONOPS section 52).
- It consumes native interfaces — `batctl`, `iw`/nl80211, Morse Micro driver
  interfaces, nftables counters, hostapd control, systemd state — normalized so
  upstream implementation changes do not leak into the operator UI (SAD section
  21.2).
- It is read-mostly by design, so its compromise does not grant configuration
  authority.
- It adds to the memory and CPU budget that `TBR-COMP-01` must size.

## Accepted cost

The program accepts writing and sustaining original software, and accepts that
this component **defines the node's observable data model**, which other parts
will conform to. The scope limit and the dependency on `TBR-TAK-01` for the
state taxonomy exist to stop that model being invented in code before the
analysis is done.

## Fallback

A collection of upstream dashboards and raw tool output, which would fail CONOPS
sections 66 and 67: normal users are not required to interpret routing tables or
container state.

## Superseded by

None.

## Verification dependency

Stages 1 and 5. The thirteen CONOPS section 67 questions are the acceptance
criteria. `TBR-TAK-01` must close before the authority-state half is
implemented.
