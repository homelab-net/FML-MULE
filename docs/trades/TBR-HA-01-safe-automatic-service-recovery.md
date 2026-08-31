---
id: TBR-HA-01
title: Safe automatic service recovery
status: OPEN
owner: Cameron Zobrist
area: HA
priority: 12
function-owner: SRE + TAK
critical-path: false
depends-on: [TBR-TAK-01, TBR-TIME-01]
feeds: []
requires-hardware: partly
evidence: docs/evidence/TBR-HA-01/
adr: [FML-ADR-035, FML-ADR-049, FML-ADR-029]
target-date: TBD-SRR
---

# TBR-HA-01 Safe automatic service recovery

**Source:** SAD v0.31 section 14.4, and the TBR register in SAD section
30.2 (priority 12 of 16).

**Function owner:** SRE + TAK. **Named owner:** `TBD-SRR`.

SAD section 30.2 records an SRR exit action: the Program Owner assigns one named
individual and one calendar target date to every open TBR. The named individual
is assigned as of 2026-08-31. **The target date is not**, and `TBD-SRR` still
marks that half of the action rather than hiding it behind an invented date.

## Question

What is the simplest safe automatic TAK recovery mechanism?

## Why it matters

SAD section 14.4 states that **no specific Patroni, etcd, Raft, witness, lease,
quorum or fencing implementation is selected in v0.31**, and that the TAK
automatic-recovery mechanism therefore receives no ADR until it is chosen.

CONOPS section 29 requires preferring loss of shared-service authority over
divergent authoritative databases. CONOPS section 30 requires that the system
not force automatic promotion merely to maximize apparent availability.

This trade also governs restart policy for the service controller
(`FML-ADR-035`). The failure mode is specific: a service fails on memory
exhaustion, restarts, exhausts memory again, and the restart loop competes with
the routing daemon until mesh links flap.

## Options

SAD section 14.4 fixes the selection criterion rather than the options: after
`TBR-TAK-01` closes, and with `TBR-TIME-01` supplying the clock and holdover
bounds, select the **simplest** mechanism that can:

1. prove which host may act as authoritative;
2. avoid uncontrolled split-brain;
3. determine whether required mission-critical state is sufficiently current;
4. promote automatically when safe authority is established;
5. refuse automatic promotion when safe authority cannot be established;
6. support explicit administrative recovery when automatic promotion is unsafe.

**Administrative promotion is the mandatory fallback, not the preferred normal
case.**

## Closure evidence

SAD section 30.2: primary loss; partition; stale standby; rejoin; no-authority;
administrative recovery.

Plus fault injection for each service failure class - crash, memory exhaustion,
storage exhaustion, dependency unavailable, and a service that starts but does
not become healthy - with recorded network plane behaviour during each,
specifically whether mesh links survive, and evidence that the restart policy
terminates rather than looping.

The state the node reports to an operator after giving up, mapped to the
`FML-ADR-046` reason codes including `NO_SAFE_AUTHORITY`.

Evidence is committed under `docs/evidence/TBR-HA-01/`.

## Closure gate

For every injected failure class the node either recovers the service or stops
trying and reports that it has, and in **all** cases the network plane retains
its mesh links.

Split-brain is prevented or safely contained under partition, and the mechanism
refuses automatic promotion when safe authority cannot be established.

The CONOPS section 27 objective of restoring synchronized shared TAK service
within 60 seconds under healthy IP-mesh conditions is assessed. SAD section 14.6
permits raising a CONOPS change request against that objective rather than
introducing an unjustified HA stack to preserve the number.

**Closure gate per SAD section 30.2:** Before CDR-lite / Stage 5.

No TBR closes on document wording alone. It closes only when its listed evidence
exists, the named owner accepts the evidence, and the resulting architecture
decision is entered into the persistent ADR register.

## Dependencies

- **Depends on:** `TBR-TAK-01`, `TBR-TIME-01`
- **Feeds:** none
- **Related decisions:** `FML-ADR-035`, `FML-ADR-049`, `FML-ADR-029`
- **Validating stage:** Stage 5 (CONOPS section 78)
- **Requires hardware:** Service fault injection runs on an ordinary machine
  against fakes. The network
plane interaction and the partition tests need radios.
