# The EUD code has to be unique to everyone who can hear the channel

**Trade:** `TBR-NET-02`.
**Date:** 2026-08-30.
**Taken by:** Cameron Zobrist, on the lab development machine.
**Status of this artifact:** analysis. It combines two results already recorded
and adds no measurement of its own.

## The question behind it

An EUD on the far side of a Meshtastic hop needs some code for its device
before a message can reach it, whether the operator reads it in ATAK or in a
browser on the local LAN. `2026-08-29-addressing-specification.md` selected that
code: **a one-byte index**, costed at 0.4% of the payload against a callsign
string's 3.4%.

That specification says, at the point where it selects the index:

> The index is allocated **per deployment** in the mission package.

Per deployment is the assumption this artifact examines, and on the LoRa bearer
it does not hold.

## Why it does not hold

`docs/evidence/TBR-NET-03/2026-08-30-what-happens-with-no-configuration.md`
establishes from the Meshtastic firmware source that two stock deployments share
a channel without anyone configuring anything: `initDefaultChannel` sets a
one-byte key of value 1 and an empty name, `getKey` expands that to a
compiled-in constant, and `generateHash` derives the channel from the name and
the key. The firmware's own comment calls that key the `public` default channel
that all devices power up on.

So on LoRa, "per deployment" is not a boundary that exists by default. **Two
deployments that have never met, never agreed anything, and never intended to
interoperate are on one channel and decrypt each other's traffic.**

## What that does to a one-byte index

Both deployments allocate indices from their own mission packages, and both
start at the low end. CONOPS section 6 plans four to eight EUDs per MULE, so a
deployment's members occupy roughly indices 1 to 8.

**The collision is not a risk, it is the expected case.** Two deployments of
eight members each, both numbering from 1, overlap on every index either of them
uses.

And the failure is worse than the addressing collision in
`docs/evidence/TBR-NET-01/2026-08-30-collision-exercise.md`. That one loses
traffic, which is at least visible as loss. This one **delivers**: a receiving
gateway reads index 3, resolves it against its own table, finds a real member of
its own deployment, and hands the message to them. A message intended for one
volunteer is delivered to a different volunteer in another organization, and
both ends believe it worked.

### The unresolved-recipient rule does not catch it

`2026-08-29-addressing-specification.md` has a fail-closed rule for a node that
**cannot** resolve the intended member, written so that a node does not fall
back to delivering to everybody.

That rule never fires here. Nothing is unresolved. The index resolves cleanly to
the wrong person, so the protection built for this class of problem is blind to
its most likely instance. **A rule that catches unknown identifiers does not
catch identifiers that are known and wrong.**

## This is a new argument for the option the trade already had

`2026-08-30-opentakserver-meshtastic-path.md` frames the open decision as:

1. Use upstream's `Contact.callsign` and `GeoChat.to`. More airtime, no custom
   encoding, consistent with `FML-ADR-048`.
2. Keep the one-byte index, which needs an ADR against `FML-ADR-048`.

The airtime comparison was 3.4% against 0.4%. **The comparison above is not
about airtime.** A callsign is a string chosen by an organization; two
deployments collide only if they pick the same string, and if they do it is
visible to an operator as two people with one callsign. A one-byte index drawn
from a 255-value space that every deployment numbers from 1 collides by
construction, and collides invisibly.

That does not decide the trade. It adds a consideration the trade did not have,
and it moves in the opposite direction to the airtime figure that was the main
argument for the index.

## What would make the index safe, and what each costs

Recorded as options, not as a selection.

- **Separate the deployments on LoRa**, by setting a channel name and key rather
  than shipping the default. Then "per deployment" is true and the index is
  sound. It also removes the ability to hear another deployment at all, which
  is the `TBR-NET-03` question and is a decision with its own consequences.
- **Scope the index**, by carrying a deployment discriminator beside it. That is
  more bytes, which was the whole argument for the index, and it re-opens the
  costing.
- **Use a string identifier** and accept the airtime.

## What this does not establish

**No measurement.** Nothing here was run. It combines the firmware reading in
`TBR-NET-03` with the specification's own statement that the index is allocated
per deployment, and draws the consequence.

**Not tested with two deployments on one channel.** `test/flatsat/` builds one
node, and the empirical half of `TBR-NET-02` still does not exist: nothing
anywhere exercises an EUD behind one MULE reaching an EUD behind another, let
alone two deployments doing it at once. `TBR-RF-02` is blocked on a second
SX1262 and that purchase would let this be demonstrated rather than reasoned.

**Nothing about what ATAK or a browser does** with a message that arrives for
the wrong member. The claim here is that the gateway resolves and delivers it;
what the receiving application then shows an operator is untested.

**The `Contact.callsign` path is still untested.** `2026-08-30-opentakserver-meshtastic-path.md`
records that `GeoChat.to`'s actual contents need a running OpenTAKServer to
confirm, and that remains true.
