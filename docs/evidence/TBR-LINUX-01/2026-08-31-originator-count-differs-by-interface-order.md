# Why two nodes on one mesh report different originator counts

**Trade:** `TBR-LINUX-01`.
**Date:** 2026-08-31.
**Taken by:** Cameron Zobrist, on the lab development machine.
**Status of this artifact:** `SIMULATED`. Four `mac80211_hwsim` radios in
network namespaces. **No radio was involved.**

## The loose end this closes

The commit adding a reverse-direction leg to `test/bench/80211s-mesh.sh`
recorded an observation it did not chase:

> The originator tables are asymmetric: node 3 lists all three of the other hard
> interfaces, node 1 lists two and never learns node 2's second radio. TQ
> differs per direction, 24 one way and 29 the other. Traffic is unaffected
> [...] and nothing here establishes whether that asymmetry is expected
> `batman-adv` behaviour or worth an investigation.

It is expected behaviour. **Nothing is dropped and nothing is missing.**

## The line topology, and what each node reports

Node 1 on segment a, node 3 on segment b, node 2 carrying a radio on each and
joining both into one `bat0`. That is the `FML-ADR-045` shape.

Sampled for 60 seconds: node 1 reports **2** originators throughout and node 3
reports **3**. It never converges to a common number, because it is not
converging towards one.

## The cause: `MainIF` is the first interface added

`batman-adv` designates the first hard interface added to a `batadv` interface
as `MainIF`. Its MAC becomes the node's originator address and is announced on
**every** interface the node holds. A secondary interface additionally appears
as an originator in its own right, but only to neighbours on its own segment,
because that is the only segment its own frames reach.

So a neighbour on the `MainIF`'s segment sees the multi-radio node as **one**
originator, and a neighbour on the far segment sees **two**: the secondary
radio directly, plus the main address reachable through it.

## Proven by reversing it

If the cause is the add order, swapping which radio node 2 adds first must swap
which neighbour sees the extra entry. It does:

```text
node 2 adds wlan1 first -> MainIF wlan1 | node1 sees 2, node3 sees 3 | 0% loss both ways
node 2 adds wlan2 first -> MainIF wlan2 | node1 sees 3, node3 sees 2 | 0% loss both ways
```

`wlan1` is on node 1's segment and `wlan2` is on node 3's. The count follows the
`MainIF`, and traffic is unaffected in both configurations.

## It is bookkeeping, not reachability

The originator table records which radio a frame should leave by. It is not a
list of reachable hosts, and the extra entry is not a host:

```text
node 2, every addressed interface:
  bat0 10.41.0.2/16
```

Node 2's radios carry no IP address at all. `bat0` is the only addressed
interface, so the originator a neighbour cannot see is not an endpoint anyone
could have addressed. Traffic to every node was 0% loss in every configuration
tested.

## Why this is worth writing down anyway

**An operator comparing `batctl originators` between two nodes will legitimately
get different counts, and the difference is not a fault.** Every failure this
program has recorded on the mesh so far presents as a radio problem, and a
mismatch in a diagnostic table is exactly the kind of thing that sends somebody
to the antenna. It is recorded so the next person reads it as normal.

**And `MainIF` depends on interface add order, which nothing currently fixes.**
`os/config/networkd.conf.template` does not constrain which bearer a
multi-bearer node adds first, and `systemd-networkd` need not bring links up in
a stable order. A node's originator address may therefore differ between boots.

That is **not** proposed as a defect to fix here. Traffic is unaffected, and
`mule/bringup.py` deliberately holds only constraints with evidence behind them;
adding one that no measurement supports is the failure that module's own
comments warn against. It is a consequence to be aware of if a future diagnostic
or configuration ever assumes the originator address is stable.

## What this does not establish

**The TQ asymmetry is not explained.** The same observation recorded 24 one way
and 29 the other between the same pair. Per-direction link quality is normal in
`BATMAN_IV`, which measures each direction separately, but nothing here checks
whether that spread is expected on a lossless simulated medium or is an
artefact of `mac80211_hwsim`. It was not chased and no traffic result depended
on it.

**`hwsim` only.** Whether a real driver reports interfaces to `batman-adv` in
the same way is untested, and `TBR-LINUX-01` is where that question lives.

**Two segments and one multi-radio node.** A node with three bearers, or two
multi-radio nodes, were not tried.
