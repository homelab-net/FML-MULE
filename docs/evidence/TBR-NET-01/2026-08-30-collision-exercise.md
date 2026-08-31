# What happens when two deployments meet using the same prefix

**Trade:** `TBR-NET-01`.
**Date:** 2026-08-30.
**Taken by:** Cameron Zobrist, on the lab development machine.
**Status of this artifact:** `SIMULATED`. Three `mac80211_hwsim` radios in
network namespaces. **No radio was involved.**

## What this supplies, and what it does not

`TBR-NET-01`'s closure evidence has three parts. This supplies **one of them**
and reports on a second:

1. **A collision analysis** over expected external networks. **Not here.**
2. **An interoperability exercise**: "what actually happens when two
   independently configured deployments form a mesh: whether they interoperate,
   coexist or conflict, and what an operator sees." **This is that.**
3. **Confirmation the scheme is expressible in the mission package schema.**
   Reported below, and the answer is qualified.

It closes nothing. The trade needs all three, a named owner, and an ADR.

## The exercise

Three nodes on one 802.11s mesh, `batman-adv` over it, as two deployments that
were built independently and have met at an incident:

| Node | Stands for | Address |
| --- | --- | --- |
| A | Deployment A's node | `10.41.0.1/16` |
| B | Deployment B's node, configured independently | `10.41.0.1/16` |
| C | A third node needing to reach `.1` | `10.41.0.5/16` |

Both deployments retained the `10.41.0.0/16` prefix SAD section 4.2 prefers,
and both allocated `.1`. Neither did anything wrong by its own configuration.

## What actually happens

**They do not fail. They conflict silently.**

Immediately after the mesh forms, `.1` does not resolve at all: `ip neigh`
reports `FAILED` and traffic is lost. That state is transient and misleading,
and an operator who tested at that moment would report a dead network.

**Once `batman-adv` converges, it works.** Node C reaches `.1` with no loss.
ARP resolves to one MAC and stays there: five flush-and-retry cycles all
resolved to deployment A's `bat0`. Deployment B's node is simply **not there**
as far as C is concerned, consistently.

The losing deployment's view is the part worth reading twice:

```text
B -> C:  2 packets transmitted, 0 received, 100% packet loss
B's neighbour table:  10.41.0.5 dev bat0 lladdr 4a:dd:9a:e5:a6:79 REACHABLE
```

**B resolves C, marks it `REACHABLE`, and cannot talk to it.** B's replies go
out; C's answers go to A. From B's console the network is up, the neighbour is
healthy, and nothing works.

## Nothing reports the collision

Checked, because a signal would change the operator story entirely:

- No kernel message mentioning a duplicate or a conflict.
- Nothing in `batctl transglobal`.
- Both nodes' own configuration is internally valid.

So the answer to "what does an operator see" is: **a healthy-looking neighbour
table and no connectivity, with no error anywhere to explain it.** The failure
presents as the far side being broken.

## What the mission package schema can and cannot do

`mission/schema/mission-package.schema.json` has `network.address_prefix`, a
plain `string`, with a description recording that everything about it is `TBD`
under this trade.

**It can express a prefix. It cannot prevent this.** There is no pattern, no
format, and nothing that makes two independently produced packages differ by
construction. Two deployments writing `10.41.0.0/16` both validate, which is
exactly the state demonstrated above.

That is not a defect in the schema. It is the trade, visible in the schema:
until the scheme is decided, there is nothing for the schema to enforce.

## What this argues, without deciding it

The trade already says a fixed prefix chosen once cannot work. This shows what
"cannot work" looks like in practice, and it is worse than a clash: it is a
silent one-way blackhole that presents as somebody else's fault.

Anything that makes two deployments differ **by construction** rather than by
convention would prevent it. The trade's own options are where that belongs,
along with `THREAT_MODEL.md`'s constraint that an address derived from a
durable node identifier is itself a durable identifier.

## What this does not establish

Two deployments of one node each, and a third node. Not a realistic incident.

No RF, no propagation, no partition, no mobility. `hwsim` is a MAC simulator.

**Not tested: what happens with different prefixes.** The exercise shows
collision; it does not show that non-colliding deployments interoperate, which
is the other half of the closure gate's wording and is a separate run.

Nothing here measures how long the transient unreachable state lasts, and that
number matters for an operator: it is the difference between "wait" and "this
is broken".
