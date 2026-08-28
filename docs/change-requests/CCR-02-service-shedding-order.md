# CCR-02 Service shedding order under constrained conditions

**Type:** CONOPS change request
**Status:** `OPEN`
**Section affected:** CONOPS v1.01 section 9, Service criticality model
**Raised by:** `FML-ADR-052` assessment of `services/service-controller/`
**Blocks:** any component that sheds services, so `FML-ADR-035` and `TBR-HA-01`
**Does not block:** `mule/`, the SAD, the TRD or prototype work

## Statement

CONOPS section 9 defines four service classes and binds the behaviour of two of
them under constrained conditions. The other two are unstated, so the shedding
order the section implies cannot be read off it.

| Class | What section 9 says about shedding |
| --- | --- |
| S0 Core node services | `[SHALL]` remain active whenever the node is operational |
| S1 Local mission services | "should remain locally available where practical" |
| S2 Shared mission services | **Nothing.** Section 9.3 states only where S2 may run |
| S3 Enhanced services | `[SHALL]` the first class stopped under constrained conditions |

"First" in section 9.4 implies a second and a third. The document never names
them.

This is not a theoretical gap. S2 is TAK Server, browser-based group chat and
shared mission files: the services a team is most likely to be using when a node
becomes constrained, and the ones whose loss an operator would most need warning
about.

## Proposed text

Editorial. It adds one `[SHALL]` where section 9.4 already implies an ordering,
so whether this is a point revision or a minor increment is a judgement for the
signatories. Recorded here as a **minor version increment, `v1.1`**, on the
conservative reading, since a new `[SHALL]` decomposes into a TRD requirement
and appears in the verification matrix.

Insert as a new section 9.5:

> [SHALL] Under constrained battery, thermal, bandwidth or compute conditions,
> service classes shall be stopped in the order S3, then S2, then S1. S0 shall
> never be stopped automatically while the node is operational.
>
> [SHALL] The node shall report which classes it has stopped, and why, without
> the operator asking.
>
> Stopping a class does not imply stopping every service in it. Section 10
> governs which individual services within a class activate and deactivate.

## Rationale for the order

Program Owner direction, 2026-08-28: **S2 sheds after S3 and before S1.**

It follows the local-first principle the CONOPS argues throughout. Section 5.4
requires that no field capability depend on a central TAK Server, and section
9.2 keeps S1 locally available "even when all external service hosts are
absent". A node that shed its local mission services while continuing to host
shared ones would be preserving the coordinated capability at the expense of the
capability that works alone, which inverts section 5.4.

Section 9.3 supports it from the other side: S2 "may run on a selected MULE, a
portable field-services host, NOMAD, or another approved host". S2 has somewhere
else to go, and S1 by definition does not.

## What this change request does not decide

**What "constrained" means.** Section 9.4 names four dimensions and quantifies
none. Battery, thermal and bandwidth can be bound to judgements the node already
makes: `mule/power.py`, `mule/thermal.py` and the capability ladder in
`mule/modes.py`. Compute cannot, and `TBR-COMP-01` governs it.

**When a shed class returns.** Section 5.8 requires damping, persistence,
minimum-residency or threshold logic sufficient to prevent oscillation, and
section 10 requires grace periods so that brief disconnects do not repeatedly
start and stop services. Both are the service controller's, and `TBR-HA-01`
decides the policy. This change request states an order, not a schedule.

**Whether an operator may override.** Section 7 governs roles, and nothing here
changes what any role may do.

## Downstream documents affected

| Document | Effect |
| --- | --- |
| `services/service-controller/README.md` | Gains the order it must implement |
| `docs/verification/requirements.md` | Two binding clauses to decompose |
| `docs/trades/TBR-HA-01-*.md` | Closure evidence covers shedding order, not only restart |
| SAD section 15 | Service controller behaviour |

## Verification impact against section 85

Both clauses are exercisable against fakes without hardware, and are `SIMULATED`
there. Neither is verifiable on a real node until `TBR-HA-01` closes and a
service controller exists, which is stage 5 and stage 7 under section 78.

The second clause, reporting what was stopped and why, is the one most likely to
be quietly dropped: it is a user-facing obligation attached to a resource
decision, and it is the half an implementer under time pressure omits.

## Approval

Not approved. No signature has been sought.

As with `CCR-01`, section 87 records the baseline as pending stakeholder
signature, so this can fold into that signature rather than being processed as a
post-signature change.
