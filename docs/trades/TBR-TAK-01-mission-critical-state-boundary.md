---
id: TBR-TAK-01
title: Mission-critical state boundary
status: OPEN
owner: TBD-SRR
area: TAK
priority: 9
function-owner: TAK + SRE
critical-path: true
depends-on: []
feeds: [TBR-HA-01, TBR-COMP-01, TBR-SEC-01, TBR-REC-01]
requires-hardware: no
evidence: docs/evidence/TBR-TAK-01/
adr: [FML-ADR-032, FML-ADR-034]
target-date: TBD-SRR
---

# TBR-TAK-01 Mission-critical state boundary

**Source:** SAD v0.31 section 14.1, and the TBR register in SAD section
30.2 (priority 9 of 16).

**Function owner:** TAK + SRE. **Named owner:** `TBD-SRR`.

SAD section 30.2 records an SRR exit action: the Program Owner assigns one named
individual and one calendar target date to every open TBR. `TBD-SRR` marks the
gap explicitly rather than hiding it behind a functional organization.

## Question

What TAK state is mission-critical and where is it stored?

## Why it matters

SAD section 14.1 marks this **CRITICAL** and makes it the design gate:

> No database-HA mechanism will be selected until the program identifies where
> OpenTAKServer or another chosen TAK implementation actually stores all
> mission-critical persistent state.

`TBR-HA-01` and `FML-ADR-034` both wait on it. Getting it wrong in the
permissive direction builds a distributed database nobody needed; getting it
wrong in the other loses an operator's work during an incident.

**It requires no hardware and can proceed in parallel**, which makes it the
highest-value work available to a contributor who owns no node.

## Options

The output is a classification, not a choice between products. Each state item is
placed into one of the three CONOPS section 26 classes:

- **Common Trust and Configuration** - consistent across all eligible service
  hosts;
- **Mission-Critical Persistent State** - must survive failover before a
  replacement service is fully authoritative;
- **Reconstructable or Ephemeral State** - rebuilt from reconnecting clients or
  new network activity.

The architectural consequence follows from where the mission-critical set
actually lives: SQL backend, DataSync content, files on disk, or certificate
enrollment state.

## Closure evidence

SAD section 14.1 requires the Stage 5 state study to classify at minimum:

- relational database state;
- DataSync and Mission API state;
- mission packages and uploaded files;
- client certificate enrollment, issuance and enrollment-authorization state;
- group and channel configuration;
- server configuration;
- RabbitMQ and transient messaging state;
- reconstructable PLI, presence and session state;
- local map, tile and cache state whose loss would be operationally visible
  after failover;
- immutable mission-package state.

SAD section 30.2 adds: a **different-node restore**, and PostgreSQL DataSync,
mission-package, certificate and map-cache tests.

Evidence is committed under `docs/evidence/TBR-TAK-01/`.

## Closure gate

The state inventory is complete, every item is classified into a CONOPS section
26 class with a stated justification, and the partition and rejoin behaviour of
the durable set is described including its conflict resolution rule.

The gate does **not** require the durable mechanism to be implemented, only for
the boundary to be decided and defensible.

SAD section 14.2 warns that **database support claimed by an ORM is not
sufficient acceptance evidence**: the actual MULE TAK workflows must be tested
against the selected backend.

**Closure gate per SAD section 30.2:** Before HA architecture lock / Stage 5.

No TBR closes on document wording alone. It closes only when its listed evidence
exists, the named owner accepts the evidence, and the resulting architecture
decision is entered into the persistent ADR register.

## Dependencies

- **Depends on:** none
- **Feeds:** `TBR-HA-01`, `TBR-COMP-01`, `TBR-SEC-01`, `TBR-REC-01`
- **Related decisions:** `FML-ADR-032`, `FML-ADR-034`
- **Validating stage:** Stage 5 (CONOPS section 78)
- **Requires hardware:** **No.** A design and analysis trade, resolvable
  against documentation, protocol
behaviour and reasoning about partition, running against fakes on an ordinary
laptop. A representative TAK build is the only prerequisite.
