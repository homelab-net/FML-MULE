# CCR-04 Optional remote-EUD overlay membership ends at the assigned MULE

**Type:** CONOPS change request
**Status:** `OPEN`
**Target version:** CONOPS **v1.1** (minor increment, stakeholder re-approval)
**Sections affected:** 12, 43, 78 Stage 6, 79 criterion 17, 85 (impact only; the
matrix row for criterion 17 keeps Stage 6)
**Raised by:** Program Owner direction, 2026-09-23
**Decision:** `FML-ADR-082` (`PROPOSED`, no weight)
**Does not block:** `FML-ADR-039`, which stays `SELECTED` until this request is
accepted. Does not block `FML-ADR-068`, `FML-ADR-069`, or `TBR-NET-04`. Does
not block v0.0.1, `mule/`, or the mission schema.
**Blocks on acceptance:** any implementation that places an EUD on the overlay,
including a flat-sat that claims the new posture is controlling.

## Statement

`FML-ADR-039` forbids EUD membership on the WAN overlay and says a change that
admits one requires a CONOPS change request. The Program Owner has directed
that change: mission creation selects a remote-EUD overlay posture, default
`DISABLED`, optional `ASSIGNED_MULE_ONLY`, and the assigned MULE remains the
boundary past that membership.

This record is that request. It does not approve it, it does not edit CONOPS
v1.01, and it does not supersede `FML-ADR-039`. `docs/conops/README.md` forbids
editing the transcribed CONOPS in place. Acceptance reissues v1.1 and, in the
same change, sets `FML-ADR-082` to `SELECTED` with `supersedes: FML-ADR-039`
and sets `FML-ADR-039` to `SUPERSEDED` with `superseded-by: FML-ADR-082`.

The change alters `[SHALL]` statements, a section 79 criterion, and a section
78 stage. Section 86 makes that a minor increment and stakeholder re-approval,
not a point revision. It does not remove a section 81 exclusion. Competing
automatic WAN gateways stay out of scope.

## 1. Sections affected

CONOPS v1.01 sections 12 and 43, section 78 Stage 6, and section 79 criterion
17. Section 85's row for criterion 17 already names sections 12 and 43 and
Stage 6. That row does not change. The criterion's words do.

## 2. Current text

Section 12, the two binding sentences:

```text
[SHALL] EUDs shall not join the Tailscale or equivalent WAN overlay directly.

[SHALL] The MULE shall be the routing, authentication, and security boundary
between EUDs and remote field services.
```

Section 43, the three binding sentences:

```text
[SHALL] EUDs shall not join the overlay directly.

[SHALL] The MULE shall remain the WAN security and routing boundary.

[SHALL] Infrastructure access control and mission authorization shall remain
separate. Overlay authentication alone shall not grant service or data
authorization.
```

Section 78, Stage 6, the bullet this request replaces:

```text
* EUD isolation from overlay;
```

Section 79, criterion 17:

```text
17. MULE remains the WAN-overlay boundary for EUDs;
```

SAD section 35.2 transcribes the same prohibitions as `C12-01`, `C43-01`, and
`C43-02`. Those rows are downstream of this request. They are not edited here.

## 3. Proposed text

Section 12, replacing both sentences above:

```text
[SHALL] An EUD shall join the Tailscale or equivalent WAN overlay only when
the mission WAN policy sets remote-EUD overlay posture to ASSIGNED_MULE_ONLY
and FML has authorized that EUD for remote continuity to its assigned MULE.
Under any other posture, including the default DISABLED, an EUD shall not
join the overlay.

[SHALL] The assigned MULE shall remain the routing, authentication, and
security boundary between that EUD and remote field services. Overlay
membership under the posture above shall not itself be that authorization.
```

Section 43, replacing the three sentences above. The separation of
infrastructure access from mission authorization is kept verbatim as its own
sentence.

```text
[SHALL] Authorized MULE infrastructure shall participate in the approved FML
WAN overlay when a WAN path is available. That participation shall be limited
to approved FML inter-MULE resources. It shall not grant unrelated home,
private, or administrative infrastructure.

[SHALL] An EUD shall join that overlay only when the mission WAN policy sets
remote-EUD overlay posture to ASSIGNED_MULE_ONLY and FML has authorized that
EUD for remote continuity to its assigned MULE.

[SHALL] Under any other posture, including the default DISABLED, an EUD shall
not join the overlay.

[SHALL] An EUD admitted under ASSIGNED_MULE_ONLY shall be granted only the
approved remote-EUD ingress of its assigned MULE. The assigned MULE shall
remain the WAN security and routing boundary past that membership. The grant
shall not extend to any other MULE, to MULE management interfaces, to peer
EUDs on the overlay, to the local RF mesh, or to unrelated home, private, or
administrative infrastructure.

[SHALL] If the assigned MULE is unavailable, that EUD shall not obtain overlay
ingress through another MULE.

[SHALL] Infrastructure access control and mission authorization shall remain
separate. Overlay authentication alone shall not grant service or data
authorization.

[SHALL] The overlay shall not extend batman-adv or any other Layer-2 mesh
across the WAN.
```

Section 78, Stage 6. The current six bullets remain, except "EUD isolation
from overlay", which is replaced by the default-posture bullet. The list
becomes:

```text
* local WAN gateway;
* secure overlay between authorized MULEs, without extending the local RF
  mesh across the WAN;
* remote field services;
* default remote-EUD posture: EUD isolation from the overlay;
* ASSIGNED_MULE_ONLY: an authorized EUD reaches only its assigned MULE's
  approved remote-EUD ingress;
* loss of the assigned MULE does not attach that EUD through another MULE;
* unauthorized Homelab access denial;
* WAN loss and local continuity;
* declining remote-EUD continuity does not remove local EUD operation.
```

Section 79, criterion 17:

```text
17. Under the default posture an EUD does not join the WAN overlay. An EUD
    admitted to the overlay reaches only its assigned MULE's approved
    remote-EUD ingress, and that MULE remains the security and routing
    boundary past that membership.
```

Criteria 16, 18, and 19 are unchanged. WAN stays optional. Remote teams still
reach approved field services when WAN exists. Unrelated home, private, and
administrative infrastructure stays inaccessible.

## 4. Operational rationale

A mission administrator who does not want EUDs on the overlay keeps MULE-to-MULE
WAN connectivity. The two memberships are independent. Turning EUDs off does
not turn MULEs off. The default preserves today's prohibition.

The boundary sentence is restated rather than deleted. Membership, when
selected, ends at one ingress on the assigned MULE. The MULE is still the
boundary between that EUD and everything else: other MULEs, management,
peer EUDs, the RF mesh, and unrelated infrastructure.

Tailscale answers which infrastructure an endpoint may reach. FML answers
mission, team, role, and authorization. A tag that spells a team name is not
introduced.

Local mission operation does not require WAN, and declining the opt-in does
not fail onboarding. A reusable Tailscale authentication key is not cached on
a field MULE to fake an offline enrollment.

This is not local uplink pooling. CONOPS section 42's one-active-local-gateway
baseline, section 81's exclusion of competing automatic WAN gateways,
`FML-ADR-069`, and `TBR-NET-04` are about how a mesh shares uplinks. Three
sites, each with its own WAN, each a MULE on the overlay, is geographic
membership. It does not elect a gateway and it does not stretch Layer 2.

`FML-ADR-068` is a different path. An EUD on the access point is forwarded to
the general uplink, and the node does not route that traffic into the overlay.
The opt-in is the EUD's own enrollment, not masquerade onto the tailnet.

## 5. Downstream documents affected

Edited in this change, as pointers only. None of them adopts the proposed
text.

| Document | What this change does |
| --- | --- |
| `docs/adr/FML-ADR-082-optional-remote-eud-overlay-membership-ends-at-the-assigned-mule.md` | The `PROPOSED` decision. No weight. |
| `docs/change-requests/README.md` | Register row. |
| `test/stages/stage-06-wan-overlay/README.md` | Points at this request. Current scope stays the CONOPS v1.01 quote. |
| `THREAT_MODEL.md` | States that the passthrough bullet is unchanged and names this request. |
| `docs/ROADMAP-DEV.md` item 4.6 | States that onboarding is not this request. |
| `docs/trades/TBR-NET-04-how-does-the-mesh-elect-and-pool-wan-gateways-across-multiple-uplinks.md` | States that this request does not decide the trade. The closure gate is unchanged. |
| `docs/prior-art/wan-and-halow-dependencies.md` | States that the 2026-09-11 evaluation stands under `FML-ADR-039`. |
| `STATUS.md`, `docs/decision-index.md` | Regenerated. |

Not edited. On acceptance, the same change that reissues CONOPS v1.1 does the
following. Doing any of it now would make proposed text look controlling.

| Document | Acceptance edit | Why not now |
| --- | --- | --- |
| `docs/conops/FML-MULE-CONOPS-v1.01.txt` | Replace the file with the v1.1 reissue. Do not patch v1.01. | Controlled transcription. Section 86. |
| `docs/conops/README.md` | Update the `[SHALL]` count check. v1.01 expects 145. The proposed section 43 text adds sentences, so the count moves. | The count is of the issued file. |
| `docs/adr/FML-ADR-039-wan-overlay-terminates-on-mule.md` | `SUPERSEDED`, `superseded-by: FML-ADR-082`. | Both directions wait for acceptance. `082` repeats every clause that would otherwise die with `039`. |
| `docs/architecture/FML-MULE-SAD-v0.31.md` | Section 0.8 row; section 18.1 "EUDs do not join the tailnet"; section 35.2 rows `C12-01`, `C43-01`, `C43-02`. Section 18.2 (tags are not mission roles) is already the rule `082` carries forward and stays. Section 18.3 (overlay loss does not remove local operation) stays. | The SAD is derived from the issued CONOPS. |
| `docs/verification/requirements.md` | Rewrite `FML-REQ-017` text to the new criterion 17. Move its allocation from `FML-ADR-039` to `FML-ADR-082`. Move `FML-REQ-016`, `FML-REQ-018`, and `FML-REQ-019` allocations the same way, because `082` carries those clauses and acceptance supersedes `039`. Regenerate `docs/verification/traceability.md`. | This file transcribes CONOPS v1.01 section 79. Changing it now makes it a second, drifting copy. |
| `test/stages/stage-06-wan-overlay/README.md` | Replace the scope list with the proposed Stage 6 bullets. Decisions line becomes `FML-ADR-082`. | The current bullets are the issued stage. |
| `test/stages/stage-12-nomad-integration/README.md` | Retarget the decisions citation from `FML-ADR-039` to `FML-ADR-082`. The stage scope does not change. | On acceptance `039` is no longer the live decision. The Homelab-denial obligation moves with `082`. |
| `THREAT_MODEL.md` | Add a paragraph for the managed enrollment. Do not rewrite the passthrough bullet that says the uplink path does not reach the overlay. | That bullet is `FML-ADR-068`, and it stays true. |
| `docs/prior-art/wan-and-halow-dependencies.md` | Replace "proof that EUDs never join the overlay" with the two-posture proof. Do not rewrite the 2026-09-11 client evaluation as if it had been run under `082`. | The evaluation is evidence of what was true that day. |
| `docs/prior-art/registry.yml` | The Tailscale rationale cites `FML-ADR-039`. Point the membership rule at `FML-ADR-082`. `FML-REQ-017` keeps its identifier. | Requirement identifiers are stable. The live ADR citation is not, after supersession. |
| `docs/change-requests/PBCR-01-field-service-plane.md` | The preserved constraint "EUDs do not join the WAN overlay (`FML-ADR-039`)" becomes the default posture, with the assigned-MULE exception cited to `FML-ADR-082`. | That constraint is still binding. |
| `os/config/nftables.conf.template` | Retarget the `FML-ADR-039` comment to `FML-ADR-068` and `FML-ADR-082`. Delete the phrase "thus the overlay". It overstates `FML-ADR-068`, which forbids routing access-point traffic into the overlay. No rule change. | A comment edit in live configuration would look like the firewall had adopted `082`. |
| `docs/adr/FML-ADR-068-an-eud-on-the-access-point-is-forwarded-to-the-wan-uplink.md` | No decision edit. A reader who needs the relationship uses `082`, which says `068` stands. | A `SELECTED` decision is not amended in place. |
| `docs/adr/FML-ADR-069-a-mule-shares-its-wan-uplink-across-the-mesh-and-available-uplinks-are-pooled.md` | No edit. Its "overlay boundary of CONOPS section 43" remains the passthrough and pooling boundary, which `082` does not relax. | Different question. |
| `docs/adr/README.md` | No hand edit. The reading-aid table already lags past `FML-ADR-051`. `STATUS.md` is the generated register. | Repairing that lag is not this request. |

Historical records. Do not rewrite them on acceptance either. They describe the
boundary as it was when they were written.

- `docs/evidence/TBR-NET-01/2026-08-31-external-network-collision-analysis.md`
- `docs/evidence/TBR-NET-03/2026-09-04-what-a-liaison-forwards-and-who-authorises.md`
- `docs/evidence/TBR-NET-04/2026-09-04-gateway-sharing-hwsim.txt`
- `docs/change-requests/CCR-03-source-dm32-roip-handoff.txt`
- `hardware/prototype/BOM-v0.4-DM32-RoIP-handoff.txt`
- `docs/prior-art/openmanetd.md` cites `FML-REQ-017` by identifier only. The
  identifier does not change.

Not in this request, and not an acceptance edit of those files:

- `mission/schema/mission-package.schema.json`. CONOPS section 19 already
  requires users, roles, and organizational scope. The schema has none of
  them. Sensor and remote-access fields wait until that foundation exists.
  SAD section 19.2 already lists WAN policy as package content, which is the
  conceptual slot. A fixture may model the posture.
- `mule/`. No production literal, including a "waiting for WAN" status.
- `docs/NON-GOALS.md`. Nothing is promoted off section 81.
- v0.0.1.

## 6. Verification impact against section 85

| Criterion | Stage now | After acceptance |
| --- | --- | --- |
| 16 WAN remains optional | 6 | Unchanged. Still Stage 6. |
| 17 boundary for EUDs | 6 | Wording changes as above. Still Stage 6. The default negative remains, and the assigned-ingress positive and the no-reattach negative are added to that stage. |
| 18 remote teams reach approved services | 6 | Unchanged. MULE-to-MULE overlay is the path this criterion already allowed. |
| 19 unrelated infrastructure inaccessible | 6 | Unchanged. Applies to MULEs and to any admitted remote EUD. |

No criterion loses its validating stage. Section 85's removal rule is not
triggered. Stage 6 is still not an executable definition; acceptance changes
the scope the definition covers. It does not invent pass thresholds.

`FML-ADR-082` names the cases. They are not evidence.

## 7. Approval

None. Status is `OPEN`.

Approval is a named Program Owner acceptance of this request, followed by the
CONOPS v1.1 reissue and the supersession edit in section 5. Approval of this
file alone, as with `CCR-03` before its reissue, does not change v1.01 and
does not by itself make `FML-ADR-082` `SELECTED`. The reissue and the
supersession are the baselining step, and they are one change.

## What this request does not decide

- How a Tailscale grant, or an equivalent, is written so the only destination
  is the assigned ingress. The policy is decided. The mechanism is not, and it
  is not given an identifier here.
- Gateway election and uplink pooling (`TBR-NET-04`, `FML-ADR-069`).
- Access-point forwarding (`FML-ADR-068`).
- Onboarding transport, EAP-TLS bootstrap, or browser-trusted TLS without WAN
  (roadmap item 4.6, `FML-ADR-038`, `FML-ADR-031`).
- Sensor permission, observation lifecycle, communications-terrain wording,
  EMCON vocabulary, or `mule/capability.py`.
- A node-status literal for remote continuity.
- Team, role, or mission identity inside Tailscale.
