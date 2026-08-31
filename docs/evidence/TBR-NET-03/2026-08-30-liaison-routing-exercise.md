# A liaison node that routes between two deployments

**Trade:** `TBR-NET-03`.
**Date:** 2026-08-30.
**Taken by:** Cameron Zobrist, on the lab development machine.
**Status of this artifact:** `SIMULATED`. Six `mac80211_hwsim` radios in
network namespaces. **No radio was involved.**

## What this tests

`TBR-NET-03`'s third option: neither deployment changes its own mesh, one node
on each side takes an additional bearer onto a shared incident mesh, and each
liaison **routes** between that mesh and its own deployment. The trade says the
word "routes" is the whole option, because a liaison that instead adds the
incident bearer to its existing `batman-adv` interface is a bridge and merges
the two deployments into one layer 2 domain. This exercises the routed form and
tests the claim that identical prefixes defeat it.

## The bench

| Node | Deployment | Mesh | Address |
| --- | --- | --- | --- |
| A1 | A, liaison | `deployment-a-mesh` ch1 + `incident-x-mesh` ch11 | `10.41.0.1/16` on `bat0`, `10.99.0.1/24` on `bat1` |
| A2 | A | `deployment-a-mesh` ch1 | `10.41.0.5/16` |
| B1 | B, liaison | `deployment-b-mesh` ch6 + `incident-x-mesh` ch11 | `10.42.0.1/16` on `bat0`, `10.99.0.2/24` on `bat1` |
| B2 | B | `deployment-b-mesh` ch6 | `10.42.0.5/16` |

Three mesh identifiers on three non-overlapping channels. **`bat0` and `bat1`
are separate `batman-adv` interfaces**: the liaison holds two layer 2 domains
and forwards between them at layer 3.

## It works, and layer 2 stays separate

Before configuration, `A2 -> B2` is `Network is unreachable`. After, with the
record-route option showing the path actually taken:

```text
A2 -> B2 : 0% packet loss        B2 -> A2 : 0% packet loss
path     : 10.41.0.5  10.99.0.1  10.42.0.1  10.42.0.5
```

Both directions, and the path crosses both liaisons as intended. Initial
convergence to the first end-to-end reply was **2034 ms**.

**Layer 2 is not merged, which is the point of the option:**

```text
A2 batman-adv originators : 1        (its own deployment only)
A2 ARP entries            : 10.41.0.1 only, its own liaison
A1 bat0 originators : 1   A1 bat1 originators : 1
```

A2 never learns a MAC address belonging to deployment B, and never resolves one.
The collision in `docs/evidence/TBR-NET-01/2026-08-30-collision-exercise.md`
cannot occur here, because no ARP resolution crosses a deployment boundary.

## What the operator does

Six commands across four nodes:

```text
A1, B1:  sysctl -w net.ipv4.ip_forward=1
A1:      ip route add 10.42.0.0/16 via 10.99.0.2
B1:      ip route add 10.41.0.0/16 via 10.99.0.1
A2:      ip route add 10.42.0.0/16 via 10.41.0.1
B2:      ip route add 10.41.0.0/16 via 10.42.0.1
```

The two leaf commands are a default route in practice, so the deliberate work is
**one route on each liaison** plus forwarding. That is a small enough procedure
to be plausible under stress, which is what the trade's closure evidence asks
about.

## The mesh heals, the configuration does not

**Read this section carefully, because the short version is misleading.** An
earlier draft led with "restoration is not automatic", which reads as the mesh
failing to heal. It does not fail. Every wireless and mesh layer recovers on its
own, and a static route typed by hand does not come back, which is a different
kind of problem with a different owner.

Taking the incident bearer down stops cross-deployment traffic immediately, and
**each deployment is entirely unaffected**: `A2 -> A1` stays at 0% loss
throughout. Reversibility, which the trade asks for, holds.

Bringing it back up does not restore end-to-end traffic: measured twice with a
45-second bound, `not within 45s` both times. **The reason is not the mesh.**
After the bounce:

```text
wlan1 802.11s peers  : 1        A1 bat1 originators : 1
A1 -> B1 (10.99.0.2) : 0% packet loss
A1 route to 10.42.0.5: RTNETLINK answers: Network is unreachable
```

**802.11s re-peered, `batman-adv` reconverged, and the two liaisons pass
traffic to each other at zero loss.** The mesh healed. What is missing is one
route.

The kernel removes a static route whose next hop is on a downed interface, and
bringing the interface back restores only the connected `/24`. That is ordinary
documented behaviour, not a fault in anything here. Re-adding the single route
restored end-to-end traffic in **5 ms**.

**The outage was administrative**, an `ip link set bat1 down`, which models an
operator withdrawing the liaison rather than a radio fading, a node moving, or a
partition. Those are different events and none of them were tested.

### The design constraint this produces

**The liaison's routes must be declared, not typed.** This is a configuration
management finding, not a networking one. An operator who types `ip route add`
has a mechanism that works until the first bearer interruption and then fails
silently, with a healed mesh, a reachable next hop, and no traffic.
`FML-ADR-059` already puts link configuration under `systemd-networkd`, where a
route in a `.network` file is reinstalled when carrier returns. That decision
was made for bring-up ordering; this is a second
reason for it, and it applies to whatever mechanism `TBR-NET-03` selects.

## Identical prefixes defeat it, in two independent ways

**This is not a finding about IP.** With distinct prefixes IP carried traffic
end to end across two deployments and two routing hops, both directions, at 0%
loss, as the top of this artifact records. What follows is the ordinary
requirement that address space be unique within a routing domain, which every IP
network has. It is recorded here because `TBR-NET-01` has not yet decided that
deployments differ, and until it does, two deployments can hold the same
prefix.

The trade claims a routing liaison cannot work while both deployments hold the
same prefix. Tested with both deployments on `10.41.0.0/16`.

**The route cannot be installed.** A1 already has `10.41.0.0/16` on `bat0`:

```text
ip route add 10.41.0.0/16 via 10.99.0.2
  -> exit 2: RTNETLINK answers: File exists
```

**And there is no address that names the other deployment.** A2 and B2 are both
`10.41.0.5/16` -- the same string. When A2 pings `10.41.0.5`:

```text
64 bytes from 10.41.0.5: icmp_seq=1 ttl=64 time=0.031 ms
A2 neigh for 10.41.0.5 : (none)
A2 bat0 MAC = e6:b5:fd:61:4b:8b     B2 bat0 MAC = be:ee:55:96:79:5f
```

It answers in 31 microseconds with no neighbour entry, because it is talking to
itself. `10.41.0.1` likewise names both liaisons at once.

This is stronger than the trade states. The trade says two interfaces in the
same subnet cannot be routed between, which is true and is the first failure.
The second is that **the address space provides no way to express "the other
deployment's node"**, so the request cannot be formed even before routing is
considered. Any mechanism that keeps a fixed prefix fails at naming, not only at
forwarding.

## What this does not establish

**Nothing about the trust boundary**, which is the liaison's real cost. This
shows a liaison can forward; it says nothing about what it should be permitted
to forward, who authorises one, or what a compromised liaison reaches. The trade
lists that as its own closure-evidence item and it is not supplied here.

**No RF.** `hwsim` has no medium. Three meshes on three channels here contend
for nothing; in reality the liaison's second radio is a real cost that
`TBR-RF-03` owns, and no node on the BOM has been shown to have a spare.

**One node per deployment behind each liaison, one bearer each, no services.**
No access point, no EUD, no TAK server, no Meshtastic. Whether a TAK server
federates across a routed boundary, which is the thing an operator would
actually want, is untested and belongs to `TBR-TAK-01`.

**Static routes only.** No routing protocol was run. Two deployments that both
already run one would interact in ways not examined here.

**Restoration was measured on a clean bounce**, an administrative interface
down and up. A real radio failure, a moving node or a partition are different
events and were not tested.
