---
id: FML-ADR-082
title: Optional remote-EUD overlay membership ends at the assigned MULE
status: SELECTED
date: 2026-09-23
supersedes: FML-ADR-039
superseded-by: none
trades: []
verification: Stage 6
---

# FML-ADR-082 Optional remote-EUD overlay membership ends at the assigned MULE

## Context

`FML-ADR-039` was `SELECTED`. It said only MULE infrastructure shall participate
in the WAN overlay and that EUDs shall not join the tailnet. This record
supersedes it. The text below is the replacement, including the clauses of
`FML-ADR-039` that still apply.

The Program Owner has directed the exception anyway: on mission creation, an
administrator may opt managed EUDs into the overlay, default off, and only as
far as the assigned MULE's approved remote-EUD ingress. MULEs stay first-class
overlay participants. Geographically separated MULEs with their own WAN paths
compose one mission fabric. That fabric is not a `batman-adv` extension, and it
is not the local uplink-pooling question in `FML-ADR-069` and `TBR-NET-04`.

Doing nothing would have left later work pretending the prohibition was already
gone, or refusing a directed capability. This record is the replacement. It was
accepted with `CCR-04` on 2026-09-23. `FML-ADR-039` is `SUPERSEDED`.

Alternatives that were rejected:

- Leave the prohibition absolute. The Program Owner declined this.
- Let a mission package contradict `FML-ADR-039` without a CONOPS change. The
  fallback of `FML-ADR-039` forbids it.
- Admit an EUD to arbitrary MULEs, management interfaces, or peer EUDs, or
  place that EUD on the field mesh. Direct unrestricted field-mesh access is
  not the directed posture. An approved mission service reached by the
  assigned MULE, including one that MULE reaches over the RF mesh, is not
  this alternative.
- Keep `FML-ADR-039`'s rule that a tag shall not name a mission or a team.
  The Program Owner directed the opposite for an admitted EUD: one tag names
  the mission and the assigned team. Several broad tags cannot be intersected,
  so that older rule would force a wider grant. A tag still shall not name an
  operational role.
- Compose the remote-EUD grant from additive broad tags, such as an EUD tag
  plus a mission tag plus a team tag. Tailscale tags are additive. A grant on
  any one of them widens the endpoint. That composition was rejected.
- Treat loss of the assigned MULE as permission to attach through another MULE.
  The Program Owner declined implicit failover.
- Supersede `FML-ADR-039` while this record was only `PROPOSED`. That was not
  done. Both directions were recorded in the acceptance change, not before.

What this record does not know: the grant syntax that enforces "assigned
ingress only", the exact spelling of the mission-and-team tag, the
state-label spelling for "remote continuity waiting for WAN", and whether
offline browser-trusted TLS for onboarding can be done. The tag's contents
are decided. The ACL text is not.

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
or to unrelated home, private, or administrative infrastructure.

The grant shall not place the EUD on the local RF mesh and shall not give the
EUD a route onto that mesh. Past the assigned ingress, the MULE may reach an
approved mission service for that EUD, including a service the MULE itself
reaches over the local RF mesh. That reach is the MULE's. It is not membership
of the mesh, and it is not an extension of `batman-adv` across the WAN. Peer
awareness, where approved, shall use a routed application service. It shall
not be a mesh route the EUD holds.

This grant shall not remove or replace the EUD's local access-point path.
Whether a local access-point EUD is also forwarded onto `batman-adv` remains
the open question in `FML-ADR-068` and `TBR-TAK-01`. This record does not
close it.

If the assigned MULE is unavailable, that EUD shall not obtain overlay ingress
through another MULE.

Overlay policy shall remain deny-by-default. Overlay membership shall not
itself authorize mission data or mission actions.

When the posture is `ASSIGNED_MULE_ONLY`, the Tailscale identity of an admitted
EUD shall be one managed tag. That tag shall name the mission and the assigned
team, and it shall not name an operational role. One tag is the whole
infrastructure grant. The program shall not compose that grant from several
broad tags, because Tailscale tags are additive and a grant on any one of them
widens the endpoint. An illustrative form is
`tag:eud-mission-<mission>-team-<team>`. The spelling is not frozen here.

That tag is how the overlay names an assignment FML has already authorized. It
is not the source of mission authorization. FML signed mission policy remains
the source of who the person is, what role they hold, and what they may see or
do. FML shall retain the mapping from that person and that EUD to the tagged
node. Ordinary operators shall not hold Tailscale user accounts. Using a tag
for a managed EUD is an explicit exception to Tailscale's guidance that tags
are for non-human devices.

A grant from that tag shall reach only the assigned MULE's approved
remote-EUD ingress. The tagged EUD shall not be a subnet router or an exit
node, and the tag shall not admit SSH, database, or management-plane access.

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

`SELECTED`. Accepted with `CCR-04` on 2026-09-23. This record supersedes
`FML-ADR-039`. Both directions are recorded.

The exact label a node shows for "remote continuity is selected but WAN is
absent" is not decided here. It shall not be invented as a `mule/status.py`
literal by this record.

## Consequences

- CONOPS v1.1 reissues sections 12 and 43, section 78 Stage 6, and section
  79 criterion 17. v1.01 is not the controlling copy. `CCR-04` is accepted.
- `FML-ADR-068` is not superseded. The access-point passthrough and the optional
  remote-EUD enrollment are different paths. The threat-model bullet that says
  passthrough does not reach the overlay stays true. The managed-enrollment
  paragraph is separate.
- The managed-EUD tag names the mission and the assigned team as the scope
  of the ingress grant. It does not answer who the user is, what role they
  hold, or what mission data they may see or do. Those remain signed mission
  policy. FML keeps the human-to-EUD-to-node mapping. Operators do not hold
  Tailscale user accounts. MULE infrastructure tags stay infrastructure tags.
  This record does not put a mission or a team into a MULE's tag.
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
  for is now the two-posture proof: default, an EUD does not join; selected,
  the EUD reaches only the assigned ingress.
- `os/config/nftables.conf.template` no longer says an EUD uplink reaches "thus
  the overlay". `FML-ADR-068` still says the node shall not route that traffic
  into the overlay. This record does not authorize that route.

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

`CCR-04` was accepted. Rejection is no longer the fallback.

If a Stage 6 negative fails — an EUD reaches another MULE, a management
interface, a peer EUD on the overlay, or unrelated infrastructure, or the EUD
is placed on the RF mesh, or overlay membership is treated as mission
authorization — the recovery is a further ADR that returns the only posture to
`DISABLED` and supersedes this one. An approved mission service that the
assigned MULE itself reaches over the RF mesh is not that failure. The same
recovery applies if operators cannot tell infrastructure reachability from
mission authorization.

## Superseded by

None.

This record does not yet have a successor.

## Verification dependency

Stage 6, `test/stages/stage-06-wan-overlay/`. The executable definition does
not exist. The stage scope is the CONOPS v1.1 list. The files under
`docs/evidence/stage-06-wan-overlay/` record the cases and state that none of
them has been run.

The definition shall eventually prove all of the following. None of them is
demonstrated here. Any flat-sat of them is `SIMULATED` and says nothing about
physical behaviour. Nothing in this record is `HARDWARE-VERIFIED`.

- Posture `DISABLED`: an EUD does not join the overlay.
- Posture `ASSIGNED_MULE_ONLY`: an authorized EUD reaches only its assigned
  MULE's approved remote-EUD ingress.
- The admitted EUD is not a participant of the local RF mesh and holds no
  route onto it. An approved mission service the assigned MULE reaches over
  that mesh is still reached through the assigned ingress. The path past the
  ingress is the MULE's.
- The assigned MULE is lost: the EUD does not attach through another MULE.
- Three geographically separated MULEs, each with its own WAN: authorized
  MULEs exchange approved inter-MULE traffic, and the local RF mesh is not
  extended across the WAN.
- WAN is lost: local EUD access, the local mesh, peer ATAK, local services, and
  LoRa continue.
- Unrelated home, private, and administrative infrastructure stays
  inaccessible, for MULEs and for any admitted remote EUD.
- The EUD declines remote continuity: local operation continues.
- The admitted EUD carries one tag that names the mission and the assigned
  team and does not name a role. A grant assembled from several broad tags is
  a failure of this case.
- Access-point passthrough still does not enter the overlay (`FML-ADR-068`).
