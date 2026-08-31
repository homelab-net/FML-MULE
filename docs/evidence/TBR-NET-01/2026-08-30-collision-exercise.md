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

## What actually happens

**They do not fail. They conflict silently.**

**CORRECTED 2026-08-30.** The first version of this section reported a long
unreachable window immediately after mesh formation and called it a transient
belonging to the collision. It was not. The bench left `bridge_loop_avoidance`
at its default, which is **enabled**, against `FML-ADR-056`. That withholds
client frames for about thirty seconds while every `batctl` table already reads
correct. The exercise was re-run in the configuration a MULE node actually
ships, and the numbers below are from those runs. See
`2026-08-30-distinct-prefix-exercise.md`.

**There is no meaningful transient.** With `bridge_loop_avoidance 0`, node C
reaches `.1` 2.04 s after the interfaces come up, in three independent mesh
builds (2045, 2038, 2045 ms). Nothing here is a wait-and-see state.

**And it works, which is the problem.** ARP resolves to one MAC and stays
there: five flush-and-retry cycles resolve to the same deployment every time.
The other deployment's node is simply **not there** as far as C is concerned,
consistently.

**Which deployment wins is arbitrary.** It is stable within one mesh but not
across builds -- deployment A won the first run, deployment B won all three
re-runs. So the surviving node is not the earlier, the lower-addressed or the
first-configured one, and an operator cannot predict which of the two will
vanish.

The losing deployment's view is the part worth reading twice. From the run
below, deployment A lost:

```text
loser -> C:  10 packets transmitted, 0 received, 100% packet loss, time 9205ms

loser's neighbour table, read 3s later:
  10.41.0.5 dev bat0 lladdr a2:19:e4:f2:1f:f7 REACHABLE

winner -> C:  0% packet loss
```

**The loser resolves C, marks it `REACHABLE`, and cannot talk to it.** Its
replies go out; C's answers go to the deployment that won. Ten packets over
nine seconds, so this is not a warm-up. From that console the network is up,
the neighbour is healthy, and nothing works.

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

**What happens with different prefixes** is the other half of the closure
gate's wording and was a separate run: see
`2026-08-30-distinct-prefix-exercise.md`. In short, distinct prefixes coexist
completely and do not interoperate at all, failing loudly at the sender rather
than silently in flight.

**Why the loser's traffic is lost is not established here.** The observation is
that it is: 100% loss to a neighbour its own table calls reachable, with
nothing logged. The mechanism inside `batman-adv`'s translation table was not
traced, and tracing it would not change what an operator sees.
