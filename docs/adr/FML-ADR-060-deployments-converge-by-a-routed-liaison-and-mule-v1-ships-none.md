---
id: FML-ADR-060
title: Deployments converge by a routed liaison, and MULE v1 ships none
status: SUPERSEDED
date: 2026-08-31
supersedes: none
superseded-by: FML-ADR-061
trades: [TBR-NET-03, TBR-NET-01]
verification: Stage 11
---

# FML-ADR-060 Deployments converge by a routed liaison, and MULE v1 ships none

**Source of rationale:** `TBR-NET-03`, and the five evidence artifacts under
`docs/evidence/TBR-NET-03/` and `docs/evidence/TBR-NET-01/` dated 2026-08-30 and
2026-08-31.

## Context

Two independently built deployments meeting at an incident must interoperate or
at least coexist. `mission/schema/mission-package.schema.json` makes `mesh_id`
required and says network identity values differ between deployments, and that
works: measured, two deployments with different `mesh_id` do not associate, and
identical address prefixes with identical host addresses are harmless.

**Coexistence is therefore already solved and costs nothing. Interoperation had
no mechanism at all**, and nothing in the repository said how two deployments
would come to share a mesh.

Three mechanisms were considered, plus deferral. The decisive input was not
airtime, cost or complexity. It was `THREAT_MODEL.md`:

> The operational domain is a **shared trust environment**. [...] **There is no
> meaningful compartmentation between admitted participants.** [...] **An
> insider is inside.**

Two deployments that agree a `mesh_id` and form one mesh have admitted each
other's members to one trust environment, and that admission is performed by
typing a mesh name into a radio. It bypasses whatever admission control either
organization operates, because the trust environment is the layer 2 domain and
nothing above it is consulted. `THREAT_MODEL.md` names the insider as an assumed
adversary and says vetting whom you admit is the primary control and an
organisational one.

## Decision

**Deployments shall not converge by merging meshes.** No MULE shall adopt
another deployment's `mesh_id`, and no program-wide `mesh_id` shall be defined.

**Where interoperation is required, it shall be provided by a routed liaison:**
one node per deployment takes an additional bearer onto a shared incident mesh,
holds that mesh in a **separate** `batadv` interface from its own, and forwards
between them at layer 3.

**A liaison shall route and shall never bridge.** Adding the incident bearer to
the deployment's existing mesh interface, which is what `FML-ADR-045` describes
for ordinary multi-bearer operation, produces one layer 2 domain and is the
thing this ADR prohibits.

**A liaison's incident mesh name and peer routes shall be declared
configuration, never operator-typed commands.** `FML-ADR-059` owns the
mechanism.

**MULE v1 ships no convergence mechanism.** No liaison is implemented, and the
shipped posture is coexistence only. This ADR fixes the direction so that
`TBR-RF-03` and the BOM account for a liaison bearer rather than discovering the
need after radios are selected.

## Status

`CONDITIONAL`.

**The condition: `TBR-NET-01` selects per-deployment address prefixes.** A
routed liaison needs an interface in each deployment, and two interfaces in one
subnet cannot be routed between. Measured: with both deployments on
`10.41.0.0/16` the route is refused, `RTNETLINK answers: File exists`, and no
address exists that names the other deployment's node at all -- a node pinging
the peer's address reaches itself.

`TBR-NET-03`'s own closure gate states that a selected mechanism is not accepted
while `TBR-NET-01` remains open. That is why this is `CONDITIONAL` and not
`SELECTED`.

**If the condition fails** and the program retains a fixed prefix, the liaison
cannot be built and the fallback below applies.

## Consequences

Interoperation becomes a deliberate act affecting **one node per deployment**
rather than a reconfiguration of every node.

**Layer 2 never merges, so the addressing collision is structurally
unreachable.** Measured: the far deployment's nodes never enter the local
node's neighbour table and are never resolved. ATAK peer multicast, ARP and
every other layer 2 discovery mechanism stop at the liaison; what crosses is
what somebody routed.

**Withdrawal is instant and contained.** Dropping the incident bearer stops
cross-deployment traffic at once and leaves each deployment untouched.

`TBR-NET-01` loses the fixed-prefix option if this ADR's condition is met, which
is a constraint on that trade and is recorded in it.

**A liaison is a trust boundary and a single point of failure**, carrying
traffic between two organizations that have not authenticated each other.

## Accepted cost

**A bearer on one node per deployment**, which `TBR-RF-03` must account for and
which no candidate node has been shown to have spare.

**An incident mesh name is audible in beacons** to anyone in range, and
`THREAT_MODEL.md`'s curious local is an assumed adversary. This is accepted as
smaller than the fixed-`mesh_id` alternative, which publishes a permanent
constant identifying every MULE deployment.

**Interoperation is impossible until somebody configures it.** Two groups who
need to cooperate and have no liaison configured cannot, and MULE v1 ships
none. That is accepted because the alternative admits strangers to a trust
environment with no compartmentation, and because volunteer groups at an
incident have radios.

**What a liaison may forward, and who authorises one, is not decided here.**
`TBR-NET-03` carries it as an open closure item.

## Fallback

**Coexistence only.** Deployments keep their own `mesh_id`, do not associate,
and do not interoperate. This is the measured default behaviour, it costs
nothing, and it is what v1 ships regardless of this ADR.

If `TBR-NET-01` retains a fixed prefix, this is not a fallback but the outcome:
no mechanism in this ADR can be built.

## Superseded by

`FML-ADR-061`, 2026-08-31, one day later.

**Why:** this ADR's central argument was that merging meshes admits another
organization's members "by typing a mesh name into a radio", bypassing admission
control. That is true of an **open** mesh and false of a keyed one, and
`os/config/wpa_supplicant.conf.template` records that mesh security was
`key_mgmt=TBD` and undecided. This ADR decided a consequence of an undecided
question. Measured afterwards: on a keyed mesh a node without the credential
never reaches `ESTAB` and gets 100% packet loss, so joining is an authenticated
act and the key is the admission control.

`FML-ADR-061` retains this ADR's routing requirements in full -- a liaison
routes and never bridges, and its configuration is declared rather than typed --
and changes only who may merge.

## Verification dependency

Stage 11. `ITEP-C01` carries the analysis; a liaison exercise on real radios
needs two deployments and is not scheduled.

**The LoRa bearer is out of scope for this ADR and needs the opposite
decision.** Two stock Meshtastic deployments converge automatically on a public
default channel, read from the firmware source, so a node separated on 802.11s
is joined on LoRa at the same time and neither state was chosen. See
`docs/evidence/TBR-NET-03/2026-08-30-what-happens-with-no-configuration.md`.
Nothing here separates them.
