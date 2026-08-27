# PBCR-01 Field Service Plane allocation

**Type:** Parent-baseline change request
**Status:** `OPEN`
**Raised by:** SAD v0.31 section 0.6
**Blocks:** parent-system integration baseline closure
**Does not block:** MULE SAD, TRD, ICD or prototype work

## Statement

From SAD v0.31 section 0.6:

> **PBCR-01:** Before MULE integration into the parent Homelab baseline, TAK and
> communications-gateway allocations must be updated from NOMAD-only to the
> controlled Field Service Plane described by the MULE subsystem.

## The conflict

The current inspectable parent TRD and ICD allocate **TAK Server and
communications gateway functions specifically to NOMAD**.

CONOPS v1.01 section 2 intentionally generalizes that. Under the MULE concept,
approved field services may operate on:

- NOMAD;
- a portable field-services host;
- an eligible MULE;
- another approved compatible platform.

This is a deliberate change, not an oversight. SAD section 0.5 item 4 requires
that where the MULE CONOPS intentionally changes an older parent allocation, the
difference is **recorded as a parent-baseline change action rather than silently
reconciled**.

SAD section 32 records this as the **only known conflict** with the existing
inspectable parent architecture.

## Why the change is necessary

The CONOPS requires that shared TAK service recover onto another eligible host
without ordinary EUD reconfiguration (section 27), and that required field
capability not depend on NOMAD (section 5.4).

A NOMAD-only allocation makes both impossible: if NOMAD is the only permitted
TAK host, its loss ends shared service, and no other node may take over.

CONOPS section 5.4 lists NOMAD explicitly among the things required field
capability **shall not** depend on.

## Scope of the parent change

Per CONOPS section 86, acceptance of the CONOPS requires a controlled Homelab
integration change package addressing the affected parent records. For this
change that is expected to include:

| Parent artifact | Change |
| --- | --- |
| TRD | TAK Server allocation generalized from NOMAD to the Field Service Plane |
| ICD | Communications-gateway interface allocation likewise generalized |
| SOW | Scope reflecting eligible-host hosting |
| Verification Matrix | Verification of TAK continuity across eligible hosts, not only on NOMAD |
| ATP | Acceptance covering an eligible MULE as a service host |
| ADR | Parent decision record for the reallocation |
| BOM / CI records | Field Service Plane hosts recorded as configuration items |

The MULE subsystem does not own these artifacts and does not modify them from
this repository. This file records the required change and its rationale so the
parent program can action it.

## Constraints the change must preserve

The generalization does not weaken the boundaries the parent architecture
establishes. CONOPS section 2 lists the parent principles the subsystem
preserves, and the following remain binding regardless of which host runs a
service:

- network reachability does not itself grant service or data authorization;
- field users do not gain unrestricted access to home, private or administrative
  systems merely because reachability exists (CONOPS section 68);
- EUDs do not join the WAN overlay (`FML-ADR-039`);
- local operation continues when parent infrastructure is unavailable.

## Verification

Stage 12, NOMAD integration, per CONOPS section 78:

- same standard field nodes;
- NOMAD-hosted services;
- parent Homelab authorization boundaries;
- **no field-node hardware changes required for integration**.

Stage 5 additionally exercises TAK service continuity across eligible hosts,
which is the capability this change request exists to permit.

## Status

`OPEN`. No parent-baseline change package has been raised.

SAD section 31 carries "Parent NOMAD-only allocations" as an **OPEN** risk, and
SAD section 33.1 lists writing PBCR-01 among the three low-cost artifacts that
should proceed immediately. This file is that artifact.
