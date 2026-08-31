# What happens when two deployments meet using different prefixes

**Trade:** `TBR-NET-01`.
**Date:** 2026-08-30.
**Taken by:** Cameron Zobrist, on the lab development machine.
**Status of this artifact:** `SIMULATED`. Four `mac80211_hwsim` radios in
network namespaces. **No radio was involved.**

## Why this exists

`2026-08-30-collision-exercise.md` showed what two deployments do when they
share `10.41.0.0/16`. It ended by saying what it had not shown:

> **Not tested: what happens with different prefixes.** The exercise shows
> collision; it does not show that non-colliding deployments interoperate,
> which is the other half of the closure gate's wording, and is a separate run.

This is that run. The gate asks whether two independently built deployments
"must be able to interoperate **or at least coexist**". Those turn out to be
two different outcomes, and distinct prefixes buy exactly one of them.

## The exercise

Four nodes, one 802.11s mesh, `batman-adv` over it, as two deployments that
chose different prefixes:

| Node | Stands for | Address |
| --- | --- | --- |
| A1 | Deployment A | `10.41.0.1/16` |
| A2 | Deployment A | `10.41.0.5/16` |
| B1 | Deployment B, which chose another prefix | `10.42.0.1/16` |
| B2 | Deployment B | `10.42.0.5/16` |

**The premise, which this exercise assumed rather than established.** Both
deployments are on **one 802.11s mesh**, sharing a mesh identifier. The bench
was built that way and the choice was mine.
`mission/schema/mission-package.schema.json` says network identity values
"differ between deployments so that two independently built deployments meeting
at an incident do not collide", and `mesh_id` is a required field of that
object. So this is **not what happens when two deployments meet**. It is what
happens once they have deliberately converged on one mesh identifier, which is
the only way the architecture lets them cooperate. See
`2026-08-30-mesh-id-separates-deployments.md`, which tests the default case and
shows that with different `mesh_id` identical addressing is harmless.

## They coexist, and they do not interoperate

**Coexistence is free and complete.** All four nodes join one mesh and stay
there. From B1: three 802.11s peers, three `batman-adv` originators, the whole
mesh. Neither deployment degrades the other, and nothing has to be configured
for that to be true. They share the airtime and the routing plane.

**Interoperation does not happen at all**, and it fails earlier than the
colliding case did:

```text
A1 -> 10.42.0.1:  ping: connect: Network is unreachable   (exit 2)
A1 routing table: 10.41.0.0/16 dev bat0 proto kernel scope link src 10.41.0.1
```

No packet leaves. There is no route, because a `/16` on `bat0` gives a node an
on-link route for its own prefix and nothing else. This is the opposite failure
mode to the collision, and it is the better one: **it is loud, immediate, local,
and it says what is wrong.** The colliding case reported a `REACHABLE`
neighbour and lost the traffic silently.

## ATAK situational awareness does not cross either, and the reason is not obvious

Multicast is the case worth testing separately, because ATAK's situational
awareness is multicast and multicast does not need a unicast route. Two
deployments on one layer-2 mesh might therefore see each other's contacts
appear while being unable to message them, which would be a confusing state to
put an operator in.

They do not. A datagram to `239.2.3.1:6969` sent by A1 is **not received** by
B1, while the same send is received by A2 on the same prefix.

`batman-adv` is not what drops it. The receiving kernel does, under reverse
path filtering:

```text
receiver bat0 rp_filter = 2
  cross-prefix, nothing changed                      NOTHING RECEIVED in 12s
  cross-prefix, rp_filter set to 0                   RECEIVED from 10.41.0.1
```

`rp_filter = 2` is loose mode: accept a datagram only if its source is
reachable through *some* interface. Deployment B has no route to
`10.41.0.0/16`, so A1's source address is unreachable and the datagram is
discarded before any application sees it.

**This is a Debian default and it will be on every MULE node.** It is shipped
by the `linux-sysctl-defaults` package in
`/usr/lib/sysctl.d/50-default.conf`:

```text
# Source route verification
net.ipv4.conf.default.rp_filter = 2
net.ipv4.conf.*.rp_filter = 2
-net.ipv4.conf.all.rp_filter
```

A fresh network namespace inherits `default = 2` with `all = 0`, measured, and
the effective value is the larger of the two. A `bat0` created inside one
therefore comes up at `2` without anyone choosing it.

## One route, not a renumber, and not disabling the filter

The fix is not to turn `rp_filter` off. Adding a single on-link route on each
side restores unicast **and** multicast with `rp_filter` left at `2`:

```text
ip route add 10.42.0.0/16 dev bat0        # on deployment A
ip route add 10.41.0.0/16 dev bat0        # on deployment B

A1 -> 10.42.0.1: 3 packets transmitted, 3 received, 0% packet loss
cross-prefix multicast, ONE route back, rp_filter untouched: RECEIVED
```

Both deployments already share the layer-2 mesh, so the route is on-link and
needs no gateway, no routing protocol and no renumbering. Interoperation
between distinct prefixes costs one command per side.

## What this argues, without deciding it

Together with the collision artifact, the two runs say the same thing from
opposite directions. A shared prefix makes collision the default and
interoperation impossible to distinguish from failure. Distinct prefixes make
collision impossible, coexistence automatic, and interoperation a deliberate
act that either succeeds or reports `Network is unreachable`.

That is an argument about **which failure an operator can act on**, not a
decision. Choosing distinct prefixes means deciding how two deployments come to
differ, which is the trade's actual question and is constrained by
`THREAT_MODEL.md`: an address derived from a durable node identifier is itself
a durable identifier. Nothing here chooses a mechanism.

## A correction: the bench was running against FML-ADR-056

The first draft of this artifact reported a fixed 31 s window after mesh
formation during which nothing crossed, said the mechanism was unidentified
after three refuted hypotheses, and suggested it might be an artefact of
`mac80211_hwsim` needing re-measurement on real radios.

**All of that was wrong, and the answer was already in this repository.**

The lab left `bridge_loop_avoidance` at its default, which is **enabled**.
`FML-ADR-056` disables it and `os/config/batman-adv.conf.template` configures
it off. Until its claim mechanism settles, `batman-adv` withholds client frames
while every `batctl` table already reads correct, which is exactly the symptom
observed: the neighbour list, the originator table and the global translation
table all populated at 1.2--2.4 s, and no traffic for another 29 s.

One variable, a fresh mesh per value:

| Configuration | Distinct prefixes | Colliding prefixes |
| --- | --- | --- |
| `bridge_loop_avoidance` default (enabled) | 30972 ms | 30973 ms |
| `bridge_loop_avoidance 0` (`FML-ADR-056`) | 2056 ms | 2051 ms |

`.github/workflows/mesh-probe.yml` measured the same effect on `veth` before
this run and recorded it in a comment: *"31.5s to first reply against 2.150s
with it off, one variable, a fresh mesh per value"*. The number in the draft
matched to three significant figures and was not recognised.

**A MULE node does not have this window.** Every measurement above and below
was re-taken with `bridge_loop_avoidance 0`, and the results in this artifact
are from those runs.

Two things were fixed rather than described:

- `test/bench/80211s-mesh.sh` omitted the setting from the day it was written.
  It now sets it, and `tools/validate-docs.sh` check 20 fails any script that
  creates a `batadv` interface without naming it.
- `2026-08-30-collision-exercise.md` described the same window as a transient
  belonging to the collision. It has been corrected.

## What this does not establish

**The mechanism behind the 31 s window is unidentified.** Three hypotheses were
tested and refuted; the residue is unexplained. It is `SIMULATED` and may be an
artefact of `mac80211_hwsim` rather than anything a real radio does. If it is
real it matters a great deal to an operator, because a node that is silent for
half a minute after the mesh forms looks broken, and the collision artifact's
"transient" is this window. **It should be re-measured the first time two real
radios are available**, and it is not a reason to change anything until then.

**The collision analysis over expected external networks is still missing.**
That is the first of the trade's three closure items and neither exercise
touches it. It is desk work against the parent Homelab prefixes and the ranges
partner organisations use, not a bench run.

**Nothing here was done with a real 802.11 driver, and no ATAK client was
involved.** The multicast result uses ATAK's group and port with a plain UDP
socket. It shows what the kernel does with the datagram, which is where the
failure is; it does not show what a client does with the result.
