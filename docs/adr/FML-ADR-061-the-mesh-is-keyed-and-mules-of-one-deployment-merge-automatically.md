---
id: FML-ADR-061
title: The mesh is keyed and MULEs of one deployment merge automatically
status: SELECTED
date: 2026-08-31
supersedes: FML-ADR-060
superseded-by: none
trades: [TBR-NET-03, TBR-NET-01, TBR-SEC-01]
verification: Stage 2
---

# FML-ADR-061 The mesh is keyed and MULEs of one deployment merge automatically

**Source of rationale:** `TBR-NET-03`, and
`docs/evidence/TBR-NET-03/2026-08-31-a-keyed-mesh-admits-only-key-holders.md`.

## Context

`FML-ADR-060`, written one day earlier, prohibited merging meshes. Its central
argument was that merging admits another organization's members to a shared
trust environment "by typing a mesh name into a radio", bypassing admission
control.

**That argument assumed an open mesh, and the program had not decided that.**
`os/config/wpa_supplicant.conf.template` carries `key_mgmt=TBD` and says in
terms that "Mesh security is not decided. An open mesh admits any device in
range, which conflicts with the admission model." `FML-ADR-060` decided a
consequence of an undecided question and got it wrong.

**On a keyed mesh the key is the admission control.** Measured on
`mac80211_hwsim`, three nodes, one mesh identifier, one channel, all in range:

| Pair | `mesh plink` | authenticated | authorized | traffic |
| --- | --- | --- | --- | --- |
| same key | `ESTAB` | yes | yes | 0% loss |
| different key | `LISTEN` | no | no | 100% loss |
| no key at all | never peers | -- | -- | -- |

Joining is an authenticated act. `FML-ADR-060`'s premise does not survive it.

## Decision

**The field mesh shall be keyed.** `key_mgmt=SAE` on the 802.11s mesh, so peers
authenticate by SAE and Authenticated Mesh Peering Exchange before a peer link
reaches `ESTAB`. An open field mesh is prohibited.

**MULEs of one deployment share one mesh credential and merge automatically.**
Automatic formation among a deployment's own nodes is the wanted behaviour and
needs no operator action. `FML-ADR-060`'s prohibition on merging is withdrawn
for this case.

**A node holding the credential is an admitted participant.** There is no
compartmentation below that, per `THREAT_MODEL.md`, so issuing the credential --
by handing over a configured MULE or by any other means -- is the admission
decision, and it is an organisational one.

**Cross-organization interoperation shall not be provided by sharing the
deployment credential.** A partner is given a **separate keyed mesh** carried on
a liaison node's additional bearer, routed rather than bridged, as
`FML-ADR-060` describes and as
`docs/evidence/TBR-NET-03/2026-08-30-liaison-routing-exercise.md` measured.
`FML-ADR-060`'s routing requirements are retained in full by this ADR.

**MULE v1 ships no cross-organization mechanism.** Unchanged from
`FML-ADR-060`.

## Status

`SELECTED`. Supersedes `FML-ADR-060`.

The liaison half remains conditional on `TBR-NET-01` selecting per-deployment
prefixes, for the reason `FML-ADR-060` gave: two interfaces in one subnet cannot
be routed between. **That condition does not affect the keyed-mesh decision**,
which is independent of addressing.

## Consequences

Two deployments that both hold one credential merge automatically when they meet.
**That makes the addressing collision the normal case rather than the
exceptional one**, which raises the priority of `TBR-NET-01` rather than
changing this decision.

A partner boundary becomes **revocable without touching the deployment's own
fleet**: change the partner mesh credential, and nothing a MULE holds changes.
That is the property sharing the deployment credential cannot provide.

`TBR-SEC-01` acquires the mesh credential as a protected asset. It is a
credential at rest on every node.

## Accepted cost

**One credential per mesh, and no per-device keys.** Measured: a second
`sae_password` with an identifier did not produce authenticated peering between
differently-keyed nodes. Whether some configuration achieves it is not
established, and this ADR does not depend on it.

So **a captured node yields the mesh credential**, and `THREAT_MODEL.md` makes
physical capture an expected condition and records that "credential revocation
in a disconnected network is hard and its effectiveness is `TBD`". Revoking one
node means rekeying every node. **This is the largest accepted cost here** and
it is accepted because the alternative -- an open mesh -- has no admission
control at all, and because a keyed mesh with awkward revocation is strictly
better than an unkeyed one.

**Rekeying has no mechanism.** Nothing in this program distributes or rotates a
mesh credential, and this ADR does not create one.

## Fallback

If a keyed mesh proves unworkable on the HaLow bearer -- the template already
warns that "whether the HaLow driver honours standard wpa_supplicant mesh
options at all" is unverified -- the fallback is `FML-ADR-060`'s posture:
deployments do not merge, and interoperation is by routed liaison only. That is
a degradation of convenience, not of security.

## Superseded by

None.

## Verification dependency

Stage 2. The keyed-mesh result is `SIMULATED` on `mac80211_hwsim` and says
nothing about a real driver.

**`TBR-LINUX-01` owns whether the HaLow bearer supports SAE at all.** That was
recorded here as this ADR's largest unverified assumption, and it has since been
researched in the published driver source. See
`docs/evidence/TBR-LINUX-01/2026-08-31-halow-driver-mesh-and-sae-support.md`.

In summary, and still `UNVERIFIED` because nothing was executed: both candidate
vendors offer `NL80211_IFTYPE_MESH_POINT` on the sub-GHz path, both gate it on
`CONFIG_MAC80211_MESH` which the Debian baseline already sets, and Morse Micro's
driver contains explicit mesh-SAE frame handling
(`auth_alg == WLAN_AUTH_SAE`) together with a purpose-built 27 kB mesh
implementation.

**The assumption is reduced, not removed.** No HaLow module is selected, no
radio exists, `regions/us-915/profile.yml` records `halow.permitted: TBD`, and
mesh at 1 MHz S1G channel width -- the configuration HaLow's range argument
depends on -- is untested. The fallback in this ADR stands until hardware says
otherwise.
