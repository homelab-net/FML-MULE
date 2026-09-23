# CCR-04 Optional remote-EUD overlay membership ends at the assigned MULE

**Type:** CONOPS change request
**Status:** `ACCEPTED`
**Target version:** CONOPS **v1.1** (issued)
**Sections affected:** 12, 43, 78 Stage 6, 79 criterion 17, 85 (impact only; the
matrix row for criterion 17 keeps Stage 6)
**Raised by:** Program Owner direction, 2026-09-23
**Accepted by:** Program Owner, 2026-09-23
**Decision:** `FML-ADR-082` (`SELECTED`; supersedes `FML-ADR-039`)

## Statement

`FML-ADR-039` forbids EUD membership on the WAN overlay and says a change that
admits one requires a CONOPS change request. The Program Owner has directed
that change: mission creation selects a remote-EUD overlay posture, default
`DISABLED`, optional `ASSIGNED_MULE_ONLY`, and the assigned MULE remains the
boundary past that membership.

This record is that request. It was accepted on 2026-09-23. CONOPS v1.1 is the
controlling copy. `FML-ADR-082` is `SELECTED` and `FML-ADR-039` is
`SUPERSEDED`. It does not block `FML-ADR-068`, `FML-ADR-069`, or `TBR-NET-04`.
It does not enlarge v0.0.1, and it does not edit `mule/` or the mission schema.
A flat-sat may now exercise the posture. Until that flat-sat exists, the
posture is decided and not demonstrated.

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

SAD section 35.2 transcribes the clauses as `C12-01`, `C12-02`, and `C43-01`
through `C43-09`. Those rows were updated in the acceptance change.

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
EUDs on the overlay, or to unrelated home, private, or administrative
infrastructure.

[SHALL] The grant shall not place the EUD on the local RF mesh and shall not
give the EUD a route onto that mesh. Past the assigned ingress, the MULE may
reach an approved mission service for that EUD, including a service the MULE
itself reaches over the local RF mesh. That reach is the MULE's. It is not
membership of the mesh, and it is not an extension of the mesh across the WAN.
Peer awareness, where approved, shall use a routed application service. It
shall not be a mesh route the EUD holds.

[SHALL] The grant shall not remove or replace local EUD access through the
MULE access point.

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
* that grant does not place the EUD on the local RF mesh; an approved mission
  service the assigned MULE reaches over that mesh is still reached through
  the assigned ingress;
* loss of the assigned MULE does not attach that EUD through another MULE;
* unauthorized Homelab access denial;
* WAN loss and local continuity;
* declining remote-EUD continuity does not remove local EUD operation.
```

Section 79, criterion 17:

```text
17. Under the default posture an EUD does not join the WAN overlay. An EUD
    admitted to the overlay reaches only its assigned MULE's approved
    remote-EUD ingress and is not placed on the local RF mesh. The assigned
    MULE remains the security and routing boundary past that ingress,
    including where it reaches an approved mission service for that EUD
    over the local RF mesh.
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
boundary past that ingress: other MULEs, management, peer EUDs on the overlay,
and unrelated infrastructure. The EUD is not placed on the RF mesh and holds
no route onto it. The MULE may still reach an approved mission service for
that EUD, including a service the MULE reaches over the RF mesh. That is the
MULE's path, not the EUD's overlay grant. The local access-point path is a
different path and is not removed.

Tailscale answers which infrastructure an endpoint may reach. For an admitted
EUD that answer is one tag, and the tag names the mission and the assigned
team. It does not name a role. The grant is not assembled from several broad
tags. FML signed mission policy still answers who the person is, what role
they hold, and what they may see or do. MULE tags do not name a mission or a
team. `FML-ADR-039`'s prohibition on a mission or team in any tag is the
clause this acceptance changes, and only for the admitted EUD.

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

Edited when this request was accepted.

| Document | What the acceptance change did |
| --- | --- |
| `docs/conops/FML-MULE-CONOPS-v1.1.txt` | Reissue. v1.01 was removed as the controlling copy. |
| `docs/conops/README.md` | `[SHALL]` count is 151. |
| `docs/adr/FML-ADR-082-optional-remote-eud-overlay-membership-ends-at-the-assigned-mule.md` | `SELECTED`. `supersedes: FML-ADR-039`. |
| `docs/adr/FML-ADR-039-wan-overlay-terminates-on-mule.md` | `SUPERSEDED`. `superseded-by: FML-ADR-082`. Decision text kept. |
| `docs/architecture/FML-MULE-SAD-v0.31.md` | Section 0.8 row; section 18.1; section 18.2 tag rule; section 35.1 counts; section 35.2 rows `C12-01`, `C12-02`, `C43-01` through `C43-09`. Section 18.3 was not relaxed. |
| `docs/verification/requirements.md` | Criterion 17 text. Allocations of `FML-REQ-016` through `FML-REQ-019` moved to `FML-ADR-082`. |
| `docs/verification/traceability.md` | Regenerated. |
| `test/stages/stage-06-wan-overlay/README.md` | Scope is the v1.1 list. Decision is `FML-ADR-082`. |
| `test/stages/stage-12-nomad-integration/README.md` | Decision citation moved to `FML-ADR-082`. Scope unchanged. |
| `THREAT_MODEL.md` | Managed-enrollment paragraph added. Passthrough bullet kept. |
| `docs/prior-art/wan-and-halow-dependencies.md` | Two-posture proof. The 2026-09-11 evaluation was not rewritten. |
| `docs/prior-art/registry.yml` | Membership rationale cites `FML-ADR-082`. |
| `docs/change-requests/PBCR-01-field-service-plane.md` | Default posture, with the assigned-MULE exception. |
| `os/config/nftables.conf.template` | Comment only. "thus the overlay" removed. No rule change. |
| `docs/evidence/stage-06-wan-overlay/` | Case files. Each states that the case has not been run. |
| `STATUS.md`, `docs/decision-index.md` | Regenerated. |

Not edited, on purpose.

| Document | Why it stays |
| --- | --- |
| `docs/adr/FML-ADR-068-an-eud-on-the-access-point-is-forwarded-to-the-wan-uplink.md` | A `SELECTED` decision is not amended in place. `082` says it stands. |
| `docs/adr/FML-ADR-069-a-mule-shares-its-wan-uplink-across-the-mesh-and-available-uplinks-are-pooled.md` | Different question. Its overlay boundary is the passthrough and pooling boundary. |
| `mission/schema/mission-package.schema.json` | Identity, role, and organizational scope are still absent. The posture is not a schema field yet. |
| `mule/` | No production literal. |
| `docs/NON-GOALS.md` | Nothing left section 81. |
| `docs/adr/README.md` | The reading-aid table already lags past `FML-ADR-051`. `STATUS.md` is the register. |
| Historical evidence and the hardware BOM | They describe the boundary as it was when they were written. |

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

Accepted. Program Owner, 2026-09-23.

Acceptance is this reissue and the supersession, in one change. The section 87
signature block in CONOPS v1.1 is still unsigned. That is a different signature
from this acceptance, and it was already unsigned on v1.01.

## What this request does not decide

- How the Tailscale grant syntax, or an equivalent, is written so the only
  destination is the assigned ingress. The tag's contents are decided. The
  ACL mechanism is not, and it is not given an identifier here.
- The exact spelling of `tag:eud-mission-<mission>-team-<team>`. The
  illustration is not a frozen field name.
- Gateway election and uplink pooling (`TBR-NET-04`, `FML-ADR-069`).
- Access-point forwarding (`FML-ADR-068`). Whether a local EUD is also
  forwarded onto `batman-adv` stays open there, with `TBR-TAK-01`. The
  remote-EUD grant does not close it, and it does not remove the access-point
  path.
- Onboarding transport, EAP-TLS bootstrap, or browser-trusted TLS without WAN
  (roadmap item 4.6, `FML-ADR-038`, `FML-ADR-031`).
- Sensor permission, observation lifecycle, communications-terrain wording,
  EMCON vocabulary, or `mule/capability.py`.
- A node-status literal for remote continuity.
- The rest of `docs/change-requests/2026-09-23-system-enhancement-direction.txt`.
  That file is not accepted by this request. The admitted-EUD tag is the only
  identity change this request makes.
