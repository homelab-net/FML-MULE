# A bridging loop, deliberately created and detected

**Trade:** `TBR-NET-01`, and it discharges the verification `FML-ADR-056`
deferred.
**Date:** 2026-08-30.
**Taken by:** Cameron Zobrist, on the lab development machine.
**Status of this artifact:** `SIMULATED`. Two `mac80211_hwsim` radios and a
`veth` pair. **No radio was involved.**

## What this discharges

`FML-ADR-056` disables `batman-adv`'s bridge loop avoidance, accepts the risk
structurally, and says of its verification:

> The structural rule is checked by `tools/validate-docs.sh`, which reads
> configuration rather than behaviour, and that is the weaker half. The
> stronger half is a loop that is deliberately created and then detected,
> which needs two nodes and a shared segment. CONOPS section 78 stage 2 is the
> first stage with the topology to do it.

Two nodes and a shared segment no longer need Stage 2. `mac80211_hwsim`
supplies the nodes and a `veth` pair supplies the segment.

## Configuration

| Item | Value |
| --- | --- |
| Host | Debian 13, kernel `6.12.105+deb13-amd64`, `batman-adv` 2024.2 |
| Nodes | Two network namespaces, one virtual radio each |
| Mesh | 802.11s, mesh id `loop-lab`, 2412 MHz |
| Shared segment | A `veth` pair joining the two namespaces directly |
| The violation | On **both** nodes, `bat0` and the shared segment in one bridge |
| Loop avoidance | **Disabled**, which is what `FML-ADR-056` specifies |

The bridge on each node holds `bat0` and a segment the other node also
reaches. That is precisely what `FML-ADR-056` forbids, and it is built here on
purpose.

**`bridge_loop_avoidance` was `enabled` by default and had to be turned off.**
Worth recording on its own: a node built without applying the setting gets
protection the architecture says it does not have, and the loop this artifact
demonstrates would not appear.

## The loop appeared, and both signatures with it

`batctl meshif bat0 transglobal` on node 1, after traffic:

```text
[B.A.T.M.A.N. adv 2024.2, MainIF/MAC: wlan0/be:bb:69:03:ea:92
                                      (bat0/56:44:6e:89:4d:94 BATMAN_IV)]
   Client             VID Flags Last ttvn     Via        ttvn
 * 56:44:6e:89:4d:94   -1 [R...] (  5) 1e:fa:23:ea:fb:69 (  5)
 * 32:ce:c9:96:a5:04   -1 [R...] (  5) 1e:fa:23:ea:fb:69 (  5)
 * 32:ce:c9:96:a5:04    1 [....] (  5) 1e:fa:23:ea:fb:69 (  5)
 * be:bb:69:03:ea:92   -1 [....] (  5) 1e:fa:23:ea:fb:69 (  5)
```

Node 1's own addresses were `wlan0 be:bb:69:03:ea:92` and
`bat0`/`br-field 56:44:6e:89:4d:94`. **Both appear as clients, announced by
the peer originator `1e:fa:23:ea:fb:69`.** Frames left node 1 and came back
through the mesh, which is the loop.

## The finding: the ADR names the address that arrives second

`FML-ADR-056` names "the node's own **bridge** address arriving from the mesh".

An earlier reading of the same table, taken before the one above, held
`be:bb:69:03:ea:92` and **not** `56:44:6e:89:4d:94`. The **mesh hard
interface's** address arrived first; the bridge address followed.

Both arrive, so a detector watching only the bridge address does **not miss**
this loop. It reports it later. On a bearer where a loop is a broadcast storm
across a low-rate mesh, later is the thing being traded.

`mule/loops.py` was written to the ADR's wording and watched only the bridge.
It now takes every address the node owns. The ADR's wording is not wrong, it
is narrower than the phenomenon, and this artifact is the record of that rather
than an edit to a `SELECTED` decision.

## What this does not establish

Not an RF result. The mesh is `hwsim` and the shared segment is `veth`: no
propagation, and a loop's real cost is airtime on a bearer this has none of.

**Nothing measured how bad the loop was.** No throughput figure, no broadcast
rate, no time-to-degradation. The artifact shows the signature appears, not
what the loop costs, and `FML-ADR-056`'s accepted cost is about the latter.

Two nodes only. Whether a larger mesh produces the signatures sooner, later or
differently is untested.
