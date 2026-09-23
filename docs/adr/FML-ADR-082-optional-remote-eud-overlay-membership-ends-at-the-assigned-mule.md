---
id: FML-ADR-082
title: Optional remote-EUD overlay membership ends at the assigned MULE
status: PROPOSED
date: 2026-09-23
supersedes: none
superseded-by: none
trades: []
verification: Stage 6
---

# FML-ADR-082 Optional remote-EUD overlay membership ends at the assigned MULE

## Context

`FML-ADR-039` is `SELECTED`. It says only MULE infrastructure shall participate
in the WAN overlay and that EUDs shall not join the tailnet. CONOPS sections 12
and 43 say the same thing, and section 79 criterion 17 says the MULE remains
the WAN-overlay boundary for EUDs. Stage 6 tests EUD isolation from the overlay
as a negative. `FML-ADR-039`'s own fallback says admitting an EUD would violate
CONOPS section 12 and requires a CONOPS change request. A mission package cannot
override that today.

The Program Owner has directed the exception anyway: on mission creation, an
administrator may opt managed EUDs into the overlay, default off, and only as
far as the assigned MULE's approved remote-EUD ingress. MULEs stay first-class
overlay participants. Geographically separated MULEs with their own WAN paths
compose one mission fabric. That fabric is not a `batman-adv` extension, and it
is not the local uplink-pooling question in `FML-ADR-069` and `TBR-NET-04`.

Doing nothing leaves later simulated work with a choice between pretending the
prohibition is already gone, or refusing a directed capability. Neither is
acceptable. This record writes the replacement policy down as `PROPOSED`. It
has no weight until `CCR-04` is accepted and both supersession directions are
recorded. Until that acceptance, `FML-ADR-039` remains the controlling decision.

Alternatives that were rejected:

- Leave the prohibition absolute. The Program Owner declined this.
- Let a mission package contradict `FML-ADR-039` without a CONOPS change. The
  fallback of `FML-ADR-039` forbids it.
- Admit an EUD to arbitrary MULEs, management interfaces, peer EUDs, or the
  field mesh. That is not the directed posture.
- Encode mission, team, or role in a Tailscale tag. `FML-ADR-039` already
  forbids that, and this record keeps the prohibition.
- Treat loss of the assigned MULE as permission to attach through another MULE.
  The Program Owner declined implicit failover.
- Supersede `FML-ADR-039` while this record is only `PROPOSED`. That would leave
  no `SELECTED` overlay decision.

What this record does not know: the grant mechanism that enforces "assigned
ingress only", the state-label spelling for "remote continuity waiting for
WAN", and whether offline browser-trusted TLS for onboarding can be done.
Roadmap item 4.6 already owns that bootstrap. `TBR-NET-04` remains open and is
not a dependency of this decision.

## Decision

On acceptance, this record replaces `FML-ADR-039` in full. The clauses below
are that replacement. Clauses carried forward are repeated here so supersession
does not drop them.

Mission creation shall select a remote-EUD overlay posture in the mission
package WAN policy. The posture shall be `DISABLED` unless an administrator
selects `ASSIGNED_MULE_ONLY`. No other posture is decided here.

An EUD shall join the WAN overlay only when that posture is
`ASSIGNED_MULE_ONLY` and FML has authorized that EUD for remote continuity to
its assigned MULE. Under every other posture, including the default, an EUD
shall not join the overlay.

An EUD admitted under `ASSIGNED_MULE_ONLY` shall be granted only the approved
remote-EUD ingress of its assigned MULE. The assigned MULE shall remain the
security and routing boundary past that membership. The grant shall not extend
to any other MULE, to MULE management interfaces, to peer EUDs on the overlay,
to the local RF mesh, or to unrelated home, private, or administrative
infrastructure.

If the assigned MULE is unavailable, that EUD shall not obtain overlay ingress
through another MULE.

Overlay policy shall remain deny-by-default. Overlay membership shall not
itself authorize mission data or mission actions. Tailscale device tags and
grants shall represent infrastructure and access scope only. They shall not
represent a mission, a team, a unit, or an operational role. FML signed mission
policy remains the source of those facts.

Authorized MULEs shall participate in the approved FML WAN overlay when their
WAN paths are available, and shall exchange the inter-MULE traffic that overlay
is for. That participation shall not grant unrelated home, private, or
administrative tailnet resources. The overlay shall not extend `batman-adv` or
any other Layer-2 mesh across the WAN.

The overlay shall remain optional to local mission operation. Loss of WAN or of
the overlay shall not remove local EUD access, the local mesh, peer ATAK, local
services, or LoRa. An EUD that declines remote continuity, or a mission whose
posture is `DISABLED`, shall not fail local onboarding or local operation for
that reason.

A field MULE shall not hold a reusable Tailscale authentication key in order to
make offline overlay enrollment appear solved.

This decision shall not be implemented by routing access-point traffic into the
overlay. `FML-ADR-068` remains `SELECTED`: an EUD on the access point is
forwarded to the general WAN uplink, and the node shall not route that traffic
into the secure overlay. Remote-EUD membership, when the posture allows it, is
the EUD's own overlay enrollment, constrained to the assigned ingress. It is
not masquerade onto the tailnet.

This decision does not select how a mesh elects or pools WAN gateways. That
remains `FML-ADR-069` and open `TBR-NET-04`. It does not promote "competing
automatic WAN gateways" out of CONOPS section 81.

## Status

`PROPOSED`.

`PROPOSED` carries no weight. `FML-ADR-039` stays `SELECTED`, and its
`superseded-by` stays `none`, until `CCR-04` is accepted. Acceptance sets this
record to `SELECTED`, sets `supersedes` to `FML-ADR-039`, and in the same change
sets `FML-ADR-039` to `SUPERSEDED` with `superseded-by: FML-ADR-082`. Both
directions, and not before.

The exact label a node shows for "remote continuity is selected but WAN is
absent" is not decided here. It shall not be invented as a `mule/status.py`
literal by this record.

## Consequences

- CONOPS sections 12 and 43, section 78 Stage 6, and section 79 criterion 17
  cannot stay as written if this record is accepted. `CCR-04` is the section 86
  request. The transcribed CONOPS v1.01 is not edited in place. Acceptance
  reissues CONOPS v1.1.
- `FML-ADR-068` is not superseded. The access-point passthrough and the optional
  remote-EUD enrollment are different paths. The threat-model bullet that says
  passthrough does not reach the overlay stays true. A separate enrollment, once
  accepted, needs its own threat-model paragraph. `CCR-04` lists that edit and
  does not make it now.
- Tailscale identity still does not answer who the user is, which mission or
  team they are in, or what they may see or do.
- Joining a MULE's onboarding WLAN may supply that MULE's organizational scope
  as context. It shall not be identity and it shall not be authorization.
  Production onboarding remains roadmap item 4.6. This record does not create a
  second onboarding architecture. Prototype PPSK stays where `FML-ADR-038`
  already permits it.
- The production mission schema shall not gain a remote-access or Tailscale
  field while CONOPS section 19 identity, role, and organizational scope are
  still absent from `mission/schema/mission-package.schema.json`. SAD section
  19.2 already names WAN policy as package content. A fixture may model the
  posture before the schema changes. Schema evolution shall keep a rollback
  path.
- Nothing in this record enters `mule/`. Nothing here enlarges v0.0.1. Stage 6
  is still an undefined executable stage. A flat-sat of the observation
  lifecycle does not depend on this record being accepted, and a flat-sat of
  remote-EUD behavior does.
- `docs/prior-art/wan-and-halow-dependencies.md` evaluated the Tailscale client
  under the absolute prohibition. That evaluation stands. The proof it asked
  for, that EUDs never join, becomes a two-posture proof only on acceptance.
- `os/config/nftables.conf.template` comments that an EUD uplink reaches "thus
  the overlay". `FML-ADR-068` says the node shall not route that traffic into
  the overlay. This record does not edit the comment and does not authorize
  that route.

## Accepted cost

A managed EUD on the overlay is a credential-bearing endpoint the absolute
prohibition did not allow. When an administrator selects `ASSIGNED_MULE_ONLY`,
compromise of that endpoint reaches the assigned MULE's remote-EUD ingress.
That is a wider blast radius than `FML-ADR-039`, accepted only for missions
that opt in.

The same rule refuses silent failover. A remote EUD whose assigned MULE is down
loses remote ingress while other MULEs stay up. A later operator files that as a
defect. It is the trust boundary the Program Owner asked for.

Supersession concentrates every surviving `FML-ADR-039` clause in this file. A
clause left only in the old record dies on acceptance. The carried-forward
shalls above are the mitigation, and they are the clause a later reader can
argue was incomplete.

## Fallback

Reject `CCR-04`. This record stays `PROPOSED` or is retired without ever
becoming `SELECTED`, and `FML-ADR-039` remains controlling. No CONOPS text
changes.

If this record is accepted and a Stage 6 negative fails — an EUD reaches
another MULE, a management interface, a peer EUD, the RF mesh, or unrelated
infrastructure, or overlay membership is treated as mission authorization — the
recovery is a further ADR that returns the only posture to `DISABLED` and
supersedes this one. The same recovery applies if operators cannot tell
infrastructure reachability from mission authorization.

## Superseded by

None.

This record does not yet supersede `FML-ADR-039`. Recording both directions
while the status is `PROPOSED` would either contradict `SELECTED` on `039` or
remove the only controlling overlay decision. `CCR-04` states the acceptance
edit. `tools/new-adr.sh` asks for both directions in the change that performs
the supersession. That change is acceptance, not this one.

## Verification dependency

Stage 6, `test/stages/stage-06-wan-overlay/`. The executable definition does
not exist. On acceptance the stage scope gains the cases below and keeps the
negative it already has. Until acceptance the directory's current scope, quoted
from CONOPS v1.01, remains the stage.

The definition shall eventually prove all of the following. None of them is
demonstrated here. Any flat-sat of them is `SIMULATED` and says nothing about
physical behaviour. Nothing in this record is `HARDWARE-VERIFIED`.

- Posture `DISABLED`: an EUD does not join the overlay.
- Posture `ASSIGNED_MULE_ONLY`: an authorized EUD reaches only its assigned
  MULE's approved remote-EUD ingress.
- The assigned MULE is lost: the EUD does not attach through another MULE.
- Three geographically separated MULEs, each with its own WAN: authorized
  MULEs exchange approved inter-MULE traffic, and the local RF mesh is not
  extended across the WAN.
- WAN is lost: local EUD access, the local mesh, peer ATAK, local services, and
  LoRa continue.
- Unrelated home, private, and administrative infrastructure stays
  inaccessible, for MULEs and for any admitted remote EUD.
- The EUD declines remote continuity: local operation continues.
- Access-point passthrough still does not enter the overlay (`FML-ADR-068`).
