---
id: FML-ADR-086
title: The WAN overlay ACL is deny-by-default grants scoped to the assigned MULE
status: SELECTED
date: 2026-09-29
supersedes: none
superseded-by: none
trades: []
verification: Stage 6
---

# FML-ADR-086 The WAN overlay ACL is deny-by-default grants scoped to the assigned MULE

## Context

`FML-ADR-082` (`SELECTED`, with `CCR-04`) decided the overlay *posture*: MULEs
participate in the WAN overlay; an admitted remote EUD under `ASSIGNED_MULE_ONLY`
reaches only its assigned MULE's approved remote-EUD ingress; the MULE stays the
boundary; the EUD is never on the RF mesh. `FML-ADR-082` deliberately left the *ACL
text* undecided: "The tag's contents are decided. The ACL text is not." It named, but
did not resolve, "the grant syntax that enforces 'assigned ingress only'".

A first attempt to write that ACL as configuration (the initial
`os/config/tailscale-acl.hujson.template`) exposed why the syntax is not incidental.
Tailscale tags are a *class*: a single `tag:mule` shared by every MULE means a grant
whose destination is `tag:mule` reaches **every** MULE. A remote-EUD ingress grant
written that way would let an EUD reach the ingress of MULEs that are not its assigned
one, and would keep reaching another MULE when the assigned one is unavailable --
exactly the two negatives `FML-ADR-082` requires (`assigned-ingress-only`,
`assigned-mule-lost-no-reattach`). Deny-by-default alone does not fix this, because the
grant that must exist for the assigned MULE is itself the over-broad one.

So the mechanism has to be decided before the ACL can be rendered safely, and that is
this ADR. What is *not* settled at proposal time: the approved remote-EUD ingress
service and port (the field-service plane has not defined it; `TBR-TAK-01` is `CLOSED`
on state storage and does not own it), and whether a field node exposes an
administrative path at all (`THREAT_MODEL.md` records an admin path as a capture-time
asset; the interface is `TBR-LINUX-01`). Those are named and deferred below rather than
invented here.

## Decision

The WAN overlay access policy **shall** be expressed as Tailscale grants and **shall**
be deny-by-default: a destination is reachable only when a grant lists it, and there is
no default-allow grant.

A remote-EUD ingress grant **shall** target the **assigned MULE's own overlay
identity**, not the shared `tag:mule` class. Each MULE **shall** carry a per-MULE
overlay identity (a per-MULE tag or the MULE's stable overlay node identity) so that an
`ASSIGNED_MULE_ONLY` grant names one MULE and no other. `tag:mule` **shall** denote
MULE infrastructure for inter-MULE participation only and **shall not** be the
destination of a remote-EUD ingress grant.

The admitted EUD's mission-and-team tag (`FML-ADR-082`) **shall not** appear in
`autoApprovers` for subnet routes or exit nodes. Because an empty `autoApprovers`
section prevents only *automatic* approval -- Tailscale defines it as approving actions
"without further approval from the admin console"
(<https://tailscale.com/docs/reference/syntax/policy-file#autoapprovers>), and omitting
it leaves the default of no auto-approval -- the prohibition on an admitted EUD being a
subnet router or exit node (`FML-ADR-082`) **shall** also be an operational rule: an
administrator **shall not** manually approve an EUD-tagged node as either.

This ADR decides the grant *mechanism* only. It does **not** decide, and its
implementations **shall not** invent: the approved remote-EUD ingress service, port, or
transport (owned by the field-service-plane definition; see `PBCR-01` and roadmap item
`4.6`), nor whether or how administrative access reaches a MULE over the overlay (the
`THREAT_MODEL.md` open question; interface `TBR-LINUX-01`). Until each is decided by its
owner, the corresponding grant **shall** be left as a named `TBD`, not rendered.

## Status

`SELECTED`. Accepted by the Program Owner (Cameron Zobrist) on 2026-09-29. It fixes the
grant mechanism (deny-by-default, per-assigned-MULE scoping, the autoApprovers rule) and
deliberately leaves the ingress service and the admin path to their owning trades and
later implementation ADRs -- those are downstream values and interfaces, not this ADR's
mechanism, so naming them later does not supersede this record. It refines `FML-ADR-082`
and supersedes nothing.

## Consequences

- The overlay ACL template can be rendered without the all-MULEs hole: the ingress
  grant is per-assigned-MULE by construction, and the two-MULE negatives become testable
  once a second MULE exists.
- It creates work: a per-MULE overlay identity has to be issued and tracked per MULE,
  and mission rendering has to bind an admitted EUD to its assigned MULE's identity, not
  just to a mission-and-team tag.
- A contributor without hardware can still exercise the firewall-boundary half on netns
  (`test/bench/wan-overlay-posture.sh`); the identity half needs a real tailnet, and the
  "not through another MULE" negative needs two MULEs.
- Threat model: keeping the admin path and the ingress service *out* of this decision
  means the ACL cannot silently acquire an SSH or management grant; each such grant must
  arrive with its own owning decision. That is the intended constraint, not an omission.
- It forecloses the convenient single-tag ACL, which is simpler to write and wrong.

## Accepted cost

Per-MULE overlay identity is more to manage than one shared `tag:mule`, and it pushes
complexity into mission rendering and into whatever issues the per-MULE identity. The
program accepts that cost because the alternative -- a shared-tag grant -- cannot express
"only the assigned MULE" and so cannot satisfy `FML-ADR-082`. The residual cost not yet
quantified is the operational overhead of per-MULE identity issuance at scale; the
field-service-plane and enrollment work (`PBCR-01`, roadmap `4.6`) will show it.

## Fallback

If per-MULE identity proves unworkable, the fallback is to narrow "assigned MULE" by
another discriminator the overlay can express (an explicit per-MULE host target in the
grant rather than a tag), which is more verbose but equivalent. If even that fails, the
posture reverts to `FML-ADR-082`'s default `DISABLED` -- no remote-EUD overlay
membership -- which removes the capability without weakening the boundary. The signal to
take the fallback is a two-MULE `assigned-ingress-only` test in which an EUD reaches a
non-assigned MULE.

## Superseded by

None.

## Verification dependency

Stage 6 (`test/stages/stage-06-wan-overlay/`). The firewall-boundary half is exercised
by `test/bench/wan-overlay-posture.sh`
(`docs/evidence/stage-06-wan-overlay/2026-09-29-firewall-boundary-flat-sat.md`,
`SIMULATED`). The identity half -- an EUD reaching only its assigned MULE's ingress, and
`assigned-mule-lost-no-reattach` -- needs a real tailnet and a second MULE and stays
not-run. The formal Stage 6 qualification remains blocked on `TBR-HW-01`.
