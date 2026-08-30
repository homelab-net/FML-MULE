---
id: FML-ADR-059
title: Link configuration is owned by systemd-networkd and nothing else reconfigures a link
status: SELECTED
date: 2026-08-30
supersedes: none
superseded-by: none
trades: [TBR-LINUX-01, TBR-NET-01, TBR-RF-01]
verification: Stage 2
---

# FML-ADR-059 Link configuration is owned by systemd-networkd and nothing else reconfigures a link

## Context

`os/config/interfaces.conf.template` says the network management stack is
`TBD`, and it has been the blocker on two roadmap items rather than one.
`docs/ROADMAP-DEV.md` item 1.2 asks for the bring-up ordering as systemd units,
and item 1.1 step 4 asks for configuration templates. Neither can be written
without saying who owns link configuration, and `docs/ROADMAP-DEV.md` records
that writing units against `ip` and `batctl` directly is not a way around the
question: choosing direct commands over a managed stack is the same decision
taken quietly.

The ordering itself is already settled and is not what this decides.
`mule/bringup.py` holds it, transcribed from the template and from
`.github/workflows/mesh-probe.yml`: driver, link up, association, routing
algorithm, hard interface MTU, add to the mesh, mesh interface up and
addressed, services. What is open is which component is allowed to act on a
link.

**The failure this is really about.** `batman-adv` attached to an interface
that is not yet up fails in a way that looks like a radio fault. A node whose
link is reconfigured underneath it, by something helpful, presents the same
way: not as "something reconfigured your link" but as a radio that appears
broken to a volunteer in a car park with no console. The property that matters
is therefore not ergonomics. It is that **nothing touches a link except the
node's own sequence**.

Two constraints narrow the field before preference enters.

**No general network manager performs the associations this program needs.**
802.11s mesh point association is `wpa_supplicant`'s, and the access point is
`hostapd`'s. Neither `systemd-networkd` nor `ifupdown` does either, and any
option therefore keeps both.

**`systemd-networkd` does attach an interface to `batman-adv`, and more.** An
earlier draft of this ADR said it did not, and that was wrong. Checked against
systemd 257, which is what Debian 13 ships: `.netdev` supports `Kind=batadv`
with a `[BatmanAdvanced]` section carrying `RoutingAlgorithm=`,
`BridgeLoopAvoidance=`, `Fragmentation=`, `HopPenalty=`,
`DistributedArpTable=`, `GatewayMode=` and `OriginatorIntervalSec=`, and
`.network` carries `BatmanAdvanced=` to add a member link.

That covers more of the sequence than the alternatives were being judged
against. `RoutingAlgorithm=` is the `FML-ADR-053` constraint and
`BridgeLoopAvoidance=` is the `FML-ADR-056` one, both expressible where the
interface is defined rather than in a script that has to run at the right
moment.

So the decision is narrower than it first appears, but not in the direction the
earlier draft claimed. It is **which component owns link state, addressing and
mesh attachment**, given that association is handled beside it whatever the
answer.

The alternatives were four.

**NetworkManager.** Rejected on the property above rather than on taste. Its
value is automatic management: it brings links up, retries, and reconfigures
when it judges it should. On an appliance whose bring-up order is load-bearing,
an automatic manager is an actor with opinions about a link the node has
deliberately configured, and the failure mode is the one that reads as a radio
fault. Turning that behaviour off leaves a large component doing very little.

**`ifupdown`.** Credible, and this was the close one. It is Debian's
traditional stack, its `pre-up` and `post-up` hooks express ordering
imperatively and legibly, and much of the published `batman-adv` configuration
in the wild is written against it. It was not selected because its ordering is
internal to itself: `systemd` cannot see it, so the dependency between a link
being up and a service that needs the mesh cannot be expressed where the rest
of this node's ordering already lives.

**Plain systemd units calling `ip` directly.** Total control and no abstraction
to fight. Rejected because it is a network stack this program would then
maintain, in shell, on a system that already ships one, and `FML-ADR-040`
counts every such thing as part of the compatibility set a volunteer keeps
working.

**`systemd-networkd`.** Selected. Its configuration is declarative and static:
it does what its files say and does not form opinions. Its ordering is
`systemd` ordering, which is where `FML-ADR-029` has already put this node's
service execution, so a unit that must run after a link is up can say so in the
same vocabulary as everything else. It configures a bridge and an address on
`bat0` once `batctl` has created it, which is the part of the sequence a
manager can usefully own.

## Decision

`systemd-networkd` **shall** own link configuration and addressing on the node.

Association **shall** remain with `wpa_supplicant` for 802.11s mesh point and
station, and with `hostapd` for the access point, because no link configuration
component performs either.

Attachment to `batman-adv` **shall** be expressed in `networkd` configuration,
using `Kind=batadv` with `RoutingAlgorithm=` and `BridgeLoopAvoidance=` on the
netdev and `BatmanAdvanced=` on the member link. `batctl` **may** be used for
inspection and for anything `networkd` cannot express, and **should not** be
the mechanism where `networkd` can.

**Nothing else shall reconfigure a link.** NetworkManager and `ifupdown`
**shall not** be installed in the image. A node **shall not** carry two
components able to act on the same interface, whatever their configuration
says, because the failure that produces is diagnosed at the antenna.

The bring-up ordering is **not** decided here. It is `mule/bringup.py`, and
this decision only fixes what expresses it.

## Status

`SELECTED`. Accepted by the Program Owner on 2026-08-30.

Implementation depends on it: `docs/ROADMAP-DEV.md` item 1.2's units and item
1.1 step 4's configuration templates are both written against it, and changing
where link configuration lives now requires a superseding ADR.

**It was accepted as a structural choice made ahead of the hardware that would
test it**, and that is recorded rather than smoothed over. No interface has
been brought up by any of these components on a MULE, because no MULE exists.
The evidence behind the reasoning is a three-node mesh in network namespaces
and two adapters on a bench.

A reviewer who has run `batman-adv` on Debian in the field is still better
placed than this document to say whether the `ifupdown` argument should have
won. The fallback below is the route if they are right.

## Consequences

Ordering becomes expressible in one vocabulary. The dependency between a
service and the mesh being up is a `systemd` dependency, alongside the
`FML-ADR-029` quadlets, rather than split between a network stack's own
sequencing and `systemd`'s.

The node carries three components that touch the network rather than one:
`systemd-networkd`, `wpa_supplicant` and `hostapd`. The `batctl` unit an
earlier draft assumed is not needed for attachment.

**The rule in the decision is therefore stronger than the component can
enforce, and that is worth saying plainly.** "Nothing else reconfigures a link"
bans NetworkManager and `ifupdown` while keeping two components that do touch
links. `wpa_supplicant` creates and associates the mesh point; `hostapd` runs
the access point. The rule means no *second general manager*, not literally one
actor, and a reader who takes it literally will find two counter-examples in
the same decision.

What becomes harder, and this is the real cost of the choice. **The ordering
stops being something the node performs and becomes something a component
resolves.** `mule/bringup.py` states an order; `networkd` reaches an
equivalent end state by its own dependency resolution and does not report the
order it used. The wireless half is still outside it, because `networkd` does
not create an 802.11s mesh point interface, so the dependency between
`wpa_supplicant` having associated and `networkd` attaching that link to the
mesh has to be expressed as a unit ordering and can be got wrong silently.

That is the same failure this decision exists to prevent, moved rather than
removed: `batman-adv` attached to an interface that is not yet up presents as a
radio fault, and a declarative component that resolves ordering internally is
harder to catch doing it than a script that ran in the wrong sequence.

**Correction, 2026-08-30, added as a consequence that was always true rather
than as a change of decision.** The paragraph above overstates the seam.
`systemd.network(5)` on `ConfigureWithoutCarrier=`: "Allows systemd-networkd to
configure a specific link even if it has no carrier. **Defaults to false.**"

`networkd` therefore already waits, and `BatmanAdvanced=` does not apply to an
interface with no carrier. The dependency between `wpa_supplicant` having
associated and `networkd` attaching the link is enforced by the component's own
default, not by a unit ordering somebody has to remember. What the units carry
instead is a setting **not** to change: `ConfigureWithoutCarrier=true` on a
mesh member turns the hazard back on, and it is exactly what someone debugging
a link that is slow to come up would reach for.

This makes the decision better than it was argued, which is worth recording
because the argument was made without checking and happened to land right.

**Verified 2026-08-30**, and it did not need Stage 2. On `mac80211_hwsim`, a
mesh point interface reports `carrier 0` while up but unjoined and `carrier 1`
after joining, so the gating this consequence depends on is real. The same run
carried IP traffic over `batman-adv` across an 802.11s mesh with no radio. See
`docs/evidence/TBR-LINUX-01/2026-08-30-80211s-mesh-in-software.md`.

What remains open is narrower than what this paragraph originally claimed:
whether a **real** driver asserts carrier at the same point. `mac80211_hwsim`
is `mac80211`'s own simulator and a vendor driver may differ. That is the thing
to check on the first board, and it takes one command each side of a join.

Published `batman-adv` configuration will mostly not apply. The community's
worked examples are largely `ifupdown`, and `FML-ADR-023` records that the
upstream MANET reference project encodes real knowledge about bring-up
ordering. Adopting its configuration now means translating it, and the
translation is where a subtle ordering constraint gets lost.

Nothing here decides an interface name or an address. Naming is
`TBR-LINUX-01`, addressing is `TBR-NET-01`, and both are open. This decision
constrains the mechanism only.

## Accepted cost

**The stack is chosen before anything has run on the hardware that would test
it.** That is the specific thing someone will later argue was a mistake, and
the argument will be that `ifupdown` would have let the program adopt the
upstream reference project's configuration directly instead of translating it.

The counter-argument is that the alternative was not "decide later". It was
two roadmap items blocked on a question nobody was going to answer without
being made to, and a template that has said `TBD` since it was written. A
decision that can be superseded on evidence is worth more than a gap that
blocks work, provided the gap is what is actually blocking, which here it is.

Second cost, smaller: `systemd-networkd` is not Debian's default on a stock
install, so the image build carries an explicit choice and an explicit
disabling of what would otherwise manage the link. That is a line in the image
manifest and a thing to get wrong once.

**Third, and the one most likely to be regretted:** the `batman-adv` settings
that make this choice attractive are version-gated in `systemd`.
`BatmanAdvanced=` arrived in one version, the `[BatmanAdvanced]` keys in
others. This binds part of the network plane's configurability to the `systemd`
version a Debian release happens to ship, which puts `systemd` into the
compatibility set `FML-ADR-040` governs in a way `ifupdown` would not have.
A release that ships an older `systemd` loses settings the configuration
depends on, and the failure is at image build rather than in the field, which
is the better end to fail at but is still a coupling taken on deliberately.

**Fourth: reversal is bounded only while the coupling stays in units.** If
configuration generation grows `networkd`-shaped templates fed by region
profiles, the choice spreads from a handful of unit files into
`tools/gen-config.py` and the generation mechanism, and "rewrite the units"
stops describing the cost. Whoever writes that generator should keep the
`networkd` shape at the edge of it.

## Fallback

Supersede with `ifupdown` if translating the upstream reference configuration
proves to lose ordering constraints in practice, which is the signal to watch
for and is observable during Stage 2 rather than after deployment. The cost is
rewriting the units, which is bounded: the ordering they express is
`mule/bringup.py` and does not change with the stack.

If the objection instead turns out to be that `systemd-networkd` cannot express
some part of the sequence at all, the fallback is a unit calling `ip` for that
step specifically, not a wholesale move.

## Superseded by

None.

## Verification dependency

Stage 2. The stage brings up multiple nodes and forms a mesh, and it is the
first point at which a bring-up sequence runs on hardware rather than in
namespaces.

The specific thing to verify is not that the links come up. It is that they
come up **in the order `mule/bringup.py` states**, and that nothing
reconfigures them afterwards. A mesh that forms is not evidence for this
decision; a mesh that forms after a link was reconfigured underneath it would
have looked the same on the day and failed later.
